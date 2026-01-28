"""Agent 5: Interview Preparation Assistant."""
import json
import re
import httpx
from typing import Dict, Optional, List
from config import STUDENT_PORTAL_BASE_URL, STUDENT_PORTAL_API_KEY
from agent_prompts import AGENT5_INTERVIEW_PREPARATION_PROMPT
from json_parser_utils import parse_llm_json_response


class InterviewPreparationAgent:
    """Agent 5: Generates comprehensive interview preparation materials."""
    
    def __init__(self, model: str = "supermind-agent-v1"):
        """
        Initialize the interview preparation agent.
        
        Args:
            model: LLM model to use (default: "supermind-agent-v1" for complex analysis)
        """
        self.base_url = STUDENT_PORTAL_BASE_URL
        self.api_key = STUDENT_PORTAL_API_KEY
        self.model = model
        self.endpoint = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("STUDENT_PORTAL_API_KEY not set")
    
    def prepare_interview(
        self,
        jd_text: str,
        final_resume: str,
        agent2_outputs: Dict,
        agent4_outputs: Dict
    ) -> Dict:
        """
        Generate comprehensive interview preparation materials.
        
        Args:
            jd_text: Job description text
            final_resume: Final optimized resume after all modifications
            agent2_outputs: Complete Agent 2 analysis output including:
                - job_role_team_analysis
                - ideal_candidate_profile
                - match_assessment
            agent4_outputs: Complete Agent 4 output including:
                - classified_projects (resume_adopted_projects, resume_not_adopted_projects)
        
        Returns:
            Dictionary with interview preparation materials
        """
        # Extract classified projects from Agent 4 outputs
        classified_projects = agent4_outputs.get("classified_projects", {
            "resume_adopted_projects": [],
            "resume_not_adopted_projects": []
        })
        
        # Build user message
        user_message = f"""Please generate comprehensive interview preparation materials based on the following:

=== JOB DESCRIPTION ===
{jd_text}

=== FINAL OPTIMIZED RESUME ===
{final_resume}

=== AGENT 2 ANALYSIS OUTPUTS ===
{json.dumps(agent2_outputs, indent=2, ensure_ascii=False)}

=== AGENT 4 CLASSIFIED PROJECTS ===
{json.dumps(classified_projects, indent=2, ensure_ascii=False)}

Please generate interview preparation materials covering:
1. Behavioral Interview Questions (Self-introduction, Storytelling example, Top 10 Behavioral Questions)
2. Project Deep-Dive Questions (Top 3 Projects with technical detail questions)
3. Business Domain Questions (10 business-related questions)

Provide all content in the specified JSON format."""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": AGENT5_INTERVIEW_PREPARATION_PROMPT
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.3,
            "max_tokens": 6000  # Longer response needed for comprehensive interview prep
        }
        
        try:
            with httpx.Client(timeout=180.0) as client:
                response = client.post(self.endpoint, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                # Extract message content
                message_content = result["choices"][0]["message"]["content"]
                
                # Check if response contains actual JSON (not just handoff tags)
                if not re.search(r'\{[^{}]*\}', message_content, re.DOTALL):
                    # No JSON found, return default structure
                    print("⚠️  Warning: Agent 5 response contains no JSON, returning default structure")
                    return self._ensure_required_fields({})
                
                # Parse JSON response
                try:
                    interview_prep = self._parse_json_response(message_content)
                    # Ensure required fields
                    interview_prep = self._ensure_required_fields(interview_prep)
                    return interview_prep
                except Exception as parse_error:
                    print(f"⚠️  Warning: Failed to parse Agent 5 JSON: {str(parse_error)}")
                    print("   Returning default structure with error message")
                    default_prep = self._ensure_required_fields({})
                    default_prep["parse_error"] = str(parse_error)
                    default_prep["raw_response_preview"] = message_content[:500]
                    return default_prep
        
        except httpx.HTTPStatusError as e:
            print(f"⚠️  Warning: API request failed: {e.response.status_code}")
            return self._ensure_required_fields({"api_error": str(e)})
        except Exception as e:
            print(f"⚠️  Warning: Error generating interview preparation: {str(e)}")
            return self._ensure_required_fields({"error": str(e)})
    
    def _parse_json_response(self, content: str) -> Dict:
        """
        Parse JSON response from LLM using enhanced parser.
        
        Args:
            content: Raw response content from LLM
        
        Returns:
            Parsed JSON dictionary
        """
        return parse_llm_json_response(content, debug_file="agent5_raw_response.txt")
    
    def _ensure_required_fields(self, interview_prep: Dict) -> Dict:
        """
        Ensure the output contains all required fields.
        
        Args:
            interview_prep: Parsed interview preparation dictionary
        
        Returns:
            Dictionary with all required fields
        """
        # Ensure theme_1_behavioral_interview exists
        if "theme_1_behavioral_interview" not in interview_prep:
            interview_prep["theme_1_behavioral_interview"] = {}
        
        theme1 = interview_prep["theme_1_behavioral_interview"]
        
        # Ensure self_introduction exists
        if "self_introduction" not in theme1:
            theme1["self_introduction"] = {
                "paragraph_1": "",
                "paragraph_2": "",
                "paragraph_3": "",
                "full_text": "",
                "key_highlights": [],
                "jd_alignment_notes": ""
            }
        
        # Ensure storytelling_example exists
        if "storytelling_example" not in theme1:
            theme1["storytelling_example"] = {
                "selected_project": {},
                "hook": "",
                "emergency": "",
                "approach": "",
                "action": "",
                "impact": "",
                "reflection": "",
                "full_storytelling_answer": "",
                "jd_skills_demonstrated": []
            }
        
        # Ensure top_10_behavioral_questions exists
        if "top_10_behavioral_questions" not in theme1:
            theme1["top_10_behavioral_questions"] = []
        
        # Ensure theme_2_project_deep_dive exists
        if "theme_2_project_deep_dive" not in interview_prep:
            interview_prep["theme_2_project_deep_dive"] = {
                "selected_projects": []
            }
        
        # Ensure theme_3_business_domain exists
        if "theme_3_business_domain" not in interview_prep:
            interview_prep["theme_3_business_domain"] = {
                "business_questions": []
            }
        
        # Ensure preparation_summary exists
        if "preparation_summary" not in interview_prep:
            interview_prep["preparation_summary"] = {
                "total_behavioral_questions": len(theme1.get("top_10_behavioral_questions", [])),
                "total_projects_analyzed": len(interview_prep.get("theme_2_project_deep_dive", {}).get("selected_projects", [])),
                "total_technical_questions": sum(
                    len(p.get("technical_deep_dive_questions", []))
                    for p in interview_prep.get("theme_2_project_deep_dive", {}).get("selected_projects", [])
                ),
                "total_business_questions": len(interview_prep.get("theme_3_business_domain", {}).get("business_questions", [])),
                "key_preparation_focus_areas": []
            }
        
        return interview_prep
