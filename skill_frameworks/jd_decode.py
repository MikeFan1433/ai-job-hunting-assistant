"""Five-layer JD decode instructions (job-description-skill jd-decoder)."""

JD_DECODE_PROMPT = """
=== JD DECODE (execute BEFORE match_assessment; Layer 5 resume cross-check goes to match_assessment only) ===
Layer 1 — Stated requirements: Extract explicit must-have / nice-to-have from JD wording.
Layer 2 — Real intent: Translate marketing phrases to real expectations (e.g. "comfortable with ambiguity" → self-directed problem definition; "deep expertise" → 5+ years verifiable depth).
Layer 3 — Hidden signals: Infer hiring-manager persona from repeated cues (ownership, cross-functional, fast-paced, craft, mission-driven). Use decode-patterns style table mentally.
Layer 4 — Level & scope: Infer seniority, IC vs lead, domain depth (enterprise vs consumer, 0→1 vs scale).
Layer 5 — Resume cross-check: ONLY in match_assessment strengths/gaps — NOT in job_role_team_analysis work_scenarios.

=== WORK SCENARIO TAB FIELD MAPPING (job_role_team_analysis) ===
Replace JD copy-paste with decoded intelligence. NO verbatim JD bullet lists in work_scenarios.

team_objectives (paragraph):
- Team purpose + who they serve + success definition
- End with Level & scope summary (seniority, IC/lead, domain) and 1-2 hidden hiring signals
- Do NOT paste JD responsibilities verbatim

work_scenarios (array, 4-6 items) — PRIMARY JD DEEP DECODE OUTPUT:
Each item MUST use this format (single string, user's preferred language):
  JD: "<short quote or paraphrase from JD>" → Real need: <what HM actually expects>. Signal: <hidden cue if any>.
Example:
  JD: "comfortable with ambiguity" → Real need: self-directed problem definition without a playbook. Signal: early-stage / high autonomy.
Forbidden: generic duty lists like "Manage product backlog" copied from JD without translation.

problems_to_solve / challenges (array, 3-5 items):
- Hidden signals + real organizational challenges HM is hiring to solve
- Format: "Signal: <cue> — Implication: <what kind of person succeeds>"
- NOT resume comparison; NOT match gaps

project_types (array, 3-5 items):
- Inferred project archetypes from decoded role scope (e.g. "0→1 AI feature launch", "enterprise rollout")
- NOT raw JD responsibility bullets

methods_technologies (array, 3-8 items):
- Methods/tools implied by decoded must-haves (short chips), deduplicated
- Prefer JD-aligned keywords, not exhaustive tool dump

daily_activities, kpis, required_knowledge, collaboration_patterns:
- Optional supporting fields; if present, must reflect DECODED intent, not JD paste

ideal_candidate_profile.hard_skills.must_have / nice_to_have:
- Each item: skill + details with decoded real bar (Layer 1-2)

match_assessment:
- Layer 5 resume cross-check → strengths/gaps with point/amplify/remedy
- Gap remedy prefix: [能补] | [难补] | [不重要]

=== JD DECODE INSIGHTS (job_role_team_analysis.jd_decode_insights) ===
Structured Layer 1-4 output — NO resume comparison here (Layer 5 stays in match_assessment only).

jd_decode_insights:
  real_intent_translations: 4-8 items
    - jd_quote: short JD phrase (verbatim or tight paraphrase)
    - real_need: what HM actually expects
    - marketing_vs_real: "hard" (non-negotiable bar) | "soft" (nice framing)
  hidden_signals: 3-5 items
    - jd_cue: repeated JD cue (e.g. ambiguity, ownership, fast-paced)
    - interpretation: what it reveals about team/HM
    - candidate_implication: who succeeds / what to demonstrate
  level_and_scope:
    - seniority: e.g. Senior IC, Lead, Director-track
    - ic_vs_lead: IC | Lead | Mixed
    - domain_depth: enterprise vs consumer, 0→1 vs scale, etc.
  must_have_summary: 3-5 verifiable must-haves (Layer 1)
  nice_to_have_summary: 3-5 nice-to-haves (Layer 1)

Sync rule: real_intent_translations should align with work_scenarios decode strings; do not duplicate resume evidence.
"""
