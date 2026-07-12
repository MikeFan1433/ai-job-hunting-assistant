"""Agent 2: JD Analysis & Matching Assessment Agent.
Uses AI Builder API endpoints as specified in: https://space.ai-builders.com/backend/openapi.json
"""
import json
import os
import re
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional, Tuple
from config import AI_BUILDER_BASE_URL, STUDENT_PORTAL_API_KEY, LLM_MODEL_JSON, RESPONSE_FORMAT_JSON, AGENT2_FAST_MODEL
from agent_prompts import AGENT2_JD_ANALYSIS_PROMPT
from json_parser_utils import parse_llm_json_response
from llm_output_language import output_language_suffix
try:
    from agent2_prompt_compressed import (
        AGENT2_SYSTEM_BRIEF,
        AGENT2_JSON_SCHEMA,
    )
except ImportError:
    AGENT2_SYSTEM_BRIEF = None
    AGENT2_JSON_SCHEMA = None
AGENT2_JD_ANALYSIS_PROMPT_FAST = AGENT2_JD_ANALYSIS_PROMPT_20S = None
AGENT2_SECTION_JOB_ROLE = AGENT2_SECTION_IDEAL_PROFILE = AGENT2_SECTION_MATCH = None


def _has_content(obj) -> bool:
    """Return False if obj is empty (dict/list) or blank string."""
    if obj is None:
        return False
    if isinstance(obj, dict):
        return len(obj) > 0
    if isinstance(obj, list):
        return len(obj) > 0
    if isinstance(obj, str):
        return bool(obj.strip())
    return True


def _match_assessment_complete(ma: Dict) -> bool:
    """True if match_assessment has industry_match, experience_match, skills_match with content."""
    if not ma or not isinstance(ma, dict):
        return False
    for key in ("industry_match", "experience_match", "skills_match"):
        block = ma.get(key)
        if not block or not isinstance(block, dict):
            return False
        if not _has_content(block.get("strengths")) and not _has_content(block.get("score")):
            return False
    return True


