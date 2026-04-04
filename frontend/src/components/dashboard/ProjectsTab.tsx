import { useState } from 'react';
import { FolderOpen, CheckCircle, Target, FileText, GitCompare, ChevronDown, ChevronUp } from 'lucide-react';

interface Props {
  data: any;
}

export default function ProjectsTab({ data }: Props) {
  const [expandedProjects, setExpandedProjects] = useState<Set<number>>(new Set());
  const [activeView, setActiveView] = useState<'original' | 'optimized' | 'comparison'>('comparison');
  
  const projects = data?.selected_projects || [];
  const skipped = data?.skipped === true;
  const skipMessage = data?.message || 'No project materials provided; project packaging was skipped.';

  const toggleExpand = (index: number) => {
    const newExpanded = new Set(expandedProjects);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedProjects(newExpanded);
  };

  if (projects.length === 0) {
    return (
      <div className="text-center py-12">
        <FolderOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        {skipped ? (
          <>
            <p className="text-gray-700 font-medium mb-1">Project packaging skipped</p>
            <p className="text-gray-500 text-sm">{skipMessage}</p>
          </>
        ) : (
          <p className="text-gray-600">No projects available</p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <FolderOpen className="w-6 h-6 text-primary-600" />
          <h2 className="text-2xl font-bold text-gray-900">Optimized Projects</h2>
          <span className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-medium">
            {projects.length} {projects.length === 1 ? 'Project' : 'Projects'}
          </span>
        </div>
        
        {/* View Toggle */}
        <div className="flex gap-2 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setActiveView('comparison')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeView === 'comparison'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <GitCompare className="w-4 h-4 inline mr-2" />
            Comparison
          </button>
          <button
            onClick={() => setActiveView('original')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeView === 'original'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <FileText className="w-4 h-4 inline mr-2" />
            Original
          </button>
          <button
            onClick={() => setActiveView('optimized')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeView === 'optimized'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <CheckCircle className="w-4 h-4 inline mr-2" />
            Optimized
          </button>
        </div>
      </div>

      {projects.map((project: any, index: number) => {
        const isExpanded = expandedProjects.has(index);
        const originalText = project.original_project_text || '';
        const optimizedText = project.optimized_project_text || {};
        const modifications = project.modification_explanation || {};

        return (
          <div key={index} className="card border-l-4 border-primary-500">
            {/* Project Header */}
            <div className="mb-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">{project.project_name}</h3>
                  <p className="text-sm text-gray-600 mb-3">{project.relevance_reason}</p>
                </div>
                <button
                  onClick={() => toggleExpand(index)}
                  className="ml-4 text-primary-600 hover:text-primary-700"
                >
                  {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Comparison View (Default) */}
            {activeView === 'comparison' && (
              <div className="space-y-6">
                {/* Side-by-Side Comparison */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {/* Original Text */}
                  <div className="border-r border-gray-200 pr-4">
                    <div className="flex items-center gap-2 mb-3">
                      <FileText className="w-5 h-5 text-gray-600" />
                      <h4 className="font-semibold text-gray-900">Original Project Text</h4>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                      <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">
                        {originalText || 'No original text available'}
                      </pre>
                    </div>
                  </div>

                  {/* Optimized Text */}
                  <div className="pl-4">
                    <div className="flex items-center gap-2 mb-3">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <h4 className="font-semibold text-gray-900">Optimized Project Text</h4>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4 max-h-96 overflow-y-auto border border-green-200">
                      {optimizedText.goals && (
                        <div className="mb-4">
                          <h5 className="font-medium text-gray-900 mb-2">Goals</h5>
                          <div className="text-sm text-gray-700 space-y-1">
                            {optimizedText.goals.business_objective && (
                              <p><span className="font-medium">Business Objective:</span> {optimizedText.goals.business_objective}</p>
                            )}
                            {optimizedText.goals.pain_point && (
                              <p><span className="font-medium">Pain Point:</span> {optimizedText.goals.pain_point}</p>
                            )}
                            {optimizedText.goals.background && (
                              <p><span className="font-medium">Background:</span> {optimizedText.goals.background}</p>
                            )}
                            {optimizedText.goals.success_definition && (
                              <p><span className="font-medium">Success Definition:</span> {optimizedText.goals.success_definition}</p>
                            )}
                          </div>
                        </div>
                      )}
                      {optimizedText.methods_solution && (
                        <div className="mb-4">
                          <h5 className="font-medium text-gray-900 mb-2">Methods & Solution</h5>
                          <div className="text-sm text-gray-700 space-y-1">
                            {optimizedText.methods_solution.selected_approach && (
                              <p><span className="font-medium">Selected Approach:</span> {optimizedText.methods_solution.selected_approach}</p>
                            )}
                            {optimizedText.methods_solution.considered_options && (
                              <div>
                                <span className="font-medium">Considered Options:</span>
                                <ul className="list-disc list-inside ml-2">
                                  {optimizedText.methods_solution.considered_options.map((opt: string, i: number) => (
                                    <li key={i}>{opt}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      {optimizedText.execution_timeline && (
                        <div className="mb-4">
                          <h5 className="font-medium text-gray-900 mb-2">Execution & Timeline</h5>
                          <div className="text-sm text-gray-700 space-y-1">
                            {optimizedText.execution_timeline.phases && (
                              <div>
                                <span className="font-medium">Phases:</span>
                                <ul className="list-disc list-inside ml-2">
                                  {optimizedText.execution_timeline.phases.map((phase: string, i: number) => (
                                    <li key={i}>{phase}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      {optimizedText.results_metrics && (
                        <div className="mb-4">
                          <h5 className="font-medium text-gray-900 mb-2">Results & Metrics</h5>
                          <div className="text-sm text-gray-700 space-y-1">
                            {optimizedText.results_metrics.primary_metric && (
                              <p><span className="font-medium">Primary Metric:</span> {optimizedText.results_metrics.primary_metric}</p>
                            )}
                            {optimizedText.results_metrics.secondary_outcomes && (
                              <div>
                                <span className="font-medium">Secondary Outcomes:</span>
                                <ul className="list-disc list-inside ml-2">
                                  {optimizedText.results_metrics.secondary_outcomes.map((outcome: string, i: number) => (
                                    <li key={i}>{outcome}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      {optimizedText.learning_reflection && (
                        <div>
                          <h5 className="font-medium text-gray-900 mb-2">Learning & Reflection</h5>
                          <div className="text-sm text-gray-700 space-y-1">
                            {optimizedText.learning_reflection.top_lessons && (
                              <div>
                                <span className="font-medium">Top Lessons:</span>
                                <ul className="list-disc list-inside ml-2">
                                  {optimizedText.learning_reflection.top_lessons.map((lesson: string, i: number) => (
                                    <li key={i}>{lesson}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      {!optimizedText.goals && !optimizedText.methods_solution && (
                        <p className="text-sm text-gray-500">No optimized text available</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Modification Explanation */}
                {modifications && (modifications.detailed_changes || modifications.summary) && (
                  <div className="mt-6 border-t border-gray-200 pt-6">
                    <div className="flex items-center gap-2 mb-4">
                      <GitCompare className="w-5 h-5 text-primary-600" />
                      <h4 className="font-semibold text-gray-900">Modification Explanation</h4>
                    </div>
                    
                    {modifications.summary && (
                      <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                        <p className="text-sm text-gray-700"><span className="font-medium">Summary:</span> {modifications.summary}</p>
                      </div>
                    )}

                    {modifications.detailed_changes && modifications.detailed_changes.length > 0 && (
                      <div className="space-y-4">
                        <h5 className="font-medium text-gray-900 mb-3">Detailed Changes</h5>
                        {modifications.detailed_changes.map((change: any, changeIndex: number) => (
                          <div key={changeIndex} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                              <div>
                                <p className="text-xs font-medium text-gray-600 mb-1">Section: {change.section}</p>
                                <p className="text-xs font-medium text-gray-600 mb-1">Subsection: {change.subsection}</p>
                                <p className="text-xs font-medium text-gray-600 mb-1">Change Type: 
                                  <span className={`ml-1 px-2 py-0.5 rounded text-xs ${
                                    change.change_type === 'ADDED' ? 'bg-green-100 text-green-800' :
                                    change.change_type === 'MODIFIED' ? 'bg-yellow-100 text-yellow-800' :
                                    change.change_type === 'ENHANCED' ? 'bg-blue-100 text-blue-800' :
                                    'bg-purple-100 text-purple-800'
                                  }`}>
                                    {change.change_type}
                                  </span>
                                </p>
                              </div>
                              <div>
                                <p className="text-xs font-medium text-gray-600 mb-1">JD Alignment:</p>
                                <p className="text-xs text-gray-700">{change.jd_alignment || 'N/A'}</p>
                              </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                              <div className="bg-red-50 p-3 rounded border border-red-200">
                                <p className="text-xs font-medium text-red-800 mb-1">Original:</p>
                                <p className="text-xs text-gray-700">{change.original_content || 'MISSING'}</p>
                              </div>
                              <div className="bg-green-50 p-3 rounded border border-green-200">
                                <p className="text-xs font-medium text-green-800 mb-1">Modified:</p>
                                <p className="text-xs text-gray-700">{change.modified_content || 'N/A'}</p>
                              </div>
                            </div>
                            <div className="mt-2">
                              <p className="text-xs font-medium text-gray-600 mb-1">Reason for Change:</p>
                              <p className="text-xs text-gray-700">{change.reason_for_change}</p>
                              {change.source_of_information && (
                                <p className="text-xs text-gray-500 mt-1">
                                  <span className="font-medium">Source:</span> {change.source_of_information}
                                </p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {modifications.gaps_identified_and_filled && modifications.gaps_identified_and_filled.length > 0 && (
                      <div className="mt-4">
                        <h5 className="font-medium text-gray-900 mb-3">Gaps Identified and Filled</h5>
                        <div className="space-y-3">
                          {modifications.gaps_identified_and_filled.map((gap: any, gapIndex: number) => (
                            <div
                              key={gapIndex}
                              className={`p-3 rounded-lg border ${
                                gap.priority === 'High'
                                  ? 'bg-red-50 border-red-200'
                                  : gap.priority === 'Med'
                                  ? 'bg-yellow-50 border-yellow-200'
                                  : 'bg-gray-50 border-gray-200'
                              }`}
                            >
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-medium text-gray-900">{gap.gap_item}</span>
                                <span
                                  className={`px-2 py-1 rounded text-xs font-medium ${
                                    gap.priority === 'High'
                                      ? 'bg-red-200 text-red-800'
                                      : gap.priority === 'Med'
                                      ? 'bg-yellow-200 text-yellow-800'
                                      : 'bg-gray-200 text-gray-800'
                                  }`}
                                >
                                  {gap.priority} Priority
                                </span>
                              </div>
                              <p className="text-sm text-gray-600 mb-1">{gap.rationale}</p>
                              <p className="text-xs text-gray-500">{gap.how_filled}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {modifications.jd_keywords_added && modifications.jd_keywords_added.length > 0 && (
                      <div className="mt-4">
                        <h5 className="font-medium text-gray-900 mb-3">JD Keywords Added</h5>
                        <div className="flex flex-wrap gap-2">
                          {modifications.jd_keywords_added.map((kw: any, kwIndex: number) => (
                            <div key={kwIndex} className="p-2 bg-purple-50 rounded border border-purple-200">
                              <p className="text-xs font-medium text-purple-900">{kw.keyword}</p>
                              <p className="text-xs text-gray-600">Added to: {kw.where_added}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Original View Only */}
            {activeView === 'original' && (
              <div className="bg-gray-50 rounded-lg p-6">
                <div className="flex items-center gap-2 mb-4">
                  <FileText className="w-5 h-5 text-gray-600" />
                  <h4 className="font-semibold text-gray-900">Original Project Text</h4>
                </div>
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans max-h-96 overflow-y-auto">
                  {originalText || 'No original text available'}
                </pre>
              </div>
            )}

            {/* Optimized View Only */}
            {activeView === 'optimized' && (
              <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                <div className="flex items-center gap-2 mb-4">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <h4 className="font-semibold text-gray-900">Optimized Project Text</h4>
                </div>
                <div className="text-sm text-gray-700 space-y-4 max-h-96 overflow-y-auto">
                  {optimizedText.goals && (
                    <div>
                      <h5 className="font-medium text-gray-900 mb-2">Goals</h5>
                      <div className="space-y-2">
                        {optimizedText.goals.business_objective && (
                          <p><span className="font-medium">Business Objective:</span> {optimizedText.goals.business_objective}</p>
                        )}
                        {optimizedText.goals.pain_point && (
                          <p><span className="font-medium">Pain Point:</span> {optimizedText.goals.pain_point}</p>
                        )}
                        {optimizedText.goals.background && (
                          <p><span className="font-medium">Background:</span> {optimizedText.goals.background}</p>
                        )}
                        {optimizedText.goals.success_definition && (
                          <p><span className="font-medium">Success Definition:</span> {optimizedText.goals.success_definition}</p>
                        )}
                      </div>
                    </div>
                  )}
                  {optimizedText.methods_solution && (
                    <div>
                      <h5 className="font-medium text-gray-900 mb-2">Methods & Solution</h5>
                      <div className="space-y-2">
                        {optimizedText.methods_solution.selected_approach && (
                          <p><span className="font-medium">Selected Approach:</span> {optimizedText.methods_solution.selected_approach}</p>
                        )}
                        {optimizedText.methods_solution.considered_options && (
                          <div>
                            <span className="font-medium">Considered Options:</span>
                            <ul className="list-disc list-inside ml-2 mt-1">
                              {optimizedText.methods_solution.considered_options.map((opt: string, i: number) => (
                                <li key={i}>{opt}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  {optimizedText.execution_timeline && (
                    <div>
                      <h5 className="font-medium text-gray-900 mb-2">Execution & Timeline</h5>
                      <div className="space-y-2">
                        {optimizedText.execution_timeline.phases && (
                          <div>
                            <span className="font-medium">Phases:</span>
                            <ul className="list-disc list-inside ml-2 mt-1">
                              {optimizedText.execution_timeline.phases.map((phase: string, i: number) => (
                                <li key={i}>{phase}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  {optimizedText.results_metrics && (
                    <div>
                      <h5 className="font-medium text-gray-900 mb-2">Results & Metrics</h5>
                      <div className="space-y-2">
                        {optimizedText.results_metrics.primary_metric && (
                          <p><span className="font-medium">Primary Metric:</span> {optimizedText.results_metrics.primary_metric}</p>
                        )}
                        {optimizedText.results_metrics.secondary_outcomes && (
                          <div>
                            <span className="font-medium">Secondary Outcomes:</span>
                            <ul className="list-disc list-inside ml-2 mt-1">
                              {optimizedText.results_metrics.secondary_outcomes.map((outcome: string, i: number) => (
                                <li key={i}>{outcome}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  {optimizedText.learning_reflection && (
                    <div>
                      <h5 className="font-medium text-gray-900 mb-2">Learning & Reflection</h5>
                      <div className="space-y-2">
                        {optimizedText.learning_reflection.top_lessons && (
                          <div>
                            <span className="font-medium">Top Lessons:</span>
                            <ul className="list-disc list-inside ml-2 mt-1">
                              {optimizedText.learning_reflection.top_lessons.map((lesson: string, i: number) => (
                                <li key={i}>{lesson}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  {!optimizedText.goals && !optimizedText.methods_solution && (
                    <p className="text-gray-500">No optimized text available</p>
                  )}
                </div>
              </div>
            )}

            {/* Resume Summary Bullets */}
            {project.resume_summary_bullets && project.resume_summary_bullets.length > 0 && (
              <div className="mt-6 border-t border-gray-200 pt-6">
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Target className="w-5 h-5 text-primary-600" />
                  Resume Summary Bullets
                </h4>
                <div className="space-y-2">
                  {project.resume_summary_bullets.map((bullet: string, bulletIndex: number) => (
                    <div key={bulletIndex} className="flex items-start gap-3 p-3 bg-primary-50 rounded-lg">
                      <CheckCircle className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" />
                      <p className="text-gray-700">{bullet}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* JD Keywords */}
            {project.jd_keywords_highlighted && project.jd_keywords_highlighted.length > 0 && (
              <div className="mt-6 border-t border-gray-200 pt-6">
                <h4 className="font-semibold text-gray-900 mb-3">JD Keywords Highlighted</h4>
                <div className="flex flex-wrap gap-2">
                  {project.jd_keywords_highlighted.map((keyword: string, kwIndex: number) => (
                    <span
                      key={kwIndex}
                      className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Fallback: Show old format if new format is not available */}
            {!originalText && !optimizedText.goals && project.optimized_version && (
              <div className="space-y-4">
                {project.optimized_version.summary_bullets && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                      <Target className="w-5 h-5 text-primary-600" />
                      Optimized Summary for Resume
                    </h4>
                    <div className="space-y-2">
                      {project.optimized_version.summary_bullets.map((bullet: string, bulletIndex: number) => (
                        <div key={bulletIndex} className="flex items-start gap-3 p-3 bg-primary-50 rounded-lg">
                          <CheckCircle className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" />
                          <p className="text-gray-700">{bullet}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
