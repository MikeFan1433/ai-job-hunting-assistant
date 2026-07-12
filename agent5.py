"""Agent 5: Interview Preparation Assistant."""
import json
import re
import time
import httpx
from typing import Dict, Optional, List
from config import AI_BUILDER_BASE_URL, STUDENT_PORTAL_API_KEY, LLM_MODEL_JSON, RESPONSE_FORMAT_JSON, AGENT5_FAST_MODEL
from agent5_prompt_compressed import AGENT5_SYSTEM_BRIEF, AGENT5_JSON_SCHEMA, AGENT5_INTERVIEW_PREPARATION_PROMPT
from json_parser_utils import parse_llm_json_response
from llm_output_language import output_language_suffix


def _work_experiences_from_agent4(agent4_outputs: Dict) -> List[Dict]:
    """Build list of work experience entries from Agent 4 experience_optimizations when optimized_work_experiences is missing."""
    out = []
    optimizations = agent4_outputs.get("experience_optimizations") or []
    for entry in optimizations:
        if isinstance(entry, dict):
            bullets = []
            opt_exp = entry.get("optimized_experience")
            if isinstance(opt_exp, dict) and opt_exp.get("optimized_bullets"):
                bullets = list(opt_exp["optimized_bullets"])
            if not bullets and entry.get("suggested"):
                bullets = [entry["suggested"]]
            if not bullets and entry.get("original"):
                bullets = [entry["original"]]
            if bullets:
                out.append({"experience_entry": entry.get("experience_entry"), "bullets": bullets})
    return out


