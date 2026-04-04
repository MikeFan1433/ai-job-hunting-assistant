"""Agent 3: Project Packaging Agent."""
import json
import re
import httpx
from typing import Dict, Optional
from config import AI_BUILDER_BASE_URL, STUDENT_PORTAL_API_KEY, LLM_MODEL_JSON, RESPONSE_FORMAT_JSON, AGENT3_FAST_MODEL
from agent_prompts import AGENT3_PROJECT_PACKAGING_PROMPT
from json_parser_utils import parse_llm_json_response
from llm_output_language import output_language_suffix


class ProjectPackagingAgent:
    """Agent 3: Packages and optimizes projects for resume."""
    
    def __init__(self, model: str = None):
        """Initialize the project packaging agent. Uses gpt-5 by default for JSON mode (AI Builder API)."""
        model = model or LLM_MODEL_JSON
        self.base_url = AI_BUILDER_BASE_URL
        self.api_key = STUDENT_PORTAL_API_KEY
        self.model = model
        self.endpoint = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("STUDENT_PORTAL_API_KEY not set")
    
    def package_projects(
        self,
        jd_text: str,
        project_materials: str,
        agent2_outputs: Dict,
        read_timeout_sec: Optional[float] = None,
        preferred_lang: Optional[str] = "en",
    ) -> Dict:
        """
        Package and optimize projects based on JD and Agent 2 analysis.
        
        Args:
            jd_text: Job description text
            project_materials: Project materials text
            agent2_outputs: Agent 2 analysis outputs
            read_timeout_sec: Optional read timeout in seconds (e.g. 8 for fast run under 30s total). Default 180.
        
        Returns:
            Dictionary with packaged projects
        """
        # Optimize input for faster processing - only include essential Agent 2 info
        agent2_summary = {
            "job_title": agent2_outputs.get("job_role_team_analysis", {}).get("job_title", ""),
            "ideal_candidate": agent2_outputs.get("ideal_candidate_profile", {}).get("overall_experience_traits", "")[:500],  # Truncate for speed
            "hard_skills": agent2_outputs.get("ideal_candidate_profile", {}).get("hard_skills", {}).get("must_have", [])[:5]  # Only top 5
        }
        
        # Truncate inputs for faster processing
        jd_text_truncated = jd_text[:2000] if len(jd_text) > 2000 else jd_text
        project_materials_truncated = project_materials[:5000] if len(project_materials) > 5000 else project_materials
        
        # Extract key skills from Agent 2 (fallback to JD excerpt if Agent 2 output is incomplete)
        key_skills_list = []
        for s in agent2_summary.get("hard_skills", [])[:5]:
            if isinstance(s, dict):
                key_skills_list.append(s.get("skill", "") or s.get("details", ""))
            else:
                key_skills_list.append(str(s))
        key_skills_str = ', '.join(filter(None, key_skills_list))
        if not key_skills_str and jd_text:
            key_skills_str = (jd_text[:800] + "...") if len(jd_text) > 800 else jd_text
        
        user_message = f"""Please package and optimize the following projects (FAST MODE - focus on core optimization):

=== JOB DESCRIPTION ===
{jd_text_truncated}

=== PROJECT MATERIALS ===
{project_materials_truncated}

=== KEY JD REQUIREMENTS (from Agent 2) ===
Job Title: {agent2_summary.get("job_title", "")}
Key Skills: {key_skills_str}

Please provide optimized projects in the specified JSON format. Focus on the most relevant projects and provide concise but complete optimization.{output_language_suffix(preferred_lang)}"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": AGENT3_PROJECT_PACKAGING_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.2,
            "max_tokens": 2500,
        }
        if RESPONSE_FORMAT_JSON is not None:
            payload["response_format"] = RESPONSE_FORMAT_JSON
        
        read_timeout = read_timeout_sec if read_timeout_sec is not None else 180.0
        # Use fast model when caller sets a timeout (e.g. test or fast workflow) to avoid empty/slow gpt-5 response
        model = AGENT3_FAST_MODEL if read_timeout_sec is not None else self.model
        payload["model"] = model
        timeout = httpx.Timeout(read_timeout, connect=15.0)
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(self.endpoint, headers=headers, json=payload)
                
                # Check for HTTP errors
                if response.status_code != 200:
                    error_detail = f"HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", error_data.get("message", error_detail))
                    except:
                        error_detail = response.text[:200] if response.text else error_detail
                    
                    return {
                        "error": f"API request failed ({response.status_code}): {error_detail}",
                        "selected_projects": [],
                        "skipped_projects": [],
                        "http_status": response.status_code
                    }
                
                response.raise_for_status()
                result = response.json()
                
                # Check if response has expected structure
                if "choices" not in result or len(result["choices"]) == 0:
                    return {
                        "error": "Invalid API response: no choices in response",
                        "selected_projects": [],
                        "skipped_projects": []
                    }
                
                message_content = result["choices"][0]["message"].get("content")
                if message_content is None:
                    message_content = ""
                if not isinstance(message_content, str):
                    message_content = str(message_content) if message_content else ""
                if not message_content.strip():
                    return {
                        "error": "API returned empty response content",
                        "selected_projects": [],
                        "skipped_projects": []
                    }
                packaged_projects = self._parse_json_response(message_content)
                
                return packaged_projects
        
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", error_data.get("message", error_detail))
            except:
                error_detail = e.response.text[:200] if e.response.text else error_detail
            
            return {
                "error": f"API request failed ({e.response.status_code}): {error_detail}",
                "selected_projects": [],
                "skipped_projects": [],
                "http_status": e.response.status_code
            }
        except Exception as e:
            import traceback
            return {
                "error": f"Agent 3 error: {str(e)}",
                "selected_projects": [],
                "skipped_projects": [],
                "traceback": traceback.format_exc()
            }
    
    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON response from LLM using enhanced parser with structure validation."""
        try:
            parsed = parse_llm_json_response(content, debug_file="agent3_raw_response.txt")
            # Ensure output structure is correct
            return self._ensure_output_structure(parsed)
        except Exception as e:
            print(f"⚠️  Agent 3 JSON parsing failed: {str(e)[:200]}")
            # Return default structure
            return {
                "error": f"JSON parsing failed: {str(e)}",
                "selected_projects": [],
                "skipped_projects": []
            }
    
    def _ensure_output_structure(self, data: Dict) -> Dict:
        """Ensure output has correct structure with selected_projects array."""
        # If data is at root level (parsing issue), try to wrap it
        project_like_keys = ["goals", "methods_solution", "execution_timeline", "results_metrics", "phases", "milestones", "primary_metric", "roi", "qualitative_impact", "secondary_outcomes"]
        has_project_like = any(k in data for k in project_like_keys)
        if "selected_projects" not in data or not data.get("selected_projects"):
            if has_project_like and ("selected_projects" not in data or not data.get("selected_projects")):
                # Single project at root (or selected_projects empty), wrap it
                project = dict(data)
                project.pop("selected_projects", None)
                project.pop("skipped_projects", None)
                if "project_index" not in project:
                    project["project_index"] = 0
                if "project_name" not in project:
                    project["project_name"] = (project.get("goals") or {}).get("primary_goal", "Project") if isinstance(project.get("goals"), dict) else "Packaged Project"
                return {
                    "selected_projects": [project],
                    "skipped_projects": data.get("skipped_projects") if isinstance(data.get("skipped_projects"), list) else []
                }
        
        # Ensure selected_projects is a list
        if "selected_projects" not in data:
            data["selected_projects"] = []
        elif not isinstance(data["selected_projects"], list):
            data["selected_projects"] = [data["selected_projects"]]
        
        # Ensure skipped_projects is a list
        if "skipped_projects" not in data:
            data["skipped_projects"] = []
        elif not isinstance(data["skipped_projects"], list):
            data["skipped_projects"] = [data["skipped_projects"]]
        
        return data
