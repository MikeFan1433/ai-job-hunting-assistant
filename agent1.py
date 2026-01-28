"""Agent 1: Input Validation Agent."""
import json
import re
import httpx
from typing import Dict, Optional
from config import STUDENT_PORTAL_BASE_URL, STUDENT_PORTAL_API_KEY
from agent_prompts import AGENT1_INPUT_VALIDATION_PROMPT
from json_parser_utils import parse_llm_json_response


class InputValidationAgent:
    """Agent 1: Validates resume and project materials completeness."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize the input validation agent.
        
        Args:
            model: LLM model to use (default: "gpt-4o-mini" for cost efficiency)
        """
        self.base_url = STUDENT_PORTAL_BASE_URL
        self.api_key = STUDENT_PORTAL_API_KEY
        self.model = model
        self.endpoint = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("STUDENT_PORTAL_API_KEY not set")
    
    def validate_inputs(
        self,
        resume_text: str,
        project_materials: Optional[str] = None
    ) -> Dict:
        """
        Validate resume and project materials.
        
        Args:
            resume_text: Resume content text
            project_materials: Optional project materials text
        
        Returns:
            Dictionary with validation results
        """
        user_message = f"""Please validate the following resume and project materials:

=== RESUME CONTENT ===
{resume_text}

=== PROJECT MATERIALS ===
{project_materials if project_materials else "No project materials provided"}

Please analyze and return the validation result in the specified JSON format."""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": AGENT1_INPUT_VALIDATION_PROMPT
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.1,
            "max_tokens": 2000
        }
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(self.endpoint, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                message_content = result["choices"][0]["message"]["content"]
                validation_result = self._parse_json_response(message_content)
                
                return validation_result
        
        except Exception as e:
            return {
                "is_valid": False,
                "error": str(e),
                "validation_summary": f"Validation failed: {str(e)}"
            }
    
    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON response from LLM using enhanced parser."""
        return parse_llm_json_response(content, debug_file="agent1_raw_response.txt")
