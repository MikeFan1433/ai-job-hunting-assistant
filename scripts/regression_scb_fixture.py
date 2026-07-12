#!/usr/bin/env python3
"""Regression checks for offer-toolkit integration (渣打 SCB fixture + unit tests)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from resume_optimization_service import ResumeOptimizationService
from agent2 import (
    postprocess_match_assessment_skill_fields,
    postprocess_jd_decode_work_scenario_fields,
    normalize_match_percentage_range,
    reconcile_dual_track_scoring,
)


def test_bullet_feedback_applies_to_final_resume() -> None:
    svc = ResumeOptimizationService()
    original = """EXPERIENCE
Acme Corp — Product Manager
• Led cross-functional team to launch AI chatbot for customer support
• Improved user satisfaction through data-driven roadmap prioritization
"""
    recommendations = {
        "bullet_level_suggestions": [
            {
                "experience_entry": "Acme Corp — Product Manager",
                "suggestions": [
                    {
                        "original_bullet": "Led cross-functional team to launch AI chatbot for customer support",
                        "suggested_bullet": "Led cross-functional team to launch agentic AI chatbot aligned with enterprise support KPIs",
                    }
                ],
            }
        ]
    }
    svc.load_original_resume(original)
    svc.load_optimization_recommendations(recommendations)
    svc.submit_feedback(
        feedback_type="bullet_suggestion",
        item_id="bls_0_0",
        feedback="accept",
    )
    result = svc.apply_feedback_and_generate_resume()
    final = result["final_resume"]
    assert "agentic AI chatbot" in final
    assert result["total_modifications"] == 1
    print("✓ bullet accept updates final resume")


def test_bullet_edit_uses_modified_text() -> None:
    svc = ResumeOptimizationService()
    original = "• Built ML pipeline for fraud detection"
    recommendations = {
        "bullet_level_suggestions": [
            {
                "experience_entry": "Role",
                "suggestions": [
                    {
                        "original_bullet": "Built ML pipeline for fraud detection",
                        "suggested_bullet": "Built ML pipeline for fraud detection with real-time scoring",
                    }
                ],
            }
        ]
    }
    svc.load_original_resume(original)
    svc.load_optimization_recommendations(recommendations)
    svc.submit_feedback(
        feedback_type="bullet_suggestion",
        item_id="bls_0_0",
        feedback="further_modify",
        modified_text="Built ML pipeline for fraud detection with agentic workflow orchestration",
    )
    result = svc.apply_feedback_and_generate_resume()
    assert "agentic workflow orchestration" in result["final_resume"]
    print("✓ bullet further_modify uses modified_text")


def test_match_percentage_range_postprocess() -> None:
    ma = {
        "overall_match_score": 3.6,
        "match_percentage": "92",
        "application_decision": {"verdict": "strong_apply", "can_try": True},
        "industry_match": {"score": 3.5, "gaps": [{"point": "CIB domain", "remedy": "Add capital markets exposure"}]},
        "experience_match": {"score": 3.6, "gaps": []},
        "skills_match": {"score": 3.4, "gaps": []},
    }
    postprocess_match_assessment_skill_fields(ma)
    assert "-" in ma["match_percentage"]
    assert ma["match_percentage"].endswith("%")
    assert ma["industry_match"]["gaps"][0]["remedy"].startswith("[")
    print(f"✓ match_percentage normalized to {ma['match_percentage']}")


def test_dual_track_reconcile() -> None:
    ma = {
        "overall_match_score": 4.5,
        "match_percentage": "55-60%",
        "application_decision": {"verdict": "strong_apply", "can_try": True},
        "industry_match": {"score": 4.5},
        "experience_match": {"score": 4.5},
        "skills_match": {"score": 4.5},
    }
    reconcile_dual_track_scoring(ma)
    assert ma["application_decision"]["verdict"] == "worth_trying"
    print("✓ dual-track scoring reconciles inflated verdict")


def test_skill_frameworks_import() -> None:
    from skill_frameworks import (
        GLOBAL_PRINCIPLES_PROMPT,
        JD_DECODE_PROMPT,
        MATCH_RUBRIC_PROMPT,
        GO_NO_GO_PROMPT,
        ORG_SALARY_PROMPT,
        RESUME_TAILORING_PROMPT,
        BQ_PREP_PROMPT,
        INTERVIEW_PREDICT_BEHAVIOR_PROMPT,
        INTERVIEW_PREDICT_TOP10_PROMPT,
    )

    for name, blob in [
        ("GLOBAL", GLOBAL_PRINCIPLES_PROMPT),
        ("JD_DECODE", JD_DECODE_PROMPT),
        ("RUBRIC", MATCH_RUBRIC_PROMPT),
        ("GO_NO_GO", GO_NO_GO_PROMPT),
        ("ORG_SALARY", ORG_SALARY_PROMPT),
        ("RESUME", RESUME_TAILORING_PROMPT),
        ("BQ", BQ_PREP_PROMPT),
        ("INTERVIEW_PREDICT", INTERVIEW_PREDICT_BEHAVIOR_PROMPT),
        ("INTERVIEW_TOP10", INTERVIEW_PREDICT_TOP10_PROMPT),
    ]:
        assert len(blob) > 50, f"{name} prompt too short"
    assert "real_intent_translations" in JD_DECODE_PROMPT
    assert "gap_improvement_cards" in GO_NO_GO_PROMPT
    assert "predicted_interview_questions" in INTERVIEW_PREDICT_TOP10_PROMPT
    print("✓ skill_frameworks imports OK")


def test_agent2_prompt_has_skill_blocks() -> None:
    from agent2_prompt_compressed import AGENT2_SYSTEM_BRIEF, AGENT2_JSON_SCHEMA

    assert "MATCH RUBRIC" in AGENT2_SYSTEM_BRIEF
    assert "interview_question_preview" in AGENT2_JSON_SCHEMA
    assert "WORK SCENARIO TAB FIELD MAPPING" in AGENT2_SYSTEM_BRIEF
    assert "JD DEEP DECODE format" in AGENT2_JSON_SCHEMA or "Real need:" in AGENT2_JSON_SCHEMA
    assert '"challenges"' in AGENT2_JSON_SCHEMA
    assert "organization_background" in AGENT2_JSON_SCHEMA
    assert "salary_reality_check" in AGENT2_JSON_SCHEMA
    assert "jd_decode_insights" in AGENT2_JSON_SCHEMA
    assert "real_intent_translations" in AGENT2_JSON_SCHEMA
    assert "gap_improvement_cards" in AGENT2_JSON_SCHEMA
    assert "why_not_apply" in AGENT2_JSON_SCHEMA
    assert "ORGANIZATION BACKGROUND" in AGENT2_SYSTEM_BRIEF or "organization_background" in AGENT2_JSON_SCHEMA
    print("✓ agent2 prompt includes skill frameworks + JD decode work scenario mapping")


def test_postprocess_jd_decode_work_scenario_fields() -> None:
    jra = {
        "work_scenarios": [
            {
                "jd_quote": "comfortable with ambiguity",
                "real_need": "self-directed problem definition",
                "signal": "high autonomy",
            },
            "JD: \"fast-paced\" → Real need: ship weekly. Signal: startup culture.",
        ],
        "problems_to_solve": ["Signal: ownership — Implication: end-to-end driver"],
        "challenges": [],
    }
    postprocess_jd_decode_work_scenario_fields(jra)
    assert jra["challenges"] == jra["problems_to_solve"]
    assert 'JD: "comfortable with ambiguity"' in jra["work_scenarios"][0]
    assert "Real need:" in jra["work_scenarios"][0]
    assert len(jra["work_scenarios"]) == 2
    print("✓ JD decode postprocess maps challenges + work_scenarios format")


def test_postprocess_org_salary_and_insights() -> None:
    jra = {
        "organization_background": {
            "culture_signals": ["fast-paced"],
        },
        "salary_reality_check": {},
        "jd_decode_insights": {
            "real_intent_translations": [
                {"jd_quote": "ambiguity", "real_need": "self-direction", "marketing_vs_real": "hard"}
            ],
        },
        "work_scenarios": [],
        "challenges": [],
    }
    postprocess_jd_decode_work_scenario_fields(jra)
    assert jra["organization_background"]["confidence"] in ("high", "medium", "low")
    assert jra["salary_reality_check"]["disclaimer"]
    assert len(jra["jd_decode_insights"]["real_intent_translations"]) == 1
    assert len(jra["work_scenarios"]) == 1
    print("✓ org/salary/jd_decode_insights postprocess defaults")


def test_postprocess_gap_cards_and_why_apply() -> None:
    ma = {
        "overall_match_score": 3.2,
        "match_percentage": "55-62%",
        "application_decision": {"verdict": "worth_trying", "can_try": True},
        "why_bullets": ["Strong AI background", "Gap: no banking domain"],
        "industry_match": {
            "score": 2.5,
            "gaps": [{"point": "Banking domain", "remedy": "[难补] Add capital markets story"}],
        },
        "experience_match": {"score": 3.5, "gaps": []},
        "skills_match": {"score": 3.4, "gaps": []},
    }
    postprocess_match_assessment_skill_fields(ma)
    assert len(ma["gap_improvement_cards"]) >= 1
    assert ma["gap_improvement_cards"][0]["tier"] == "难补"
    assert len(ma["why_apply"]) >= 1
    print("✓ gap_improvement_cards + why_apply postprocess")


def test_agent4_prompt_has_tailor_strategy() -> None:
    from agent4_prompt_compressed import AGENT4_JSON_SCHEMA, AGENT4_SYSTEM_BRIEF, RESUME_TAILORING_PROMPT

    assert "tailor_strategy" in AGENT4_JSON_SCHEMA
    assert "summary_suggestion" in AGENT4_JSON_SCHEMA
    assert "reason_struct" in AGENT4_JSON_SCHEMA
    assert "PHASE B" in RESUME_TAILORING_PROMPT or "tailor_strategy" in RESUME_TAILORING_PROMPT
    assert "HM-style" in RESUME_TAILORING_PROMPT or "HM template" in RESUME_TAILORING_PROMPT.lower()
    assert "keyword" in RESUME_TAILORING_PROMPT.lower()
    assert "1-page" in RESUME_TAILORING_PROMPT.lower() or "1 page" in RESUME_TAILORING_PROMPT.lower()
    assert "recommended_version" in AGENT4_JSON_SCHEMA or "THREE-VERSION" in RESUME_TAILORING_PROMPT
    assert "ATS" in RESUME_TAILORING_PROMPT and "HM" in RESUME_TAILORING_PROMPT
    print("✓ agent4 prompt includes tailor_strategy + skill rules")


def test_summary_accept_prepends_to_final_resume() -> None:
    svc = ResumeOptimizationService()
    original = """Boyang Fan
