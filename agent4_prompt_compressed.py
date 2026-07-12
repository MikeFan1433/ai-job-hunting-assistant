"""
Agent 4 compressed prompt — resume tailoring with strategy, diagnosis, optional summary.
Backward-compatible exports: AGENT4_SYSTEM_BRIEF, AGENT4_JSON_SCHEMA, etc.
"""

from skill_frameworks.resume_tailoring import RESUME_TAILORING_PROMPT

_AGENT4_OUTPUT_JSON_SCHEMA = """
{
  "tailor_strategy": {
    "recommended_version": "ATS|Recruiter|HM",
    "top_3_jd_keywords": ["string"],
    "core_narrative_one_liner": "string",
    "sections_to_emphasize": ["string"],
    "sections_to_compress_or_remove": ["string"],
    "match_too_low_warning": "string or empty"
  },
  "resume_diagnosis": {
    "issues": [
      {"issue": "string", "severity": "high|medium|low", "fix_hint": "string"}
    ]
  },
  "summary_suggestion": {
    "recommended_action": "add|replace|skip",
    "has_existing_summary": true,
    "original_summary": "exact existing summary body from resume when present",
    "suggested_summary": "string or empty",
    "suggested_headline": "string or empty",
    "jd_keywords_embedded": ["string"],
    "feedback_actions": ["accept", "reject", "further_modify"]
  },
  "experience_replacements": [],
  "bullet_level_suggestions": [
    {
      "experience_entry": "string",
      "experience_jd_importance": "High|Medium|Low",
      "suggestions": [
        {
          "original_bullet": "string",
          "suggested_bullet": "string",
          "priority": "High|Medium|Low",
          "reason_struct": {
            "align": "Must-have / Gap — JD requirement",
            "rewrite": "What changed in wording or emphasis",
            "evidence": "Exact resume fact (no fabrication)",
            "expected_impact": "What recruiter/HM should take away"
          },
          "reason": "One paragraph merging align/rewrite/evidence/expected_impact",
          "jd_keywords_added": ["array, can be empty"],
          "feedback_actions": ["accept", "reject", "further_modify"]
        }
      ]
    }
  ],
  "experience_level_rewrites": [
    {
      "experience_entry": "string",
      "rewrite_goal": "Short paragraph",
      "optimized_bullets": ["string"],
      "major_improvements": ["string"],
      "feedback_actions": ["accept", "modify", "reject"]
    }
  ],
  "format_content_adjustments": [],
  "experience_optimizations": [],
  "skills_section_optimization": {
    "has_skills_section": true,
    "current_skills": ["array"],
    "recommended_skills_section": {
      "section_title": "string",
      "skills_to_keep": ["array"],
      "skills_to_add": ["array"],
      "skills_to_remove_or_deemphasize": ["array"],
      "grouping_suggestion": "string"
    },
    "reason": "string",
    "feedback_actions": ["accept", "modify", "reject"]
  },
  "additional_content_integration": [],
  "optimization_summary": {
    "total_experiences_analyzed": 0,
    "total_bullets_reviewed": 0,
    "experiences_recommended_for_replacement": 0,
    "total_bullet_suggestions": 0,
    "total_adjustments_suggested": 0,
    "total_experiences_rewritten": 0,
    "total_experiences_optimized": 0,
    "skills_section_optimized": false,
    "high_priority_changes": ["string"],
    "expected_match_score_improvement": "string",
    "key_improvements": ["string or paragraph"]
  },
  "revised_resume_full": ""
}
"""

AGENT4_JSON_SCHEMA = _AGENT4_OUTPUT_JSON_SCHEMA.strip()

AGENT4_SYSTEM_BRIEF = f"""You are the Resume Optimization Assistant (Agent 4).
Return ONLY one valid JSON object; the user message includes the required schema. No markdown or prose outside JSON.
Ground every change in the JD, resume, and (when provided) Agent 2/3 outputs. Be factual; do not invent outcomes, metrics, ownership, or tools.

{RESUME_TAILORING_PROMPT}

Output order: tailor_strategy → resume_diagnosis → summary_suggestion → bullet_level_suggestions → experience_level_rewrites → skills_section_optimization → optimization_summary → revised_resume_full (empty string; app applies accepted edits).

For bullet_level_suggestions: every original_bullet must match a line from the supplied resume. Every suggested_bullet must be complete—never empty or placeholder.
Use the user's preferred output language for all strings (full Chinese OR full English, never mixed)."""

AGENT4_JD_RESUME_ONLY_PROMPT = AGENT4_SYSTEM_BRIEF

AGENT4_RESUME_OPTIMIZATION_PROMPT = f"""You are the Resume Optimization Assistant.

Task: Optimize the candidate's resume for the target JD using JD, resume, Agent 2 (when provided) and optional supplemental content.

{RESUME_TAILORING_PROMPT}

Execution rules:
1. Output tailor_strategy BEFORE bullet edits (strategy-first).
2. summary_suggestion: when resume has Summary/Profile section, ALWAYS recommended_action "replace" with JD-tailored suggested_summary; set has_existing_summary and original_summary. Use "skip" only when resume truly lacks a summary section and adding one would not help.
3. bullet_level_suggestions: EVERY substantive bullet in recent roles gets one suggestion row.
4. High-priority bullets use HM template: Problem → Decision → Action → Result.
5. Keyword density: top_3_jd_keywords each appear 2-4× across Summary + Skills + bullets.
6. 1-page constraint: pair adds with remove/tighten suggestions when length is at risk.
7. reason_struct + reason required on every bullet suggestion.
8. revised_resume_full: empty string (downstream applies user-accepted edits).
9. When Agent 2 resume_adjustment_suggestions provided: every High-priority bullet maps to priority_rank ≤3 item or must-have gap; honor recommended_version wording (ATS/Recruiter/HM).

Required top-level keys:
tailor_strategy, resume_diagnosis, summary_suggestion, experience_replacements, bullet_level_suggestions,
experience_level_rewrites, skills_section_optimization, additional_content_integration, optimization_summary, revised_resume_full

Required JSON schema:
{_AGENT4_OUTPUT_JSON_SCHEMA}

Return only valid JSON.
"""

# Aliases for tests / imports
RESUME_OPTIMIZATION_JSON_SCHEMA = AGENT4_JSON_SCHEMA
RESUME_OPTIMIZATION_PROMPT = AGENT4_RESUME_OPTIMIZATION_PROMPT
GLOBAL_PRINCIPLES_PROMPT = AGENT4_SYSTEM_BRIEF.split("Ground every change")[0].strip()
RESUME_TAILORING_PROMPT_FULL = AGENT4_RESUME_OPTIMIZATION_PROMPT
