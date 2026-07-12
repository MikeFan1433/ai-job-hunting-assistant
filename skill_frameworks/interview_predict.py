"""Behavioral interview question prediction (job-description-skill interview-predictor Category 1)."""

INTERVIEW_PREDICT_BEHAVIOR_PROMPT = """
=== BEHAVIORAL QUESTION PREDICTION (interview-predictor · Category 1) ===
Generate EXACTLY 10 behavioral questions in top_behavioral_questions — ranked by (probability × candidate gap risk).

Prerequisites (use Agent 2 context + JD decode mentally before drafting questions):
- Must-haves from ideal_candidate_profile.hard_skills.must_have
- Hidden signals from job_role_team_analysis.problems_to_solve / team_objectives tail
- Gaps from match_assessment (industry/experience/skills) — prioritize questions that probe weak areas
- Agent 2 interview_question_preview seeds (reuse/adapt when relevant; do not duplicate verbatim)

Iron rules:
- Do NOT claim access to company interview question banks. Frame as "JD inference + industry norm".
- Every question MUST map to a specific JD must-have OR hidden signal — cite in source_jd_anchor.
- Do NOT generate Product/Domain/Craft/Company-specific questions in top_behavioral_questions (Behavior only).

Hidden signal → question templates (adapt wording to JD; do not copy blindly):
| JD cue | Example question angle |
| ambiguity / unstructured / no playbook | Decision with incomplete information |
| ownership / accountable / drive | Ownership outside formal role |
| influence / partner / align / cross-functional | Influence without authority; stakeholder friction |
| fast-paced / ship / move quickly | Prioritization under time pressure |
| craft / high bar / pixel-perfect | Quality vs speed tradeoff |
| end-to-end / 0→1 / from concept to ship | Project owned from idea to launch |
| stakeholder management | Cross-functional conflict resolution |
| data-driven / metrics / KPI | Metric-defined success; changing decisions with data |

Per-question output (top_behavioral_questions[]):
- question: full interview-ready wording (English or user's preferred_lang)
- source_jd_anchor: "Hidden Signal: …" OR "Must-have: …" with JD quote/paraphrase
- competency_tested: e.g. "Dealing with Ambiguity", "Ownership", "Influence without authority"
- priority_rank: 1 (highest) … 10 (lowest) — sort list ascending by priority_rank
- priority: high|medium — top 5 should mostly be high
- why_they_ask_this: "[Behavior] …" — why HM asks this for THIS JD + THIS candidate gap/strength
- answer_framework: 3-5 steps with resume-grounded content (see BQ answer rules below)
- key_points_to_emphasize: 2-4 resume facts to stress

Priority ranking (Step 3 from skill):
- Score each question: P(probe this area) × P(candidate weak on this area from gaps)
- Top 5 = highest combined risk; assign priority_rank 1-5 with priority "high"
- Questions 6-10 = medium priority unless gap is severe

preparation_summary additions:
- top_5_must_practice: array of 5 strings "Q{n}: {short question} — {one-line why critical}"
- additional_question_bank: 8-14 EXTRA behavioral question strings (Q11+) for export only — NOT full objects
- highest_risk_gaps_to_prepare: align with Agent 2 match_assessment gaps
"""

INTERVIEW_PREDICT_TOP10_PROMPT = """
=== PREDICTED INTERVIEW QUESTIONS TOP 10 (preparation_summary.predicted_interview_questions) ===
Generate EXACTLY 10 questions across four categories for the Dashboard "Top 10" block.
Categories (interview-predictor): Behavior | Domain | Craft | Company

Distribution guideline (flex ±1 based on JD):
- Behavior: 3-4 (overlap allowed with top_behavioral_questions — same wording OK)
- Domain: 2-3 (business/industry/product domain depth)
- Craft: 2-3 (technical craft, execution, tools, quality bar)
- Company: 1-2 (mission, culture, why this company/team)

Prerequisites:
- Agent 2 jd_decode_insights.hidden_signals + must_have_summary
- Agent 2 match_assessment gaps + interview_question_preview seeds
- JD text + final resume

Per-item schema (predicted_interview_questions[]):
- question: interview-ready wording
- category: Behavior|Domain|Craft|Company
- why_likely: cite Must-have / Hidden signal / Gap — specific JD anchor
- priority: high|medium — top 5 mostly high
- answer_framework: 3-5 steps with resume-grounded content (see BQ answer rules) — REQUIRED for every Top 10 question
- key_points_to_emphasize: 2-4 resume facts to stress in the answer

Rules:
- Top 10 ONLY in predicted_interview_questions (sorted: high priority first, then Behavior→Domain→Craft→Company).
- Generate answer_framework for EACH predicted question (not only Behavior). User sees frameworks under Predicted Top 10 in the product UI.
- top_behavioral_questions may be omitted or left empty — all behavioral prep lives in predicted_interview_questions.
- Questions 11-20 → additional_question_bank (strings) alongside behavioral Q11+.
- Do NOT claim access to company question banks.
- Every question must be plausible for THIS JD — no generic filler.
"""