Toronto, ON

WORK EXPERIENCE
Acme — PM
• Led team
"""
    recommendations = {
        "summary_suggestion": {
            "recommended_action": "add",
            "suggested_headline": "Senior AI Product Leader",
            "suggested_summary": "AI product leader with enterprise delivery experience.",
        }
    }
    svc.load_original_resume(original)
    svc.load_optimization_recommendations(recommendations)
    svc.submit_feedback(
        feedback_type="summary_suggestion",
        item_id="summary_suggestion",
        feedback="accept",
    )
    result = svc.apply_feedback_and_generate_resume()
    final = result["final_resume"]
    assert "SUMMARY" in final
    assert "Senior AI Product Leader" in final
    assert result.get("resume_data_yaml")
    print("✓ summary accept inserts SUMMARY section + yaml export")


def test_experience_level_rewrites_mapped_on_load() -> None:
    svc = ResumeOptimizationService()
    recommendations = {
        "experience_level_rewrites": [
            {
                "experience_entry": "Acme — PM",
                "rewrite_goal": "Emphasize AI portfolio ownership",
                "optimized_bullets": ["Owned AI roadmap"],
            }
        ]
    }
    svc.load_optimization_recommendations(recommendations)
    opts = svc.optimization_recommendations.get("experience_optimizations") or []
    assert len(opts) == 1
    assert opts[0]["experience_entry"]["title"] == "Acme — PM"
    print("✓ experience_level_rewrites mapped to experience_optimizations")


def test_agent4_normalize_reason_struct() -> None:
    from agent4 import ResumeOptimizationAgent, _normalize_bullet_reason

    s = {"reason_struct": {"align": "JD backlog", "rewrite": "Stronger verb", "evidence": "Resume fact", "expected_impact": "Director signal"}}
    _normalize_bullet_reason(s)
    assert "对齐" in s["reason"] or "JD backlog" in s["reason"]
    print("✓ reason_struct normalized to reason string")


def test_rehydrate_empty_service_then_generate() -> None:
    """Simulate backend restart: empty optimization_service + workflow_results → rehydrate → generate."""
    from workflow_api import (
        _persist_optimization_state,
        _rehydrate_optimization_service,
        optimization_service,
        workflow_results,
    )

    workflow_id = "test_rehydrate_fixture"
    original = """EXPERIENCE