def _safe_float(val, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def derive_match_fit_tier(ma: Dict) -> str:
    """Deterministic tier from overall and dimension scores (same rules as Agent 2 prompt)."""
    o = _safe_float(ma.get("overall_match_score"), 0.0)
    dims = []
    for key in ("industry_match", "experience_match", "skills_match"):
        block = ma.get(key)
        if isinstance(block, dict) and block.get("score") is not None:
            dims.append(_safe_float(block.get("score"), o))
    min_dim = min(dims) if dims else o
    if o >= 3.8 and min_dim >= 2.0:
        return "full"
    if o < 2.5:
        return "none"
    return "partial"


def _parse_percentage_upper_bound(raw: str) -> Optional[float]:
    """Extract upper bound from match_percentage like '68-74%' or '72%'."""
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip().replace("%", "")
    if "-" in s:
        parts = s.split("-", 1)
        try:
            return float(parts[1].strip())
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def normalize_match_percentage_range(ma: Dict) -> None:
    """Ensure match_percentage is a range string; derive from 0-5 score if missing."""
    if not ma or not isinstance(ma, dict):
        return
    raw = ma.get("match_percentage")
    if isinstance(raw, (int, float)):
        pct = int(round(float(raw)))
        ma["match_percentage"] = f"{max(0, pct - 4)}-{min(100, pct + 4)}%"
        return
    if isinstance(raw, str) and raw.strip():
        s = raw.strip()
        if "-" not in s and s.replace("%", "").replace(".", "", 1).isdigit():
            try:
                pct = float(s.replace("%", ""))
                ma["match_percentage"] = f"{max(0, int(pct) - 4)}-{min(100, int(pct) + 4)}%"
            except ValueError:
                pass
        elif not s.endswith("%") and re.match(r"^\d+\s*-\s*\d+$", s):
            ma["match_percentage"] = s.replace(" ", "") + "%"
        return
    try:
        score = _safe_float(ma.get("overall_match_score"), 0.0)
        mid = int(round(score * 20))
        lo = max(0, mid - 6)
        hi = min(100, mid + 6)
        ma["match_percentage"] = f"{lo}-{hi}%"
    except (TypeError, ValueError):
        ma["match_percentage"] = "0-10%"


def reconcile_dual_track_scoring(ma: Dict) -> None:
    """Downgrade verdict when 0-5 scores and match_percentage range contradict."""
    if not ma or not isinstance(ma, dict):
        return
    upper = _parse_percentage_upper_bound(str(ma.get("match_percentage", "")))
    overall = _safe_float(ma.get("overall_match_score"), 0.0)
    ad = ma.get("application_decision")
    if not isinstance(ad, dict):
        return
    if upper is not None and overall >= 4.0 and upper < 65:
        if ad.get("verdict") == "strong_apply":
            ad["verdict"] = "worth_trying"
        ma["match_level"] = "Moderate"
    if upper is not None and overall < 2.8 and upper > 80:
        lo = max(0, int(overall * 20) - 8)
        hi = int(overall * 20) + 4
        ma["match_percentage"] = f"{lo}-{hi}%"
        if ad.get("verdict") in ("strong_apply", "worth_trying"):
            ad["verdict"] = "low_priority"
    ma["application_decision"] = ad


def normalize_interview_question_preview(ma: Dict) -> None:
    """Keep interview_question_preview as a list for Agent 5 handoff."""
    if not ma or not isinstance(ma, dict):
        return
    preview = ma.get("interview_question_preview")
    if preview is None:
        ma["interview_question_preview"] = []
        return
    if not isinstance(preview, list):
        ma["interview_question_preview"] = []
        return
    cleaned = []
    for item in preview:
        if isinstance(item, dict) and str(item.get("question") or "").strip():
            cleaned.append({
                "question": str(item.get("question", "")).strip(),
                "why_likely": str(item.get("why_likely") or item.get("why") or "").strip(),
                "category": str(item.get("category") or "Behavior").strip(),
            })
    ma["interview_question_preview"] = cleaned[:12]


def normalize_gap_remedy_tiers(ma: Dict) -> None:
    """Ensure gap remedy lines have tier prefix when missing."""
    if not ma or not isinstance(ma, dict):
        return
    tier_tags = ("[能补]", "[难补]", "[不重要]", "[Fixable]", "[Hard]", "[Low impact]")
    for dim in ("industry_match", "experience_match", "skills_match"):
        block = ma.get(dim)
        if not isinstance(block, dict):
            continue
        for gap in block.get("gaps") or []:
            if not isinstance(gap, dict):
                continue
            remedy = str(gap.get("remedy") or "").strip()
            if remedy and not any(remedy.startswith(t) for t in tier_tags):
                gap["remedy"] = f"[能补] {remedy}"


def _extract_tier_from_remedy(remedy: str) -> str:
    remedy = (remedy or "").strip()
    if remedy.startswith("[难补]") or remedy.startswith("[Hard]"):
        return "难补"
    if remedy.startswith("[不重要]") or remedy.startswith("[Low impact]"):
        return "不重要"
    return "能补"


def _infer_severity_from_remedy(remedy: str) -> str:
    tier = _extract_tier_from_remedy(remedy)
    if tier == "难补":
        return "high"
    if tier == "不重要":
        return "low"
    return "medium"


def normalize_gap_improvement_cards(ma: Dict) -> None:
    """Ensure gap_improvement_cards exist; derive from dimension gaps when missing."""
    if not ma or not isinstance(ma, dict):
        return
    cards = ma.get("gap_improvement_cards")
    if not isinstance(cards, list):
        cards = []
    normalized = []
    seen_names = set()
    for item in cards:
        if not isinstance(item, dict):
            continue
        gap_name = str(item.get("gap_name") or item.get("point") or item.get("gap") or "").strip()
        if not gap_name or gap_name.lower() in seen_names:
            continue
        seen_names.add(gap_name.lower())
        tier = str(item.get("tier") or "").strip()
        if tier not in ("能补", "难补", "不重要"):
            tier = _extract_tier_from_remedy(str(item.get("remedy") or ""))
        severity = str(item.get("severity") or "").strip().lower()
        if severity not in ("high", "medium", "low"):
            severity = _infer_severity_from_remedy(str(item.get("remedy") or ""))
        normalized.append({
            "gap_name": gap_name,
            "severity": severity,
            "tier": tier,
            "hm_concern": str(item.get("hm_concern") or item.get("concern") or "").strip(),
            "fix_within_4_weeks": str(
                item.get("fix_within_4_weeks") or item.get("fix") or item.get("remedy") or ""
            ).strip(),
        })
    if len(normalized) < 3:
        for dim in ("industry_match", "experience_match", "skills_match"):
            block = ma.get(dim)
            if not isinstance(block, dict):
                continue
            for gap in block.get("gaps") or []:
                if not isinstance(gap, dict):
                    continue
                gap_name = str(gap.get("point") or gap.get("gap") or "").strip()
                if not gap_name or gap_name.lower() in seen_names:
                    continue
                seen_names.add(gap_name.lower())
                remedy = str(gap.get("remedy") or "").strip()
                normalized.append({
                    "gap_name": gap_name,
                    "severity": _infer_severity_from_remedy(remedy),
                    "tier": _extract_tier_from_remedy(remedy),
                    "hm_concern": f"Screening risk: {gap_name}",
                    "fix_within_4_weeks": remedy,
                })
                if len(normalized) >= 6:
                    break
            if len(normalized) >= 6:
                break
    ma["gap_improvement_cards"] = normalized[:6]


def _normalize_why_not_entry(entry) -> Optional[Dict[str, str]]:
    if isinstance(entry, str):
        s = entry.strip()
        return {"reason": s, "hm_probe_response": ""} if s else None
    if isinstance(entry, dict):
        reason = str(entry.get("reason") or entry.get("text") or entry.get("point") or "").strip()
        if not reason:
            return None
        probe = str(entry.get("hm_probe_response") or entry.get("hm_probe") or "").strip()
        return {"reason": reason, "hm_probe_response": probe}
    return None


def normalize_why_apply_not(ma: Dict) -> None:
    """Normalize why_apply / why_not_apply; sync from why_bullets when needed."""
    if not ma or not isinstance(ma, dict):
        return
    why_apply = _normalize_str_list(ma.get("why_apply"))
    why_not = []
    for item in ma.get("why_not_apply") or []:
        norm = _normalize_why_not_entry(item)
        if norm:
            why_not.append(norm)
    bullets = _normalize_str_list(ma.get("why_bullets"))
    negative_markers = ("not recommend", "risk", "gap", "weak", "lack", "missing", "concern", "however", "but ", "不", "缺", "风险", "弱")
    if not why_apply and bullets:
        why_apply = [b for b in bullets if not any(m in b.lower() for m in negative_markers)]
        if not why_apply:
            why_apply = bullets[:3]
    if not why_not and bullets:
        for b in bullets:
            if any(m in b.lower() for m in negative_markers):
                why_not.append({"reason": b, "hm_probe_response": ""})
    ma["why_apply"] = why_apply[:6]
    ma["why_not_apply"] = why_not[:6]


def normalize_organization_background(jra: Dict) -> None:
    if not jra or not isinstance(jra, dict):
        return
    ob = jra.get("organization_background")
    if not isinstance(ob, dict):
        ob = {}
    signals = ob.get("culture_signals") or []
    norm_signals = []
    if isinstance(signals, list):
        for s in signals:
            if isinstance(s, str) and s.strip():
                norm_signals.append({"signal": s.strip(), "jd_evidence": ""})
            elif isinstance(s, dict):
                sig = str(s.get("signal") or s.get("text") or "").strip()
                if sig:
                    norm_signals.append({
                        "signal": sig,
                        "jd_evidence": str(s.get("jd_evidence") or s.get("evidence") or "").strip(),
                    })
    ob.setdefault("company_snapshot", "")
    ob["culture_signals"] = norm_signals
    ob["recent_product_moves"] = _normalize_str_list(ob.get("recent_product_moves"))
    ob.setdefault("why_care_for_this_candidate", "")
    sources = ob.get("sources")
    if not isinstance(sources, list):
        sources = [str(sources).strip()] if sources else ["JD only"]
    ob["sources"] = [str(x).strip() for x in sources if str(x).strip()] or ["JD only"]
    conf = str(ob.get("confidence") or "medium").strip().lower()
    ob["confidence"] = conf if conf in ("high", "medium", "low") else "medium"
    jra["organization_background"] = ob


def normalize_salary_reality_check(jra: Dict) -> None:
    if not jra or not isinstance(jra, dict):
        return
    sal = jra.get("salary_reality_check")
    if not isinstance(sal, dict):
        sal = {}
    sal.setdefault("jd_stated_range", "")
    sal.setdefault("market_range_estimate", "")
    sal["negotiation_talking_points"] = _normalize_str_list(sal.get("negotiation_talking_points"))
    sal.setdefault("vs_candidate_context", "")
    disclaimer = str(sal.get("disclaimer") or "").strip()
    if not disclaimer:
        disclaimer = "非报价，需用户自行核实；非录用承诺。"
    sal["disclaimer"] = disclaimer
    jra["salary_reality_check"] = sal


def normalize_jd_decode_insights(jra: Dict) -> None:
    if not jra or not isinstance(jra, dict):
        return
    insights = jra.get("jd_decode_insights")
    if not isinstance(insights, dict):
        insights = {}
    translations = []
    for item in insights.get("real_intent_translations") or []:
        if isinstance(item, dict):
            jq = str(item.get("jd_quote") or item.get("jd") or "").strip()
            rn = str(item.get("real_need") or item.get("real_intent") or "").strip()
            if jq and rn:
                mvr = str(item.get("marketing_vs_real") or "soft").strip().lower()
                translations.append({
                    "jd_quote": jq,
                    "real_need": rn,
                    "marketing_vs_real": mvr if mvr in ("hard", "soft") else "soft",
                })
    hidden = []
    for item in insights.get("hidden_signals") or []:
        if isinstance(item, dict):
            cue = str(item.get("jd_cue") or item.get("cue") or "").strip()
            if cue:
                hidden.append({
                    "jd_cue": cue,
                    "interpretation": str(item.get("interpretation") or "").strip(),
                    "candidate_implication": str(
                        item.get("candidate_implication") or item.get("implication") or ""
                    ).strip(),
                })
    level = insights.get("level_and_scope")
    if not isinstance(level, dict):
        level = {}
    level.setdefault("seniority", "")
    level.setdefault("ic_vs_lead", "")
    level.setdefault("domain_depth", "")
    insights["real_intent_translations"] = translations
    insights["hidden_signals"] = hidden
    insights["level_and_scope"] = level
    insights["must_have_summary"] = _normalize_str_list(insights.get("must_have_summary"))
    insights["nice_to_have_summary"] = _normalize_str_list(insights.get("nice_to_have_summary"))
    jra["jd_decode_insights"] = insights

    if translations and not jra.get("work_scenarios"):
        jra["work_scenarios"] = [
            f'JD: "{t["jd_quote"]}" → Real need: {t["real_need"]}.'
            for t in translations[:6]
        ]


def postprocess_match_assessment_skill_fields(ma: Dict) -> None:
    """Apply offer-toolkit post-processing for match_assessment."""
    normalize_match_dimension_strengths_gaps(ma)
    normalize_match_percentage_range(ma)
    normalize_match_assessment_ui_fields(ma)
    reconcile_dual_track_scoring(ma)
    normalize_gap_remedy_tiers(ma)
    normalize_gap_improvement_cards(ma)
    normalize_why_apply_not(ma)
    normalize_interview_question_preview(ma)


def _format_work_scenario_decode_item(item) -> str:
    """Normalize work_scenarios entries to JD deep-decode string format."""
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        jd = str(item.get("jd_quote") or item.get("jd") or item.get("quote") or "").strip()
        real = str(
            item.get("real_need")
            or item.get("real_intent")
            or item.get("expectation")
            or item.get("translation")
            or ""
        ).strip()
        signal = str(item.get("signal") or item.get("hidden_signal") or "").strip()
        if jd and real:
            line = f'JD: "{jd}" → Real need: {real}'
            if signal:
                line += f". Signal: {signal}"
            return line
        for key in ("text", "description", "scenario"):
            if item.get(key):
                return str(item[key]).strip()
    return str(item).strip() if item is not None else ""


def postprocess_jd_decode_work_scenario_fields(jra: Dict) -> None:
    """Map JD decode outputs to Work Scenario tab fields (UI-compatible)."""
    if not jra or not isinstance(jra, dict):
        return

    raw_scenarios = jra.get("work_scenarios")
    if isinstance(raw_scenarios, str):
        raw_scenarios = [raw_scenarios] if raw_scenarios.strip() else []
    elif not isinstance(raw_scenarios, list):
        raw_scenarios = []
    jra["work_scenarios"] = [
        s for s in (_format_work_scenario_decode_item(x) for x in raw_scenarios) if s
    ]

    challenges = _normalize_str_list(jra.get("challenges"))
    problems = _normalize_str_list(jra.get("problems_to_solve"))
    if not challenges and problems:
        jra["challenges"] = problems
    elif challenges and not problems:
        jra["problems_to_solve"] = challenges
    else:
        jra["challenges"] = challenges
        jra["problems_to_solve"] = problems or challenges

    jra["project_types"] = _normalize_str_list(jra.get("project_types"))
    jra["methods_technologies"] = _normalize_str_list(jra.get("methods_technologies"))

    normalize_organization_background(jra)
    normalize_salary_reality_check(jra)
    normalize_jd_decode_insights(jra)


def _normalize_str_list(val) -> list:
    if not val:
        return []
    if isinstance(val, str):
        s = val.strip()
        return [s] if s else []
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    return []


def _normalize_application_decision(ma: Dict, tier: str) -> None:
    ad = ma.get("application_decision")
    if not isinstance(ad, dict):
        ad = {}
    valid_verdicts = ("strong_apply", "worth_trying", "low_priority", "not_recommended")
    verdict = ad.get("verdict")
    if verdict not in valid_verdicts:
        ad["verdict"] = {"full": "strong_apply", "partial": "worth_trying", "none": "not_recommended"}[tier]
    if ad.get("verdict") == "not_recommended":
        ad["can_try"] = False
    elif "can_try" not in ad:
        ad["can_try"] = True
    else:
        ad["can_try"] = bool(ad["can_try"])
    ol = ad.get("one_line_summary")
    if not isinstance(ol, str) or not ol.strip():
        summary = (ma.get("overall_summary") or ma.get("application_prospects") or "").strip()
        ad["one_line_summary"] = (summary[:240] + ("..." if len(summary) > 240 else "")) if summary else ""
    ma["application_decision"] = ad


def normalize_match_assessment_ui_fields(ma: Dict) -> None:
    """Ensure match_fit_tier, bullets, and application_decision exist for UI and older cached runs."""
    if not ma or not isinstance(ma, dict):
        return
    tier = derive_match_fit_tier(ma)
    ma["match_fit_tier"] = tier
    ma["why_bullets"] = _normalize_str_list(ma.get("why_bullets"))
    ma["action_bullets"] = _normalize_str_list(ma.get("action_bullets"))
    _normalize_application_decision(ma, tier)


def _coerce_strength_entry(entry) -> Optional[Dict[str, str]]:
    if entry is None:
        return None
    if isinstance(entry, str):
        s = entry.strip()
        return {"point": s, "amplify": ""} if s else None
    if isinstance(entry, dict):
        point = (
            entry.get("point")
            or entry.get("text")
            or entry.get("summary")
            or entry.get("strength")
            or entry.get("description")
        )
        point = str(point).strip() if point is not None else ""
        if not point and len(entry) == 1:
            v = next(iter(entry.values()))
            if isinstance(v, str) and v.strip():
                point = v.strip()
        amp = entry.get("amplify") or entry.get("leverage") or entry.get("resume_interview_tip")
        amplify = str(amp).strip() if amp is not None else ""
        if not point:
            return None
        return {"point": point, "amplify": amplify}
    s = str(entry).strip()
    return {"point": s, "amplify": ""} if s else None


def _coerce_gap_entry(entry) -> Optional[Dict[str, str]]:
    if entry is None:
        return None
    if isinstance(entry, str):
        s = entry.strip()
        return {"point": s, "remedy": ""} if s else None
    if isinstance(entry, dict):
        point = (
            entry.get("point")
            or entry.get("text")
            or entry.get("summary")
            or entry.get("gap")
            or entry.get("description")
        )
        point = str(point).strip() if point is not None else ""
        if not point and len(entry) == 1:
            v = next(iter(entry.values()))
            if isinstance(v, str) and v.strip():
                point = v.strip()
        rem = entry.get("remedy") or entry.get("address") or entry.get("how_to_close") or entry.get("mitigation")
        remedy = str(rem).strip() if rem is not None else ""
        if not point:
            return None
        return {"point": point, "remedy": remedy}
    s = str(entry).strip()
    return {"point": s, "remedy": ""} if s else None


def normalize_match_dimension_strengths_gaps(ma: Dict) -> None:
    """Coerce strengths/gaps to {point, amplify}/{point, remedy} for each dimension (legacy strings supported)."""
    if not ma or not isinstance(ma, dict):
        return
    for dim in ("industry_match", "experience_match", "skills_match"):
        block = ma.get(dim)
        if not isinstance(block, dict):
            continue
        raw_s = block.get("strengths")
        if isinstance(raw_s, list):
            out_s = []
            for x in raw_s:
                coerced = _coerce_strength_entry(x)
                if coerced:
                    out_s.append(coerced)
            block["strengths"] = out_s
        raw_g = block.get("gaps")
        if isinstance(raw_g, list):
            out_g = []
            for x in raw_g:
                coerced = _coerce_gap_entry(x)
                if coerced:
                    out_g.append(coerced)
            block["gaps"] = out_g


class JDAnalysisAgent:
    """Agent 2: Analyzes JD and provides matching assessment."""
    
    def __init__(self, model: str = None):
        """Initialize the JD analysis agent. Uses gpt-5 by default for JSON mode (AI Builder API)."""
        model = model or LLM_MODEL_JSON
        self.base_url = AI_BUILDER_BASE_URL
        self.api_key = STUDENT_PORTAL_API_KEY
        self.model = model
        self.endpoint = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("STUDENT_PORTAL_API_KEY not set")
    
    def analyze_jd_and_match(
        self,
        jd_text: str,
        resume_text: str,
        project_materials: Optional[str] = None,
        fast_mode: bool = False,
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
        country_or_region: Optional[str] = None,
        parallel_20s: bool = False,
        preferred_lang: Optional[str] = "en",
    ) -> Dict:
        """
        Analyze JD and provide matching assessment.
        fast_mode: If True, single API call only (no follow-up calls), truncated input, ~30s target. No external search.
        parallel_20s: If True, run three section calls in parallel (job_role_team_analysis, ideal_candidate_profile, match_assessment) for ~20s total with full detail.
        job_title, company_name, country_or_region: Optional context; all reasoning must be from JD + user input only (no external search).
        """
        meta = []
        if job_title:
            meta.append(f"Job title: {job_title}")
        if company_name:
            meta.append(f"Company: {company_name}")
        if country_or_region:
            meta.append(f"Country/Region: {country_or_region}")
        meta_block = "\n".join(meta) if meta else ""

        if parallel_20s:
            return self._analyze_jd_single_call_20s(
                jd_text=jd_text,
                resume_text=resume_text,
                project_materials=project_materials,
                meta_block=meta_block,
                preferred_lang=preferred_lang,
            )

        _schema = AGENT2_JSON_SCHEMA or ""
        _sys = AGENT2_SYSTEM_BRIEF or AGENT2_JD_ANALYSIS_PROMPT
        if fast_mode:
            jd_use = jd_text[:4000] + ("..." if len(jd_text) > 4000 else "")
            resume_use = resume_text[:4000] + ("..." if len(resume_text) > 4000 else "")
            system_prompt = _sys
            user_message = f"""=== CONTEXT ===\n{meta_block or "Not provided"}\n\n=== JD ===\n{jd_use}\n\n=== RESUME ===\n{resume_use}\n\n=== REQUIRED JSON SCHEMA ===\n{_schema}\n\nOutput the JSON analysis.{output_language_suffix(preferred_lang)}"""
            max_tokens = 8000
            timeout = httpx.Timeout(60.0, connect=10.0)
        else:
            jd_use = jd_text
            resume_use = resume_text
            system_prompt = _sys
            user_message = f"""=== CONTEXT ===
{meta_block or "Not provided"}

=== JOB DESCRIPTION ===
{jd_use}

=== RESUME ===
{resume_use}

=== PROJECT MATERIALS ===
{project_materials if project_materials else "No project materials provided"}

=== REQUIRED JSON SCHEMA ===
{_schema}

Please provide comprehensive analysis in the specified JSON format.{output_language_suffix(preferred_lang)}"""
            max_tokens = 16000
            timeout = httpx.Timeout(600.0, connect=30.0)
        
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
            "max_tokens": max_tokens,
        }
        if RESPONSE_FORMAT_JSON is not None:
            payload["response_format"] = RESPONSE_FORMAT_JSON
        
        response = None
        _empty = {"job_role_team_analysis": {}, "ideal_candidate_profile": {}, "match_assessment": {}}
        for attempt in range(2):
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(self.endpoint, headers=headers, json=payload)
                break
            except httpx.ReadTimeout:
                if attempt == 1:
                    return {"error": "Agent 2 error: The read operation timed out (retried once).", **_empty}
                continue
            except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.WriteError, OSError) as e:
                if attempt == 1:
                    return {"error": f"Agent 2 error: {type(e).__name__} - {str(e)[:200]}", **_empty}
                continue
        try:
            if response is None:
                return {"error": "Agent 2 error: No response after retries.", **_empty}
            if response.status_code != 200:
                error_detail = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", error_data.get("message", error_detail))
                except Exception:
                    error_detail = response.text[:200] if response.text else error_detail
                return {
                    "error": f"API request failed ({response.status_code}): {error_detail}",
                    "job_role_team_analysis": {},
                    "ideal_candidate_profile": {},
                    "match_assessment": {},
                    "http_status": response.status_code
                }
            response.raise_for_status()
            result = response.json()
            if "choices" not in result or len(result["choices"]) == 0:
                return {
                    "error": "Invalid API response: no choices in response",
                    "job_role_team_analysis": {},
                    "ideal_candidate_profile": {},
                    "match_assessment": {}
                }
            message_content = result["choices"][0]["message"].get("content")
            if message_content is None or (isinstance(message_content, str) and not message_content.strip()):
                return {
                    "error": "LLM returned empty response",
                    "job_role_team_analysis": {},
                    "ideal_candidate_profile": {},
                    "match_assessment": {},
                }
            analysis_result = self._parse_json_response(message_content)
            # Follow-up API calls only when not in fast_mode (they add latency; fast_mode targets ~30s single call)
            if not fast_mode:
                ma = analysis_result.get("match_assessment") or {}
                if not _match_assessment_complete(ma):
                    extra_ma = self._fetch_match_assessment_only(jd_text, resume_text, preferred_lang)
                    if extra_ma:
                        analysis_result["match_assessment"] = {**ma, **extra_ma}
                        postprocess_match_assessment_skill_fields(analysis_result["match_assessment"])
                jra = analysis_result.get("job_role_team_analysis") or {}
                if not _has_content(jra):
                    extra_jra = self._fetch_job_role_analysis_only(jd_text, preferred_lang)
                    if extra_jra:
                        analysis_result["job_role_team_analysis"] = extra_jra
                icp = analysis_result.get("ideal_candidate_profile") or {}
                if not _has_content(icp.get("overall_experience_traits")) or not _has_content(icp.get("hard_skills")):
                    extra_icp = self._fetch_ideal_candidate_profile_only(jd_text, preferred_lang)
                    if extra_icp:
                        for k, v in extra_icp.items():
                            if _has_content(v):
                                icp[k] = v
                        analysis_result["ideal_candidate_profile"] = icp
            return analysis_result
        
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", error_data.get("message", error_detail))
            except:
                error_detail = e.response.text[:200] if e.response.text else error_detail
            
            return {
                "error": f"API request failed ({e.response.status_code}): {error_detail}",
                "job_role_team_analysis": {},
                "ideal_candidate_profile": {},
                "match_assessment": {},
                "http_status": e.response.status_code
            }
        except Exception as e:
            import traceback
            return {
                "error": f"Agent 2 error: {str(e)}",
                "job_role_team_analysis": {},
                "ideal_candidate_profile": {},
                "match_assessment": {},
                "traceback": traceback.format_exc()
            }

    def _call_one_section(
        self,
        section_key: str,
        jd_use: str,
        resume_use: str,
        meta_block: str,
        project_materials: Optional[str],
    ) -> Tuple[str, Optional[Dict]]:
        """Run one section-specific LLM call; return (section_key, section_dict or None). Uses concise section prompts for ~20s total."""
        section_prompts = {
            "job_role_team_analysis": AGENT2_SECTION_JOB_ROLE,
            "ideal_candidate_profile": AGENT2_SECTION_IDEAL_PROFILE,
            "match_assessment": AGENT2_SECTION_MATCH,
        }
        system_prompt = (section_prompts.get(section_key) if section_prompts.get(section_key) else None) or AGENT2_JD_ANALYSIS_PROMPT
        if section_prompts.get(section_key):
            user_msg = (
                f"=== CONTEXT ===\n{meta_block or 'Not provided'}\n\n=== JOB DESCRIPTION ===\n{jd_use}\n\n=== RESUME ===\n{resume_use}\n\n"
                f"=== PROJECT MATERIALS ===\n{project_materials if project_materials else 'None'}\n\n"
                f"Output ONLY the JSON for \"{section_key}\" as specified in the system prompt."
            )
        else:
            user_msg = (
                f"Output ONLY the key '{section_key}' with the exact structure and depth described in the system prompt. "
                f"Omit the other two keys. Return valid JSON with a single top-level key \"{section_key}\".\n\n"
                f"=== CONTEXT ===\n{meta_block or 'Not provided'}\n\n=== JOB DESCRIPTION ===\n{jd_use}\n\n=== RESUME ===\n{resume_use}\n\n"
                f"=== PROJECT MATERIALS ===\n{project_materials if project_materials else 'None'}"
            )
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        # Use fast model for parallel_20s (OpenAPI: deepseek = fast; gpt-5 = long reasoning chains → slow)
        payload = {
            "model": AGENT2_FAST_MODEL,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_msg}],
            "temperature": 0.2,
            "max_tokens": 3500,
        }
        if RESPONSE_FORMAT_JSON is not None:
            payload["response_format"] = RESPONSE_FORMAT_JSON
        timeout = httpx.Timeout(18.0, connect=8.0)
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(self.endpoint, headers=headers, json=payload)
            if resp.status_code != 200:
                return (section_key, None)
            data = resp.json()
            content = (data.get("choices") or [{}])[0].get("message") or {}
            content = content.get("content") or ""
            if not content or not content.strip():
                return (section_key, None)
            parsed = parse_llm_json_response(content, debug_file=None)
            if not parsed or not isinstance(parsed, dict):
                return (section_key, None)
            # Direct key (exact or camelCase)
            for k in (section_key, section_key.replace("_", " ").title().replace(" ", "")):
                if k in parsed and parsed[k] and isinstance(parsed[k], dict):
                    return (section_key, parsed[k])
            if section_key in parsed and parsed[section_key]:
                return (section_key, parsed[section_key])
            # response may be the section object at root (no wrapper key)
            job_role_fields = {"team_objectives", "work_scenarios", "daily_activities", "project_types", "methods_technologies", "collaboration_patterns", "kpis", "required_knowledge", "target_audience", "problems_to_solve", "context_notes"}
            if section_key == "job_role_team_analysis" and (job_role_fields & set(parsed.keys()) or _has_content(parsed)):
                return (section_key, parsed)
            if section_key == "ideal_candidate_profile" and _has_content(parsed):
                return (section_key, parsed)
            if section_key == "match_assessment" and (
                parsed.get("overall_match_score") is not None
                or parsed.get("match_level")
                or parsed.get("match_fit_tier")
            ):
                return (section_key, parsed)
            # single top-level key: use its value as section
            if len(parsed) == 1:
                only_val = next(iter(parsed.values()))
                if isinstance(only_val, dict) and _has_content(only_val):
                    return (section_key, only_val)
            return (section_key, None)
        except Exception:
            return (section_key, None)

    def _analyze_jd_single_call_20s(
        self,
        jd_text: str,
        resume_text: str,
        project_materials: Optional[str] = None,
        meta_block: str = "",
        preferred_lang: Optional[str] = "en",
    ) -> Dict:
        """One API call with fast model. Uses split prompt (short system + schema in user msg)
        to work around AI Builder API stripping content for long system prompts."""
        import logging
        logger = logging.getLogger(__name__)
        jd_use = jd_text[:4000] + ("..." if len(jd_text) > 4000 else "")
        resume_use = resume_text[:4000] + ("..." if len(resume_text) > 4000 else "")
        logger.info(f"Agent2 20s mode: JD {len(jd_text)}→{len(jd_use)} chars, Resume {len(resume_text)}→{len(resume_use)} chars")

        sys_prompt = AGENT2_SYSTEM_BRIEF or AGENT2_JD_ANALYSIS_PROMPT
        schema_block = AGENT2_JSON_SCHEMA or ""
        user_msg = f"""=== CONTEXT ===
{meta_block or 'Not provided'}

=== JOB DESCRIPTION ===
{jd_use}

=== RESUME ===
{resume_use}

=== PROJECT MATERIALS ===
{project_materials if project_materials else 'None'}

=== REQUIRED JSON SCHEMA ===
{schema_block}

Output the complete JSON with all three top-level keys. No markdown wrapping.{output_language_suffix(preferred_lang)}"""

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": AGENT2_FAST_MODEL,
            "messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}],
            "temperature": 0.2,
            "max_tokens": 8000,
        }
        if RESPONSE_FORMAT_JSON is not None:
            payload["response_format"] = RESPONSE_FORMAT_JSON
        timeout = httpx.Timeout(60.0, connect=10.0)
        _empty = {"job_role_team_analysis": {}, "ideal_candidate_profile": {}, "match_assessment": {}}
        logger.info(f"Agent2 20s mode: system prompt {len(sys_prompt)} chars, user msg {len(user_msg)} chars")
        for attempt in range(2):
            try:
                with httpx.Client(timeout=timeout) as client:
                    resp = client.post(self.endpoint, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.warning(f"Agent2 20s mode: HTTP {resp.status_code} on attempt {attempt+1}")
                    if attempt == 0:
                        continue
                    return self._ensure_required_sections(_empty)
                data = resp.json()
                usage = data.get("usage", {})
                logger.info(f"Agent2 20s mode: tokens prompt={usage.get('prompt_tokens')}, completion={usage.get('completion_tokens')}")
                content = (data.get("choices") or [{}])[0].get("message") or {}
                content = (content.get("content") or "").strip()
                if not content:
                    logger.warning(f"Agent2 20s mode: empty content on attempt {attempt+1} (completion_tokens={usage.get('completion_tokens')})")
                    if attempt == 0:
                        continue
                    return self._ensure_required_sections(_empty)
                logger.info(f"Agent2 20s mode: got {len(content)} chars response, parsing...")
                parsed = self._parse_json_response(content)
                jra = parsed.get("job_role_team_analysis") or {}
                if _has_content(jra):
                    logger.info(f"Agent2 20s mode: parse OK, job_role_team_analysis has content")
                    return self._ensure_required_sections(parsed)
                else:
                    logger.warning(f"Agent2 20s mode: parsed but job_role_team_analysis empty, keys={list(parsed.keys())[:10]}")
                    if attempt == 0:
                        continue
                    return self._ensure_required_sections(parsed)
            except httpx.ReadTimeout:
                logger.warning(f"Agent2 20s mode: timeout on attempt {attempt+1}")
                continue
            except Exception as e:
                logger.warning(f"Agent2 20s mode: error on attempt {attempt+1}: {e}")
                if attempt == 1:
                    return self._ensure_required_sections(_empty)
                continue
        return self._ensure_required_sections(_empty)

    def _analyze_jd_parallel_20s(
        self,
        jd_text: str,
        resume_text: str,
        project_materials: Optional[str] = None,
        meta_block: str = "",
    ) -> Dict:
        """Run three section calls in parallel for ~20s total; merge and return full-detail result."""
        jd_use = jd_text[:1800] + ("..." if len(jd_text) > 1800 else "")
        resume_use = resume_text[:1800] + ("..." if len(resume_text) > 1800 else "")
        sections = ("job_role_team_analysis", "ideal_candidate_profile", "match_assessment")
        merged = {"job_role_team_analysis": {}, "ideal_candidate_profile": {}, "match_assessment": {}}
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(
                    self._call_one_section,
                    key,
                    jd_use,
                    resume_use,
                    meta_block,
                    project_materials,
                ): key
                for key in sections
            }
            for future in as_completed(futures, timeout=22):
                try:
                    key, value = future.result()
                    if value is not None:
                        merged[key] = value
                except Exception:
                    pass
        return self._ensure_required_sections(merged)

    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON response from LLM using enhanced parser with multiple fallback strategies."""
        # Strategy 1: Try enhanced parser
        try:
            parsed = parse_llm_json_response(content, debug_file="agent2_raw_response.txt")
            if parsed and isinstance(parsed, dict) and len(parsed) > 0:
                # Ensure all required sections exist
                return self._ensure_required_sections(parsed)
        except Exception as e:
            print(f"⚠️  Strategy 1 (enhanced parser) failed: {str(e)[:200]}")
        
        # Strategy 2: Try to extract JSON from text using regex
        try:
            # Look for JSON object boundaries more aggressively
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.finditer(json_pattern, content, re.DOTALL)
            largest_match = None
            largest_size = 0
            
            for match in matches:
                try:
                    test_json = json.loads(match.group(0))
                    if isinstance(test_json, dict) and len(test_json) > largest_size:
                        largest_match = test_json
                        largest_size = len(test_json)
                except:
                    continue
            
            if largest_match:
                print("✅ Strategy 2 (regex extraction) succeeded")
                return self._ensure_required_sections(largest_match)
        except Exception as e:
            print(f"⚠️  Strategy 2 (regex extraction) failed: {str(e)[:200]}")
        
        # Strategy 3: Try to extract key information from text
        result = {
            "error": "Failed to parse JSON after all attempts",
            "job_role_team_analysis": {},
            "ideal_candidate_profile": {},
            "match_assessment": {}
        }
        
        # Extract match score from text
        match_score_patterns = [
            r'(\d+\.?\d*)\s*out of\s*5',
            r'(\d+\.?\d*)\s*/\s*5',
            r'score.*?(\d+\.?\d*)',
            r'match.*?(\d+\.?\d*)',
        ]
        for pattern in match_score_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    if 0 <= score <= 5:
                        result["match_assessment"] = {
                            "overall_match_score": str(score),
                            "match_level": "Strong" if score >= 4.0 else "Moderate" if score >= 3.0 else "Weak",
                            "match_percentage": str(score * 20)
                        }
                        break
                except:
                    continue
        
        return self._ensure_required_sections(result)
    
    def _fetch_match_assessment_only(
        self, jd_text: str, resume_text: str, preferred_lang: Optional[str] = "en"
    ) -> Optional[Dict]:
        """When main response was truncated, fetch only match_assessment in a second call. Returns dict to merge into match_assessment."""
        prompt = """Output ONLY a JSON object for "match_assessment". Keys: overall_match_score (0-5 number), match_level (Excellent|Strong|Moderate|Weak|Poor), match_percentage (string), match_fit_tier (full|partial|none), application_decision (object: verdict strong_apply|worth_trying|low_priority|not_recommended, can_try boolean, one_line_summary string), why_bullets (array of 3-6 strings), action_bullets (array of 3-6 strings), industry_match, experience_match, skills_match (each: score; strengths array of {point, amplify}; gaps array of {point, remedy}; competitive_advantage; disadvantage), overall_summary, application_prospects. No other keys. Return valid JSON only, starting with { and ending with }."""
        user_msg = f"JD:\n{jd_text[:2500]}\n\nResume:\n{resume_text[:2500]}\n\nProvide match_assessment JSON only.{output_language_suffix(preferred_lang)}"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": user_msg}],
            "temperature": 0.2,
            "max_tokens": 4000,
        }
        if RESPONSE_FORMAT_JSON is not None:
            payload["response_format"] = RESPONSE_FORMAT_JSON
        timeout = httpx.Timeout(120.0, connect=30.0)
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(self.endpoint, headers=headers, json=payload)
            if resp.status_code != 200:
                return None
            data = resp.json()
            if not data.get("choices"):
                return None
            content = (data["choices"][0].get("message") or {}).get("content")
            if not content or not content.strip():
                return None
            parsed = parse_llm_json_response(content, debug_file=None)
            if not parsed or not isinstance(parsed, dict):
                return None
            if "match_assessment" in parsed and _match_assessment_complete(parsed["match_assessment"]):
                return parsed["match_assessment"]
            if _match_assessment_complete(parsed):
                return parsed
            return None
        except Exception:
            return None
    
    def _fetch_job_role_analysis_only(self, jd_text: str, preferred_lang: Optional[str] = "en") -> Optional[Dict]:
        """When main response omitted job_role_team_analysis, fetch it from JD in a second call."""
        prompt = """Output ONLY a JSON object for "job_role_team_analysis" from the job description. Keys: team_objectives (string), work_scenarios (array of strings), daily_activities (array), project_types (array), methods_technologies (array), kpis (array), required_knowledge (array), collaboration_patterns (string). No other keys. Return valid JSON only, starting with { and ending with }."""
        user_msg = f"Job description:\n{jd_text[:3000]}\n\nProvide job_role_team_analysis JSON only.{output_language_suffix(preferred_lang)}"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": user_msg}],
            "temperature": 0.2,
            "max_tokens": 4000,
        }
        if RESPONSE_FORMAT_JSON is not None:
            payload["response_format"] = RESPONSE_FORMAT_JSON
        timeout = httpx.Timeout(120.0, connect=30.0)
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(self.endpoint, headers=headers, json=payload)
            if resp.status_code != 200:
                return None
            data = resp.json()
            if not data.get("choices"):
                return None
            content = (data["choices"][0].get("message") or {}).get("content")
            if not content or not content.strip():
                return None
            parsed = parse_llm_json_response(content, debug_file=None)
            if not parsed or not isinstance(parsed, dict):
                return None
            if "job_role_team_analysis" in parsed and _has_content(parsed["job_role_team_analysis"]):
                return parsed["job_role_team_analysis"]
            if "team_objectives" in parsed or "work_scenarios" in parsed:
                return parsed
            return None
        except Exception:
            return None
    
    def _fetch_ideal_candidate_profile_only(self, jd_text: str, preferred_lang: Optional[str] = "en") -> Optional[Dict]:
        """When main response omitted ideal_candidate_profile, fetch it from JD in a second call."""
        prompt = """Output ONLY a JSON object for "ideal_candidate_profile" from the job description. Include: overall_experience_traits (string, 1 paragraph), hard_skills (object with must_have array of {skill, details}, nice_to_have array, tools_platforms, methodologies_frameworks), hard_skills_top5 (array of 1-5 {skill, why_critical} from JD responsibilities only, ranked, professional names, no overlap with soft list), soft_skills_top5 (array of 1-5 with skill/why_critical/manifestation, same sourcing rules, no overlap with hard list). No other keys. Return valid JSON only, starting with { and ending with }."""
        user_msg = f"Job description:\n{jd_text[:3000]}\n\nProvide ideal_candidate_profile JSON only.{output_language_suffix(preferred_lang)}"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": user_msg}],
            "temperature": 0.2,
            "max_tokens": 4000,
        }
        if RESPONSE_FORMAT_JSON is not None:
            payload["response_format"] = RESPONSE_FORMAT_JSON
        timeout = httpx.Timeout(120.0, connect=30.0)
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(self.endpoint, headers=headers, json=payload)
            if resp.status_code != 200:
                return None
            data = resp.json()
            if not data.get("choices"):
                return None
            content = (data["choices"][0].get("message") or {}).get("content")
            if not content or not content.strip():
                return None
            parsed = parse_llm_json_response(content, debug_file=None)
            if not parsed or not isinstance(parsed, dict):
                return None
            if "ideal_candidate_profile" in parsed and _has_content(parsed["ideal_candidate_profile"]):
                return parsed["ideal_candidate_profile"]
            if "overall_experience_traits" in parsed or "hard_skills" in parsed:
                return parsed
            return None
        except Exception:
            return None
    
    def _ensure_required_sections(self, data: Dict) -> Dict:
        """Ensure all required sections exist in the parsed result and fix structure."""
        # Check if data has fields at root level that should be in job_role_team_analysis
        # This handles cases where JSON parsing puts fields at wrong level
        if "job_role_team_analysis" not in data or not data.get("job_role_team_analysis"):
            # Check if root level has job_role_team_analysis fields
            job_fields = ["team_objectives", "work_scenarios", "challenges", "daily_activities", "project_types", 
                         "methods_technologies", "collaboration_patterns", "kpis", "required_knowledge",
                         "target_audience", "problems_to_solve", "context_notes"]
            found_job_fields = [field for field in job_fields if field in data]
            if found_job_fields:
                # These fields are at root, move them to job_role_team_analysis
                if "job_role_team_analysis" not in data:
                    data["job_role_team_analysis"] = {}
                for field in found_job_fields:
                    data["job_role_team_analysis"][field] = data.pop(field)
            else:
                if "job_role_team_analysis" not in data:
                    data["job_role_team_analysis"] = {}
        
        # Check if ideal_candidate_profile fields are at root level
        if "ideal_candidate_profile" not in data or not data.get("ideal_candidate_profile"):
            ideal_fields = ["overall_experience_traits", "business_experience_cognitive_abilities",
                           "relevant_project_portfolio_experience", "hard_skills", "hard_skills_top5", "soft_skills_top5",
                           "overall_industry_experience", "business_domain_understanding", "project_portfolio"]
            found_ideal_fields = [field for field in ideal_fields if field in data]
            if found_ideal_fields:
                if "ideal_candidate_profile" not in data:
                    data["ideal_candidate_profile"] = {}
                for field in found_ideal_fields:
                    data["ideal_candidate_profile"][field] = data.pop(field)
            else:
                if "ideal_candidate_profile" not in data:
                    data["ideal_candidate_profile"] = {}
        
        # Check if match_assessment fields are at root level
        if "match_assessment" not in data or not data.get("match_assessment"):
            match_fields = ["overall_match_score", "match_level", "match_percentage", "match_fit_tier",
                           "application_decision", "why_bullets", "action_bullets", "score",
                           "industry_match", "experience_match", "skills_match", "strengths", "gaps",
                           "competitive_advantage", "disadvantage", "overall_summary", "application_prospects"]
            found_match_fields = [field for field in match_fields if field in data]
            if found_match_fields:
                if "match_assessment" not in data:
                    data["match_assessment"] = {}
                for field in found_match_fields:
                    data["match_assessment"][field] = data.pop(field)
            else:
                if "match_assessment" not in data:
                    data["match_assessment"] = {}
        
        # Ensure ideal_candidate_profile exists with all required fields
        if "ideal_candidate_profile" not in data:
            data["ideal_candidate_profile"] = {}
        # When parser returns only a fragment (e.g. hard_skills as root), merge root-level hard_skills keys into ideal_candidate_profile
        hard_skills_at_root = ["must_have", "nice_to_have", "tools_platforms", "methodologies_frameworks"]
        if any(k in data for k in hard_skills_at_root):
            ideal_profile = data["ideal_candidate_profile"]
            if "hard_skills" not in ideal_profile or not _has_content(ideal_profile.get("hard_skills")):
                if "hard_skills" not in ideal_profile:
                    ideal_profile["hard_skills"] = {}
                for k in hard_skills_at_root:
                    if k in data and data[k] is not None:
                        ideal_profile["hard_skills"][k] = data.pop(k)
        
        ideal_profile = data["ideal_candidate_profile"]
        if "overall_experience_traits" not in ideal_profile:
            ideal_profile["overall_experience_traits"] = ""
        if "business_experience_cognitive_abilities" not in ideal_profile:
            ideal_profile["business_experience_cognitive_abilities"] = {}
        if "relevant_project_portfolio_experience" not in ideal_profile:
            ideal_profile["relevant_project_portfolio_experience"] = {}
        if "hard_skills" not in ideal_profile:
            ideal_profile["hard_skills"] = {"must_have": [], "nice_to_have": [], "tools_platforms": {}, "methodologies_frameworks": {}}
        if "soft_skills_top5" not in ideal_profile:
            ideal_profile["soft_skills_top5"] = []
        if "hard_skills_top5" not in ideal_profile:
            ideal_profile["hard_skills_top5"] = []
        elif not isinstance(ideal_profile.get("hard_skills_top5"), list):
            ideal_profile["hard_skills_top5"] = []
        
        # Ensure match_assessment exists
        if "match_assessment" not in data:
            data["match_assessment"] = {}
        # Always move dimension matches from root into match_assessment if present at root
        for field in ("industry_match", "experience_match", "skills_match"):
            if field in data and field not in data["match_assessment"]:
                data["match_assessment"][field] = data.pop(field)
        # Normalize root-level "score" into overall_match_score when missing
        if "score" in data and data["score"] is not None:
            data["match_assessment"]["overall_match_score"] = str(data.pop("score"))
        if "disadvantage" in data:
            data["match_assessment"]["disadvantage"] = data.pop("disadvantage")
        
        match_assessment = data["match_assessment"]
        if "overall_match_score" not in match_assessment or match_assessment.get("overall_match_score") in (None, "0.0", 0):
            if "score" in match_assessment:
                match_assessment["overall_match_score"] = str(match_assessment.pop("score", 0))
        if "overall_match_score" not in match_assessment:
            match_assessment["overall_match_score"] = "0.0"
        if "match_level" not in match_assessment or match_assessment.get("match_level") == "Unknown":
            try:
                s = float(match_assessment.get("overall_match_score", 0))
                match_assessment["match_level"] = "Excellent" if s >= 4.5 else "Strong" if s >= 4.0 else "Moderate" if s >= 3.0 else "Weak" if s >= 2.0 else "Poor"
            except (TypeError, ValueError):
                match_assessment["match_level"] = "Unknown"
        if "match_percentage" not in match_assessment:
            try:
                score = float(match_assessment.get("overall_match_score", "0.0"))
                mid = int(round(score * 20))
                match_assessment["match_percentage"] = f"{max(0, mid - 6)}-{min(100, mid + 6)}%"
            except (TypeError, ValueError):
                match_assessment["match_percentage"] = "0-10%"
        
        postprocess_match_assessment_skill_fields(match_assessment)

        jra = data.get("job_role_team_analysis")
        if isinstance(jra, dict):
            postprocess_jd_decode_work_scenario_fields(jra)
        
        return data
