"""Agent 4: Resume Optimization Assistant."""
import json
import re
import time
import difflib
import httpx
from typing import Dict, Optional, List, Any
from config import AI_BUILDER_BASE_URL, STUDENT_PORTAL_API_KEY, LLM_MODEL_JSON, RESPONSE_FORMAT_JSON, AGENT4_FAST_MODEL
from agent4_prompt_compressed import AGENT4_SYSTEM_BRIEF, AGENT4_JSON_SCHEMA, AGENT4_JD_RESUME_ONLY_PROMPT, AGENT4_RESUME_OPTIMIZATION_PROMPT
from json_parser_utils import parse_llm_json_response
from llm_output_language import output_language_suffix

_MAX_STR = 500
_MAX_ITEMS = 6


def _cap_resume_preserving_experience(resume_text: str, max_chars: int) -> str:
    """Truncate resume while keeping WORK EXPERIENCE section when possible."""
    if not resume_text or len(resume_text) <= max_chars:
        return resume_text or ""
    upper = resume_text.upper()
    exp_idx = upper.find("WORK EXPERIENCE")
    if exp_idx < 0:
        exp_idx = upper.find("\nEXPERIENCE")
    if exp_idx < 0:
        exp_idx = upper.find("EXPERIENCE")
    if exp_idx >= 0:
        head_budget = min(exp_idx + 400, max_chars // 3)
        head = resume_text[:head_budget]
        exp_budget = max_chars - len(head) - 30
        exp_part = resume_text[exp_idx : exp_idx + max(exp_budget, max_chars // 2)]
        return head + "\n" + exp_part + "\n... (truncated)"
    return resume_text[: max_chars - 20] + "\n... (truncated)"


def _normalize_bullet_reason(suggestion: Dict) -> None:
    """Ensure reason + reason_struct are present and aligned."""
    if not isinstance(suggestion, dict):
        return
    rs = suggestion.get("reason_struct")
    if isinstance(rs, dict):
        parts = []
        for key, label in (
            ("align", "对齐"),
            ("rewrite", "改写"),
            ("evidence", "依据"),
            ("expected_impact", "预期"),
        ):
            val = rs.get(key)
            if isinstance(val, str) and val.strip():
                parts.append(f"{label}: {val.strip()}")
        if parts and not (isinstance(suggestion.get("reason"), str) and suggestion["reason"].strip()):
            suggestion["reason"] = " | ".join(parts)
    elif isinstance(suggestion.get("reason"), str) and suggestion["reason"].strip():
        suggestion.setdefault(
            "reason_struct",
            {"align": "", "rewrite": suggestion["reason"].strip(), "evidence": "", "expected_impact": ""},
        )


_SUMMARY_HEADER_RE = re.compile(
    r"(?im)^\s*(?:SUMMARY|PROFESSIONAL\s+SUMMARY|PROFILE|EXECUTIVE\s+SUMMARY|CAREER\s+SUMMARY)\s*$"
)
_NEXT_MAJOR_SECTION_RE = re.compile(
    r"(?im)^\s*(?:WORK\s+EXPERIENCE|EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EMPLOYMENT|SKILLS|EDUCATION|PROJECTS|CERTIFICATIONS)\s*$"
)


def _extract_resume_summary(resume_text: str) -> Dict[str, Any]:
    """Detect summary section body and whether it uses bullet formatting."""
    text = resume_text or ""
    if not text.strip():
        return {"has_summary": False, "header": "", "body": "", "uses_bullets": False, "bullets": []}

    header_match = _SUMMARY_HEADER_RE.search(text)
    if not header_match:
        return {"has_summary": False, "header": "", "body": "", "uses_bullets": False, "bullets": []}

    start = header_match.end()
    tail = text[start:]
    next_match = _NEXT_MAJOR_SECTION_RE.search(tail)
    body = (tail[: next_match.start()] if next_match else tail).strip()
    if not body:
        return {"has_summary": True, "header": header_match.group(0).strip(), "body": "", "uses_bullets": False, "bullets": []}

    bullets: List[str] = []
    uses_bullets = False
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^[\s•\-\*●·]+\s*\S", stripped):
            uses_bullets = True
            bullets.append(re.sub(r"^[\s•\-\*●·]+\s*", "", stripped).strip())
        elif bullets and uses_bullets:
            bullets[-1] = f"{bullets[-1]} {stripped}"
        else:
            bullets.append(stripped)

    if not uses_bullets and bullets:
        body = "\n".join(bullets)
    return {
        "has_summary": True,
        "header": header_match.group(0).strip(),
        "body": body,
        "uses_bullets": uses_bullets,
        "bullets": bullets,
    }


def _format_summary_suggestion_text(body: str, uses_bullets: bool) -> str:
    """Normalize suggested summary to match original bullet/paragraph style."""
    text = (body or "").strip()
    if not text:
        return ""
    if not uses_bullets:
        return text
    lines = [ln.strip() for ln in re.split(r"[\n\r]+", text) if ln.strip()]
    formatted: List[str] = []
    for ln in lines:
        core = re.sub(r"^[\s•\-\*●·]+\s*", "", ln).strip()
        if core:
            formatted.append(f"● {core}")
    return "\n".join(formatted) if formatted else text


def _normalize_summary_suggestion(result: Dict, resume_text: Optional[str]) -> None:
    """Align summary_suggestion with detected resume summary; force replace when summary exists."""
    ss = result.get("summary_suggestion")
    if not isinstance(ss, dict):
        ss = {}
        result["summary_suggestion"] = ss

    detected = _extract_resume_summary(resume_text or "")
    has_existing = bool(detected.get("has_summary"))
    ss["has_existing_summary"] = has_existing or bool(ss.get("has_existing_summary"))

    if has_existing and not (ss.get("original_summary") or "").strip():
        ss["original_summary"] = detected.get("body") or ""

    suggested = (ss.get("suggested_summary") or "").strip()
    action = (ss.get("recommended_action") or "skip").lower()

    if has_existing:
        if action in ("skip", "keep_existing") and suggested:
            ss["recommended_action"] = "replace"
        elif action in ("skip", "keep_existing") and not suggested:
            # LLM skipped — still surface replace so UI can prompt user (empty suggestion = no UI row)
            ss["recommended_action"] = "replace"
        elif action == "add":
            ss["recommended_action"] = "replace"
        if suggested and detected.get("uses_bullets"):
            ss["suggested_summary"] = _format_summary_suggestion_text(suggested, True)
    elif suggested and action == "skip":
        ss["recommended_action"] = "add"

    ss.setdefault("suggested_headline", "")
    ss.setdefault("jd_keywords_embedded", [])
    ss.setdefault("feedback_actions", ["accept", "reject", "further_modify"])


def _map_experience_level_rewrites(result: Dict) -> None:
    """Map Agent 4 experience_level_rewrites into experience_optimizations for UI/service."""
    rewrites = result.get("experience_level_rewrites") or []
    if not isinstance(rewrites, list) or not rewrites:
        return
    existing = result.get("experience_optimizations") or []
    if isinstance(existing, list) and len(existing) > 0:
        return
    mapped: List[Dict] = []
    for i, rw in enumerate(rewrites):
        if not isinstance(rw, dict):
            continue
        entry = rw.get("experience_entry") or f"Experience {i + 1}"
        bullets = rw.get("optimized_bullets") or []
        details = []
        for j, b in enumerate(bullets):
            if isinstance(b, str) and b.strip():
                details.append(
                    {
                        "original": rw.get("rewrite_goal", "") if j == 0 else "",
                        "optimized": b.strip(),
                        "optimization_rationale": rw.get("rewrite_goal", ""),
                    }
                )
        mapped.append(
            {
                "experience_entry": {"title": entry, "company": "", "entry_index": i + 1},
                "optimized_experience": {"optimized_bullets": bullets},
                "optimization_details": details or [{"optimization_rationale": rw.get("rewrite_goal", "")}],
                "_from_experience_level_rewrite": True,
            }
        )
    result["experience_optimizations"] = mapped


def _norm_resume_compare(s: str) -> str:
    if not s:
        return ""
    t = s.lower().strip()
    return re.sub(r"\s+", " ", t)


def _is_placeholder_bullet_text(s: str) -> bool:
    t = (s or "").strip().lower()
    if len(t) < 6:
        return True
    if t in ("n/a", "na", "tbd", "none", "...", "-", "—", "n/a.", "待定"):
        return True
    if "n/a" in t or "not applicable" in t or t.startswith("[todo"):
        return True
    return False


def _original_bullet_in_resume(original: str, resume_text: str) -> bool:
    """Lenient check: LLM often paraphrases punctuation or breaks lines; avoid dropping valid rows."""
    o = _norm_resume_compare(original)
    r = _norm_resume_compare(resume_text)
    if len(o) < 6:
        return False
    if o in r:
        return True
    o2 = re.sub(r"^[\s\-–•*·]+", "", o).strip()
    if len(o2) >= 6 and o2 in r:
        return True
    for line in re.split(r"[\r\n]+", resume_text):
        ln = _norm_resume_compare(line)
        if len(ln) < 8:
            continue
        if o2 in ln or ln in o2:
            return True
        if len(o2) >= 12 and difflib.SequenceMatcher(None, o2, ln).ratio() >= 0.62:
            return True
    return len(o2) >= 20 and difflib.SequenceMatcher(None, o2, r).ratio() >= 0.38


def _filter_invalid_bullet_suggestions(result: Dict, resume_text: Optional[str]) -> None:
    """Remove bullet suggestions with placeholders or original_bullet not found in resume (normalized)."""
    if not resume_text or not isinstance(resume_text, str):
        return
    bls = result.get("bullet_level_suggestions")
    if not isinstance(bls, list):
        return
    new_groups: List[Dict[str, Any]] = []
    for group in bls:
        if not isinstance(group, dict):
            continue
        suggestions = group.get("suggestions")
        if not isinstance(suggestions, list):
            new_groups.append(group)
            continue
        kept: List[Dict[str, Any]] = []
        for s in suggestions:
            if not isinstance(s, dict):
                continue
            ob = (s.get("original_bullet") or "").strip() if isinstance(s.get("original_bullet"), str) else ""
            sb = (s.get("suggested_bullet") or "").strip() if isinstance(s.get("suggested_bullet"), str) else ""
            if _is_placeholder_bullet_text(ob) or _is_placeholder_bullet_text(sb):
                continue
            if not _original_bullet_in_resume(ob, resume_text):
                continue
            kept.append(s)
        if kept:
            g = dict(group)
            g["suggestions"] = kept
            new_groups.append(g)
    result["bullet_level_suggestions"] = new_groups


def build_condensed_jd_from_agent2(agent2_outputs: Dict, max_chars: int = 1800) -> str:
    """
    Build a short JD summary from Agent 2 output: core responsibilities, qualifications, and key words/phrases.
    Use this as the JD input to Agent 4 to reduce token count and speed up response without losing key signal.
    """
    if not agent2_outputs:
        return ""
    parts = []
    jra = agent2_outputs.get("job_role_team_analysis") or {}
    icp = agent2_outputs.get("ideal_candidate_profile") or {}

    # Core responsibilities (from work_scenarios, daily_activities, team_objectives)
    resp = []
    for key in ("team_objectives", "work_scenarios", "daily_activities"):
        val = jra.get(key)
        if isinstance(val, str) and val.strip():
            resp.append(val.strip())
        elif isinstance(val, list):
            resp.extend(str(x).strip() for x in val if x and str(x).strip())
    if resp:
        parts.append("Core responsibilities:\n" + "\n".join("- " + s for s in resp[:12]))

    # Qualifications (from overall_experience_traits, hard_skills)
    qual = []
    if isinstance(icp.get("overall_experience_traits"), str) and icp["overall_experience_traits"].strip():
        qual.append(icp["overall_experience_traits"].strip())
    hs = icp.get("hard_skills") or {}
    for key in ("must_have", "nice_to_have"):
        items = hs.get(key) if isinstance(hs, dict) else []
        if isinstance(items, list):
            for item in items[:6]:
                if isinstance(item, dict) and item.get("skill"):
                    qual.append(item.get("skill") + (": " + str(item.get("details", ""))[:80] if item.get("details") else ""))
                elif isinstance(item, str):
                    qual.append(item)
    if qual:
        parts.append("Qualifications:\n" + "\n".join("- " + str(s) for s in qual[:10]))

    # Key words/phrases (from required_knowledge, methods_technologies, kpis, project_types)
    keywords = []
    for key in ("required_knowledge", "methods_technologies", "kpis", "project_types"):
        val = jra.get(key)
        if isinstance(val, list):
            keywords.extend(str(x).strip() for x in val if x and str(x).strip())
    soft = icp.get("soft_skills_top5") or []
    if isinstance(soft, list):
        for item in soft[:5]:
            if isinstance(item, dict) and item.get("skill"):
                keywords.append(item.get("skill"))
            elif isinstance(item, str):
                keywords.append(item)
    if keywords:
        parts.append("Key words/phrases: " + ", ".join(keywords[:25]))

    text = "\n\n".join(parts)
    if len(text) > max_chars:
        text = text[: max_chars - 20] + "\n... (truncated)"
    return text.strip() or ""


def _compact_agent2_for_api(data: Dict) -> Dict:
    """Produce a smaller copy of Agent 2 output for API payload: truncate long strings, cap array lengths."""
    if not data:
        return data
    out = {}
    for key, val in data.items():
        if val is None:
            continue
        if isinstance(val, str):
            out[key] = val[:_MAX_STR] + ("..." if len(val) > _MAX_STR else "")
        elif isinstance(val, list):
            out[key] = [_compact_agent2_for_api(x) if isinstance(x, dict) else (x[:_MAX_STR] + "..." if isinstance(x, str) and len(x) > _MAX_STR else x) for x in val[:_MAX_ITEMS]]
        elif isinstance(val, dict):
            out[key] = _compact_agent2_for_api(val)
        else:
            out[key] = val
    return out


class ResumeOptimizationAgent:
    """Agent 4: Optimizes resume by replacing experiences and adjusting content/format."""
    
    def __init__(self, model: str = None):
        """Initialize the resume optimization agent. Uses gpt-5 by default for JSON mode (AI Builder API)."""
        model = model or LLM_MODEL_JSON
        self.base_url = AI_BUILDER_BASE_URL
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
        agent3_outputs: Dict,
        read_timeout_sec: Optional[float] = None,
        fast_run: bool = False,
        jd_resume_only: bool = False,
        use_condensed_jd: bool = False,
        preferred_lang: Optional[str] = "en",
    ) -> Dict:
        """
        Optimize resume based on JD requirements, and optionally Agent 2 analysis and Agent 3 optimized projects.
        
        Args:
            jd_text: Job description text
            resume_text: Current resume text
            agent2_outputs: Complete Agent 2 analysis output (ignored if jd_resume_only=True)
            agent3_outputs: Complete Agent 3 output (ignored if jd_resume_only=True)
            read_timeout_sec: Optional read timeout in seconds (e.g. 8 for fast run). Default 600.
            fast_run: If True, use fewer retries (1) and shorter retry delay (2s) to finish under 30s total.
            jd_resume_only: If True, use only JD and resume to generate suggestions (no Agent 2/3). Reduces payload for faster response; rationales are grounded in JD only.
            use_condensed_jd: If True and agent2_outputs has content, replace full JD with a short summary (responsibilities, qualifications, keywords) derived from Agent 2. Reduces input tokens to speed up Agent 4; requires Agent 2 to have run first.
        
        Returns:
            Dictionary with resume optimization recommendations
        """
        use_fast_path = read_timeout_sec is not None and read_timeout_sec <= 120
        use_ultra_fast = read_timeout_sec is not None and read_timeout_sec <= 15
        # Truncate large inputs to avoid API timeouts / empty responses
        if use_ultra_fast:
            jd_text_use = jd_text[:1200] if len(jd_text) > 1200 else jd_text
            resume_text_use = _cap_resume_preserving_experience(resume_text, 6000)
        elif use_fast_path:
            jd_text_use = jd_text[:2500] if len(jd_text) > 2500 else jd_text
            resume_text_use = _cap_resume_preserving_experience(resume_text, 12000)
        else:
            if read_timeout_sec is None or read_timeout_sec >= 180:
                _jd_cap, _res_cap = 8000, 16000
            else:
                _jd_cap, _res_cap = 4000, 8000
            jd_text_use = jd_text[:_jd_cap] if len(jd_text) > _jd_cap else jd_text
            resume_text_use = _cap_resume_preserving_experience(resume_text, _res_cap)
        # When requested, use Agent 2–derived condensed JD (responsibilities, qualifications, keywords) to cut tokens
        if use_condensed_jd and agent2_outputs:
            condensed = build_condensed_jd_from_agent2(agent2_outputs, max_chars=1800 if use_fast_path else 2500)
            if condensed:
                jd_text_use = condensed
        _schema = AGENT4_JSON_SCHEMA or ""
        if jd_resume_only:
            user_message = f"""Please optimize the following resume based ONLY on the job description and the current resume.

=== JOB DESCRIPTION ===
{jd_text_use}

=== CURRENT RESUME ===
{resume_text_use}

=== REQUIRED JSON SCHEMA ===
{_schema}

Analyze the resume and provide optimization recommendations. Ground all improvement rationales in the JD. Return only valid JSON.{output_language_suffix(preferred_lang)}"""
            system_prompt = AGENT4_SYSTEM_BRIEF
        else:
            agent2_compact = _compact_agent2_for_api(agent2_outputs)
            agent2_str = json.dumps(agent2_compact, indent=2, ensure_ascii=False)
            agent3_str = json.dumps(agent3_outputs, indent=2, ensure_ascii=False)
            if len(agent2_str) > 10000:
                agent2_str = agent2_str[:10000] + "\n... (truncated)"
            if use_ultra_fast:
                agent2_str = agent2_str[:2500] + "\n... (truncated)" if len(agent2_str) > 2500 else agent2_str
            elif use_fast_path and len(agent2_str) > 6000:
                agent2_str = agent2_str[:6000] + "\n... (truncated)"
            if len(agent3_str) > 3500:
                agent3_str = agent3_str[:3500] + "\n... (truncated)"
            user_message = f"""Please optimize the following resume based on the JD, Agent 2 analysis, and Agent 3 optimized projects:

=== JOB DESCRIPTION ===
{jd_text_use}

=== CURRENT RESUME ===
{resume_text_use}

=== AGENT 2 ANALYSIS OUTPUTS ===
{agent2_str}

=== AGENT 3 OPTIMIZED PROJECTS ===
{agent3_str}

=== REQUIRED JSON SCHEMA ===
{_schema}

Analyze the resume and provide optimization recommendations. Return only valid JSON.{output_language_suffix(preferred_lang)}"""
            system_prompt = AGENT4_SYSTEM_BRIEF

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.3,
            "max_tokens": 8000,
        }
        if RESPONSE_FORMAT_JSON is not None:
            payload["response_format"] = RESPONSE_FORMAT_JSON
        
        read_timeout = read_timeout_sec if read_timeout_sec is not None else 600.0
        use_fast = read_timeout_sec is not None and read_timeout_sec <= 30
        # Use AGENT4_FAST_MODEL (e.g. gemini-3-flash-preview) whenever time-bound for better speed/capability balance
        if use_ultra_fast:
            payload["model"] = AGENT4_FAST_MODEL
            payload["max_tokens"] = min(payload.get("max_tokens", 8000), 2500)
        elif use_fast:
            payload["model"] = AGENT4_FAST_MODEL
            payload["max_tokens"] = min(payload.get("max_tokens", 8000), 4500)
        elif use_fast_path:
            payload["model"] = AGENT4_FAST_MODEL
            payload["max_tokens"] = min(payload.get("max_tokens", 8000), 8000)  # allow full output for 60–120s
        elif read_timeout_sec is not None:
            payload["model"] = AGENT4_FAST_MODEL
            payload["max_tokens"] = 8000  # e.g. deepseek with 600s timeout
        timeout = httpx.Timeout(read_timeout, connect=15.0)
        max_attempts = 1 if fast_run else 3
        retry_delay_sec = 2 if fast_run else 5
        _default_error_result = {
            "experience_replacements": [],
            "format_content_adjustments": [],
            "experience_optimizations": [],
            "skills_section_optimization": {"has_skills_section": False, "current_skills": [], "user_feedback_options": {}},
            "optimization_summary": {
                "total_experiences_analyzed": 0, "experiences_recommended_for_replacement": 0,
                "total_adjustments_suggested": 0, "total_experiences_optimized": 0, "total_experiences_with_adjustments": 0,
                "skills_section_optimized": False, "expected_match_score_improvement": "0.0 points", "key_improvements": []
            },
            "revised_resume_full": "",
        }
        # Retry on connection/server disconnect (RemoteProtocolError: "Server disconnected without sending a response")
        try:
            response = None
            for attempt in range(max_attempts):
                try:
                    with httpx.Client(timeout=timeout) as client:
                        response = client.post(self.endpoint, headers=headers, json=payload)
                    break
                except httpx.ReadTimeout:
                    if attempt == max_attempts - 1:
                        return {"error": "Agent 4 error: The read operation timed out (retried).", **_default_error_result}
                    time.sleep(retry_delay_sec)
                    continue
                except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.WriteError, OSError) as e:
                    if attempt == max_attempts - 1:
                        return {"error": f"Agent 4 error: {type(e).__name__} - {str(e)[:300]} (retried {max_attempts} times).", **_default_error_result}
                    time.sleep(retry_delay_sec)
                    continue
            if response is None:
                return {"error": "Agent 4 error: No response.", **_default_error_result}
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
                        "total_experiences_with_adjustments": 0,
                        "skills_section_optimized": False,
                        "expected_match_score_improvement": "0.0 points",
                        "key_improvements": []
                    },
                    "revised_resume_full": "",
                    "http_status": response.status_code
                }
            response.raise_for_status()
            result = response.json()
            # Check if response has expected structure
            if "choices" not in result or len(result["choices"]) == 0:
                return {
                    "error": "Invalid API response: no choices in response",
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
                        "total_experiences_with_adjustments": 0,
                        "skills_section_optimized": False,
                        "expected_match_score_improvement": "0.0 points",
                        "key_improvements": []
                    },
                    "revised_resume_full": "",
                }
            # Extract message content (may be None or empty if API truncated/failed)
            message_content = result["choices"][0]["message"].get("content")
            if message_content is None or (isinstance(message_content, str) and not message_content.strip()):
                # Retry up to 2 more times on empty response (transient or overload)
                for retry in range(2):
                    with httpx.Client(timeout=timeout) as client2:
                        response2 = client2.post(self.endpoint, headers=headers, json=payload)
                    if response2.status_code != 200:
                        break
                    result2 = response2.json()
                    if result2.get("choices") and result2["choices"][0].get("message", {}).get("content"):
                        message_content = result2["choices"][0]["message"]["content"]
                        if message_content and message_content.strip():
                            return self._parse_json_response(message_content, resume_text=resume_text)
                # Last resort: minimal prompt (JD + resume only, short) to get at least format_content_adjustments + summary
                fallback = self._fallback_minimal_optimization(jd_text[:1500], resume_text[:2500])
                if fallback:
                    return self._ensure_required_fields(fallback, resume_text=resume_text)
                # Build minimal valid structure from resume so pipeline and Agent 5 can continue
                minimal = self._minimal_output_from_resume(resume_text)
                if minimal:
                    return self._ensure_required_fields(minimal, resume_text=resume_text)
                return {
                    "error": "LLM returned empty response (retried twice)",
                    "experience_replacements": [],
                    "format_content_adjustments": [],
                    "experience_optimizations": [],
                    "skills_section_optimization": {"has_skills_section": False, "current_skills": [], "user_feedback_options": {}},
                    "optimization_summary": {"total_experiences_analyzed": 0, "experiences_recommended_for_replacement": 0, "total_adjustments_suggested": 0, "total_experiences_optimized": 0, "total_experiences_with_adjustments": 0, "skills_section_optimized": False, "expected_match_score_improvement": "0.0 points", "key_improvements": []},
                }
            return self._parse_json_response(message_content, resume_text=resume_text)
                
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", error_data.get("message", error_detail))
            except:
                error_detail = e.response.text[:200] if e.response.text else error_detail
            
            return {
                "error": f"API request failed ({e.response.status_code}): {error_detail}",
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
                },
                "http_status": e.response.status_code
            }
        except Exception as e:
            import traceback
            return {
                "error": f"Agent 4 error: {str(e)}",
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
                },
                "traceback": traceback.format_exc()
            }
    
    def _fallback_minimal_optimization(self, jd_snippet: str, resume_snippet: str) -> Optional[Dict]:
        """When main Agent 4 call returns empty, try one minimal request: JD + resume only, ask for format_content_adjustments + optimization_summary."""
        prompt = 'Output ONLY valid JSON. Keys: "format_content_adjustments" (array, one item per work experience in the resume, each with experience_entry and adjustments array), "optimization_summary" (total_experiences_analyzed, total_adjustments_suggested, key_improvements array). No other keys. Start with { end with }.'
        user_msg = f"JD:\n{jd_snippet}\n\nResume:\n{resume_snippet}\n\nProvide the JSON."
        payload = {"model": self.model, "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": user_msg}], "temperature": 0.2, "max_tokens": 3000}
        if RESPONSE_FORMAT_JSON:
            payload["response_format"] = RESPONSE_FORMAT_JSON
        try:
            with httpx.Client(timeout=httpx.Timeout(120.0, connect=15.0)) as c:
                r = c.post(self.endpoint, headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, json=payload)
            if r.status_code != 200 or not r.json().get("choices"):
                return None
            content = (r.json()["choices"][0].get("message") or {}).get("content")
            if not content or not content.strip():
                return None
            parsed = parse_llm_json_response(content, debug_file=None)
            if isinstance(parsed, dict) and (parsed.get("format_content_adjustments") or parsed.get("optimization_summary")):
                return parsed
        except Exception:
            pass
        return None

    def _minimal_output_from_resume(self, resume_text: str) -> Optional[Dict]:
        """Build minimal valid Agent 4 structure from resume when LLM returns nothing (so pipeline can continue)."""
        import re
        entries = []
        for m in re.finditer(r"(?m)^(.+?)(?:\s+[-–—]\s+|\s+\|\s+)(.+?)(?:\s+\d{4}|\s*$)", resume_text):
            line = (m.group(0) or "").strip()
            if line and len(line) > 10 and any(x in line.upper() for x in ["EXPERIENCE", "MANAGER", "SCIENTIST", "ANALYST", "BANK", "INC", "LTD"]):
                entries.append({"title": m.group(1).strip()[:80], "company": (m.group(2).strip() if m.lastindex >= 2 else "")[:80], "entry_index": len(entries) + 1})
        if not entries:
            entries = [{"title": "Work experience", "company": "", "entry_index": 1}]
        return {
            "experience_replacements": [],
            "format_content_adjustments": [{"experience_entry": e, "adjustments": []} for e in entries],
            "experience_optimizations": [{"experience_entry": e, "optimized_experience": {"optimized_bullets": []}, "optimization_details": [], "user_feedback_options": {}} for e in entries],
            "skills_section_optimization": {"has_skills_section": "skills" in resume_text.lower(), "current_skills": [], "user_feedback_options": {}},
            "optimization_summary": {"total_experiences_analyzed": len(entries), "experiences_recommended_for_replacement": 0, "total_adjustments_suggested": 0, "total_experiences_optimized": len(entries), "total_experiences_with_adjustments": 0, "skills_section_optimized": False, "expected_match_score_improvement": "0 points", "key_improvements": ["LLM returned no content; resume passed through unchanged."]},
        }

    def _parse_json_response(self, content: str, resume_text: Optional[str] = None) -> Dict:
        """
        Parse JSON response from LLM using enhanced parser.
        
        Args:
            content: Raw response content from LLM
            resume_text: Full resume text for validating original_bullet lines
        
        Returns:
            Parsed JSON dictionary with required fields ensured
        """
        try:
            result = parse_llm_json_response(content, debug_file="agent4_raw_response.txt")
            # Ensure required fields exist
            return self._ensure_required_fields(result, resume_text=resume_text)
        except Exception as e:
            # Try to extract JSON-like structures even if full parsing fails
            error_msg = str(e)
            result = {
                "error": f"Failed to parse JSON response: {str(e)}",
                "raw_content_preview": content[:1000] if len(content) > 1000 else content,
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
            
            # Try to find JSON fragments in the error content
            # Look for experience_replacements pattern
            if '"experience_replacements"' in content or "'experience_replacements'" in content:
                # Try to extract a partial structure
                try:
                    # Find the start of experience_replacements array
                    start_idx = content.find('"experience_replacements"')
                    if start_idx == -1:
                        start_idx = content.find("'experience_replacements'")
                    if start_idx != -1:
                        # Try to extract the array
                        array_start = content.find('[', start_idx)
                        if array_start != -1:
                            # Count brackets to find the end
                            bracket_count = 0
                            for i in range(array_start, min(array_start + 5000, len(content))):
                                if content[i] == '[':
                                    bracket_count += 1
                                elif content[i] == ']':
                                    bracket_count -= 1
                                    if bracket_count == 0:
                                        array_content = content[array_start:i+1]
                                        # Try to parse just this array
                                        try:
                                            replacements = json.loads(array_content)
                                            if isinstance(replacements, list) and len(replacements) > 0:
                                                result["experience_replacements"] = replacements
                                        except:
                                            pass
                                        break
                except:
                    pass
            
            return result
    
    def _ensure_required_fields(self, result: Dict, resume_text: Optional[str] = None) -> Dict:
        """
        Ensure all required fields exist in the result and fix structure issues.
        
        Args:
            result: Parsed result dictionary
            resume_text: When set, invalid bullet_level_suggestions rows are dropped
        
        Returns:
            Result dictionary with all required fields
        """
        # Check if there's a single optimization at root level (parsing issue)
        if "experience_replacements" not in result and "format_content_adjustments" not in result and "experience_optimizations" not in result:
            # Check if this looks like a single optimization (has original, suggested, etc.)
            if any(key in result for key in ["original", "suggested", "improvement_type", "star_analysis"]):
                # This is a single optimization, wrap it in experience_optimizations
                result["experience_optimizations"] = [result.copy()]
                # Remove the optimization fields from root
                for key in ["original", "suggested", "improvement_type", "improvement_rationale", "star_analysis", "jd_keywords_added", "expected_impact"]:
                    result.pop(key, None)
        
        if "experience_replacements" not in result:
            result["experience_replacements"] = []
        elif not isinstance(result["experience_replacements"], list):
            result["experience_replacements"] = [result["experience_replacements"]]
        
        if "format_content_adjustments" not in result:
            result["format_content_adjustments"] = []
        elif not isinstance(result["format_content_adjustments"], list):
            result["format_content_adjustments"] = [result["format_content_adjustments"]]
        
        if "experience_optimizations" not in result:
            result["experience_optimizations"] = []
        elif not isinstance(result["experience_optimizations"], list):
            result["experience_optimizations"] = [result["experience_optimizations"]]
        
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
                "total_experiences_optimized": 0,
                "total_experiences_with_adjustments": 0,
                "skills_section_optimized": False,
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
            if "total_experiences_optimized" not in summary:
                summary["total_experiences_optimized"] = 0
            if "total_experiences_with_adjustments" not in summary:
                summary["total_experiences_with_adjustments"] = 0
            if "skills_section_optimized" not in summary:
                summary["skills_section_optimized"] = False
            if "expected_match_score_improvement" not in summary:
                summary["expected_match_score_improvement"] = "0.0 points"
            if "key_improvements" not in summary:
                summary["key_improvements"] = []
            if "total_experiences_optimized" not in summary:
                summary["total_experiences_optimized"] = 0
            if "skills_section_optimized" not in summary:
                summary["skills_section_optimized"] = False
        
        if "revised_resume_full" not in result:
            result["revised_resume_full"] = ""
        elif not isinstance(result["revised_resume_full"], str):
            result["revised_resume_full"] = str(result["revised_resume_full"]) if result["revised_resume_full"] else ""

        if "bullet_level_suggestions" not in result:
            result["bullet_level_suggestions"] = []
        elif not isinstance(result["bullet_level_suggestions"], list):
            result["bullet_level_suggestions"] = [result["bullet_level_suggestions"]]
        else:
            _tri = ("High", "Medium", "Low")
            for group in result["bullet_level_suggestions"]:
                if not isinstance(group, dict):
                    continue
                if group.get("experience_jd_importance") not in _tri:
                    group["experience_jd_importance"] = "Medium"
                suggestions = group.get("suggestions")
                if not isinstance(suggestions, list):
                    group["suggestions"] = []
                    continue
                for s in suggestions:
                    if not isinstance(s, dict):
                        continue
                    s.pop("jd_match_level", None)
                    _normalize_bullet_reason(s)

        _filter_invalid_bullet_suggestions(result, resume_text)
        _map_experience_level_rewrites(result)

        if "tailor_strategy" not in result or not isinstance(result.get("tailor_strategy"), dict):
            result["tailor_strategy"] = {
                "top_3_jd_keywords": [],
                "core_narrative_one_liner": "",
                "sections_to_emphasize": [],
                "sections_to_compress_or_remove": [],
                "match_too_low_warning": "",
            }

        if "resume_diagnosis" not in result or not isinstance(result.get("resume_diagnosis"), dict):
            result["resume_diagnosis"] = {"issues": []}

        if "summary_suggestion" not in result or not isinstance(result.get("summary_suggestion"), dict):
            result["summary_suggestion"] = {
                "recommended_action": "skip",
                "has_existing_summary": False,
                "original_summary": "",
                "suggested_summary": "",
                "suggested_headline": "",
                "jd_keywords_embedded": [],
                "feedback_actions": ["accept", "reject", "further_modify"],
            }
        _normalize_summary_suggestion(result, resume_text)

        if "experience_level_rewrites" not in result:
            result["experience_level_rewrites"] = []
        elif not isinstance(result["experience_level_rewrites"], list):
            result["experience_level_rewrites"] = [result["experience_level_rewrites"]]

        # API/UI only expose bullet_level_suggestions; never return replacement blocks.
        result["experience_replacements"] = []

        return result