Acme Corp — Product Manager
• Led cross-functional team to launch AI chatbot for customer support
"""
    agent4 = {
        "bullet_level_suggestions": [
            {
                "experience_entry": "Acme Corp — Product Manager",
                "suggestions": [
                    {
                        "original_bullet": "Led cross-functional team to launch AI chatbot for customer support",
                        "suggested_bullet": "Led cross-functional team to launch agentic AI chatbot aligned with enterprise support KPIs",
                    }
                ],
            }
        ]
    }
    workflow_results[workflow_id] = {
        "resume_text": original,
        "agent3_outputs": {"selected_projects": [], "skipped": True},
        "agent4_outputs": agent4,
    }

    optimization_service.original_resume = ""
    optimization_service.optimization_recommendations = {}
    optimization_service.user_feedback = {}
    optimization_service.final_resume = ""
    optimization_service.agent3_outputs = {}

    _rehydrate_optimization_service(workflow_id)
    optimization_service.submit_feedback(
        feedback_type="bullet_suggestion",
        item_id="bls_0_0",
        feedback="accept",
    )
    _persist_optimization_state(workflow_id)

    optimization_service.original_resume = ""
    optimization_service.optimization_recommendations = {}
    optimization_service.user_feedback = {}
    optimization_service.final_resume = ""
    optimization_service.agent3_outputs = {}

    _rehydrate_optimization_service(workflow_id)
    result = optimization_service.apply_feedback_and_generate_resume()
    assert "error" not in result, result.get("error")
    assert "agentic AI chatbot" in result["final_resume"]

    workflow_results.pop(workflow_id, None)
    print("✓ rehydrate empty service then generate succeeds")


def test_agent5_prompt_uses_interview_predictor() -> None:
    from agent5_prompt_compressed import AGENT5_SYSTEM_BRIEF, AGENT5_JSON_SCHEMA
    from skill_frameworks.interview_predict import INTERVIEW_PREDICT_BEHAVIOR_PROMPT

    assert "INTERVIEW PREDICTOR" in AGENT5_SYSTEM_BRIEF or "BEHAVIORAL QUESTION PREDICTION" in AGENT5_SYSTEM_BRIEF
    assert "Exactly 10" in INTERVIEW_PREDICT_BEHAVIOR_PROMPT or "EXACTLY 10" in INTERVIEW_PREDICT_BEHAVIOR_PROMPT
    assert "predicted_interview_questions" in AGENT5_JSON_SCHEMA
    assert "answer_framework" in AGENT5_JSON_SCHEMA
    assert "key_points_to_emphasize" in AGENT5_JSON_SCHEMA
    print("✓ agent5 prompt uses interview-predictor behavioral flow")


def test_agent5_normalize_predicted_questions() -> None:
    from agent5 import InterviewPreparationAgent

    agent = InterviewPreparationAgent.__new__(InterviewPreparationAgent)
    summary = {
        "predicted_interview_questions": [
            {"question": "Q2", "category": "Domain", "priority": "medium", "why_likely": "Must-have"},
            {"question": "Q1", "category": "Behavior", "priority": "high", "why_likely": "Gap"},
        ]
    }
    agent._normalize_predicted_interview_questions(summary)
    qs = summary["predicted_interview_questions"]
    assert qs[0]["question"] == "Q1"
    assert qs[0]["category"] == "Behavior"
    print("✓ agent5 predicted_interview_questions normalization")


def test_agent5_normalize_behavioral_questions() -> None:
    from agent5 import InterviewPreparationAgent

    agent = InterviewPreparationAgent.__new__(InterviewPreparationAgent)
    theme1 = {
        "top_behavioral_questions": [
            {"question": "Q2", "priority_rank": 2},
            {"question": "Q1", "priority_rank": 1, "why_they_ask_this": "tests ambiguity"},
        ]
    }
    agent._normalize_behavioral_questions(theme1)
    qs = theme1["top_10_behavioral_questions"]
    assert len(qs) == 2
    assert qs[0]["question"] == "Q1"
    assert qs[0]["why_they_ask_this"].startswith("[Behavior]")
    assert qs[0]["category"] == "Behavior"
    print("✓ agent5 behavioral question normalization")


def test_modifications_to_replacements() -> None:
    from pdf_resume_editor import modifications_to_replacements

    mods = [
        {"type": "bullet_suggestion", "original": "Led team", "replaced_with": "Led cross-functional team"},
        {"type": "summary_suggestion", "original": "Professional summary", "replaced_with": "New summary"},
        {"type": "summary_bullet", "original": "Old bullet", "replaced_with": "New bullet"},
    ]
    pairs = modifications_to_replacements(mods)
    assert len(pairs) == 1
    assert pairs[0][0] == "Led team"
    print("✓ modifications_to_replacements filters summary (handled as section replace)")


def test_summary_section_replace_no_overlap() -> None:
    """Replacing an existing SUMMARY must clear old bullets (no overlap) before rewrite."""
    from pdf_resume_editor import apply_summary_section_replace, PYMUPDF_AVAILABLE

    if not PYMUPDF_AVAILABLE:
        print("⚠ PyMuPDF not installed — skip summary section replace test")
        return

    import fitz

    src = "/Users/mikefan/Desktop/渣打/Resume - Mike Fan.pdf"
    try:
        with open(src, "rb") as f:
            pdf_bytes = f.read()
    except FileNotFoundError:
        print("⚠ sample resume PDF not found — skip summary section replace test")
        return

    new_body = (
        "● End-to-end AI Product Owner in global banking with 6+ years shipping GenAI products.\n"
        "● China market experience leading AI product decisions across regulated environments.\n"
        "● Built OKR frameworks and audit-ready model risk governance for LLM products."
    )
    out, stats = apply_summary_section_replace(pdf_bytes, new_body)
    assert stats.get("replaced"), stats
    doc = fitz.open(stream=out, filetype="pdf")
    text = doc[0].get_text()
    doc.close()
    assert "End-to-end AI Product Owner" in text or "End-to-end" in text
    # Old first summary bullet should be gone
    assert "Proven AI Product Owner in global banking" not in text
    # No soft-hyphen / null artifacts from writer
    assert "\x00" not in text
    print("✓ summary section replace clears old bullets without overlap")


def test_pdf_preserve_layout_roundtrip() -> None:
    from pdf_resume_editor import apply_pdf_text_replacements, PYMUPDF_AVAILABLE

    if not PYMUPDF_AVAILABLE:
        print("⚠ PyMuPDF not installed — skip PDF layout test")
        return

    import fitz

    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 100), "Led cross-functional team to launch AI chatbot", fontname="helv", fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()

    edited, stats = apply_pdf_text_replacements(
        pdf_bytes,
        [("Led cross-functional team to launch AI chatbot", "Led team to launch agentic AI chatbot for support KPIs")],
    )
    assert stats.get("applied", 0) >= 1
    reopened = fitz.open(stream=edited, filetype="pdf")
    text = reopened[0].get_text()
    reopened.close()
    assert "agentic AI chatbot" in text
    print("✓ PDF in-place replacement preserves document structure")


def test_export_preserves_layout_when_pdf_edits_miss() -> None:
    """When in-place PDF search fails, keep original PDF layout — do not regenerate via ReportLab."""
    from workflow_api import _build_resume_pdf_bytes, PYMUPDF_AVAILABLE

    if not PYMUPDF_AVAILABLE:
        print("⚠ PyMuPDF not installed — skip export layout test")
        return

    import fitz

    original_text = "Led cross-functional team to launch AI chatbot for customer support"
    final_resume = original_text.replace(
        "AI chatbot for customer support",
        "agentic AI chatbot aligned with enterprise support KPIs",
    )
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 100), "Totally different PDF text that will not match", fontname="helv", fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()

    wf_data = {
        "resume_text": original_text,
        "modifications_applied": [
            {
                "type": "bullet_suggestion",
                "original": original_text,
                "replaced_with": final_resume,
            }
        ],
    }
    out = _build_resume_pdf_bytes(pdf_bytes, wf_data, final_resume, "Resume")
    reopened = fitz.open(stream=out, filetype="pdf")
    text = reopened[0].get_text()
    producer = reopened.metadata.get("producer", "")
    reopened.close()
    assert "Totally different PDF text" in text
    assert "ReportLab" not in (producer or "")
    print("✓ export preserves original PDF when in-place edits miss")


def test_export_summary_inserts_into_uploaded_pdf() -> None:
    """Summary-only optimizations insert SUMMARY into uploaded PDF instead of ReportLab export."""
    from workflow_api import _build_resume_pdf_bytes, PYMUPDF_AVAILABLE

    if not PYMUPDF_AVAILABLE:
        print("⚠ PyMuPDF not installed — skip summary layout test")
        return

    import fitz

    original = "Boyang Fan\nTel: test@test.com\nWORK EXPERIENCE\nAcme — PM\n• Led team\n"
    final = (
        "Boyang Fan\nTel: test@test.com\nSUMMARY\nSenior AI Product Leader\nAI product leader.\n\n"
        "WORK EXPERIENCE\nAcme — PM\n• Led team\n"
    )
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Boyang Fan", fontname="helv", fontsize=11)
    page.insert_text((72, 100), "Tel: test@test.com", fontname="helv", fontsize=10)
    page.insert_text((72, 130), "WORK EXPERIENCE", fontname="helv", fontsize=11)
    page.insert_text((72, 150), "Acme — PM", fontname="helv", fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()

    wf_data = {
        "resume_text": original,
        "modifications_applied": [
            {
                "type": "summary_suggestion",
                "original": "Professional summary",
                "replaced_with": "Senior AI Product Leader",
            }
        ],
    }
    out = _build_resume_pdf_bytes(pdf_bytes, wf_data, final, "Resume")
    reopened = fitz.open(stream=out, filetype="pdf")
    text = reopened[0].get_text()
    producer = reopened.metadata.get("producer", "")
    reopened.close()
    assert "SUMMARY" in text
    assert "Senior AI Product Leader" in text
    assert "ReportLab" not in (producer or "")
    print("✓ summary-only export inserts into uploaded PDF layout")


def test_scb_fixture_files_exist() -> None:
    jd_docx = Path("/Users/mikefan/Desktop/渣打/Senior AI Analyst.docx")
    resume_pdf = Path("/Users/mikefan/Desktop/Resume/AI Product Manager/Resume - Boyang Fan.pdf")
    baseline_html = Path("/Users/mikefan/Desktop/job-hunt")
    if jd_docx.exists():
        print(f"✓ SCB JD fixture found: {jd_docx}")
    else:
        print(f"⚠ SCB JD fixture missing (optional): {jd_docx}")
    if resume_pdf.exists():
        print(f"✓ SCB resume fixture found: {resume_pdf}")
    else:
        print(f"⚠ SCB resume fixture missing (optional): {resume_pdf}")
    html_files = list(baseline_html.glob("offer-strategy-scb-*.html")) if baseline_html.exists() else []
    if html_files:
        print(f"✓ offer-toolkit baseline HTML: {html_files[0].name}")
    else:
        print("⚠ offer-toolkit baseline HTML not found (optional comparison)")


def main() -> int:
    tests = [
        test_skill_frameworks_import,
        test_agent2_prompt_has_skill_blocks,
        test_postprocess_jd_decode_work_scenario_fields,
        test_postprocess_org_salary_and_insights,
        test_postprocess_gap_cards_and_why_apply,
        test_agent4_prompt_has_tailor_strategy,
        test_bullet_feedback_applies_to_final_resume,
        test_bullet_edit_uses_modified_text,
        test_summary_accept_prepends_to_final_resume,
        test_experience_level_rewrites_mapped_on_load,
        test_rehydrate_empty_service_then_generate,
        test_agent4_normalize_reason_struct,
        test_agent5_prompt_uses_interview_predictor,
        test_agent5_normalize_behavioral_questions,
        test_agent5_normalize_predicted_questions,
        test_modifications_to_replacements,
        test_summary_section_replace_no_overlap,
        test_pdf_preserve_layout_roundtrip,
        test_export_preserves_layout_when_pdf_edits_miss,
        test_export_summary_inserts_into_uploaded_pdf,
        test_match_percentage_range_postprocess,
        test_dual_track_reconcile,
        test_scb_fixture_files_exist,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            failed += 1
            print(f"✗ {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
