import { BarChart3, TrendingUp, TrendingDown, AlertCircle, Award, Target, ThumbsUp, ThumbsDown } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { getUiStrings } from '../../i18n/uiStrings';

interface Props {
  data: any;
}

type MatchFitTier = 'full' | 'partial' | 'none';

function deriveMatchFitTier(ma: Record<string, unknown>): MatchFitTier {
  const o = parseFloat(String(ma.overall_match_score ?? '0')) || 0;
  const dimKeys = ['industry_match', 'experience_match', 'skills_match'] as const;
  const dims: number[] = [];
  for (const k of dimKeys) {
    const block = ma[k] as { score?: unknown } | undefined;
    if (block && block.score != null && block.score !== '') {
      const d = parseFloat(String(block.score));
      if (!Number.isNaN(d)) dims.push(d);
    }
  }
  const minDim = dims.length ? Math.min(...dims) : o;
  if (o >= 3.8 && minDim >= 2.0) return 'full';
  if (o < 2.5) return 'none';
  return 'partial';
}

function normalizeBulletList(raw: unknown): string[] {
  if (!raw) return [];
  if (Array.isArray(raw)) {
    return raw.map((x) => String(x).trim()).filter(Boolean);
  }
  if (typeof raw === 'string' && raw.trim()) return [raw.trim()];
  return [];
}

type StrengthRow = { point: string; amplify: string };
type GapRow = { point: string; remedy: string };
type EnrichedGapRow = GapRow & {
  severity?: string;
  tier?: string;
  hm_concern?: string;
  fix_within_4_weeks?: string;
};

function parseStrengthRows(raw: unknown): StrengthRow[] {
  if (!Array.isArray(raw)) return [];
  const out: StrengthRow[] = [];
  for (const x of raw) {
    if (typeof x === 'string' && x.trim()) {
      out.push({ point: x.trim(), amplify: '' });
      continue;
    }
    if (x && typeof x === 'object') {
      const o = x as Record<string, unknown>;
      const point = String(o.point ?? o.text ?? o.summary ?? o.strength ?? '').trim();
      const amplify = String(o.amplify ?? o.leverage ?? '').trim();
      if (point) out.push({ point, amplify });
    }
  }
  return out;
}

function parseGapRows(raw: unknown): GapRow[] {
  if (!Array.isArray(raw)) return [];
  const out: GapRow[] = [];
  for (const x of raw) {
    if (typeof x === 'string' && x.trim()) {
      out.push({ point: x.trim(), remedy: '' });
      continue;
    }
    if (x && typeof x === 'object') {
      const o = x as Record<string, unknown>;
      const point = String(o.point ?? o.text ?? o.summary ?? o.gap ?? '').trim();
      const remedy = String(o.remedy ?? o.address ?? o.how_to_close ?? '').trim();
      if (point) out.push({ point, remedy });
    }
  }
  return out;
}

type GapCard = {
  gap_name: string;
  severity: string;
  tier: string;
  hm_concern: string;
  fix_within_4_weeks: string;
};

type WhyNotRow = { reason: string; hm_probe_response?: string };

function parseGapCards(raw: unknown): GapCard[] {
  if (!Array.isArray(raw)) return [];
  const out: GapCard[] = [];
  for (const x of raw) {
    if (!x || typeof x !== 'object') continue;
    const o = x as Record<string, unknown>;
    const gap_name = String(o.gap_name ?? o.point ?? o.gap ?? '').trim();
    if (!gap_name) continue;
    out.push({
      gap_name,
      severity: String(o.severity ?? 'medium').trim(),
      tier: String(o.tier ?? '').trim(),
      hm_concern: String(o.hm_concern ?? o.concern ?? '').trim(),
      fix_within_4_weeks: String(o.fix_within_4_weeks ?? o.fix ?? o.remedy ?? '').trim(),
    });
  }
  return out;
}

