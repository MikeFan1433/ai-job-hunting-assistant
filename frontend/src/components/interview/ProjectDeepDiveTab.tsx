import { FolderOpen, HelpCircle, Target } from 'lucide-react';

interface Props {
  data: any;
}

export default function ProjectDeepDiveTab({ data }: Props) {
  if (!data || !data.selected_projects || data.selected_projects.length === 0) {
    return <div className="text-center py-12 text-gray-600">No project deep-dive data available</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3 mb-6">
        <FolderOpen className="w-6 h-6 text-primary-600" />
        <h2 className="text-2xl font-bold text-gray-900">Project Deep-Dive Questions</h2>
        <span className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-medium">
          {data.selected_projects.length} {data.selected_projects.length === 1 ? 'Project' : 'Projects'}
        </span>
      </div>

      {data.selected_projects.map((project: any, index: number) => (
        <div key={index} className="card border-l-4 border-primary-500">
          {/* Project Overview */}
          <div className="mb-6">
            <h3 className="text-xl font-bold text-gray-900 mb-3">{project.project_name}</h3>
            
            {project.star_overview && (
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 mb-4">
                <p className="text-sm font-semibold text-blue-900 mb-2">STAR Overview:</p>
                <p className="text-gray-700 whitespace-pre-wrap">{project.star_overview}</p>
              </div>
            )}
          </div>

          {/* Technical Deep-Dive Questions */}
          {project.technical_deep_dive_questions && project.technical_deep_dive_questions.length > 0 && (
            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-primary-600" />
                Technical Deep-Dive Questions ({project.technical_deep_dive_questions.length})
              </h4>
              <div className="space-y-6">
                {project.technical_deep_dive_questions.map((question: any, qIndex: number) => (
                  <div key={qIndex} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <div className="mb-3">
                      <h5 className="font-semibold text-gray-900 mb-1">
                        {qIndex + 1}. {question.question}
                      </h5>
                      {question.why_they_ask_this && (
                        <p className="text-sm text-gray-600">{question.why_they_ask_this}</p>
                      )}
                    </div>

                    {question.answer_approach && (
                      <div className="mt-3 p-3 bg-white rounded border border-gray-300">
                        <p className="text-sm font-semibold text-gray-900 mb-2">Answer Approach:</p>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{question.answer_approach}</p>
                      </div>
                    )}

                    {question.key_points && question.key_points.length > 0 && (
                      <div className="mt-3">
                        <p className="text-sm font-semibold text-gray-900 mb-2">Key Points:</p>
                        <ul className="space-y-1">
                          {question.key_points.map((point: string, pointIndex: number) => (
                            <li key={pointIndex} className="text-sm text-gray-700 flex items-start gap-2">
                              <Target className="w-4 h-4 text-primary-600 flex-shrink-0 mt-0.5" />
                              <span>{point}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
