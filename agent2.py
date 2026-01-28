"""Agent 2: JD Analysis & Matching Assessment Agent."""
import json
import re
import httpx
from typing import Dict, Optional
from config import STUDENT_PORTAL_BASE_URL, STUDENT_PORTAL_API_KEY
from agent_prompts import AGENT2_JD_ANALYSIS_PROMPT
from json_parser_utils import parse_llm_json_response


class JDAnalysisAgent:
    """Agent 2: Analyzes JD and provides matching assessment."""
    
    def __init__(self, model: str = "supermind-agent-v1"):
        """
        Initialize the JD analysis agent.
        
        Args:
            model: LLM model to use (default: "supermind-agent-v1" for complex analysis)
        """
        self.base_url = STUDENT_PORTAL_BASE_URL
        self.api_key = STUDENT_PORTAL_API_KEY
        self.model = model
        self.endpoint = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("STUDENT_PORTAL_API_KEY not set")
    
    def analyze_jd_and_match(
        self,
        jd_text: str,
        resume_text: str,
        project_materials: Optional[str] = None
    ) -> Dict:
        """
        Analyze JD and provide matching assessment.
        
        Args:
            jd_text: Job description text
            resume_text: Resume content text
            project_materials: Optional project materials text
        
        Returns:
            Dictionary with analysis results
        """
        user_message = f"""Please analyze the following JD, resume, and project materials:

=== JOB DESCRIPTION ===
{jd_text}

=== RESUME ===
{resume_text}

=== PROJECT MATERIALS ===
{project_materials if project_materials else "No project materials provided"}

Please provide comprehensive analysis in the specified JSON format."""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": AGENT2_JD_ANALYSIS_PROMPT
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.3,
            "max_tokens": 6000
        }
        
        try:
            with httpx.Client(timeout=180.0) as client:
                response = client.post(self.endpoint, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                message_content = result["choices"][0]["message"]["content"]
                analysis_result = self._parse_json_response(message_content)
                
                return analysis_result
        
        except Exception as e:
            return {
                "error": str(e),
                "job_role_team_analysis": {},
                "ideal_candidate_profile": {},
                "match_assessment": {}
            }
    
    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON response from LLM using enhanced parser."""
        return parse_llm_json_response(content, debug_file="agent2_raw_response.txt")
