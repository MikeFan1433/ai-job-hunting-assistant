import { useState } from 'react';
import { CheckCircle, ChevronDown, ChevronUp, Check, X } from 'lucide-react';
import { resumeAPI } from '../../services/api';

interface Props {
  data: any;
  onFeedbackUpdate: () => void;
  feedbackStatus: any;
}

export default function ResumeOptimizationTab({ data, onFeedbackUpdate }: Props) {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [userFeedback, setUserFeedback] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState<string | null>(null);

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
      });
      setUserFeedback({ ...userFeedback, [itemId]: feedback });
      onFeedbackUpdate();
    } catch (error: any) {
      alert(`Error submitting feedback: ${error.message}`);
    } finally {
      setSubmitting(null);
    }
  };

  const handleAcceptAll = async () => {
    if (!confirm('Accept all recommendations?')) return;

    const allFeedbacks: any[] = [];

    // Collect all experience replacements
    (data?.experience_replacements || []).forEach((_: any, index: number) => {
      allFeedbacks.push({
        feedback_type: 'experience_replacement',
        item_id: `replacement_${index}`,
        feedback: 'accept',
      });
    });

    // Collect all experience optimizations
    (data?.experience_optimizations || []).forEach((opt: any) => {
      const entry = opt.experience_entry;
      const entryId = `${entry.title}_${entry.company}_${entry.entry_index}`;
      allFeedbacks.push({
        feedback_type: 'experience_optimization',
        item_id: `experience_opt_${entryId}`,
        feedback: 'accept',
      });
    });

    // Collect all format adjustments
    (data?.format_content_adjustments || []).forEach((group: any) => {
      const entryId = `${group.experience_entry?.title}_${group.experience_entry?.company}_${group.experience_entry?.entry_index}`;
      (group.adjustments || []).forEach((_: any, adjIndex: number) => {
        allFeedbacks.push({
          feedback_type: 'format_adjustment',
          item_id: `adjustment_${entryId}_${adjIndex}`,
          feedback: 'accept',
        });
      });
    });

    // Skills optimization
    if (data?.skills_section_optimization?.has_skills_section) {
      allFeedbacks.push({
        feedback_type: 'skills_optimization',
        item_id: 'skills_section',
        feedback: 'accept',
      });
    }

    try {
      await resumeAPI.submitBatchFeedback(allFeedbacks);
      alert('All recommendations accepted!');
      onFeedbackUpdate();
    } catch (error: any) {
      alert(`Error accepting all: ${error.message}`);
    }
  };

  const experienceReplacements = data?.experience_replacements || [];
  const experienceOptimizations = data?.experience_optimizations || [];
  // const formatAdjustments = data?.format_content_adjustments || []; // TODO: Implement format adjustments UI
  const skillsOptimization = data?.skills_section_optimization;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <CheckCircle className="w-6 h-6 text-primary-600" />
          <h2 className="text-2xl font-bold text-gray-900">Resume Optimization Recommendations</h2>
        </div>
        {(experienceReplacements.length > 0 || experienceOptimizations.length > 0) && (
          <button onClick={handleAcceptAll} className="btn btn-primary">
            Accept All
          </button>
        )}
      </div>

      {/* Experience Replacements */}
      {experienceReplacements.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Experience Replacements ({experienceReplacements.length})
          </h3>
          <div className="space-y-4">
            {experienceReplacements.map((replacement: any, index: number) => {
              const itemId = `replacement_${index}`;
              const isExpanded = expandedItems.has(itemId);
              const feedback = userFeedback[itemId];

              return (
                <div key={index} className="card border-l-4 border-blue-500">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-2">
                        Replace: {replacement.experience_to_replace?.title} at{' '}
                        {replacement.experience_to_replace?.company}
                      </h4>
                      <p className="text-sm text-gray-600 mb-3">
                        {replacement.replacement_rationale?.why_replace}
                      </p>
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
                      <div>
                        <h5 className="font-medium text-gray-900 mb-2">Current Experience:</h5>
                        <div className="bg-gray-50 p-3 rounded-lg">
                          <p className="text-sm text-gray-700">
                            {replacement.experience_to_replace?.title} |{' '}
                            {replacement.experience_to_replace?.company} |{' '}
                            {replacement.experience_to_replace?.duration}
                          </p>
                          <ul className="mt-2 space-y-1">
                            {replacement.experience_to_replace?.current_description?.map(
                              (desc: string, i: number) => (
                                <li key={i} className="text-sm text-gray-600">• {desc}</li>
                              )
                            )}
                          </ul>
                        </div>
                      </div>

                      <div>
                        <h5 className="font-medium text-gray-900 mb-2">New Experience:</h5>
                        <div className="bg-green-50 p-3 rounded-lg border border-green-200">
                          <p className="text-sm font-medium text-gray-900">
                            {replacement.replacement_instructions?.new_title}
                          </p>
                          <ul className="mt-2 space-y-1">
                            {replacement.replacement_instructions?.new_bullets?.map(
                              (bullet: string, i: number) => (
                                <li key={i} className="text-sm text-gray-700">• {bullet}</li>
                              )
                            )}
                          </ul>
                        </div>
                      </div>

                      {!feedback && (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleFeedback('experience_replacement', itemId, 'accept')}
                            disabled={submitting === itemId}
                            className="btn btn-primary flex items-center gap-2"
                          >
                            <Check className="w-4 h-4" />
                            Accept
                          </button>
                          <button
                            onClick={() => handleFeedback('experience_replacement', itemId, 'reject')}
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

      {/* Experience Optimizations */}
      {experienceOptimizations.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
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
                      {optimization.optimization_details?.map((detail: any, detailIndex: number) => (
                        <div key={detailIndex} className="space-y-2">
                          <div className="grid grid-cols-2 gap-4">
                            <div className="bg-gray-50 p-3 rounded-lg">
                              <p className="text-xs font-medium text-gray-600 mb-1">Original:</p>
                              <p className="text-sm text-gray-700">{detail.original}</p>
                            </div>
                            <div className="bg-green-50 p-3 rounded-lg border border-green-200">
                              <p className="text-xs font-medium text-gray-600 mb-1">Optimized:</p>
                              <p className="text-sm text-gray-700">{detail.optimized}</p>
                            </div>
                          </div>
                          <p className="text-xs text-gray-600">{detail.optimization_rationale}</p>
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

      {/* Skills Optimization */}
      {skillsOptimization?.has_skills_section && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Skills Section Optimization</h3>
          <div className="card border-l-4 border-indigo-500">
            {skillsOptimization.current_skills?.map((skillCat: any, index: number) => (
              <div key={index} className="mb-4 last:mb-0">
                <h4 className="font-semibold text-gray-900 mb-3">{skillCat.skill_category}</h4>
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div>
                    <p className="text-xs font-medium text-gray-600 mb-2">Current:</p>
                    <div className="flex flex-wrap gap-2">
                      {skillCat.current_skills_list?.map((skill: string, i: number) => (
                        <span key={i} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-600 mb-2">Optimized:</p>
                    <div className="flex flex-wrap gap-2">
                      {skillCat.optimized_skills_list?.map((skill: string, i: number) => (
                        <span key={i} className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                {!userFeedback['skills_section'] && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleFeedback('skills_optimization', 'skills_section', 'accept')}
                      className="btn btn-primary flex items-center gap-2"
                    >
                      <Check className="w-4 h-4" />
                      Accept
                    </button>
                    <button
                      onClick={() => handleFeedback('skills_optimization', 'skills_section', 'reject')}
                      className="btn btn-outline flex items-center gap-2"
                    >
                      <X className="w-4 h-4" />
                      Reject
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary */}
      {data?.optimization_summary && (
        <div className="card bg-blue-50 border-blue-200">
          <h3 className="font-semibold text-gray-900 mb-3">Optimization Summary</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Experiences Analyzed:</span>
              <span className="font-semibold ml-2">{data.optimization_summary.total_experiences_analyzed}</span>
            </div>
            <div>
              <span className="text-gray-600">Replacements Recommended:</span>
              <span className="font-semibold ml-2">
                {data.optimization_summary.experiences_recommended_for_replacement}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Experiences Optimized:</span>
              <span className="font-semibold ml-2">{data.optimization_summary.total_experiences_optimized}</span>
            </div>
            <div>
              <span className="text-gray-600">Expected Improvement:</span>
              <span className="font-semibold ml-2">
                {data.optimization_summary.expected_match_score_improvement}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
