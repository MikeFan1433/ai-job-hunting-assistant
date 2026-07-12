import { useState } from 'react';
import { MessageSquare, User, FolderOpen, Briefcase, ChevronDown, ChevronUp, Loader2, FileEdit, Download } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { getUiStrings } from '../../i18n/uiStrings';
import { resumeAPI } from '../../services/api';
import { buildInterviewPrepFullExportText } from '../../utils/interviewPrepFullText';

interface Props {
  data: any;
  preparingInterview?: boolean;
  confirmedModifications?: boolean;
}

function normalizeInterviewData(raw: unknown): Record<string, unknown> {
  if (!raw || typeof raw !== 'object') return {};
  const d = { ...(raw as Record<string, unknown>) };
  const keyMap: Record<string, string> = {
    behavioral_interview: 'theme_1_behavioral_interview',
    project_deep_dive: 'theme_2_project_deep_dive',
    business_domain: 'theme_3_business_domain',
  };
  for (const [newK, oldK] of Object.entries(keyMap)) {
    const block = d[newK];
    if (block && typeof block === 'object' && !d[oldK]) {
      d[oldK] = block;
    }
  }
  const t1 = (d.theme_1_behavioral_interview as Record<string, unknown>) || {};
  if (Array.isArray(t1.top_behavioral_questions) && !t1.top_10_behavioral_questions) {
    t1.top_10_behavioral_questions = t1.top_behavioral_questions;
  }
  d.theme_1_behavioral_interview = t1;
  return d;
}

function hasInterviewContent(raw: unknown): boolean {
  if (!raw || typeof raw !== 'object') return false;
  const src = raw as Record<string, unknown>;
  if (src.error || src.skipped) return true;
  const d = normalizeInterviewData(raw);
  const behavioral = (d.theme_1_behavioral_interview as Record<string, unknown>) || {};
  const projectDeepDive = (d.theme_2_project_deep_dive as Record<string, unknown>) || {};
  const businessDomain = (d.theme_3_business_domain as Record<string, unknown>) || {};
  const summary = (d.preparation_summary as Record<string, unknown>) || {};

  const selfIntro = (behavioral.self_introduction as Record<string, unknown>) || {};
  if (String(selfIntro.full_text || '').trim() || String(selfIntro.paragraph_1 || '').trim()) return true;

  const storytelling = (behavioral.storytelling_example as Record<string, unknown>) || {};
  if (String(storytelling.full_storytelling_answer || '').trim() || String(storytelling.hook || '').trim()) {
    return true;
  }

  if (Array.isArray(behavioral.top_10_behavioral_questions) && behavioral.top_10_behavioral_questions.length > 0) {
    return true;
  }
  const predicted = summary.predicted_interview_questions as unknown;
  if (Array.isArray(predicted) && predicted.length > 0) {
    return true;
  }
  if (Array.isArray(projectDeepDive.selected_projects) && projectDeepDive.selected_projects.length > 0) {
    return true;
  }
  if (Array.isArray(businessDomain.business_questions) && businessDomain.business_questions.length > 0) {
    return true;
  }
  return false;
}

