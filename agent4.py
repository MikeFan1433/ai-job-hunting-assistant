"""Agent 4: Resume Optimization Assistant."""
import json
import re
import httpx
from typing import Dict, Optional, List
from config import STUDENT_PORTAL_BASE_URL, STUDENT_PORTAL_API_KEY
from agent_prompts import AGENT4_RESUME_OPTIMIZATION_PROMPT
from json_parser_utils import parse_llm_json_response


class ResumeOptimizationAgent:
    """Agent 4: Optimizes resume by replacing experiences and adjusting content/format."""
    
    def __init__(self, model: str = "supermind-agent-v1"):
        """
        Initialize the resume optimization agent.
        
        Args:
            model: LLM model to use (default: "supermind-agent-v1" for complex analysis)
        """
        self.base_url = STUDENT_PORTAL_BASE_URL
        self.api_key = STUDENT_PORTAL_API_KEY
        self.model = model
        self.endpoint = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("STUDENT_PORTAL_API_KEY not set")
    
    def optimize_resume(
        self,
        jd_text: str,
        resume_text: str,
        agent2_outputs: Dict,
        agent3_outputs: Dict
    ) -> Dict:
        """
        Optimize resume based on JD requirements, Agent 2 analysis, and Agent 3 optimized projects.
        
        Args:
            jd_text: Job description text
            resume_text: Current resume text
            agent2_outputs: Complete Agent 2 analysis output including:
                - job_role_team_analysis
                - ideal_candidate_profile
                - match_assessment
                - improvement_recommendations
            agent3_outputs: Complete Agent 3 output including:
                - selected_projects
                - skipped_projects
        
        Returns:
            Dictionary with resume optimization recommendations
        """
        # Build user message
        user_message = f"""Please optimize the following resume based on the JD, Agent 2 analysis, and Agent 3 optimized projects:

=== JOB DESCRIPTION ===
{jd_text}

=== CURRENT RESUME ===
{resume_text}

=== AGENT 2 ANALYSIS OUTPUTS ===
{json.dumps(agent2_outputs, indent=2, ensure_ascii=False)}

=== AGENT 3 OPTIMIZED PROJECTS ===
{json.dumps(agent3_outputs, indent=2, ensure_ascii=False)}

Please analyze the resume and provide optimization recommendations in the specified JSON format."""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": AGENT4_RESUME_OPTIMIZATION_PROMPT
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(self.endpoint, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                # Extract message content
                message_content = result["choices"][0]["message"]["content"]
                
                # Parse JSON response
                return self._parse_json_response(message_content)
                
        except httpx.HTTPError as e:
            return {
                "error": f"HTTP error during resume optimization: {str(e)}",
                "experience_replacements": [],
                "format_content_adjustments": [],
                "optimization_summary": {
                    "total_experiences_analyzed": 0,
                    "experiences_recommended_for_replacement": 0,
                    "total_adjustments_suggested": 0,
                    "expected_match_score_improvement": "0.0 points",
                    "key_improvements": []
                }
            }
        except Exception as e:
            return {
                "error": f"Error during resume optimization: {str(e)}",
                "experience_replacements": [],
                "format_content_adjustments": [],
                "optimization_summary": {
                    "total_experiences_analyzed": 0,
                    "experiences_recommended_for_replacement": 0,
                    "total_adjustments_suggested": 0,
                    "expected_match_score_improvement": "0.0 points",
                    "key_improvements": []
                }
            }
    
    def _parse_json_response(self, content: str) -> Dict:
        """
        Parse JSON response from LLM using enhanced parser.
        
        Args:
            content: Raw response content from LLM
        
        Returns:
            Parsed JSON dictionary with required fields ensured
        """
        try:
            result = parse_llm_json_response(content, debug_file="agent4_raw_response.txt")
            # Ensure required fields exist
            return self._ensure_required_fields(result)
        except Exception as e:
            return {
                "error": f"Failed to parse JSON response: {str(e)}",
                "raw_content_preview": content[:500] if len(content) > 500 else content,
                "experience_replacements": [],
                "format_content_adjustments": [],
                "experience_optimizations": [],
                "skills_section_optimization": {
                    "has_skills_section": False,
                    "current_skills": [],
                    "user_feedback_options": {}
                },
                "optimization_summary": {
                    "total_experiences_analyzed": 0,
                    "experiences_recommended_for_replacement": 0,
                    "total_adjustments_suggested": 0,
                    "total_experiences_optimized": 0,
                    "skills_section_optimized": False,
                    "expected_match_score_improvement": "0.0 points",
                    "key_improvements": []
                }
            }
    
    def _ensure_required_fields(self, result: Dict) -> Dict:
        """
        Ensure all required fields exist in the result.
        
        Args:
            result: Parsed result dictionary
        
        Returns:
            Result dictionary with all required fields
        """
        if "experience_replacements" not in result:
            result["experience_replacements"] = []
        
        if "format_content_adjustments" not in result:
            result["format_content_adjustments"] = []
        
        if "experience_optimizations" not in result:
            result["experience_optimizations"] = []
        
        if "skills_section_optimization" not in result:
            result["skills_section_optimization"] = {
                "has_skills_section": False,
                "current_skills": [],
                "user_feedback_options": {}
            }
        
        if "optimization_summary" not in result:
            result["optimization_summary"] = {
                "total_experiences_analyzed": 0,
                "experiences_recommended_for_replacement": 0,
                "total_adjustments_suggested": 0,
                "expected_match_score_improvement": "0.0 points",
                "key_improvements": []
            }
        else:
            summary = result["optimization_summary"]
            if "total_experiences_analyzed" not in summary:
                summary["total_experiences_analyzed"] = 0
            if "experiences_recommended_for_replacement" not in summary:
                summary["experiences_recommended_for_replacement"] = 0
            if "total_adjustments_suggested" not in summary:
                summary["total_adjustments_suggested"] = 0
            if "expected_match_score_improvement" not in summary:
                summary["expected_match_score_improvement"] = "0.0 points"
            if "key_improvements" not in summary:
                summary["key_improvements"] = []
            if "total_experiences_optimized" not in summary:
                summary["total_experiences_optimized"] = 0
            if "skills_section_optimized" not in summary:
                summary["skills_section_optimized"] = False
        
        return result
