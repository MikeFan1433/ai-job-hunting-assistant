"""Enhanced JSON parsing utilities for LLM responses."""
import json
import re
from typing import Dict, Any, Optional


def parse_llm_json_response(content: str, debug_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Robustly parse JSON response from LLM, handling various edge cases.
    
    Args:
        content: Raw response content from LLM
        debug_file: Optional file path to save raw content for debugging
    
    Returns:
        Parsed JSON dictionary
    
    Raises:
        Exception: If JSON cannot be parsed after all attempts
    """
    # Save raw response for debugging
    if debug_file:
        try:
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass  # Ignore file write errors
    
    original_content = content
    
    # Step 1: Remove handoff tags and XML/HTML-like tags
    # But preserve content that might be after handoff tags
    # First, try to find JSON after handoff tags
    handoff_match = re.search(r'</handoff>\s*(\{.*\})', content, re.DOTALL | re.IGNORECASE)
    if handoff_match:
        content = handoff_match.group(1)
    else:
        # If no JSON after handoff, remove handoff tags
        content = re.sub(r'<handoff>.*?</handoff>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<parameter.*?>.*?</parameter>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<[^>]+>', '', content)  # Remove any remaining HTML/XML tags
    
    # Step 2: Remove markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        content = json_match.group(1)
    
    # Step 3: Find JSON object boundaries more carefully
    # Count braces to find the complete JSON object, respecting strings
    brace_count = 0
    start_idx = -1
    end_idx = -1
    in_string = False
    escape_next = False
    
    for i, char in enumerate(content):
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        
        if not in_string:
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    end_idx = i
                    break
    
    if start_idx != -1 and end_idx != -1:
        content = content[start_idx:end_idx + 1]
    else:
        # Fallback: simple first/last brace
        first_brace = content.find('{')
        last_brace = content.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            content = content[first_brace:last_brace + 1]
    
    # Step 4: Remove comments (both // and /* */ style)
    content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    # Step 5: Fix common JSON issues
    # Remove trailing commas before closing braces/brackets (but not inside strings)
    # We need to be careful not to break strings that contain commas
    def remove_trailing_commas(text):
        """Remove trailing commas but respect string boundaries."""
        result = []
        in_string = False
        escape_next = False
        i = 0
        
        while i < len(text):
            char = text[i]
            
            if escape_next:
                result.append(char)
                escape_next = False
                i += 1
                continue
            
            if char == '\\':
                result.append(char)
                escape_next = True
                i += 1
                continue
            
            if char == '"':
                in_string = not in_string
                result.append(char)
                i += 1
                continue
            
            if not in_string:
                # Check if this is a trailing comma
                if char == ',':
                    # Look ahead to see if next non-whitespace is } or ]
                    j = i + 1
                    while j < len(text) and text[j] in ' \t\n\r':
                        j += 1
                    if j < len(text) and text[j] in '}]':
                        # This is a trailing comma, skip it
                        i += 1
                        continue
                
            result.append(char)
            i += 1
        
        return ''.join(result)
    
    content = remove_trailing_commas(content)
    
    # Step 6: Try to parse
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        # Try more aggressive fixes
        
        # Fix 1: Remove trailing commas more aggressively
        content = re.sub(r',\s*([}\]])', r'\1', content)
        
        # Fix 2: Fix unquoted keys (more carefully)
        # Only fix keys that are not already quoted and not in strings
        def fix_unquoted_key(match):
            key = match.group(1)
            # Check if this key is already quoted (look backwards)
            start_pos = match.start()
            # Simple check: if the character before is a quote, it's already quoted
            if start_pos > 0 and content[start_pos - 1] == '"':
                return match.group(0)
            return f'"{key}":'
        
        # Only fix keys that appear to be unquoted (not preceded by quote or colon)
        content = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:', fix_unquoted_key, content)
        
        # Fix 3: Remove any text before first { or after last }
        first_brace = content.find('{')
        last_brace = content.rfind('}')
        if first_brace != -1 and last_brace != -1:
            content = content[first_brace:last_brace + 1]
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Last resort: try to extract just the JSON structure
            # Find nested JSON objects, respecting strings
            brace_count = 0
            start_idx = -1
            end_idx = -1
            in_string = False
            escape_next = False
            
            for i, char in enumerate(content):
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                if not in_string:
                    if char == '{':
                        if brace_count == 0:
                            start_idx = i
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0 and start_idx != -1:
                            end_idx = i
                            break
            
            if start_idx != -1 and end_idx != -1:
                try:
                    extracted = content[start_idx:end_idx + 1]
                    # Try to fix common issues in extracted content
                    extracted = re.sub(r',(\s*[}\]])', r'\1', extracted)
                    return json.loads(extracted)
                except json.JSONDecodeError:
                    pass
            
            # If all else fails, raise with helpful error message
            error_msg = f"Failed to parse JSON after all attempts: {str(e)}\n"
            error_msg += f"Content preview (first 1000 chars):\n{original_content[:1000]}\n"
            error_msg += f"Extracted content preview:\n{content[:500]}"
            raise Exception(error_msg)


def ensure_json_structure(data: Dict, default_structure: Dict) -> Dict:
    """
    Ensure the parsed JSON has the required structure with defaults.
    
    Args:
        data: Parsed JSON data
        default_structure: Default structure to merge with
    
    Returns:
        Dictionary with ensured structure
    """
    result = default_structure.copy()
    
    def merge_dicts(base: Dict, updates: Dict):
        """Recursively merge dictionaries."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                merge_dicts(base[key], value)
            else:
                base[key] = value
    
    merge_dicts(result, data)
    return result