export default function InterviewPrepTab({ data, preparingInterview, confirmedModifications }: Props) {
  const lang = useAppStore((s) => s.inputs.preferred_lang);
  const ui = getUiStrings(lang);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [fullPdfBusy, setFullPdfBusy] = useState(false);

  const normalizedData = normalizeInterviewData(data);
  const hasContent = hasInterviewContent(data);

  // #region agent log
  fetch('http://127.0.0.1:7589/ingest/6c0eeebb-9460-4871-89ae-8e5257503ace',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'e8b8c3'},body:JSON.stringify({sessionId:'e8b8c3',location:'InterviewPrepTab.tsx:render',message:'tab render state',data:{preparingInterview:!!preparingInterview,confirmedModifications:!!confirmedModifications,hasContent,showLoadingBranch:!!(preparingInterview||(confirmedModifications&&!hasContent)),dataKeys:data&&typeof data==='object'?Object.keys(data):[]},timestamp:Date.now(),hypothesisId:'H2'})}).catch(()=>{});
  // #endregion

  // State 1: Error or skipped
  if (data?.error || data?.skipped) {
    return (
      <div className="text-center py-12 text-gray-500">
        <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>{ui.interview.unavailable}</p>
        {data?.error && <p className="text-sm text-red-500 mt-2">{data.error}</p>}
      </div>
    );
  }

  // State 2: Generating — show loading ONLY while prepare is in flight
  if (preparingInterview) {
    return (
      <div className="text-center py-16">
        <Loader2 className="w-16 h-16 mx-auto mb-4 text-primary-500 animate-spin" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">{ui.interview.loadingTitle}</h3>
        <p className="text-sm text-gray-500">{ui.interview.loadingSub}</p>
      </div>
    );
  }

  // State 3: Before confirmation — guide user to complete resume review first
  if (!confirmedModifications && !hasContent) {
    return (
      <div className="text-center py-16">
        <FileEdit className="w-16 h-16 mx-auto mb-4 text-gray-300" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">{ui.interview.gateTitle}</h3>
        <p className="text-sm text-gray-500 max-w-md mx-auto">
          {ui.interview.gateBody}
        </p>
      </div>
    );
  }

  // State 4: Confirmed / finished prepare but no renderable content
  if (!hasContent) {
    return (
      <div className="text-center py-12 text-gray-500">
        <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>{ui.interview.unavailable}</p>
      </div>
    );
  }

  const toggle = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const downloadFullPrepPdf = async () => {
    const text = buildInterviewPrepFullExportText(normalizedData, ui);
    if (!text.trim()) {
      alert(ui.interview.unavailable);
      return;
    }
    setFullPdfBusy(true);
    try {
      await resumeAPI.exportInterviewPrepFullPdf(text, 'Interview_Prep_Full');
    } catch (e: any) {
      alert(`${ui.dashboard.exportErr} ${e?.message || e}`);
    } finally {
      setFullPdfBusy(false);
    }
  };

  const fullPrepPdfButton = (
    <button
      type="button"
      disabled={fullPdfBusy}
      onClick={downloadFullPrepPdf}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border border-purple-200 bg-white text-purple-800 hover:bg-purple-50 disabled:opacity-60 disabled:cursor-wait shrink-0"
    >
      {fullPdfBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
      {fullPdfBusy ? ui.interview.exportFullPdfBusy : ui.interview.exportFullPdf}
    </button>
  );

  const prep = normalizedData as any;
  const behavioral = prep.theme_1_behavioral_interview || {};
  const projectDeepDive = prep.theme_2_project_deep_dive || {};
  const businessDomain = prep.theme_3_business_domain || {};
  const summary = prep.preparation_summary || {};

  const selfIntro = behavioral.self_introduction || {};
  const storytelling = behavioral.storytelling_example || {};
  const predictedTop10 = summary.predicted_interview_questions || [];
  const projects = projectDeepDive.selected_projects || [];
  const businessQs = businessDomain.business_questions || [];

  const categoryLabel = (cat: string) => {
    const map: Record<string, string> = {
      Behavior: ui.interview.categoryBehavior,
      Domain: ui.interview.categoryDomain,
      Craft: ui.interview.categoryCraft,
      Company: ui.interview.categoryCompany,
    };
    return map[cat] || cat;
  };

  const categoryBadge = (cat: string) => {
    switch (cat) {
      case 'Behavior':
        return 'bg-indigo-100 text-indigo-900';
      case 'Domain':
        return 'bg-blue-100 text-blue-900';
      case 'Craft':
        return 'bg-emerald-100 text-emerald-900';
      case 'Company':
        return 'bg-purple-100 text-purple-900';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const hasSelfIntroBlock = Boolean(selfIntro.full_text || selfIntro.paragraph_1);

  return (
    <div className="space-y-8">
      {!hasSelfIntroBlock && <div className="flex justify-end">{fullPrepPdfButton}</div>}
      {/* Self Introduction */}
      {(selfIntro.full_text || selfIntro.paragraph_1) && (
        <section>
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <User className="w-5 h-5 text-purple-600" />
              {ui.interview.selfIntro}
            </h3>
            {fullPrepPdfButton}
          </div>
          <div className="card bg-purple-50 border-purple-200">
            <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">
              {selfIntro.full_text || [selfIntro.paragraph_1, selfIntro.paragraph_2, selfIntro.paragraph_3].filter(Boolean).join('\n\n')}
            </p>
            {selfIntro.key_highlights?.length > 0 && (
              <div className="mt-4 pt-3 border-t border-purple-200">
                <p className="text-sm font-medium text-gray-700 mb-2">{ui.interview.highlights}</p>
                <ul className="space-y-1">
                  {selfIntro.key_highlights.map((h: string, i: number) => (
                    <li key={i} className="text-sm text-gray-600">• {h}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Storytelling Example */}
      {(storytelling.full_storytelling_answer || storytelling.hook) && (
        <section>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-blue-600" />
            {ui.interview.storyTitle}
            {(storytelling.project_name || storytelling.selected_project?.project_name) && (
              <span className="text-sm font-normal text-gray-500">
                — {storytelling.project_name || storytelling.selected_project?.project_name}
              </span>
            )}
          </h3>
          <div className="card bg-blue-50 border-blue-200">
            {storytelling.full_storytelling_answer ? (
              <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{storytelling.full_storytelling_answer}</p>
            ) : (
              <div className="space-y-3 text-sm text-gray-700">
                {storytelling.hook && <div><p className="font-semibold text-blue-700 mb-1">{ui.interview.hook}</p><p>{storytelling.hook}</p></div>}
                {storytelling.emergency && <div><p className="font-semibold text-red-700 mb-1">{ui.interview.emergency}</p><p>{storytelling.emergency}</p></div>}
                {storytelling.approach && <div><p className="font-semibold text-amber-700 mb-1">{ui.interview.approach}</p><p>{storytelling.approach}</p></div>}
                {storytelling.action && <div><p className="font-semibold text-green-700 mb-1">{ui.interview.action}</p><p>{storytelling.action}</p></div>}
                {storytelling.impact && <div><p className="font-semibold text-purple-700 mb-1">{ui.interview.impact}</p><p>{storytelling.impact}</p></div>}
                {storytelling.reflection && <div><p className="font-semibold text-gray-700 mb-1">{ui.interview.reflection}</p><p>{storytelling.reflection}</p></div>}
              </div>
            )}
            {storytelling.jd_skills_demonstrated?.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {storytelling.jd_skills_demonstrated.map((s: string, i: number) => (
                  <span key={i} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">{s}</span>
                ))}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Predicted Top 10 (4 categories) */}
      {predictedTop10.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-violet-600" />
            {ui.interview.predictedTop10}
          </h3>
          <div className="space-y-3">
            {predictedTop10.map((q: any, i: number) => {
              const id = `pred_${i}`;
              const isOpen = expanded.has(id);
              return (
                <div key={i} className="card border-l-4 border-violet-400">
                  <button onClick={() => toggle(id)} className="w-full flex items-start justify-between text-left gap-2">
                    <div className="flex flex-wrap items-start gap-2 justify-between flex-1 min-w-0">
                      <p className="font-medium text-gray-900">
                        Q{i + 1}: {q.question}
                      </p>
                      <div className="flex flex-wrap gap-2 shrink-0">
                        {q.category && (
                          <span className={`text-xs px-2 py-0.5 rounded font-medium ${categoryBadge(q.category)}`}>
                            {categoryLabel(q.category)}
                          </span>
                        )}
                        {q.priority === 'high' && (
                          <span className="text-xs px-2 py-0.5 rounded bg-amber-100 text-amber-900 font-medium">
                            {ui.interview.priorityHigh}
                          </span>
                        )}
                      </div>
                    </div>
                    {isOpen ? <ChevronUp className="w-4 h-4 text-gray-400 mt-1 shrink-0" /> : <ChevronDown className="w-4 h-4 text-gray-400 mt-1 shrink-0" />}
                  </button>
                  {q.why_likely && (
                    <p className="mt-2 text-sm text-gray-600">
                      <span className="font-medium text-gray-700">{ui.interview.whyLikely}:</span> {q.why_likely}
                    </p>
                  )}
                  {isOpen && (
                    <div className="mt-3 pt-3 border-t border-gray-200 space-y-3">
                      {q.answer_framework?.length > 0 && (
                        <div className="bg-green-50 p-3 rounded-lg text-sm">
                          <p className="font-medium text-gray-700 mb-2">{ui.interview.framework}</p>
                          <ol className="space-y-2">
                            {q.answer_framework.map((step: string, j: number) => (
                              <li key={j} className="text-gray-700 flex items-start gap-2">
                                <span className="flex-shrink-0 w-5 h-5 bg-green-600 text-white rounded-full flex items-center justify-center text-xs font-bold mt-0.5">{j + 1}</span>
                                <span>{step}</span>
                              </li>
                            ))}
                          </ol>
                        </div>
                      )}
                      {q.key_points_to_emphasize?.length > 0 && (
                        <div className="text-sm">
                          <p className="font-medium text-gray-700 mb-1">{ui.interview.keyPoints}</p>
                          <ul className="space-y-1">
                            {q.key_points_to_emphasize.map((p: string, j: number) => (
                              <li key={j} className="text-gray-600">• {p}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Project Deep Dive */}
      {projects.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <FolderOpen className="w-5 h-5 text-green-600" />
            {ui.interview.projectTitle(projects.length)}
          </h3>
          <div className="space-y-4">
            {projects.map((proj: any, pi: number) => {
              const pid = `proj_${pi}`;
              const isOpen = expanded.has(pid);
              const overview = proj.project_overview_star || {};
              const scenario = proj.answer_scenario || {};
              const whyJd = String(scenario.why_important_for_jd || '').trim();
              const whenTell = String(scenario.when_to_use_in_interview || '').trim();
              const questions = proj.technical_deep_dive_questions || proj.deep_dive_questions || [];
              const starBlocks = [
                { key: 'situation' as const, label: ui.interview.starSituation },
                { key: 'task' as const, label: ui.interview.starTask },
                { key: 'action' as const, label: ui.interview.starAction },
                { key: 'result' as const, label: ui.interview.starResult },
              ];
              const hasStarBody = starBlocks.some(({ key }) => String(overview[key] || '').trim());
              const legacyOverview = String(
                overview.full_overview_answer || proj.project_overview_answer || ''
              ).trim();
              return (
                <div key={pi} className="card border-l-4 border-green-400">
                  <button onClick={() => toggle(pid)} className="w-full flex items-start justify-between text-left">
                    <div>
                      <span className="font-semibold text-gray-900">{proj.project_name}</span>
                    </div>
                    {isOpen ? <ChevronUp className="w-4 h-4 text-gray-400 mt-1 shrink-0" /> : <ChevronDown className="w-4 h-4 text-gray-400 mt-1 shrink-0" />}
                  </button>
                  {isOpen && (
                    <div className="mt-3 pt-3 border-t border-gray-200 space-y-4">
                      {(whyJd || whenTell) && (
                        <div className="rounded-lg border border-indigo-200 bg-indigo-50/70 p-3 space-y-3">
                          <p className="text-sm font-semibold text-indigo-950">{ui.interview.answerScenarioTitle}</p>
                          {whyJd && (
                            <div>
                              <p className="text-xs font-semibold text-gray-700 mb-1">{ui.interview.whyImportantJd}</p>
                              <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{whyJd}</p>
                            </div>
                          )}
                          {whenTell && (
                            <div>
                              <p className="text-xs font-semibold text-gray-700 mb-1">{ui.interview.whenToTell}</p>
                              <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{whenTell}</p>
                            </div>
                          )}
                        </div>
                      )}
                      {hasStarBody ? (
                        <div className="space-y-3">
                          {starBlocks.map(({ key, label }) => {
                            const text = String(overview[key] || '').trim();
                            if (!text) return null;
                            return (
                              <div key={key} className="rounded-lg border border-green-200 bg-green-50/85 p-3">
                                <p className="text-xs font-bold text-green-900 tracking-wide mb-1.5">{label}</p>
                                <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{text}</p>
                              </div>
                            );
                          })}
                        </div>
                      ) : legacyOverview ? (
                        <div className="bg-amber-50/80 p-3 rounded-lg text-sm border border-amber-200">
                          <p className="font-medium text-amber-950 mb-1">{ui.interview.starSummary}</p>
                          <p className="text-gray-800 whitespace-pre-wrap">{legacyOverview}</p>
                        </div>
                      ) : null}
                      {questions.map((dq: any, qi: number) => {
                        const qid = `proj_${pi}_q_${qi}`;
                        const qOpen = expanded.has(qid);
                        return (
                          <div key={qi} className="bg-gray-50 rounded-lg p-3">
                            <button onClick={() => toggle(qid)} className="w-full flex items-start justify-between text-left">
                              <span className="font-medium text-gray-800 text-sm">Q{qi + 1}: {dq.question}</span>
                              {qOpen ? <ChevronUp className="w-3 h-3 text-gray-400 mt-1 shrink-0" /> : <ChevronDown className="w-3 h-3 text-gray-400 mt-1 shrink-0" />}
                            </button>
                            {qOpen && dq.how_to_answer && (
                              <div className="mt-2 pt-2 border-t border-gray-200 text-sm space-y-2">
                                {dq.why_they_ask_this && <p className="text-gray-500 italic">{dq.why_they_ask_this}</p>}
                                {dq.how_to_answer.structure && (
                                  <div>
                                    <p className="font-medium text-gray-700 mb-1">{ui.interview.answerStructure}</p>
                                    <ol className="list-decimal list-inside space-y-1 text-gray-600">
                                      {(Array.isArray(dq.how_to_answer.structure) ? dq.how_to_answer.structure : [dq.how_to_answer.structure]).map((s: string, si: number) => (
                                        <li key={si}>{s}</li>
                                      ))}
                                    </ol>
                                  </div>
                                )}
                                {dq.how_to_answer.key_points?.length > 0 && (
                                  <div>
                                    <p className="font-medium text-gray-700 mb-1">{ui.interview.points}</p>
                                    <ul className="space-y-1 text-gray-600">
                                      {dq.how_to_answer.key_points.map((p: string, ki: number) => (
                                        <li key={ki}>• {p}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                      {proj.most_important_takeaways?.length > 0 && (
                        <div className="bg-yellow-50 p-3 rounded-lg text-sm">
                          <p className="font-medium text-gray-700 mb-1">{ui.interview.corePoints}</p>
                          <ul className="space-y-1 text-gray-600">
                            {proj.most_important_takeaways.map((t: string, ti: number) => (
                              <li key={ti}>• {t}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Business Domain Questions */}
      {businessQs.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-orange-600" />
            {ui.interview.businessTitle(businessQs.length)}
          </h3>
          <div className="space-y-3">
            {businessQs.map((q: any, i: number) => {
              const id = `biz_${i}`;
              const isOpen = expanded.has(id);
              return (
                <div key={i} className="card border-l-4 border-orange-400">
                  <button onClick={() => toggle(id)} className="w-full flex items-start justify-between text-left">
                    <span className="font-medium text-gray-900">Q{i + 1}: {q.question}</span>
                    {isOpen ? <ChevronUp className="w-4 h-4 text-gray-400 mt-1 shrink-0" /> : <ChevronDown className="w-4 h-4 text-gray-400 mt-1 shrink-0" />}
                  </button>
                  {isOpen && q.how_to_answer && (
                    <div className="mt-3 pt-3 border-t border-gray-200 space-y-2 text-sm">
                      {q.why_they_ask_this && <p className="text-gray-500 italic">{q.why_they_ask_this}</p>}
                      {q.how_to_answer.structure && (
                        <div>
                          <p className="font-medium text-gray-700 mb-1">{ui.interview.answerStructure}</p>
                          <ol className="list-decimal list-inside space-y-1 text-gray-600">
                            {(Array.isArray(q.how_to_answer.structure) ? q.how_to_answer.structure : [q.how_to_answer.structure]).map((s: string, si: number) => (
                              <li key={si}>{s}</li>
                            ))}
                          </ol>
                        </div>
                      )}
                      {q.how_to_answer.key_points?.length > 0 && (
                        <div>
                          <p className="font-medium text-gray-700 mb-1">{ui.interview.points}</p>
                          <ul className="space-y-1 text-gray-600">
                            {q.how_to_answer.key_points.map((p: string, ki: number) => (
                              <li key={ki}>• {p}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

    </div>
  );
}
