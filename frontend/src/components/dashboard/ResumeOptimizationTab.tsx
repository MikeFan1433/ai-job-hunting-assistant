import { useState, useMemo } from 'react';
import { CheckCircle, ChevronDown, ChevronUp, Check, X, FileText, Target, Lightbulb, Star, TrendingUp, Edit3, Loader2, Sparkles } from 'lucide-react';
import { resumeAPI } from '../../services/api';
import { useAppStore } from '../../store/useAppStore';
import { getUiStrings } from '../../i18n/uiStrings';

type JdTriLevel = 'High' | 'Medium' | 'Low';

function triLevelFromApi(v: unknown): JdTriLevel {
  return v === 'High' || v === 'Medium' || v === 'Low' ? v : 'Medium';
}

function ExperienceJdImportanceBadge({
  level,
  ui,
}: {
  level: JdTriLevel;
  ui: ReturnType<typeof getUiStrings>;
}) {
  const label =
    level === 'High' ? ui.resume.jdTierHigh : level === 'Medium' ? ui.resume.jdTierMed : ui.resume.jdTierLow;
  const cls =
    level === 'High'
      ? 'bg-emerald-100 text-emerald-900 border-emerald-200'
      : level === 'Medium'
        ? 'bg-amber-50 text-amber-950 border-amber-200'
        : 'bg-slate-100 text-slate-700 border-slate-200';
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border ${cls}`}
    >
      <span className="opacity-80 font-normal">{ui.resume.expJdImportance}</span>
      <span>{label}</span>
    </span>
  );
}

const SUMMARY_ITEM_ID = 'summary_suggestion';

function ReasonStructDisplay({
  suggestion,
  ui,
}: {
  suggestion: any;
  ui: ReturnType<typeof getUiStrings>;
}) {
  const rs = suggestion?.reason_struct;
  const hasStruct =
    rs &&
    typeof rs === 'object' &&
    (rs.align || rs.rewrite || rs.evidence || rs.expected_impact);
  if (hasStruct) {
    const rows: { key: keyof typeof rs; label: string }[] = [
      { key: 'align', label: ui.resume.reasonAlign },
      { key: 'rewrite', label: ui.resume.reasonRewrite },
      { key: 'evidence', label: ui.resume.reasonEvidence },
      { key: 'expected_impact', label: ui.resume.reasonImpact },
    ];
    return (
      <div className="px-3 py-2.5 bg-amber-50/60 space-y-2">
        {rows.map(({ key, label }) => {
          const val = typeof rs[key] === 'string' ? rs[key].trim() : '';
          if (!val) return null;
          return (
            <div key={String(key)}>
              <p className="text-xs font-semibold text-amber-950">{label}</p>
              <p className="text-sm text-gray-800 leading-relaxed mt-0.5">{val}</p>
            </div>
          );
        })}
      </div>
    );
  }
  if (suggestion?.reason && String(suggestion.reason).trim()) {
    return (
      <div className="px-3 py-2.5 bg-amber-50/60">
        <p className="text-sm text-gray-800 leading-relaxed">{suggestion.reason}</p>
      </div>
    );
  }
  return null;
}

interface Props {
  workflowId: string | null;
  data: any;
  onFeedbackUpdate: () => void;
  feedbackStatus: any;
  onConfirmModifications?: (feedbackMap: Record<string, { action: string; text?: string }>) => void;
  generatingResume?: boolean;
  preparingInterview?: boolean;
  generatedResume?: string | null;
  confirmedModifications?: boolean;
  userFeedback: Record<string, string>;
  setUserFeedback: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  editedTexts: Record<string, string>;
  setEditedTexts: React.Dispatch<React.SetStateAction<Record<string, string>>>;
}

export default function ResumeOptimizationTab({
  workflowId, data, onFeedbackUpdate,
  onConfirmModifications, generatingResume, preparingInterview, generatedResume,
  confirmedModifications,
  userFeedback, setUserFeedback,
  editedTexts, setEditedTexts,
}: Props) {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [editingItem, setEditingItem] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState('');
  const [regeneratedSuggestions, setRegeneratedSuggestions] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState<string | null>(null);
  const [modifyModal, setModifyModal] = useState<{ open: boolean; itemId: string | null; instruction: string }>({
    open: false,
    itemId: null,
    instruction: '',
  });

  const lang = useAppStore((s) => s.inputs.preferred_lang);
  const ui = getUiStrings(lang);

  const toggleExpand = (itemId: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  const handleFeedback = async (
    feedbackType: string,
    itemId: string,
    feedback: 'accept' | 'reject' | 'further_modify',
    modifiedText?: string
  ) => {
    setSubmitting(itemId);
    try {
      await resumeAPI.submitFeedback({
        feedback_type: feedbackType,
        item_id: itemId,
        feedback,
        modified_text: modifiedText,
        workflow_id: workflowId || undefined,
      });
      setUserFeedback((prev) => ({ ...prev, [itemId]: feedback }));
      onFeedbackUpdate();
    } catch (error: any) {
      alert(`Error submitting feedback: ${error.message}`);
    } finally {
      setSubmitting(null);
    }
  };

  const openModifyModal = (itemId: string) => {
    setModifyModal({ open: true, itemId, instruction: '' });
  };

  const submitRegenerate = async () => {
    if (!modifyModal.itemId || !workflowId || !modifyModal.instruction.trim()) return;
    setSubmitting(modifyModal.itemId);
    try {
      const result = await resumeAPI.regenerateSuggestion({
        workflow_id: workflowId,
        feedback_type: 'format_adjustment',
        item_id: modifyModal.itemId,
        user_instruction: modifyModal.instruction.trim(),
      });
      setRegeneratedSuggestions((prev) => ({ ...prev, [modifyModal.itemId!]: result.suggested_text }));
      setUserFeedback((prev) => {
        const next = { ...prev };
        delete next[modifyModal.itemId!];
        return next;
      });
      setModifyModal({ open: false, itemId: null, instruction: '' });
      onFeedbackUpdate();
    } catch (error: any) {
      alert(`${ui.resume.regenerateFailed} ${error.message}`);
    } finally {
      setSubmitting(null);
    }
  };

  const experienceOptimizations = data?.experience_optimizations || [];
  const formatAdjustments = data?.format_content_adjustments || [];
  const bulletSuggestions = data?.bullet_level_suggestions || [];
  const tailorStrategy = data?.tailor_strategy;
  const resumeDiagnosis = data?.resume_diagnosis;
  const summarySuggestion = data?.summary_suggestion;
  const showSummarySuggestion = useMemo(() => {
    const action = (summarySuggestion?.recommended_action || 'skip').toLowerCase();
    return action === 'add' || action === 'replace';
  }, [summarySuggestion]);
  const filteredBulletSuggestions = useMemo(() => {
    return bulletSuggestions
      .map((group: any, gi: number) => ({
        ...group,
        // Keep original backend indices so bls_{gi}_{si} matches resume_optimization_service
        suggestions: (group.suggestions || [])
          .map((s: any, si: number) => ({ ...s, _gi: gi, _si: si }))
          .filter((s: any) => {
            const suggested = s.suggested_bullet;
            if (!suggested || suggested === 'N/A' || suggested.trim() === '') return false;
            return true;
          }),
      }))
      .filter((group: any) => group.suggestions.length > 0);
  }, [bulletSuggestions]);

  const bulletSuggestionCount = useMemo(
    () =>
      filteredBulletSuggestions.reduce((n: number, g: any) => n + (g.suggestions?.length || 0), 0),
    [filteredBulletSuggestions]
  );

  const totalRecommendations =
    experienceOptimizations.length + formatAdjustments.length + bulletSuggestionCount;

  const allBulletItemIds = useMemo(() => {
    const ids: string[] = [];
    filteredBulletSuggestions.forEach((group: any) => {
      (group.suggestions || []).forEach((s: any) => {
        ids.push(`bls_${s._gi}_${s._si}`);
      });
    });
    return ids;
  }, [filteredBulletSuggestions]);

  const totalFeedbackRequired =
    allBulletItemIds.length + (showSummarySuggestion ? 1 : 0);
  const feedbackCompleted =
    allBulletItemIds.filter((id) => userFeedback[id]).length +
    (showSummarySuggestion && userFeedback[SUMMARY_ITEM_ID] ? 1 : 0);
  const allFeedbackDone = totalFeedbackRequired > 0 && feedbackCompleted === totalFeedbackRequired;

  const handleConfirmModifications = () => {
    if (!allFeedbackDone) {
      alert(ui.resume.alertPending(totalFeedbackRequired - feedbackCompleted));
      return;
    }
    if (!onConfirmModifications) return;

    const feedbackMap: Record<string, { action: string; text?: string }> = {};
    if (showSummarySuggestion && userFeedback[SUMMARY_ITEM_ID]) {
      const fb = userFeedback[SUMMARY_ITEM_ID];
      if (fb === 'accept') {
        feedbackMap[SUMMARY_ITEM_ID] = { action: 'accept' };
      } else if (fb === 'edited') {
        feedbackMap[SUMMARY_ITEM_ID] = { action: 'edited', text: editedTexts[SUMMARY_ITEM_ID] };
      } else {
        feedbackMap[SUMMARY_ITEM_ID] = { action: 'reject' };
      }
    }
    allBulletItemIds.forEach((id) => {
      const fb = userFeedback[id];
      if (fb === 'accept') {
        feedbackMap[id] = { action: 'accept' };
      } else if (fb === 'edited') {
        feedbackMap[id] = { action: 'edited', text: editedTexts[id] };
      } else {
        feedbackMap[id] = { action: 'reject' };
      }
    });
    onConfirmModifications(feedbackMap);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <FileText className="w-6 h-6 text-primary-600" />
          <h2 className="text-2xl font-bold text-gray-900">{ui.resume.title}</h2>
          {totalRecommendations > 0 && (
            <span className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-medium">
              {ui.resume.countSuggestions(totalRecommendations)}
            </span>
          )}
        </div>
        {totalFeedbackRequired > 0 && !confirmedModifications && (
          <button
            onClick={handleConfirmModifications}
            disabled={!allFeedbackDone || generatingResume || preparingInterview}
            className="px-5 py-2.5 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-lg font-medium hover:from-primary-700 hover:to-primary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg flex items-center gap-2"
          >
            {generatingResume ? (
              <><Loader2 className="w-4 h-4 animate-spin" />{ui.resume.generating}</>
            ) : preparingInterview ? (
              <><Loader2 className="w-4 h-4 animate-spin" />{ui.resume.preparingInterview}</>
            ) : (
              <><Sparkles className="w-4 h-4" />{ui.resume.confirmBtn}</>
            )}
          </button>
        )}
        {confirmedModifications && (
          <span className="px-4 py-2 bg-green-100 text-green-800 rounded-lg text-sm font-medium flex items-center gap-2">
            <CheckCircle className="w-4 h-4" />
            {ui.resume.confirmed}
          </span>
        )}
      </div>

      {/* Feedback progress */}
      {totalFeedbackRequired > 0 && !confirmedModifications && (
        <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">{ui.resume.progressLabel}</span>
            <span className="text-sm text-primary-600 font-semibold">
              {feedbackCompleted}/{totalFeedbackRequired}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
            <div
              className={`h-2.5 rounded-full transition-all duration-500 ${allFeedbackDone ? 'bg-green-500' : 'bg-gradient-to-r from-primary-500 to-primary-600'}`}
              style={{ width: `${totalFeedbackRequired > 0 ? (feedbackCompleted / totalFeedbackRequired) * 100 : 0}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {allFeedbackDone
              ? ui.resume.progressHintDone
              : ui.resume.progressHintPending(totalFeedbackRequired - feedbackCompleted)}
          </p>
        </div>
      )}

      {/* Summary — strategy, optional summary */}
      {(tailorStrategy || resumeDiagnosis || showSummarySuggestion) && (
        <div className="card bg-blue-50 border-blue-200 space-y-4">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-blue-600" />
            {ui.resume.summaryTitle}
          </h3>

          {tailorStrategy && (
            <div className="bg-white rounded-lg border border-blue-100 p-4 space-y-3">
              <h4 className="text-sm font-semibold text-gray-900">{ui.resume.strategyTitle}</h4>
              {tailorStrategy.core_narrative_one_liner && (
                <p className="text-sm text-gray-800 leading-relaxed">
                  <span className="font-medium text-gray-600">{ui.resume.strategyNarrative}: </span>
                  {tailorStrategy.core_narrative_one_liner}
                </p>
              )}
              {Array.isArray(tailorStrategy.top_3_jd_keywords) && tailorStrategy.top_3_jd_keywords.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-600 mb-1">{ui.resume.strategyKeywords}</p>
                  <div className="flex flex-wrap gap-2">
                    {tailorStrategy.top_3_jd_keywords.map((kw: string, i: number) => (
                      <span key={i} className="px-2 py-1 bg-blue-100 text-blue-900 rounded text-xs">{kw}</span>
                    ))}
                  </div>
                </div>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                {Array.isArray(tailorStrategy.sections_to_emphasize) && tailorStrategy.sections_to_emphasize.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-emerald-700 mb-1">{ui.resume.strategyEmphasize}</p>
                    <ul className="list-disc list-inside text-gray-700 space-y-0.5">
                      {tailorStrategy.sections_to_emphasize.map((s: string, i: number) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {Array.isArray(tailorStrategy.sections_to_compress_or_remove) && tailorStrategy.sections_to_compress_or_remove.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-amber-800 mb-1">{ui.resume.strategyCompress}</p>
                    <ul className="list-disc list-inside text-gray-700 space-y-0.5">
                      {tailorStrategy.sections_to_compress_or_remove.map((s: string, i: number) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              {tailorStrategy.match_too_low_warning && (
                <p className="text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded p-2">
                  {ui.resume.strategyLowMatch}: {tailorStrategy.match_too_low_warning}
                </p>
              )}
            </div>
          )}

          {resumeDiagnosis?.issues?.length > 0 && (
            <div className="bg-white rounded-lg border border-blue-100 p-4">
              <h4 className="text-sm font-semibold text-gray-900 mb-2">{ui.resume.diagnosisTitle}</h4>
              <ul className="space-y-2">
                {resumeDiagnosis.issues.map((issue: any, i: number) => (
                  <li key={i} className="text-sm border-l-2 border-blue-200 pl-2">
                    <span className={`text-xs font-medium mr-2 ${
                      issue.severity === 'high' ? 'text-red-700' : issue.severity === 'medium' ? 'text-amber-700' : 'text-gray-500'
                    }`}>
                      {issue.severity === 'high' ? ui.resume.severityHigh : issue.severity === 'medium' ? ui.resume.severityMed : ui.resume.severityLow}
                    </span>
                    {issue.issue}
                    {issue.fix_hint && <span className="text-gray-500"> — {issue.fix_hint}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {showSummarySuggestion && (
            <div className="bg-white rounded-lg border border-indigo-200 p-4">
              <h4 className="text-sm font-semibold text-gray-900 mb-3">{ui.resume.optionalSummaryTitle}</h4>
              {summarySuggestion?.original_summary && (
                <div className="mb-3 p-3 bg-gray-50 rounded border border-gray-200">
                  <p className="text-xs font-medium text-gray-600 mb-1">{ui.resume.original}:</p>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{summarySuggestion.original_summary}</p>
                </div>
              )}
              <div className="mb-3">
                <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                  {editedTexts[SUMMARY_ITEM_ID] ?? summarySuggestion?.suggested_summary ?? ''}
                </p>
              </div>
              {editingItem === SUMMARY_ITEM_ID && (
                <textarea
                  className="w-full border border-blue-300 rounded-lg p-3 text-sm mb-3"
                  rows={4}
                  value={editDraft}
                  onChange={(e) => setEditDraft(e.target.value)}
                  autoFocus
                />
              )}
              {!userFeedback[SUMMARY_ITEM_ID] ? (
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleFeedback('summary_suggestion', SUMMARY_ITEM_ID, 'accept')}
                    disabled={submitting === SUMMARY_ITEM_ID}
                    className="btn btn-primary flex items-center gap-2 text-sm"
                  >
                    <Check className="w-4 h-4" />{ui.resume.accept}
                  </button>
                  <button
                    onClick={() => {
                      setEditingItem(SUMMARY_ITEM_ID);
                      setEditDraft(editedTexts[SUMMARY_ITEM_ID] ?? summarySuggestion?.suggested_summary ?? '');
                    }}
                    className="btn btn-outline flex items-center gap-2 text-sm"
                  >
                    <Edit3 className="w-4 h-4" />{ui.resume.edit}
                  </button>
                  <button
                    onClick={() => {
                      setUserFeedback((prev) => ({ ...prev, [SUMMARY_ITEM_ID]: 'reject' }));
                    }}
                    className="btn btn-outline flex items-center gap-2 text-sm"
                  >
                    <X className="w-4 h-4" />{ui.resume.reject}
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    userFeedback[SUMMARY_ITEM_ID] === 'accept' ? 'bg-green-100 text-green-800' :
                    userFeedback[SUMMARY_ITEM_ID] === 'edited' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-200 text-gray-600'
                  }`}>
                    {userFeedback[SUMMARY_ITEM_ID] === 'accept' ? ui.resume.statusAccepted :
                     userFeedback[SUMMARY_ITEM_ID] === 'edited' ? ui.resume.statusEdited : ui.resume.statusRejected}
                  </span>
                  {editingItem === SUMMARY_ITEM_ID && (
                    <button
                      onClick={() => {
                        if (editDraft.trim()) {
                          setEditedTexts((prev) => ({ ...prev, [SUMMARY_ITEM_ID]: editDraft.trim() }));
                          setUserFeedback((prev) => ({ ...prev, [SUMMARY_ITEM_ID]: 'edited' }));
                        }
                        setEditingItem(null);
                        setEditDraft('');
                      }}
                      className="btn btn-primary text-sm"
                    >
                      {ui.resume.ok}
                    </button>
                  )}
                  <button
                    onClick={() => {
                      setUserFeedback((prev) => { const n = { ...prev }; delete n[SUMMARY_ITEM_ID]; return n; });
                      setEditedTexts((prev) => { const n = { ...prev }; delete n[SUMMARY_ITEM_ID]; return n; });
                    }}
                    className="text-xs text-gray-400 hover:text-gray-600 underline"
                  >
                    {ui.resume.undo}
                  </button>
                </div>
              )}
            </div>
          )}

        </div>
      )}

      {/* Format & Content Adjustments - STAR Method Analysis for Each Bullet Point */}
      {formatAdjustments.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Star className="w-5 h-5 text-yellow-600" />
            <h3 className="text-lg font-semibold text-gray-900">
              Detailed Improvement Suggestions (STAR Method Analysis)
            </h3>
            <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">
              {formatAdjustments.length} {formatAdjustments.length === 1 ? 'Experience' : 'Experiences'}
            </span>
          </div>
          <div className="space-y-6">
            {formatAdjustments.map((adjustmentGroup: any, groupIndex: number) => {
              const entry = adjustmentGroup.experience_entry;
              const entryId = `${entry?.title}_${entry?.company}_${entry?.entry_index || groupIndex}`;
              const groupItemId = `format_group_${entryId}`;
              const isGroupExpanded = expandedItems.has(groupItemId);

              return (
                <div key={groupIndex} className="card border-l-4 border-yellow-500">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-1">
                        {entry?.title} at {entry?.company}
                      </h4>
                      {entry?.duration && (
                        <p className="text-sm text-gray-600">{entry.duration}</p>
                      )}
                      <p className="text-sm text-gray-500 mt-1">
                        {adjustmentGroup.adjustments?.length || 0} bullet point
                        {(adjustmentGroup.adjustments?.length || 0) !== 1 ? 's' : ''} with suggestions
                      </p>
                    </div>
                    <button
                      onClick={() => toggleExpand(groupItemId)}
                      className="ml-4 text-primary-600 hover:text-primary-700"
                    >
                      {isGroupExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </button>
                  </div>

                  {isGroupExpanded && (
                    <div className="space-y-4 pt-4 border-t border-gray-200">
                      {adjustmentGroup.adjustments?.map((adjustment: any, adjIndex: number) => {
                        const bullet = adjustment.bullet_point;
                        const adjItemId = `adjustment_${entryId}_${adjIndex}`;
                        const isBulletExpanded = expandedItems.has(adjItemId);
                        const bulletFeedback = userFeedback[adjItemId];

                        return (
                          <div key={adjIndex} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="px-2 py-0.5 bg-primary-100 text-primary-800 rounded text-xs font-medium">
                                    Bullet Point {adjIndex + 1}
                                  </span>
                                  {bullet?.improvement_type && (
                                    <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs">
                                      {bullet.improvement_type}
                                    </span>
                                  )}
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                                  <div className="bg-white p-3 rounded border border-gray-300">
                                    <p className="text-xs font-medium text-gray-600 mb-1 flex items-center gap-1">
                                      <FileText className="w-3 h-3" />
                                      Original:
                                    </p>
                                    <p className="text-sm text-gray-700">{bullet?.original || 'N/A'}</p>
                                  </div>
                                  <div className="bg-green-50 p-3 rounded border border-green-300">
                                    <p className="text-xs font-medium text-gray-600 mb-1 flex items-center gap-1">
                                      <Target className="w-3 h-3" />
                                      Suggested:
                                    </p>
                                    <p className="text-sm text-gray-900 font-medium">
                                      {regeneratedSuggestions[adjItemId] ?? bullet?.suggested ?? 'N/A'}
                                    </p>
                                  </div>
                                </div>
                              </div>
                              <button
                                onClick={() => toggleExpand(adjItemId)}
                                className="ml-2 text-gray-600 hover:text-gray-800"
                              >
                                {isBulletExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                              </button>
                            </div>

                            {isBulletExpanded && (
                              <div className="space-y-3 pt-3 border-t border-gray-300">
                                {bullet?.star_analysis && (
                                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                                    <h5 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                                      <Star className="w-4 h-4 text-blue-600" />
                                      STAR Method Analysis
                                    </h5>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                      <div>
                                        <p className="text-xs font-medium text-gray-700 mb-1">Situation:</p>
                                        <p className="text-sm text-gray-600 bg-white p-2 rounded">
                                          {bullet.star_analysis.situation || 'Not specified'}
                                        </p>
                                      </div>
                                      <div>
                                        <p className="text-xs font-medium text-gray-700 mb-1">Task:</p>
                                        <p className="text-sm text-gray-600 bg-white p-2 rounded">
                                          {bullet.star_analysis.task || 'Not specified'}
                                        </p>
                                      </div>
                                      <div>
                                        <p className="text-xs font-medium text-gray-700 mb-1">Action:</p>
                                        <p className="text-sm text-gray-600 bg-white p-2 rounded">
                                          {bullet.star_analysis.action || 'Not specified'}
                                        </p>
                                      </div>
                                      <div>
                                        <p className="text-xs font-medium text-gray-700 mb-1">Result:</p>
                                        <p className="text-sm text-gray-600 bg-white p-2 rounded">
                                          {bullet.star_analysis.result || 'Not specified'}
                                        </p>
                                      </div>
                                    </div>
                                  </div>
                                )}

                                {bullet?.improvement_rationale && (
                                  <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
                                    <p className="text-xs font-medium text-gray-700 mb-1 flex items-center gap-1">
                                      <Lightbulb className="w-3 h-3" />
                                      Why This Change:
                                    </p>
                                    <p className="text-sm text-gray-700">{bullet.improvement_rationale}</p>
                                  </div>
                                )}

                                {bullet?.jd_keywords_added && bullet.jd_keywords_added.length > 0 && (
                                  <div>
                                    <p className="text-xs font-medium text-gray-700 mb-2">JD Keywords Added:</p>
                                    <div className="flex flex-wrap gap-2">
                                      {bullet.jd_keywords_added.map((keyword: string, kwIndex: number) => (
                                        <span
                                          key={kwIndex}
                                          className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs"
                                        >
                                          {keyword}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {bullet?.expected_impact && (
                                  <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
                                    <p className="text-xs font-medium text-gray-700 mb-1 flex items-center gap-1">
                                      <TrendingUp className="w-3 h-3" />
                                      Expected Impact:
                                    </p>
                                    <p className="text-sm text-gray-700">{bullet.expected_impact}</p>
                                  </div>
                                )}

                                {!bulletFeedback && (
                                  <div className="flex flex-wrap gap-2 pt-2">
                                    <button
                                      onClick={() => handleFeedback('format_adjustment', adjItemId, 'accept')}
                                      disabled={submitting === adjItemId}
                                      className="btn btn-primary flex items-center gap-2 text-sm"
                                    >
                                      <Check className="w-4 h-4" />
                                      Accept
                                    </button>
                                    <button
                                      onClick={() => openModifyModal(adjItemId)}
                                      disabled={submitting === adjItemId}
                                      className="btn btn-outline flex items-center gap-2 text-sm"
                                    >
                                      <Edit3 className="w-4 h-4" />
                                      Modify
                                    </button>
                                    <button
                                      onClick={() => handleFeedback('format_adjustment', adjItemId, 'reject')}
                                      disabled={submitting === adjItemId}
                                      className="btn btn-outline flex items-center gap-2 text-sm"
                                    >
                                      <X className="w-4 h-4" />
                                      Reject
                                    </button>
                                  </div>
                                )}

                                {bulletFeedback && (
                                  <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                                    <p className="text-sm text-blue-800">
                                      Feedback: <span className="font-semibold">{bulletFeedback}</span>
                                    </p>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Experience Optimizations */}
      {experienceOptimizations.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-purple-600" />
            Experience Optimizations ({experienceOptimizations.length})
          </h3>
          <div className="space-y-4">
            {experienceOptimizations.map((optimization: any, index: number) => {
              const entry = optimization.experience_entry;
              const entryId = `${entry.title}_${entry.company}_${entry.entry_index}`;
              const itemId = `experience_opt_${entryId}`;
              const isExpanded = expandedItems.has(itemId);
              const feedback = userFeedback[itemId];

              return (
                <div key={index} className="card border-l-4 border-purple-500">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-2">
                        {entry.title} at {entry.company}
                      </h4>
                      {entry.duration && <p className="text-sm text-gray-600">{entry.duration}</p>}
                    </div>
                    <button
                      onClick={() => toggleExpand(itemId)}
                      className="ml-4 text-primary-600 hover:text-primary-700"
                    >
                      {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </button>
                  </div>

                  {isExpanded && (
                    <div className="mt-4 space-y-4 pt-4 border-t border-gray-200">
                      {optimization.optimized_experience?.optimized_bullets && (
                        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                          <h5 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                            <CheckCircle className="w-4 h-4 text-green-600" />
                            Optimized Version:
                          </h5>
                          <ul className="space-y-1">
                            {optimization.optimized_experience.optimized_bullets.map(
                              (bullet: string, i: number) => (
                                <li key={i} className="text-sm text-gray-700">• {bullet}</li>
                              )
                            )}
                          </ul>
                        </div>
                      )}

                      {optimization.optimization_details?.map((detail: any, detailIndex: number) => (
                        <div key={detailIndex} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                            <div className="bg-white p-3 rounded border border-gray-300">
                              <p className="text-xs font-medium text-gray-600 mb-1 flex items-center gap-1">
                                <FileText className="w-3 h-3" />
                                Original:
                              </p>
                              <p className="text-sm text-gray-700">{detail.original}</p>
                            </div>
                            <div className="bg-green-50 p-3 rounded border border-green-300">
                              <p className="text-xs font-medium text-gray-600 mb-1 flex items-center gap-1">
                                <Target className="w-3 h-3" />
                                Optimized:
                              </p>
                              <p className="text-sm text-gray-900 font-medium">{detail.optimized}</p>
                            </div>
                          </div>
                          {detail.optimization_type && (
                            <p className="text-xs text-gray-600 mb-2">
                              <span className="font-medium">Type:</span> {detail.optimization_type}
                            </p>
                          )}
                          {detail.optimization_rationale && (
                            <div className="bg-yellow-50 p-2 rounded border border-yellow-200">
                              <p className="text-xs font-medium text-gray-700 mb-1">Rationale:</p>
                              <p className="text-sm text-gray-700">{detail.optimization_rationale}</p>
                            </div>
                          )}
                          {detail.jd_keywords_added && detail.jd_keywords_added.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs font-medium text-gray-700 mb-1">JD Keywords Added:</p>
                              <div className="flex flex-wrap gap-2">
                                {detail.jd_keywords_added.map((keyword: string, kwIndex: number) => (
                                  <span
                                    key={kwIndex}
                                    className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs"
                                  >
                                    {keyword}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          {detail.expected_impact && (
                            <div className="mt-2 bg-purple-50 p-2 rounded border border-purple-200">
                              <p className="text-xs font-medium text-gray-700 mb-1">Expected Impact:</p>
                              <p className="text-sm text-gray-700">{detail.expected_impact}</p>
                            </div>
                          )}
                        </div>
                      ))}

                      {!feedback && (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleFeedback('experience_optimization', itemId, 'accept')}
                            disabled={submitting === itemId}
                            className="btn btn-primary flex items-center gap-2"
                          >
                            <Check className="w-4 h-4" />
                            Accept
                          </button>
                          <button
                            onClick={() => handleFeedback('experience_optimization', itemId, 'reject')}
                            disabled={submitting === itemId}
                            className="btn btn-outline flex items-center gap-2"
                          >
                            <X className="w-4 h-4" />
                            Reject
                          </button>
                        </div>
                      )}

                      {feedback && (
                        <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                          <p className="text-sm text-blue-800">
                            Feedback: <span className="font-semibold">{feedback}</span>
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Bullet-Level Suggestions (new Agent 4 schema) */}
      {filteredBulletSuggestions.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Edit3 className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">
              {ui.resume.bulletSection}
            </h3>
            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
              {ui.resume.expGroups(filteredBulletSuggestions.length)}
            </span>
          </div>
          <div className="space-y-6">
            {filteredBulletSuggestions.map((group: any, gi: number) => {
              const gid = `bls_group_${group.suggestions?.[0]?._gi ?? gi}`;
              const isOpen = expandedItems.has(gid);
              const suggestions = group.suggestions || [];
              return (
                <div key={gid} className="card border-l-4 border-blue-500">
                  <div className="flex items-start justify-between mb-2">
                    <div className="min-w-0 pr-2">
                      <div className="flex flex-wrap items-center gap-2 gap-y-1">
                        <h4 className="font-semibold text-gray-900">{group.experience_entry}</h4>
                        <ExperienceJdImportanceBadge
                          level={triLevelFromApi(group.experience_jd_importance)}
                          ui={ui}
                        />
                      </div>
                      <p className="text-sm text-gray-500 mt-0.5">{ui.resume.suggestionsCount(suggestions.length)}</p>
                    </div>
                    <button onClick={() => toggleExpand(gid)} className="text-primary-600 hover:text-primary-700">
                      {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </button>
                  </div>
                  {isOpen && (
                    <div className="space-y-4 pt-4 border-t border-gray-200">
                      {suggestions.map((s: any) => {
                        const itemId = `bls_${s._gi}_${s._si}`;
                        const fb = userFeedback[itemId];
                        const isEditing = editingItem === itemId;
                        const finalText = editedTexts[itemId];
                        const displaySuggested = finalText ?? s.suggested_bullet ?? 'N/A';

                        return (
                          <div key={itemId} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                            {fb && (
                              <div className="flex flex-wrap items-center gap-2 mb-3">
                                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                                  fb === 'accept' ? 'bg-green-100 text-green-800' :
                                  fb === 'edited' ? 'bg-blue-100 text-blue-800' :
                                  'bg-gray-200 text-gray-600'
                                }`}>
                                  {fb === 'accept' ? ui.resume.statusAccepted : fb === 'edited' ? ui.resume.statusEdited : ui.resume.statusRejected}
                                </span>
                              </div>
                            )}

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                              <div className={`p-3 rounded border ${fb === 'reject' ? 'bg-white border-gray-300 ring-2 ring-blue-200' : 'bg-white border-gray-300'}`}>
                                <p className="text-xs font-medium text-gray-600 mb-1">{fb === 'reject' ? ui.resume.originalKept : `${ui.resume.original}:`}</p>
                                <p className="text-sm text-gray-700">{s.original_bullet || 'N/A'}</p>
                              </div>
                              <div className={`p-3 rounded border ${
                                fb === 'accept' || fb === 'edited' ? 'bg-green-50 border-green-400 ring-2 ring-green-200' :
                                fb === 'reject' ? 'bg-gray-50 border-gray-200 opacity-60' :
                                'bg-green-50 border-green-300'
                              }`}>
                                <p className="text-xs font-medium text-gray-600 mb-1">
                                  {fb === 'edited' ? ui.resume.yourVersion : ui.resume.suggested}
                                </p>
                                <p className={`text-sm font-medium ${fb === 'reject' ? 'text-gray-400 line-through' : 'text-gray-900'}`}>
                                  {displaySuggested}
                                </p>
                              </div>
                            </div>

                            {/* Inline editing */}
                            {isEditing && (
                              <div className="mb-3 space-y-2">
                                <label className="text-xs font-medium text-gray-700">{ui.resume.betterWording}</label>
                                <textarea
                                  className="w-full border border-blue-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 resize-y"
                                  rows={3}
                                  value={editDraft}
                                  onChange={(e) => setEditDraft(e.target.value)}
                                  autoFocus
                                />
                                <div className="flex gap-2">
                                  <button
                                    onClick={() => {
                                      if (editDraft.trim()) {
                                        setEditedTexts((prev) => ({ ...prev, [itemId]: editDraft.trim() }));
                                        setUserFeedback((prev) => ({ ...prev, [itemId]: 'edited' }));
                                      }
                                      setEditingItem(null);
                                      setEditDraft('');
                                    }}
                                    disabled={!editDraft.trim()}
                                    className="px-4 py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                                  >
                                    <Check className="w-3.5 h-3.5" />
                                    {ui.resume.ok}
                                  </button>
                                  <button
                                    onClick={() => { setEditingItem(null); setEditDraft(''); }}
                                    className="px-4 py-1.5 bg-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-300 flex items-center gap-1"
                                  >
                                    <X className="w-3.5 h-3.5" />
                                    {ui.resume.cancel}
                                  </button>
                                </div>
                              </div>
                            )}

                            {/* Action buttons — hidden after confirmation */}
                            {!fb && !isEditing && !confirmedModifications && (
                              <div className="flex flex-wrap gap-2 mt-3">
                                <button
                                  onClick={() => setUserFeedback((prev) => ({ ...prev, [itemId]: 'accept' }))}
                                  className="px-4 py-1.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors flex items-center gap-1.5"
                                >
                                  <Check className="w-3.5 h-3.5" />
                                  {ui.resume.accept}
                                </button>
                                <button
                                  onClick={() => {
                                    setEditDraft(s.suggested_bullet || '');
                                    setEditingItem(itemId);
                                  }}
                                  className="px-4 py-1.5 bg-white border border-blue-300 text-blue-700 rounded-lg text-sm font-medium hover:bg-blue-50 transition-colors flex items-center gap-1.5"
                                >
                                  <Edit3 className="w-3.5 h-3.5" />
                                  {ui.resume.edit}
                                </button>
                                <button
                                  onClick={() => setUserFeedback((prev) => ({ ...prev, [itemId]: 'reject' }))}
                                  className="px-4 py-1.5 bg-white border border-gray-300 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-100 transition-colors flex items-center gap-1.5"
                                >
                                  <X className="w-3.5 h-3.5" />
                                  {ui.resume.reject}
                                </button>
                              </div>
                            )}

                            {/* Undo after decision — only before confirmation */}
                            {fb && !isEditing && !confirmedModifications && (
                              <div className="mt-2">
                                <button
                                  onClick={() => {
                                    setUserFeedback((prev) => { const n = { ...prev }; delete n[itemId]; return n; });
                                    setEditedTexts((prev) => { const n = { ...prev }; delete n[itemId]; return n; });
                                  }}
                                  className="text-xs text-gray-400 hover:text-gray-600 underline"
                                >
                                  {ui.resume.undo}
                                </button>
                              </div>
                            )}

                            {(() => {
                              const kwList = Array.isArray(s.jd_keywords_added) ? s.jd_keywords_added : [];
                              const hasKw = kwList.length > 0;
                              const rs = s.reason_struct;
                              const hasReason = Boolean(
                                (s.reason && String(s.reason).trim()) ||
                                (rs && typeof rs === 'object' && (rs.align || rs.rewrite || rs.evidence || rs.expected_impact))
                              );
                              if (isEditing || (!hasReason && !hasKw)) return null;
                              return (
                                <div className="mt-3 rounded-lg border border-gray-200 bg-white overflow-hidden shadow-sm">
                                  {hasReason ? (
                                    <div className={hasKw ? 'border-b border-slate-200/80' : ''}>
                                      <ReasonStructDisplay suggestion={s} ui={ui} />
                                    </div>
                                  ) : null}
                                  {hasKw ? (
                                    <div className="px-3 py-2.5 bg-slate-50/90">
                                      <div className="flex flex-wrap gap-2">
                                        {kwList.map((kw: string, ki: number) => (
                                          <span
                                            key={ki}
                                            className="px-2 py-1 bg-emerald-100/90 text-emerald-900 rounded-md text-xs border border-emerald-200/80"
                                          >
                                            {kw}
                                          </span>
                                        ))}
                                      </div>
                                    </div>
                                  ) : null}
                                </div>
                              );
                            })()}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Revised Resume Preview */}
      {(generatedResume || data?.revised_resume_full) && (
        <div className="card bg-green-50 border-green-200">
          <div className="flex items-center gap-2 mb-3">
            <FileText className="w-5 h-5 text-green-600" />
            <h3 className="font-semibold text-gray-900">
              {generatedResume ? ui.resume.previewAfter : ui.resume.previewBefore}
            </h3>
            {generatedResume && (
              <span className="px-2 py-0.5 bg-green-200 text-green-800 rounded text-xs font-medium">{ui.resume.generatedBadge}</span>
            )}
          </div>
          <pre className="text-sm text-gray-800 whitespace-pre-wrap bg-white p-4 rounded-lg border border-gray-200 max-h-[500px] overflow-y-auto leading-relaxed">
            {generatedResume || data.revised_resume_full}
          </pre>
        </div>
      )}

      {/* Modify modal */}
      {modifyModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setModifyModal((m) => ({ ...m, open: false }))}>
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">{ui.resume.modalTitle}</h3>
            <p className="text-sm text-gray-600 mb-3">{ui.resume.modalDesc}</p>
            <textarea
              className="textarea w-full mb-4"
              rows={3}
              placeholder={ui.resume.modalPlaceholder}
              value={modifyModal.instruction}
              onChange={(e) => setModifyModal((m) => ({ ...m, instruction: e.target.value }))}
            />
            <div className="flex justify-end gap-2">
              <button type="button" className="btn btn-outline" onClick={() => setModifyModal({ open: false, itemId: null, instruction: '' })}>
                {ui.resume.modalCancel}
              </button>
              <button
                type="button"
                className="btn btn-primary"
                disabled={!modifyModal.instruction.trim() || submitting === modifyModal.itemId}
                onClick={submitRegenerate}
              >
                {submitting === modifyModal.itemId ? ui.resume.regenerating : ui.resume.modalApply}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
