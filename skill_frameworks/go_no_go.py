"""Should I apply + HM probe templates (job-description-skill)."""

GO_NO_GO_PROMPT = """
=== SHOULD I APPLY + HM PROBE ===
application_decision.verdict mapping:
- strong_apply: match_percentage upper bound ≥78% AND no deal-breaker must-have miss
- worth_trying: partial fit, 1-2 fixable gaps, upper 55-77%
- low_priority: several gaps or weak trajectory fit
- not_recommended: deal-breaker miss OR upper bound <45%

why_bullets: legacy combined list — still populate for backward compatibility.
why_apply: REQUIRED 3+ specific, verifiable positives (resume/JD grounded). Distill from why_bullets positives.
why_not_apply: REQUIRED 3+ honest reasons NOT to apply — skill soul. Each item:
  - string: "reason text" OR object { "reason": "…", "hm_probe_response": "optional HM follow-up + answer strategy" }
  - At least one item should include hm_probe_response when a gap is probeable.
gap_improvement_cards: REQUIRED 3-6 aggregated cards (NOT duplicate per-dimension gap rows):
  - gap_name: short label
  - severity: high|medium|low
  - tier: 能补|难补|不重要
  - hm_concern: what HM worries about in screening
  - fix_within_4_weeks: concrete remedial action (resume, story, or skill sprint)
  Aggregate from must-have matrix misses — one card per distinct concern, not three copies of same gap.

action_bullets: 3-6 concrete next steps; MUST include ≥1 HM probe line:
  Format: "HM probe: [likely question about gap X] → [honest answer strategy using resume facts]"
one_line_summary: include realistic interview probability RANGE (e.g. "30-45% phone screen if gaps X addressed").

resume_adjustment_suggestions: prioritize changes that move must-have hits from 0/0.5 → 1.0; rank by priority_rank.
interview_question_preview (inside match_assessment, optional): top 8-10 likely questions tied to must-haves:
  [{ "question": "...", "why_likely": "Must-have: ...", "category": "Behavior|Values|Craft|Level" }]
"""
