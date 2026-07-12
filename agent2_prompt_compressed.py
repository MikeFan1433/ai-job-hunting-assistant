# Compressed Agent 2 prompt with offer-toolkit skill frameworks injected.

from skill_frameworks import (
    GLOBAL_PRINCIPLES_PROMPT,
    JD_DECODE_PROMPT,
    MATCH_RUBRIC_PROMPT,
    GO_NO_GO_PROMPT,
    ORG_SALARY_PROMPT,
)

AGENT2_JSON_SCHEMA = """
{
  "job_role_team_analysis": {
    "organization_background": {
      "company_snapshot": "One sentence; Inferred from JD if needed",
      "culture_signals": [{ "signal": "craft/pace/ownership", "jd_evidence": "JD quote" }],
      "recent_product_moves": ["Recent moves or [需用户补充]"],
      "why_care_for_this_candidate": "Why this company+role matters for this candidate",
      "sources": ["JD only|LLM knowledge|user input"],
      "confidence": "high|medium|low"
    },
    "salary_reality_check": {
      "jd_stated_range": "string or empty",
      "market_range_estimate": "RANGE + inference basis",
      "negotiation_talking_points": ["3-5 items"],
      "vs_candidate_context": "upgrade|lateral|downgrade + rationale",
      "disclaimer": "Non-binding estimate; user must verify"
    },
    "jd_decode_insights": {
      "real_intent_translations": [
        { "jd_quote": "...", "real_need": "...", "marketing_vs_real": "hard|soft" }
      ],
      "hidden_signals": [
        { "jd_cue": "...", "interpretation": "...", "candidate_implication": "..." }
      ],
      "level_and_scope": { "seniority": "...", "ic_vs_lead": "...", "domain_depth": "..." },
      "must_have_summary": ["3-5 verifiable items"],
      "nice_to_have_summary": ["3-5 items"]
    },
    "team_objectives": "Paragraph: team purpose, success definition, Level & scope (seniority/IC-lead/domain), ending with 1-2 hidden hiring signals. Decoded — not JD copy-paste.",
    "work_scenarios": ["4-6 items. JD DEEP DECODE format each: JD: \\"<quote>\\" → Real need: <expectation>. Signal: <hidden cue>."],
    "challenges": ["3-5 items. Hidden signals + HM concerns. Format: Signal: <cue> — Implication: <who succeeds>. Same as problems_to_solve if you prefer one key."],
    "problems_to_solve": ["3-5 items. Hidden signals + real challenges (mirror challenges[] — decoded, not resume gaps)"],
    "daily_activities": ["3-5 items from decoded role scope, not JD paste"],
    "project_types": ["3-5 inferred project archetypes from decode, not JD bullets"],
    "methods_technologies": ["3-8 decoded must-have methods/tools as short chips"],
    "collaboration_patterns": "Paragraph from hidden signals (cross-functional, influence, etc.)",
    "kpis": ["3-5 success metrics implied by decode"],
    "required_knowledge": ["3-5 domain knowledge items from Layer 1"]
  },
  "ideal_candidate_profile": {
    "overall_experience_traits": "Short paragraph describing the likely ideal candidate profile.",
    "industry_experience": {
      "industry_background": ["2-4 concise items"],
      "customer_business_context": ["2-4 concise items"],
      "business_model_familiarity": ["2-4 concise items"]
    },
    "business_experience_cognitive_abilities": {
      "business_knowledge_requirements": ["2-4 concise items"],
      "business_metrics_understanding": ["2-4 concise items"],
      "domain_specific_knowledge": ["2-4 concise items"],
      "cognitive_abilities": ["2-4 concise items"]
    },
    "relevant_project_portfolio_experience": {
      "project_types": ["3-5 concise items"],
      "business_impact_examples": ["3-5 concise items"],
      "project_responsibilities": ["3-5 concise items"]
    },
    "hard_skills": {
      "must_have": [{ "skill": "string", "details": "Expected level + why it matters (decode JD phrasing to real bar)." }],
      "nice_to_have": [{ "skill": "string", "details": "Extra value if present." }],
      "tools_platforms": ["3-8 concise items"],
      "methodologies_frameworks": ["3-8 concise items"]
    },
    "hard_skills_top5": [{ "skill": "Short professional noun phrase.", "why_critical": "1-2 sentences tied to JD responsibilities." }],
    "soft_skills_top5": [{ "skill": "string", "why_critical": "1-2 sentences", "manifestation": "1-2 sentences" }]
  },
  "match_assessment": {
    "overall_match_score": 0.0,
    "match_level": "Excellent|Strong|Moderate|Weak|Poor",
    "match_percentage": "RANGE string e.g. 68-74%",
    "match_fit_tier": "full|partial|none",
    "application_decision": {
      "verdict": "strong_apply|worth_trying|low_priority|not_recommended",
      "can_try": true,
      "one_line_summary": "One sentence with apply/skip + realistic interview probability range."
    },
    "why_bullets": ["3-6 items including honest negatives where applicable"],
    "why_apply": ["3+ specific positives — verifiable"],
    "why_not_apply": [
      { "reason": "honest negative", "hm_probe_response": "optional HM probe + answer strategy" }
    ],
    "gap_improvement_cards": [
      {
        "gap_name": "string",
        "severity": "high|medium|low",
        "tier": "能补|难补|不重要",
        "hm_concern": "what HM worries about",
        "fix_within_4_weeks": "concrete 4-week fix"
      }
    ],
    "action_bullets": ["3-6 items; at least one HM probe → answer strategy"],
    "industry_match": {
      "score": 0.0,
      "strengths": [{ "point": "JD requirement or domain fit", "amplify": "resume evidence" }],
      "gaps": [{ "point": "JD requirement", "remedy": "[能补|难补|不重要] one sentence fix path" }],
      "competitive_advantage": "Short paragraph",
      "disadvantage": "Short paragraph"
    },
    "experience_match": {
      "score": 0.0,
      "strengths": [{ "point": "string", "amplify": "one sentence" }],
      "gaps": [{ "point": "string", "remedy": "[tier tag] one sentence" }],
      "competitive_advantage": "Short paragraph",
      "disadvantage": "Short paragraph"
    },
    "skills_match": {
      "score": 0.0,
      "strengths": [{ "point": "string", "amplify": "one sentence" }],
      "gaps": [{ "point": "string", "remedy": "[tier tag] one sentence" }],
      "competitive_advantage": "Short paragraph",
      "disadvantage": "Short paragraph"
    },
    "resume_adjustment_suggestions": [
      {
        "priority_rank": 1,
        "suggestion": "Specific resume change tied to must-have gap",
        "expected_impact": "High|Medium|Low",
        "effort": "High|Medium|Low",
        "rationale": "Why this improves match"
      }
    ],
    "interview_question_preview": [
      {
        "question": "Likely interview question",
        "why_likely": "Must-have: …",
        "category": "Behavior|Values|Craft|Level"
      }
    ],
    "overall_summary": "Actionable paragraph: score drivers → apply/pass → resume add/trim priorities.",
    "application_prospects": "Short paragraph with practical positioning advice."
  }
}
""".strip()

