"""Organization background + salary reality check (offer-strategy-report §1 / §7)."""

ORG_SALARY_PROMPT = """
=== ORGANIZATION BACKGROUND (job_role_team_analysis.organization_background) ===
Phase 1: JD + LLM knowledge only — NO web search, NO pretending Glassdoor/Levels/Crunchbase access.

company_snapshot: One sentence — founding/scale/business. If unknown: "Inferred from JD: …" or "[需用户补充]".
culture_signals: 3-4 items. Each MUST cite jd_evidence (JD quote or paraphrase). Signals: craft, pace, ownership, mission, etc.
recent_product_moves: 0-3 items for last 12-24 months. Without external data → "[需用户补充]" — NEVER invent funding rounds or acquisitions.
why_care_for_this_candidate: 1-2 sentences — what is special about THIS company+role for THIS candidate context (from resume if provided).
sources: array e.g. ["JD only"], ["JD only", "LLM knowledge"], ["user input"] — be honest.
confidence: high|medium|low — low when mostly inferred; UI will warn.

Iron rules:
- Do NOT fabricate revenue, valuation, headcount, or Glassdoor ratings.
- Do NOT cite specific salary survey sites unless user provided data.
- Mark stale or uncertain facts explicitly.

=== SALARY REALITY CHECK (job_role_team_analysis.salary_reality_check) ===
jd_stated_range: Copy JD compensation text if present; else empty string.
market_range_estimate: Base (+ equity if role implies it) as RANGE with inference basis, e.g. "CAD 120-150k base (inferred: Senior PM, Toronto, enterprise SaaS)".
negotiation_talking_points: 3-5 concrete, role-specific bullets (scope, level, location, niche skills) — not generic "negotiate well".
vs_candidate_context: Relative to candidate's apparent level — upgrade / lateral / downgrade with brief rationale.
disclaimer: REQUIRED — e.g. "非报价，需用户自行核实；非录用承诺。" (adapt to user's preferred language).

Iron rules:
- Always give a RANGE, never a single precise number as fact.
- Must include disclaimer field every time.
- If JD silent and region unknown → wide range + low confidence note inside market_range_estimate.
"""
