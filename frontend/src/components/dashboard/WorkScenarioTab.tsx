import { Briefcase, Target, Search, Layers } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { getUiStrings } from '../../i18n/uiStrings';

interface Props {
  data: any;
}

function categoryBadgeClass(cat: string): string {
  switch (cat) {
    case 'hard':
      return 'bg-red-100 text-red-800';
    case 'soft':
      return 'bg-slate-100 text-slate-700';
    default:
      return 'bg-slate-100 text-slate-700';
  }
}

export default function WorkScenarioTab({ data }: Props) {
  const lang = useAppStore((s) => s.inputs.preferred_lang);
  const ui = getUiStrings(lang);
  const analysis = data?.job_role_team_analysis || {};

  const insights = analysis.jd_decode_insights || {};
  const translations = insights.real_intent_translations || [];
  const hiddenSignals = insights.hidden_signals || [];
  const levelScope = insights.level_and_scope || {};
  const mustHave = insights.must_have_summary || [];
  const niceToHave = insights.nice_to_have_summary || [];

  const hasInsights =
    translations.length > 0 ||
    hiddenSignals.length > 0 ||
    levelScope.seniority ||
    levelScope.ic_vs_lead ||
    levelScope.domain_depth ||
    mustHave.length > 0 ||
    niceToHave.length > 0;

  const hasContent = Boolean(analysis.team_objectives) || hasInsights;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <Briefcase className="w-6 h-6 text-primary-600" />
        <h2 className="text-2xl font-bold text-gray-900">{ui.workScenario.title}</h2>
      </div>

      {/* Team Objectives */}
      {analysis.team_objectives && (
        <div className="card">
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900">{ui.workScenario.teamObjectives}</h3>
          </div>
          <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{analysis.team_objectives}</p>
        </div>
      )}

      {/* JD decode insights */}
      {hasInsights && (
        <div className="card border-l-4 border-indigo-500">
          <div className="flex items-center gap-2 mb-4">
            <Search className="w-5 h-5 text-indigo-600" />
            <h3 className="text-lg font-semibold text-gray-900">{ui.workScenario.jdDecodeInsights}</h3>
          </div>

          {translations.length > 0 && (
            <div className="mb-6">
              <p className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                <Layers className="w-4 h-4" />
                {ui.workScenario.realIntent}
              </p>
              <div className="space-y-3">
                {translations.map((t: any, i: number) => (
                  <div key={i} className="p-4 bg-indigo-50 rounded-lg border border-indigo-100">
                    <div className="flex flex-wrap gap-2 mb-2">
                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${categoryBadgeClass(t.marketing_vs_real)}`}>
                        {t.marketing_vs_real === 'hard' ? ui.workScenario.marketingHard : ui.workScenario.marketingSoft}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-1">
                      <span className="font-medium">{ui.workScenario.jdQuote}:</span> &ldquo;{t.jd_quote}&rdquo;
                    </p>
                    <p className="text-sm text-gray-800">
                      <span className="font-medium">{ui.workScenario.realNeed}:</span> {t.real_need}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {hiddenSignals.length > 0 && (
            <div className="mb-6">
              <p className="text-sm font-medium text-gray-700 mb-3">{ui.workScenario.hiddenSignals}</p>
              <div className="space-y-2">
                {hiddenSignals.map((s: any, i: number) => (
                  <div key={i} className="p-3 bg-slate-50 rounded-lg text-sm border border-slate-200">
                    <p className="font-medium text-gray-800">{ui.workScenario.jdCue}: {s.jd_cue}</p>
                    {s.interpretation && (
                      <p className="text-gray-600 mt-1">{ui.workScenario.interpretation}: {s.interpretation}</p>
                    )}
                    {s.candidate_implication && (
                      <p className="text-gray-700 mt-1">{ui.workScenario.candidateImplication}: {s.candidate_implication}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {(levelScope.seniority || levelScope.ic_vs_lead || levelScope.domain_depth) && (
            <div className="mb-6 p-4 bg-violet-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700 mb-2">{ui.workScenario.levelScope}</p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                {levelScope.seniority && (
                  <div>
                    <span className="text-gray-500">{ui.workScenario.seniority}:</span>{' '}
                    <span className="text-gray-800">{levelScope.seniority}</span>
                  </div>
                )}
                {levelScope.ic_vs_lead && (
                  <div>
                    <span className="text-gray-500">{ui.workScenario.icVsLead}:</span>{' '}
                    <span className="text-gray-800">{levelScope.ic_vs_lead}</span>
                  </div>
                )}
                {levelScope.domain_depth && (
                  <div>
                    <span className="text-gray-500">{ui.workScenario.domainDepth}:</span>{' '}
                    <span className="text-gray-800">{levelScope.domain_depth}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {(mustHave.length > 0 || niceToHave.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              {mustHave.length > 0 && (
                <div>
                  <p className="font-medium text-gray-700 mb-2">{ui.workScenario.mustHaveSummary}</p>
                  <ul className="list-disc pl-5 space-y-1 text-gray-700">
                    {mustHave.map((m: string, i: number) => (
                      <li key={i}>{m}</li>
                    ))}
                  </ul>
                </div>
              )}
              {niceToHave.length > 0 && (
                <div>
                  <p className="font-medium text-gray-700 mb-2">{ui.workScenario.niceToHaveSummary}</p>
                  <ul className="list-disc pl-5 space-y-1 text-gray-700">
                    {niceToHave.map((m: string, i: number) => (
                      <li key={i}>{m}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {!hasContent && (
        <div className="text-center py-12">
          <Briefcase className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">{ui.workScenario.empty}</p>
        </div>
      )}
    </div>
  );
}
