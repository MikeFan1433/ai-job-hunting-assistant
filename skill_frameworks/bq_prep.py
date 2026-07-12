"""BQ answer generation rules (bq-skill) — question selection handled by interview_predict."""

BQ_ANSWER_PROMPT = """
=== BEHAVIORAL ANSWER GENERATION (after questions are predicted) ===
For EACH top_behavioral_questions item, still generate full answer support:
- answer_framework: 3-5 steps; EACH step combines STAR structure guidance + specific resume experience (not generic advice)
- key_points_to_emphasize: 2-4 grounded resume facts

STAR / project_overview_star (unchanged):
- situation & task: ONLY facts from final resume / projects
- action & result: use [待你补充具体动作/数字] or [Add specific metric] when resume lacks detail — NEVER fabricate metrics
- Time budget: Action ~50%, Result ~20% of narrative

self_introduction / storytelling_example: unchanged — full interview-ready prose per system brief.
"""

# Backward-compatible alias
BQ_PREP_PROMPT = BQ_ANSWER_PROMPT