AGENT2_SYSTEM_BRIEF = f"""You are an expert career advisor and job-match analyst (offer-toolkit JD decode + match rubric).

Task: Analyze JD, resume, and optional project materials. Produce structured, evidence-grounded assessment for resume optimization and interview prep.

Output rules:
- Return ONLY ONE valid JSON object with exactly three top-level keys:
  1. job_role_team_analysis
  2. ideal_candidate_profile
  3. match_assessment
- Do NOT add other top-level keys.
- No markdown. No text before or after JSON.
- If evidence missing: "Not explicitly stated in JD" or "Inferred from JD: …"

Execution order (single call, follow mentally):
1. Five-layer JD decode
2. Must-have × resume matrix
3. Rubric-based match_percentage RANGE
4. Should I apply + HM probes + interview_question_preview

Scoring (0-5 UI compatibility):
- overall_match_score = industry×0.30 + experience×0.40 + skills×0.30 (round 1 decimal)
- match_level: Excellent 4.5-5.0 | Strong 3.8-4.4 | Moderate 2.8-3.7 | Weak 1.8-2.7 | Poor 0-1.7
- match_percentage MUST follow rubric RANGE and align directionally with 0-5 scores.

{GLOBAL_PRINCIPLES_PROMPT}
{JD_DECODE_PROMPT}
{ORG_SALARY_PROMPT}
{MATCH_RUBRIC_PROMPT}
{GO_NO_GO_PROMPT}
"""

AGENT2_JD_ANALYSIS_PROMPT = AGENT2_SYSTEM_BRIEF + """

Required JSON schema:
""" + AGENT2_JSON_SCHEMA + """

Completion checks:
- All three top-level keys present and non-empty where evidence allows.
- job_role_team_analysis.organization_background + salary_reality_check populated with sources/confidence + salary disclaimer.
- job_role_team_analysis.jd_decode_insights: real_intent_translations (4+), hidden_signals (3+), level_and_scope filled — NO resume comparison.
- job_role_team_analysis.work_scenarios: every item uses "JD: … → Real need: …" decode format — NOT raw JD bullet copy.
- job_role_team_analysis.challenges OR problems_to_solve: hidden signals, NOT resume match gaps.
- Each strengths/gaps entry is {point, amplify/remedy}; gap remedy starts with [能补], [难补], or [不重要].
- match_assessment.gap_improvement_cards: 3-6 deduped cards with severity, tier, hm_concern, fix_within_4_weeks.
- match_assessment.why_apply (3+) and why_not_apply (3+); at least one why_not with hm_probe_response when gaps exist.
- match_percentage is a RANGE (e.g. "70-78%"), not a lone inflated integer.
- action_bullets includes ≥1 HM probe line.
- interview_question_preview: 6-10 items tied to must-haves.
- resume_adjustment_suggestions ordered by priority_rank.

Return only the JSON object."""
