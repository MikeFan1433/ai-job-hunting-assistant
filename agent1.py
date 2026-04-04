"""Agent 1: Input Validation Agent."""
import json
import re
import httpx
from typing import Dict, Optional
from config import AI_BUILDER_BASE_URL, STUDENT_PORTAL_API_KEY, LLM_MODEL_JSON, RESPONSE_FORMAT_JSON
from agent_prompts import AGENT1_INPUT_VALIDATION_PROMPT
from json_parser_utils import parse_llm_json_response


class InputValidationAgent:
    """Agent 1: Validates resume and project materials completeness."""
    
    def __init__(self, model: str = None):
        """
        Initialize the input validation agent.
        Uses gpt-5 by default for reliable JSON mode output (AI Builder API).
        """
        model = model or LLM_MODEL_JSON
        self.base_url = AI_BUILDER_BASE_URL
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
                {"role": "system", "content": AGENT1_INPUT_VALIDATION_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.1,
            "max_tokens": 2000,
        }
        if RESPONSE_FORMAT_JSON is not None:
            payload["response_format"] = RESPONSE_FORMAT_JSON
        
        try:
            with httpx.Client(timeout=60.0) as client:
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
                        "is_valid": False,
                        "error": f"API request failed ({response.status_code}): {error_detail}",
                        "validation_summary": f"API request failed: {error_detail}",
                        "http_status": response.status_code
                    }
                
                response.raise_for_status()
                result = response.json()
                
                # Check if response has expected structure
                if "choices" not in result or len(result["choices"]) == 0:
                    return {
                        "is_valid": False,
                        "error": "Invalid API response: no choices in response",
                        "validation_summary": "Invalid API response format"
                    }

                message_content = result["choices"][0].get("message", {}).get("content")
                if message_content is None:
                    message_content = ""
                if not isinstance(message_content, str):
                    message_content = str(message_content) if message_content else ""
                message_content = message_content.strip()

                # Empty response: LLM returned nothing (rate limit, timeout, or model issue). Don't block user.
                if not message_content:
                    return {
                        "is_valid": True,
                        "has_work_experience": True,
                        "has_education": True,
                        "has_project_materials": bool(project_materials),
                        "validation_summary": "Validation skipped (service returned empty response). Please ensure your resume includes work experience and education.",
                        "issues": [],
                    }

                try:
                    validation_result = self._parse_json_response(message_content)
                except Exception as _e:
                    # LLM returned non-JSON or malformed JSON; don't block workflow
                    return {
                        "is_valid": True,
                        "has_work_experience": True,
                        "has_education": True,
                        "has_project_materials": bool(project_materials),
                        "validation_summary": "Validation skipped (response format issue). Please ensure your resume includes work experience and education.",
                        "issues": [],
                    }

                # Ensure error field is set if validation failed
                if not validation_result.get("is_valid", False) and "error" not in validation_result:
                    validation_result["error"] = "Validation failed - see issues for details"

                return validation_result

        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", error_data.get("message", error_detail))
            except:
                error_detail = e.response.text[:200] if e.response.text else error_detail
            
            return {
                "is_valid": False,
                "error": f"API request failed ({e.response.status_code}): {error_detail}",
                "validation_summary": f"API request failed: {error_detail}",
                "http_status": e.response.status_code
            }
        except Exception as e:
            import traceback
            return {
                "is_valid": False,
                "error": f"Validation error: {str(e)}",
                "validation_summary": f"Validation failed: {str(e)}",
                "traceback": traceback.format_exc()
            }
    
    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON response from LLM using enhanced parser."""
        return parse_llm_json_response(content, debug_file="agent1_raw_response.txt")
