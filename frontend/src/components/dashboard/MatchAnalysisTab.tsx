import { BarChart3, TrendingUp, TrendingDown, AlertCircle, Award, Target, ListTodo } from 'lucide-react';
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

function MatchGapRow({ point, remedy }: { point: string; remedy: string }) {
  return (
    <div className="flex items-start gap-2 p-2 bg-orange-50 rounded border border-orange-200">
      <AlertCircle className="w-4 h-4 text-orange-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-800 font-medium leading-snug">{point}</p>
        {remedy ? (
          <div className="mt-2 border-l-2 border-orange-400/90 pl-2.5">
            <p className="text-sm text-gray-700 leading-relaxed">{remedy}</p>
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
  const industryGaps = parseGapRows(industryMatch.gaps);
  const experienceStrengths = parseStrengthRows(experienceMatch.strengths);
  const experienceGaps = parseGapRows(experienceMatch.gaps);
  const skillsStrengths = parseStrengthRows(skillsMatch.strengths);
  const skillsGaps = parseGapRows(skillsMatch.gaps);

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

  const actionBullets = normalizeBulletList(matchAssessment.action_bullets);

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

  const textareaBox =
    'rounded-lg border border-gray-200 bg-white shadow-inner px-4 py-3 text-sm text-gray-800 leading-relaxed min-h-[7.5rem]';

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

      {/* What to do next (action bullets only; assessment narrative lives in score card above) */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
        {actionBullets.length === 0 ? (
          <div className="px-4 py-6 sm:px-6">
            <p className="text-sm text-gray-600 leading-relaxed">{ui.match.sectionEmptyHint}</p>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2 px-4 py-3 sm:px-5 bg-emerald-50/80 border-l-4 border-emerald-500">
              <ListTodo className="w-4 h-4 text-emerald-700 shrink-0" />
              <h3 className="text-sm font-semibold text-gray-900 tracking-tight">{ui.match.sectionActions}</h3>
            </div>
            <div className="px-4 py-4 sm:px-5 sm:py-5 bg-gray-50/50">
              <div className={textareaBox}>
                <ul className="list-disc pl-5 space-y-2 m-0">
                  {actionBullets.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </>
        )}
        <p className="text-xs text-gray-500 px-4 pb-3 sm:px-5 leading-snug border-t border-gray-100 pt-3 bg-white">
          {ui.match.disclaimerShort}
        </p>
      </div>

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
                  <MatchGapRow key={index} point={row.point} remedy={row.remedy} />
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
                  <MatchGapRow key={index} point={row.point} remedy={row.remedy} />
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
                  <MatchGapRow key={index} point={row.point} remedy={row.remedy} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