function parseWhyNotRows(raw: unknown): WhyNotRow[] {
  if (!Array.isArray(raw)) return [];
  const out: WhyNotRow[] = [];
  for (const x of raw) {
    if (typeof x === 'string' && x.trim()) {
      out.push({ reason: x.trim() });
      continue;
    }
    if (x && typeof x === 'object') {
      const o = x as Record<string, unknown>;
      const reason = String(o.reason ?? o.text ?? o.point ?? '').trim();
      if (reason) {
        out.push({
          reason,
          hm_probe_response: String(o.hm_probe_response ?? o.hm_probe ?? '').trim() || undefined,
        });
      }
    }
  }
  return out;
}

function severityClass(sev: string): string {
  const s = sev.toLowerCase();
  if (s === 'high') return 'bg-red-100 text-red-800';
  if (s === 'low') return 'bg-slate-100 text-slate-700';
  return 'bg-amber-100 text-amber-900';
}

function gapMatchKey(s: string): string {
  return s.toLowerCase().replace(/\s+/g, ' ').trim();
}

function gapsMatch(a: string, b: string): boolean {
  const ka = gapMatchKey(a);
  const kb = gapMatchKey(b);
  if (!ka || !kb) return false;
  return ka === kb || ka.includes(kb) || kb.includes(ka);
}

function enrichGapRow(row: GapRow, card?: GapCard): EnrichedGapRow {
  if (!card) return { ...row };
  return {
    point: row.point,
    remedy: row.remedy || card.fix_within_4_weeks,
    severity: card.severity || undefined,
    tier: card.tier || undefined,
    hm_concern: card.hm_concern || undefined,
    fix_within_4_weeks: card.fix_within_4_weeks || undefined,
  };
}

function cardToGapRow(card: GapCard): EnrichedGapRow {
  return {
    point: card.gap_name,
    remedy: card.fix_within_4_weeks,
    severity: card.severity || undefined,
    tier: card.tier || undefined,
    hm_concern: card.hm_concern || undefined,
    fix_within_4_weeks: card.fix_within_4_weeks || undefined,
  };
}

function mergeGapCardsIntoDimensions(
  dimGaps: { industry: GapRow[]; experience: GapRow[]; skills: GapRow[] },
  gapCards: GapCard[],
  scores: { industry: number; experience: number; skills: number },
): { industry: EnrichedGapRow[]; experience: EnrichedGapRow[]; skills: EnrichedGapRow[] } {
  const usedCardIdx = new Set<number>();
  const dimKeys = ['industry', 'experience', 'skills'] as const;

  const enrichList = (rows: GapRow[]): EnrichedGapRow[] =>
    rows.map((row) => {
      const cardIdx = gapCards.findIndex(
        (c, i) => !usedCardIdx.has(i) && gapsMatch(row.point, c.gap_name),
      );
      if (cardIdx >= 0) {
        usedCardIdx.add(cardIdx);
        return enrichGapRow(row, gapCards[cardIdx]);
      }
      return { ...row };
    });

  const result = {
    industry: enrichList(dimGaps.industry),
    experience: enrichList(dimGaps.experience),
    skills: enrichList(dimGaps.skills),
  };

  const orphanCards = gapCards.filter((_, i) => !usedCardIdx.has(i));
  for (const card of orphanCards) {
    let targetDim: (typeof dimKeys)[number] | null = null;
    for (const dim of dimKeys) {
      if (dimGaps[dim].some((g) => gapsMatch(g.point, card.gap_name))) {
        targetDim = dim;
        break;
      }
    }
    if (!targetDim) {
      targetDim = dimKeys.reduce((a, b) => (scores[a] <= scores[b] ? a : b));
    }
    const alreadyIn = result[targetDim].some((g) => gapsMatch(g.point, card.gap_name));
    if (!alreadyIn) {
      result[targetDim].push(cardToGapRow(card));
    }
  }

  return result;
}

