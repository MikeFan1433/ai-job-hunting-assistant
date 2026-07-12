"""Match rubric 0.6/0.2/0.2 + hit tiers (job-description-skill)."""

MATCH_RUBRIC_PROMPT = """
=== MATCH RUBRIC (compute match_percentage as RANGE) ===
Formula: Match = 0.6×MustHaveScore + 0.2×NiceToHaveScore + 0.2×HiddenSignalFit

Per-item hit tiers (each must-have / nice-to-have):
- 1.0 Full hit: direct resume evidence + concrete detail + recent (≤3y primary)
- 0.5 Partial: adjacent domain, claim without numbers, older experience, or contributor not lead
- 0.0 Miss: no resume evidence (resume silent = 0)

Must-have caps on total percentage:
- Any must-have = 0 → max ~75%
- 2+ must-haves = 0 → max ~55%
- Deal-breaker must-have miss (cert, mandatory domain) → ~25-35%

Output match_percentage as RANGE string aligned with rubric, e.g. "68-74%" (NOT "92%" unless evidence supports it).

Dual-track consistency (UI uses 0-5 dimension scores):
- industry/experience/skills 0-5 scores must point the SAME direction as match_percentage.
- Avoid 4.5/5 overall with 90%+ percentage unless must-haves are nearly all full hits.

Must-have matrix → distribute across industry_match, experience_match, skills_match gaps/strengths with explicit JD↔resume mapping in point/amplify/remedy.

gap_improvement_cards (match_assessment):
- Build AFTER dimension gaps — dedupe by gap_name / underlying must-have.
- Map tier from gap remedy prefix: [能补]→能补, [难补]→难补, [不重要]→不重要.
- severity: high if must-have hit=0 or deal-breaker; medium if partial (0.5); low if nice-to-have.
- hm_concern: screening risk in HM's words (30-second resume scan).
- fix_within_4_weeks: actionable within ~4 weeks — bullet rewrite, portfolio piece, cert plan, or honest "难补" mitigation story.
- Prefer 3-6 cards total across all dimensions.
"""
