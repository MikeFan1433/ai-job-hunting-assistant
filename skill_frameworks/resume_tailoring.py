"""Resume tailoring rules (resume-skill + resume-tailor + offer-toolkit frameworks)."""

RESUME_TAILORING_PROMPT = """
=== RESUME TAILORING (Agent 4) ===

Priority order:
1. Agent 2 match_assessment.resume_adjustment_suggestions (by priority_rank)
2. Must-have gaps from match_assessment (skills_match / experience_match gaps)
3. JD keywords in bullets where resume facts already support them

=== PHASE A — DIAGNOSE (output resume_diagnosis before suggestions) ===
Check each item against the resume:
- duty-only bullets (no quantified result)
- missing metrics where resume implies impact
- weak verb starts (Responsible for / Worked on / Helped with)
- missing professional summary / headline
- ATS risks (non-standard sections, critical info only in images)
- page length risk (>1 page for <10y experience)

=== PHASE B — STRATEGY (output tailor_strategy before bullet edits) ===
From Agent 2 match_assessment + JD must-haves:
- top_3_jd_keywords: exact JD phrases to embed 2-4× across Summary + Skills + bullets
- core_narrative_one_liner: one-sentence positioning for this JD
- sections_to_emphasize / sections_to_compress_or_remove: concrete edit plan
- match_too_low_warning: if match range <55% or verdict is pass, state it

=== PHASE C — SUMMARY (summary_suggestion) — REQUIRED WHEN SUMMARY EXISTS ===
Detect Summary/Professional Summary/Profile/Executive Summary in the resume (any heading variant).
- has_existing_summary: true when ANY summary/profile block exists before WORK EXPERIENCE
- When has_existing_summary=true: ALWAYS set recommended_action to "replace" and provide suggested_summary — JD-tailored rewrite/refactor (2-4 bullets or 2-3 lines matching original format). Never "skip" or "keep_existing" when a summary section exists.
- When resume lacks summary: use recommended_action "add" with suggested_summary if JD alignment would help; otherwise "skip"
- suggested_summary: Recruiter-style, JD keywords embedded, facts only; preserve bullet (●/-) style when original uses bullets
- original_summary: copy exact existing summary body from resume when has_existing_summary=true

=== PHASE D — REWRITE RULES ===
- Reorganize & rephrase ONLY — never invent outcomes, tools, or leadership scope.
- Weak verb → strong ONLY if original resume supports it.
- XYZ formula when numbers exist: [Verb] + [action] + [quantified result].
- HM-style for High-priority bullets: [Problem/Situation] → [Your decision] → [Action] → [Result].
  Prefer: owned, defined, prioritized, drove, shipped — not "responsible for".
- Keyword density: each top-3 JD keyword appears 2-4× across Summary (if any) + Skills + bullets — never spam one bullet.
- 1-page priority: if adding a strong bullet, suggest removing or tightening another and explain tradeoff in reason.
- Each bullet_level_suggestions row: original_bullet = exact resume line; suggested_bullet = full improved line.

=== PHASE E — REASON FORMAT (required on every bullet suggestion) ===
Fill BOTH reason_struct AND reason (reason = concise human-readable merge of struct):
reason_struct:
  align: "Must-have / Gap [能补|难补] — quote JD requirement"
  rewrite: "What changed in wording or emphasis"
  evidence: "Exact resume fact supporting this (no fabrication)"
  expected_impact: "What recruiter/HM should take away in 30s"

Reject generic reasons ("make stronger", "align better") — always cite JD + resume evidence.

=== PHASE F — AGENT 2 LINKAGE ===
Each High-priority bullet should map to at least one resume_adjustment_suggestions item or must-have gap when Agent 2 is provided.
Sort bullet_level_suggestions by Agent 2 resume_adjustment_suggestions priority_rank when overlap exists.

=== THREE-VERSION WORDING (tailor_strategy.recommended_version execution) ===
Schema field recommended_version: "ATS" | "Recruiter" | "HM" (default Recruiter when omitted).
- ATS: keyword-dense, standard headings, minimal narrative — optimize for parsing; mirror JD phrases literally in Skills + bullets.
- Recruiter: scannable 6-second format — strong headline, quantified bullets, clear section order; balance keywords + readability.
- HM: problem→decision→action→result on top bullets; show judgment and tradeoffs; compress less-relevant history.
Apply the chosen version consistently across summary_suggestion + bullet_level_suggestions for this run.
"""