function MatchStrengthRow({ point, amplify }: { point: string; amplify: string }) {
  return (
    <div className="flex items-start gap-2 p-2 bg-green-50 rounded border border-green-200">
      <div className="w-1.5 h-1.5 bg-green-600 rounded-full mt-1.5 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-800 font-medium leading-snug">{point}</p>
        {amplify ? (
          <div className="mt-2 border-l-2 border-green-400/90 pl-2.5">
            <p className="text-sm text-gray-700 leading-relaxed">{amplify}</p>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function MatchGapRow({
  point,
  remedy,
  severity,
  tier,
  hm_concern,
  fix_within_4_weeks,
  ui,
}: EnrichedGapRow & { ui: ReturnType<typeof getUiStrings> }) {
  const displayRemedy = remedy || fix_within_4_weeks || '';
  return (
    <div className="flex items-start gap-2 p-2 bg-orange-50 rounded border border-orange-200">
      <AlertCircle className="w-4 h-4 text-orange-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-800 font-medium leading-snug">{point}</p>
        {(severity || tier) && (
          <div className="flex flex-wrap items-center gap-2 mt-1.5">
            {severity ? (
              <span className={`text-xs px-2 py-0.5 rounded font-medium ${severityClass(severity)}`}>
                {ui.match.gapSeverity}: {severity}
              </span>
            ) : null}
            {tier ? (
              <span className="text-xs px-2 py-0.5 rounded bg-white border border-violet-200 text-violet-900">
                {ui.match.gapTier}: {tier}
              </span>
            ) : null}
          </div>
        )}
        {hm_concern ? (
          <p className="mt-2 text-sm text-gray-700">
            <span className="font-medium">{ui.match.hmConcern}:</span> {hm_concern}
          </p>
        ) : null}
        {displayRemedy ? (
          <div className="mt-2 border-l-2 border-orange-400/90 pl-2.5">
            <p className="text-sm text-gray-700 leading-relaxed">
              {fix_within_4_weeks && remedy && remedy !== fix_within_4_weeks ? (
                <>
                  <span className="font-medium">{ui.match.fixWithin4Weeks}: </span>
                  {fix_within_4_weeks}
                  {remedy ? (
                    <>
                      <br />
                      <span className="font-medium">{ui.match.gapRemedy}: </span>
                      {remedy}
                    </>
                  ) : null}
                </>
              ) : (
                <>
                  {fix_within_4_weeks && !remedy ? (
                    <>
                      <span className="font-medium">{ui.match.fixWithin4Weeks}: </span>
                      {fix_within_4_weeks}
                    </>
                  ) : (
                    displayRemedy
                  )}
                </>
              )}
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function MatchAnalysisTab({ data }: Props) {
  const lang = useAppStore((s) => s.inputs.preferred_lang);
  const ui = getUiStrings(lang);
  const matchAssessment = data?.match_assessment || {};
  const overallScore = parseFloat(matchAssessment.overall_match_score || '0');

  const industryMatch = matchAssessment.industry_match || {};
  const experienceMatch = matchAssessment.experience_match || {};
  const skillsMatch = matchAssessment.skills_match || {};

  const industryScore = parseFloat(industryMatch.score || '0');
  const experienceScore = parseFloat(experienceMatch.score || '0');
  const skillsScore = parseFloat(skillsMatch.score || '0');

  const industryStrengths = parseStrengthRows(industryMatch.strengths);
  const experienceStrengths = parseStrengthRows(experienceMatch.strengths);
  const skillsStrengths = parseStrengthRows(skillsMatch.strengths);

  const gapCards = parseGapCards(matchAssessment.gap_improvement_cards);
  const mergedGaps = mergeGapCardsIntoDimensions(
    {
      industry: parseGapRows(industryMatch.gaps),
      experience: parseGapRows(experienceMatch.gaps),
      skills: parseGapRows(skillsMatch.gaps),
    },
    gapCards,
    { industry: industryScore, experience: experienceScore, skills: skillsScore },
  );
  const industryGaps = mergedGaps.industry;
  const experienceGaps = mergedGaps.experience;
  const skillsGaps = mergedGaps.skills;

  const rawTier = matchAssessment.match_fit_tier;
  const tier: MatchFitTier =
    rawTier === 'full' || rawTier === 'partial' || rawTier === 'none'
      ? rawTier
      : deriveMatchFitTier(matchAssessment as Record<string, unknown>);

  const tierLabel =
    tier === 'full' ? ui.match.tierFull : tier === 'partial' ? ui.match.tierPartial : ui.match.tierNone;

  const tierPillClass =
    tier === 'full'
      ? 'bg-green-100 text-green-900 border-green-200'
      : tier === 'partial'
        ? 'bg-amber-50 text-amber-950 border-amber-200'
        : 'bg-red-50 text-red-900 border-red-200';

  const ad = matchAssessment.application_decision;
  const oneLine =
    ad && typeof ad === 'object' && typeof (ad as { one_line_summary?: string }).one_line_summary === 'string'
      ? (ad as { one_line_summary: string }).one_line_summary.trim()
      : '';

  const whyApply = normalizeBulletList(matchAssessment.why_apply);
  const whyNotApply = parseWhyNotRows(matchAssessment.why_not_apply);

  const getScoreColor = (score: number) => {
    if (score >= 4) return 'text-green-600';
    if (score >= 3) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreGradient = (score: number) => {
    if (score >= 4) return 'from-green-400 to-green-600';
    if (score >= 3) return 'from-yellow-400 to-yellow-600';
    return 'from-red-400 to-red-600';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <BarChart3 className="w-6 h-6 text-primary-600" />
        <h2 className="text-2xl font-bold text-gray-900">{ui.match.title}</h2>
      </div>

      {/* Overall Score */}
      <div className="bg-gradient-to-r from-primary-50 via-blue-50 to-indigo-50 rounded-xl p-8 border border-primary-200 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">{ui.match.overallScoreHeading}</h3>
          </div>
          <div className={`text-5xl font-bold ${getScoreColor(overallScore)}`}>
            {overallScore.toFixed(1)}
            <span className="text-2xl text-gray-500">/ 5.0</span>
          </div>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-6 mb-4">
          <div
            className={`h-6 rounded-full transition-all bg-gradient-to-r ${getScoreGradient(overallScore)}`}
            style={{ width: `${(overallScore / 5) * 100}%` }}
          />
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-start sm:gap-3 mb-1">
          <span
            className={`inline-flex items-center w-fit px-4 py-1.5 rounded-full text-sm font-semibold border shrink-0 ${tierPillClass}`}
          >
            {tierLabel}
          </span>
        </div>
        {(oneLine || matchAssessment.overall_summary) && (
          <div className="mt-4 p-4 sm:p-5 bg-white rounded-lg border border-gray-100 shadow-sm space-y-4">
            {oneLine ? <p className="text-sm text-gray-800 leading-relaxed">{oneLine}</p> : null}
            {matchAssessment.overall_summary ? (
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{matchAssessment.overall_summary}</p>
            ) : null}
          </div>
        )}
      </div>

      {/* Why apply / Why not apply */}
      {(whyApply.length > 0 || whyNotApply.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {whyApply.length > 0 && (
            <div className="rounded-xl border border-green-200 bg-white shadow-sm overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 bg-green-50 border-l-4 border-green-500">
                <ThumbsUp className="w-4 h-4 text-green-700 shrink-0" />
                <h3 className="text-sm font-semibold text-gray-900">{ui.match.whyApply}</h3>
              </div>
              <ul className="px-4 py-4 space-y-2 text-sm text-gray-800 list-disc pl-8">
                {whyApply.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </div>
          )}
          {whyNotApply.length > 0 && (
            <div className="rounded-xl border border-orange-200 bg-white shadow-sm overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 bg-orange-50 border-l-4 border-orange-500">
                <ThumbsDown className="w-4 h-4 text-orange-700 shrink-0" />
                <h3 className="text-sm font-semibold text-gray-900">{ui.match.whyNotApply}</h3>
              </div>
              <div className="px-4 py-4 space-y-3">
                {whyNotApply.map((row, i) => (
                  <div key={i} className="text-sm">
                    <p className="text-gray-800">• {row.reason}</p>
                    {row.hm_probe_response && (
                      <p className="mt-1 ml-4 text-gray-600 border-l-2 border-orange-300 pl-2">
                        <span className="font-medium">{ui.match.hmProbeResponse}:</span> {row.hm_probe_response}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Detailed Match Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Industry Match */}
        <div className="card border-l-4 border-blue-500">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-gray-700">Industry Match</span>
              <span className="text-xs text-gray-500">(30%)</span>
            </div>
            <span className={`text-2xl font-bold ${getScoreColor(industryScore)}`}>{industryScore.toFixed(1)}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
            <div
              className={`h-3 rounded-full bg-gradient-to-r ${getScoreGradient(industryScore)}`}
              style={{ width: `${(industryScore / 5) * 100}%` }}
            />
          </div>
        </div>

        {/* Experience Match */}
        <div className="card border-l-4 border-purple-500">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Award className="w-5 h-5 text-purple-600" />
              <span className="text-sm font-medium text-gray-700">Experience Match</span>
              <span className="text-xs text-gray-500">(40%)</span>
            </div>
            <span className={`text-2xl font-bold ${getScoreColor(experienceScore)}`}>
              {experienceScore.toFixed(1)}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
            <div
              className={`h-3 rounded-full bg-gradient-to-r ${getScoreGradient(experienceScore)}`}
              style={{ width: `${(experienceScore / 5) * 100}%` }}
            />
          </div>
        </div>

        {/* Skills Match */}
        <div className="card border-l-4 border-green-500">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-green-600" />
              <span className="text-sm font-medium text-gray-700">Skills Match</span>
              <span className="text-xs text-gray-500">(30%)</span>
            </div>
            <span className={`text-2xl font-bold ${getScoreColor(skillsScore)}`}>{skillsScore.toFixed(1)}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
            <div
              className={`h-3 rounded-full bg-gradient-to-r ${getScoreGradient(skillsScore)}`}
              style={{ width: `${(skillsScore / 5) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Detailed Match Analysis — Strengths & Gaps */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Industry Match Details */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-blue-600" />
            Industry Match Analysis
          </h3>

          {industryStrengths.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-600" />
                {ui.match.strengthsHeading}
              </h4>
              <div className="space-y-2">
                {industryStrengths.map((row, index) => (
                  <MatchStrengthRow key={index} point={row.point} amplify={row.amplify} />
                ))}
              </div>
            </div>
          )}

          {industryGaps.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-orange-600" />
                {ui.match.gapsHeading}
              </h4>
              <div className="space-y-2">
                {industryGaps.map((row, index) => (
                  <MatchGapRow key={index} {...row} ui={ui} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Experience Match Details */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Award className="w-5 h-5 text-purple-600" />
            Experience Match Analysis
          </h3>

          {experienceStrengths.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-600" />
                {ui.match.strengthsHeading}
              </h4>
              <div className="space-y-2">
                {experienceStrengths.map((row, index) => (
                  <MatchStrengthRow key={index} point={row.point} amplify={row.amplify} />
                ))}
              </div>
            </div>
          )}

          {experienceGaps.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-orange-600" />
                {ui.match.gapsHeading}
              </h4>
              <div className="space-y-2">
                {experienceGaps.map((row, index) => (
                  <MatchGapRow key={index} {...row} ui={ui} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Skills Match Details */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-green-600" />
          Skills Match Analysis
        </h3>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {skillsStrengths.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-600" />
                {ui.match.strengthsHeading}
              </h4>
              <div className="space-y-2">
                {skillsStrengths.map((row, index) => (
                  <MatchStrengthRow key={index} point={row.point} amplify={row.amplify} />
                ))}
              </div>
            </div>
          )}

          {skillsGaps.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-orange-600" />
                {ui.match.gapsHeading}
              </h4>
              <div className="space-y-2">
                {skillsGaps.map((row, index) => (
                  <MatchGapRow key={index} {...row} ui={ui} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