class InterviewPreparationAgent:
    """Agent 5: Generates comprehensive interview preparation materials."""
    
    def __init__(self, model: str = None):
        """Initialize the interview preparation agent. Uses gpt-5 by default for JSON mode (AI Builder API)."""
        model = model or LLM_MODEL_JSON
        self.base_url = AI_BUILDER_BASE_URL
        self.api_key = STUDENT_PORTAL_API_KEY
        self.model = model
        self.endpoint = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("STUDENT_PORTAL_API_KEY not set")
    
    def _build_agent2_skill_context(self, agent2_outputs: Dict) -> str:
        """Extract must-haves, gaps, hidden signals, and interview preview for interview-predictor."""
        jra = agent2_outputs.get("job_role_team_analysis") or {}
        icp = agent2_outputs.get("ideal_candidate_profile") or {}
        ma = agent2_outputs.get("match_assessment") or {}
        must_haves = []
        for item in (icp.get("hard_skills") or {}).get("must_have") or []:
            if isinstance(item, dict) and item.get("skill"):
                must_haves.append(f"- {item['skill']}: {item.get('details', '')}")
            elif isinstance(item, str) and item.strip():
                must_haves.append(f"- {item.strip()}")
        hidden_signals = []
        for item in jra.get("problems_to_solve") or []:
            if isinstance(item, str) and item.strip():
                hidden_signals.append(f"- {item.strip()}")
        if isinstance(jra.get("team_objectives"), str) and jra["team_objectives"].strip():
            hidden_signals.append(f"- team_objectives: {jra['team_objectives'][:400]}")
        gaps = []
        for dim in ("industry_match", "experience_match", "skills_match"):
            block = ma.get(dim) or {}
            for g in block.get("gaps") or []:
                if isinstance(g, dict) and g.get("point"):
                    gaps.append(f"- [{dim}] {g['point']} → {g.get('remedy', '')}")
        preview_lines = []
        for p in ma.get("interview_question_preview") or []:
            if isinstance(p, dict) and p.get("question"):
                preview_lines.append(
                    f"- [{p.get('category', 'Behavior')}] {p['question']} ({p.get('why_likely', '')})"
                )
        parts = []
        if must_haves:
            parts.append("Must-haves (for question mapping):\n" + "\n".join(must_haves[:12]))
        if hidden_signals:
            parts.append("Hidden signals / decoded real needs:\n" + "\n".join(hidden_signals[:10]))
        if gaps:
            parts.append("Gaps to prepare (prioritize probes):\n" + "\n".join(gaps[:15]))
        if preview_lines:
            parts.append("Agent 2 interview_question_preview seeds:\n" + "\n".join(preview_lines[:10]))
        if ma.get("match_percentage"):
            parts.append(f"Match percentage: {ma.get('match_percentage')}")
        verdict = (ma.get("application_decision") or {}).get("verdict")
        if verdict:
            parts.append(f"Application verdict: {verdict}")
        return "\n\n".join(parts) if parts else "No structured Agent 2 skill context available."

    def _normalize_behavioral_questions(self, theme1: Dict) -> None:
        """Sort and normalize top_behavioral_questions from interview-predictor schema."""
        key = "top_10_behavioral_questions"
        questions = theme1.get(key) or theme1.get("top_behavioral_questions") or []
        if not isinstance(questions, list):
            questions = []
        normalized = []
        for i, q in enumerate(questions):
            if not isinstance(q, dict):
                continue
            item = dict(q)
            if "priority_rank" not in item or not isinstance(item.get("priority_rank"), (int, float)):
                item["priority_rank"] = i + 1
            else:
                item["priority_rank"] = int(item["priority_rank"])
            item.setdefault("priority", "high" if item["priority_rank"] <= 5 else "medium")
            item.setdefault("category", "Behavior")
            item.setdefault("source_jd_anchor", "")
            item.setdefault("competency_tested", "")
            why = item.get("why_they_ask_this")
            if isinstance(why, str) and why.strip() and not why.strip().startswith("[Behavior]"):
                item["why_they_ask_this"] = f"[Behavior] {why.strip()}"
            normalized.append(item)
        normalized.sort(key=lambda x: x.get("priority_rank", 99))
        theme1[key] = normalized
        if "top_behavioral_questions" in theme1:
            theme1.pop("top_behavioral_questions", None)

    def _normalize_predicted_interview_questions(self, summary: Dict) -> None:
        """Normalize preparation_summary.predicted_interview_questions Top 10."""
        if not isinstance(summary, dict):
            return
        questions = summary.get("predicted_interview_questions") or []
        if not isinstance(questions, list):
            questions = []
        valid_categories = ("Behavior", "Domain", "Craft", "Company")
        normalized = []
        for q in questions:
            if not isinstance(q, dict):
                continue
            question = str(q.get("question") or "").strip()
            if not question:
                continue
            cat = str(q.get("category") or "Behavior").strip()
            if cat not in valid_categories:
                cat = "Behavior"
            priority = str(q.get("priority") or "medium").strip().lower()
            if priority not in ("high", "medium"):
                priority = "medium"
            normalized.append({
                "question": question,
                "category": cat,
                "why_likely": str(q.get("why_likely") or q.get("why") or "").strip(),
                "priority": priority,
                "answer_framework": list(q.get("answer_framework") or []) if isinstance(q.get("answer_framework"), list) else [],
                "key_points_to_emphasize": list(q.get("key_points_to_emphasize") or []) if isinstance(q.get("key_points_to_emphasize"), list) else [],
            })
        priority_order = {"high": 0, "medium": 1}
        cat_order = {"Behavior": 0, "Domain": 1, "Craft": 2, "Company": 3}
        normalized.sort(key=lambda x: (priority_order.get(x["priority"], 1), cat_order.get(x["category"], 9)))
        summary["predicted_interview_questions"] = normalized[:10]

    def _migrate_behavioral_frameworks_to_predicted(self, interview_prep: Dict) -> None:
        """Copy answer_framework from legacy top_behavioral_questions into predicted Top 10 when missing."""
        summary = interview_prep.get("preparation_summary") or {}
        predicted = summary.get("predicted_interview_questions") or []
        if not predicted:
            return
        theme1 = interview_prep.get("theme_1_behavioral_interview") or interview_prep.get("behavioral_interview") or {}
        behavioral = theme1.get("top_10_behavioral_questions") or theme1.get("top_behavioral_questions") or []
        if not behavioral:
            return
        by_q: Dict[str, Dict] = {}
        for bq in behavioral:
            if not isinstance(bq, dict):
                continue
            qtext = str(bq.get("question") or "").strip().lower()
            if qtext:
                by_q[qtext] = bq
        for pq in predicted:
            if not isinstance(pq, dict):
                continue
            if pq.get("answer_framework"):
                continue
            key = str(pq.get("question") or "").strip().lower()
            src = by_q.get(key)
            if not src:
                continue
            if src.get("answer_framework"):
                pq["answer_framework"] = list(src["answer_framework"])
            if src.get("key_points_to_emphasize") and not pq.get("key_points_to_emphasize"):
                pq["key_points_to_emphasize"] = list(src["key_points_to_emphasize"])
            if src.get("why_they_ask_this") and not pq.get("why_likely"):
                pq["why_likely"] = str(src["why_they_ask_this"])

    def _sanitize_star_placeholders(self, interview_prep: Dict) -> None:
        """Ensure action/result fields use placeholders when they contain suspicious bare metrics."""
        placeholder_en = "[Add specific metric]"
        placeholder_zh = "[待你补充具体动作/数字]"
        metric_pattern = re.compile(r"\b\d{1,3}%\b|\b\d{4,}\b")

        def _maybe_tag(text: str) -> str:
            if not text or placeholder_en in text or placeholder_zh in text:
                return text
            if metric_pattern.search(text) and "[" not in text:
                return text + f" {placeholder_zh}"
            return text

        t1 = interview_prep.get("theme_1_behavioral_interview") or interview_prep.get("behavioral_interview") or {}
        story = t1.get("storytelling_example") or {}
        for key in ("action", "impact", "result"):
            if key in story and isinstance(story[key], str):
                story[key] = _maybe_tag(story[key])
        t2 = interview_prep.get("theme_2_project_deep_dive") or interview_prep.get("project_deep_dive") or {}
        for proj in t2.get("selected_projects") or []:
            star = proj.get("project_overview_star") or {}
            for key in ("action", "result"):
                if key in star and isinstance(star[key], str):
                    star[key] = _maybe_tag(star[key])

    def prepare_interview(
        self,
        jd_text: str,
        final_resume: str,
        agent2_outputs: Dict,
        agent4_outputs: Dict,
        read_timeout_sec: Optional[float] = None,
        fast_run: bool = False,
        preferred_lang: Optional[str] = "en",
    ) -> Dict:
        """
        Generate comprehensive interview preparation materials.
        
        Args:
            jd_text: Job description text
            final_resume: Final optimized resume after all modifications (from Agent 4)
            agent2_outputs: Complete Agent 2 analysis output
            agent4_outputs: Complete Agent 4 output
            read_timeout_sec: Optional read timeout in seconds (e.g. 8 for fast run). Default 600.
            fast_run: If True, use fewer retries (1) and shorter retry delay (2s) to finish under 30s total.
        
        Returns:
            Dictionary with interview preparation materials
        """
        # Extract data from Agent 4 outputs
        classified_projects = agent4_outputs.get("classified_projects", {
            "resume_adopted_projects": [],
            "resume_not_adopted_projects": []
        })
        optimized_work_experiences = agent4_outputs.get("optimized_work_experiences", [])
        optimized_project_documents = agent4_outputs.get("optimized_project_documents", [])
        # Derive work experiences from experience_optimizations when Agent 4 uses that schema
        if not optimized_work_experiences:
            optimized_work_experiences = _work_experiences_from_agent4(agent4_outputs)
        # Truncate large inputs to reduce server-side timeout / disconnect risk (same rationale as Agent 4)
        jd_use = jd_text[:3500] if len(jd_text) > 3500 else jd_text
        resume_use = final_resume[:5000] if len(final_resume) > 5000 else final_resume
        agent2_str = json.dumps(agent2_outputs, indent=2, ensure_ascii=False)
        if len(agent2_str) > 12000:
            agent2_str = agent2_str[:12000] + "\n... (truncated)"
        work_exp_str = json.dumps(optimized_work_experiences, indent=2, ensure_ascii=False)
        if len(work_exp_str) > 6000:
            work_exp_str = work_exp_str[:6000] + "\n... (truncated)"
        proj_doc_str = json.dumps(optimized_project_documents, indent=2, ensure_ascii=False)
        if len(proj_doc_str) > 6000:
            proj_doc_str = proj_doc_str[:6000] + "\n... (truncated)"
        classified_str = json.dumps(classified_projects, indent=2, ensure_ascii=False)
        if len(classified_str) > 3000:
            classified_str = classified_str[:3000] + "\n... (truncated)"
        skill_context = self._build_agent2_skill_context(agent2_outputs)
        _schema = AGENT5_JSON_SCHEMA or ""
        user_message = f"""Please generate comprehensive interview preparation materials based on the following:

=== JOB DESCRIPTION ===
{jd_use}

=== FINAL OPTIMIZED RESUME (Complete Format) ===
{resume_use}

=== AGENT 2 SKILL CONTEXT (must-haves, gaps, interview preview) ===
{skill_context}

=== OPTIMIZED WORK EXPERIENCES (Bullet Points) ===
{work_exp_str}

=== OPTIMIZED PROJECT DOCUMENTS (Adopted into Resume) ===
{proj_doc_str}

=== AGENT 2 ANALYSIS OUTPUTS ===
{agent2_str}

=== CLASSIFIED PROJECTS ===
{classified_str}

=== REQUIRED JSON SCHEMA ===
{_schema}

Generate interview preparation materials with all 4 top-level keys. Return only valid JSON.{output_language_suffix(preferred_lang)}"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        use_fast_model = fast_run or (read_timeout_sec is not None and read_timeout_sec <= 120)
        model_to_use = AGENT5_FAST_MODEL if use_fast_model else self.model
        # Large interview packages routinely exceed 8k tokens; truncation yields empty parse.
        max_tokens = 16384
        payload = {
            "model": model_to_use,
            "messages": [
                {"role": "system", "content": AGENT5_SYSTEM_BRIEF},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.3,
            "max_tokens": max_tokens,
        }
        if RESPONSE_FORMAT_JSON is not None:
            payload["response_format"] = RESPONSE_FORMAT_JSON
        
        read_timeout = read_timeout_sec if read_timeout_sec is not None else 600.0
        timeout = httpx.Timeout(read_timeout, connect=15.0)
        max_attempts = 1 if fast_run else 3
        retry_delay_sec = 2 if fast_run else 5
        try:
            response = None
            for attempt in range(max_attempts):
                try:
                    with httpx.Client(timeout=timeout) as client:
                        response = client.post(self.endpoint, headers=headers, json=payload)
                    break
                except httpx.ReadTimeout:
                    if attempt == max_attempts - 1:
                        result = self._ensure_required_fields({})
                        result["error"] = "Agent 5 error: The read operation timed out (retried)."
                        return result
                    time.sleep(retry_delay_sec)
                    continue
                except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.WriteError, OSError) as e:
                    if attempt == max_attempts - 1:
                        result = self._ensure_required_fields({})
                        result["error"] = f"Agent 5 error: {type(e).__name__} - {str(e)[:300]} (retried {max_attempts} times)."
                        return result
                    time.sleep(retry_delay_sec)
                    continue
            if response is None:
                return self._ensure_required_fields({"error": "Agent 5 error: No response."})
            # Check for HTTP errors
            if response.status_code != 200:
                error_detail = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", error_data.get("message", error_detail))
                except:
                    error_detail = response.text[:200] if response.text else error_detail
                print(f"⚠️  Warning: API request failed ({response.status_code}): {error_detail}")
                result = self._ensure_required_fields({})
                result["error"] = f"API request failed ({response.status_code}): {error_detail}"
                result["http_status"] = response.status_code
                return result
            response.raise_for_status()
            result = response.json()
            # Check if response has expected structure
            if "choices" not in result or len(result["choices"]) == 0:
                print("⚠️  Warning: Agent 5 response has no choices, returning default structure")
                return self._ensure_required_fields({"error": "Invalid API response: no choices in response"})
            # Extract message content (may be None or empty)
            message_content = result["choices"][0]["message"].get("content")
            if message_content is None or (isinstance(message_content, str) and not message_content.strip()):
                # Retry once on empty
                for _ in range(1):
                    with httpx.Client(timeout=timeout) as client2:
                        response2 = client2.post(self.endpoint, headers=headers, json=payload)
                    if response2.status_code != 200:
                        break
                    result2 = response2.json()
                    if result2.get("choices") and result2["choices"][0].get("message", {}).get("content"):
                        message_content = result2["choices"][0]["message"]["content"]
                        if message_content and message_content.strip():
                            break
                if not message_content or not (isinstance(message_content, str) and message_content.strip()):
                    print("⚠️  Warning: Agent 5 returned empty response after retry")
                    return self._ensure_required_fields(self._minimal_interview_prep())
            import logging
            _log = logging.getLogger("agent5")
            _log.info(f"Agent 5 raw response: {len(message_content)} chars, preview: {message_content[:300]}")
            if not re.search(r'\{[^{}]*\}', message_content, re.DOTALL):
                _log.warning("Agent 5 response contains no JSON")
                return self._ensure_required_fields({})
            try:
                interview_prep = self._parse_json_response(message_content)
                _log.info(f"Agent 5 parsed keys: {list(interview_prep.keys())[:10]}")
                self._sanitize_star_placeholders(interview_prep)
                interview_prep = self._ensure_required_fields(interview_prep)
                return interview_prep
            except Exception as parse_error:
                print(f"⚠️  Warning: Failed to parse Agent 5 JSON: {str(parse_error)}")
                print("   Attempting to extract partial structure...")
                try:
                    partial_prep = self._extract_partial_structure(message_content)
                    partial_prep = self._ensure_required_fields(partial_prep)
                    partial_prep["parse_error"] = str(parse_error)
                    partial_prep["raw_response_preview"] = message_content[:500]
                    return partial_prep
                except:
                    default_prep = self._ensure_required_fields({})
                    default_prep["parse_error"] = str(parse_error)
                    default_prep["raw_response_preview"] = message_content[:500]
                    return default_prep
        
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", error_data.get("message", error_detail))
            except:
                error_detail = e.response.text[:200] if e.response.text else error_detail
            
            print(f"⚠️  Warning: API request failed ({e.response.status_code}): {error_detail}")
            result = self._ensure_required_fields({})
            result["error"] = f"API request failed ({e.response.status_code}): {error_detail}"
            result["http_status"] = e.response.status_code
            return result
        except Exception as e:
            import traceback
            print(f"⚠️  Warning: Error generating interview preparation: {str(e)}")
            result = self._ensure_required_fields({})
            result["error"] = f"Agent 5 error: {str(e)}"
            result["traceback"] = traceback.format_exc()
            return result
    
    def _minimal_interview_prep(self) -> Dict:
        """Return minimal valid structure when LLM returns empty (no error key so pipeline continues)."""
        return {
            "theme_1_behavioral_interview": {
                "self_introduction": {"paragraph_1": "", "paragraph_2": "", "paragraph_3": "", "full_text": "LLM did not return content. Prepare based on your resume and the job description.", "key_highlights": [], "jd_alignment_notes": ""},
                "storytelling_example": {},
                "top_10_behavioral_questions": []
            },
            "theme_2_project_deep_dive": {"selected_projects": []},
            "theme_3_business_domain": {"business_questions": []}
        }

    def _parse_json_response(self, content: str) -> Dict:
        """
        Parse JSON response from LLM using enhanced parser.
        
        Args:
            content: Raw response content from LLM
        
        Returns:
            Parsed JSON dictionary
        """
        try:
            result = parse_llm_json_response(content, debug_file="agent5_raw_response.txt")
            if result and isinstance(result, dict):
                _has_new = any(k in result for k in ("behavioral_interview", "project_deep_dive", "business_domain", "interview_rounds"))
                _has_old = any(k in result for k in ("theme_1_behavioral_interview", "theme_2_project_deep_dive"))
                if _has_new or _has_old:
                    return result
                elif "self_introduction" in result or "storytelling_example" in result:
                    partial = self._extract_partial_structure(content)
                    return {
                        "theme_1_behavioral_interview": result,
                        "theme_2_project_deep_dive": partial.get("theme_2_project_deep_dive", {}),
                        "theme_3_business_domain": partial.get("theme_3_business_domain", {}),
                        "preparation_summary": {}
                    }
                else:
                    return self._extract_partial_structure(content)
            else:
                return self._extract_partial_structure(content)
        except Exception as e:
            # If parsing fails, try to extract partial structure
            print(f"⚠️  Warning: Agent 5 JSON parsing failed: {str(e)}")
            print("   Attempting to extract partial structure...")
            
            # Try to extract at least some structure
            result = {}
            
            # Try to find theme_1_behavioral_interview
            if '"theme_1_behavioral_interview"' in content or "'theme_1_behavioral_interview'" in content:
                try:
                    # Extract the theme_1 section
                    start_idx = content.find('"theme_1_behavioral_interview"')
                    if start_idx == -1:
                        start_idx = content.find("'theme_1_behavioral_interview'")
                    if start_idx != -1:
                        # Try to extract the JSON object for this theme
                        brace_count = 0
                        in_string = False
                        escape_next = False
                        obj_start = content.find('{', start_idx)
                        if obj_start != -1:
                            for i in range(obj_start, min(obj_start + 10000, len(content))):
                                char = content[i]
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
                                            obj_start = i
                                        brace_count += 1
                                    elif char == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            theme1_content = content[obj_start:i+1]
                                            try:
                                                theme1_obj = json.loads(theme1_content)
                                                result["theme_1_behavioral_interview"] = theme1_obj
                                            except:
                                                pass
                                            break
                except:
                    pass
            
            # Return partial result with error info
            result["parse_error"] = str(e)
            result["raw_response_preview"] = content[:1000]
            return result
    
    def _extract_partial_structure(self, content: str) -> Dict:
        """
        Extract partial structure from content when full JSON parsing fails.
        Uses more robust extraction to handle nested JSON objects.
        
        Args:
            content: Raw response content
        
        Returns:
            Dictionary with any extracted structure
        """
        result = {}
        
        def extract_nested_json(key: str) -> Optional[Dict]:
            """Extract nested JSON object for a given key."""
            # Find the key position
            key_pattern = rf'"{re.escape(key)}"\s*:\s*'
            match = re.search(key_pattern, content)
            if not match:
                return None
            
            start_pos = match.end()
            
            # Find the opening brace
            brace_start = content.find('{', start_pos)
            if brace_start == -1:
                return None
            
            # Count braces to find the matching closing brace
            brace_count = 0
            in_string = False
            escape_next = False
            
            for i in range(brace_start, len(content)):
                char = content[i]
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
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Found the complete JSON object
                            json_str = content[brace_start:i+1]
                            try:
                                return json.loads(json_str)
                            except:
                                return None
            return None
        
        # Try to extract theme_1_behavioral_interview (legacy) or behavioral_interview (new)
        theme1 = extract_nested_json("theme_1_behavioral_interview") or extract_nested_json("behavioral_interview")
        if theme1:
            result["theme_1_behavioral_interview"] = theme1
        
        # Try to extract theme_2_project_deep_dive / project_deep_dive
        theme2 = extract_nested_json("theme_2_project_deep_dive") or extract_nested_json("project_deep_dive")
        if theme2:
            result["theme_2_project_deep_dive"] = theme2
        
        # Try to extract theme_3_business_domain / business_domain
        theme3 = extract_nested_json("theme_3_business_domain") or extract_nested_json("business_domain")
        if theme3:
            result["theme_3_business_domain"] = theme3

        prep = extract_nested_json("preparation_summary")
        if prep:
            result["preparation_summary"] = prep
        
        return result
    
    def _ensure_required_fields(self, interview_prep: Dict) -> Dict:
        """
        Ensure the output contains all required fields.
        Maps new schema keys to legacy theme-based keys for frontend compatibility.
        """
        # Map new schema keys → legacy theme-based keys
        _key_map = {
            "behavioral_interview": "theme_1_behavioral_interview",
            "project_deep_dive": "theme_2_project_deep_dive",
            "business_domain": "theme_3_business_domain",
        }
        for new_k, old_k in _key_map.items():
            if new_k in interview_prep and old_k not in interview_prep:
                interview_prep[old_k] = interview_prep.pop(new_k)
        # Map sub-key differences (new prompt uses different question list names)
        t1 = interview_prep.get("theme_1_behavioral_interview", {})
        if "top_behavioral_questions" in t1 and "top_10_behavioral_questions" not in t1:
            t1["top_10_behavioral_questions"] = t1.pop("top_behavioral_questions")
        self._normalize_behavioral_questions(t1)
        t2 = interview_prep.get("theme_2_project_deep_dive", {})
        for proj in (t2.get("selected_projects") or []):
            if "deep_dive_questions" in proj and "technical_deep_dive_questions" not in proj:
                proj["technical_deep_dive_questions"] = proj.pop("deep_dive_questions")
            if "project_overview_answer" in proj:
                legacy = proj.pop("project_overview_answer")
                legacy_s = legacy.strip() if isinstance(legacy, str) else (str(legacy).strip() if legacy else "")
                if legacy_s:
                    existing = proj.get("project_overview_star")
                    if not isinstance(existing, dict):
                        proj["project_overview_star"] = {"full_overview_answer": legacy_s}
                    else:
                        has_star = any(
                            str(existing.get(k) or "").strip() for k in ("situation", "task", "action", "result")
                        )
                        if not has_star and not str(existing.get("full_overview_answer") or "").strip():
                            existing["full_overview_answer"] = legacy_s
            elif "project_overview_star" not in proj:
                proj["project_overview_star"] = {}

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
        # Ensure each behavioral question has required fields
        for question in theme1.get("top_10_behavioral_questions", []):
            if "question" not in question:
                question["question"] = ""
            if "why_they_ask_this" not in question:
                question["why_they_ask_this"] = ""
            if "answer_framework" not in question:
                question["answer_framework"] = []
            if "key_points_to_emphasize" not in question:
                question["key_points_to_emphasize"] = []
            question.setdefault("source_jd_anchor", "")
            question.setdefault("competency_tested", "")
            question.setdefault("priority_rank", 0)
            question.setdefault("priority", "medium")
            question.setdefault("category", "Behavior")
        
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
        
        # Ensure theme_2_project_deep_dive has proper structure
        theme2 = interview_prep.get("theme_2_project_deep_dive", {})
        if "selected_projects" not in theme2:
            theme2["selected_projects"] = []
        # Ensure each project has required fields
        for project in theme2.get("selected_projects", []):
            project.pop("selection_reason", None)
            pos = project.get("project_overview_star")
            if isinstance(pos, str):
                project["project_overview_star"] = {
                    "situation": "",
                    "task": "",
                    "action": "",
                    "result": "",
                    "full_overview_answer": pos.strip(),
                }
                pos = project["project_overview_star"]
            elif "project_overview_star" not in project or not isinstance(pos, dict):
                project["project_overview_star"] = {
                    "situation": "",
                    "task": "",
                    "action": "",
                    "result": "",
                    "full_overview_answer": "",
                }
                pos = project["project_overview_star"]
            else:
                for k in ("situation", "task", "action", "result", "full_overview_answer"):
                    v = pos.get(k)
                    pos[k] = v.strip() if isinstance(v, str) else ("" if v is None else str(v).strip())
            if "answer_scenario" not in project or not isinstance(project.get("answer_scenario"), dict):
                project["answer_scenario"] = {}
            ac = project["answer_scenario"]
            for k in ("why_important_for_jd", "when_to_use_in_interview"):
                v = ac.get(k)
                ac[k] = v.strip() if isinstance(v, str) else ""
            if "technical_deep_dive_questions" not in project:
                project["technical_deep_dive_questions"] = []
            # Ensure each question has required fields
            for question in project.get("technical_deep_dive_questions", []):
                if "how_to_answer" not in question:
                    question["how_to_answer"] = {
                        "structure": "",
                        "key_points": [],
                        "technical_details_to_include": [],
                        "what_to_emphasize": ""
                    }
        
        # Ensure theme_3_business_domain has proper structure
        theme3 = interview_prep.get("theme_3_business_domain", {})
        if "business_questions" not in theme3:
            theme3["business_questions"] = []
        # Ensure each question has required fields
        for question in theme3.get("business_questions", []):
            if "how_to_answer" not in question:
                question["how_to_answer"] = {
                    "structure": "",
                    "key_points": [],
                    "business_acumen_to_demonstrate": "",
                    "connection_to_role": ""
                }

        # Ensure preparation_summary exists
        if "preparation_summary" not in interview_prep:
            interview_prep["preparation_summary"] = {
                "total_behavioral_questions": len(theme1.get("top_10_behavioral_questions", [])),
                "total_projects_analyzed": len(theme2.get("selected_projects", [])),
                "total_technical_questions": sum(
                    len(p.get("technical_deep_dive_questions", []))
                    for p in theme2.get("selected_projects", [])
                ),
                "total_business_questions": len(theme3.get("business_questions", [])),
                "key_preparation_focus_areas": [],
                "predicted_interview_questions": [],
            }
        summary = interview_prep["preparation_summary"]
        summary["total_behavioral_questions"] = len(theme1.get("top_10_behavioral_questions", []))
        summary["total_projects_analyzed"] = len(theme2.get("selected_projects", []))
        summary["total_technical_questions"] = sum(
            len(p.get("technical_deep_dive_questions", []))
            for p in theme2.get("selected_projects", [])
        )
        summary["total_business_questions"] = len(theme3.get("business_questions", []))
        summary.setdefault("key_preparation_focus_areas", [])
        summary.setdefault("highest_risk_gaps_to_prepare", [])
        summary.setdefault("additional_question_bank", [])
        summary.setdefault("top_5_must_practice", [])
        summary.setdefault("strongest_stories_to_lead_with", [])
        summary.setdefault("predicted_interview_questions", [])
        self._normalize_predicted_interview_questions(summary)
        self._migrate_behavioral_frameworks_to_predicted(interview_prep)

        return interview_prep
