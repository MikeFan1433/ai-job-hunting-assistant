import { FolderOpen, CheckCircle, AlertCircle, Target } from 'lucide-react';

interface Props {
  data: any;
}

export default function ProjectsTab({ data }: Props) {
  const projects = data?.selected_projects || [];

  if (projects.length === 0) {
    return (
      <div className="text-center py-12">
        <FolderOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No projects available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <FolderOpen className="w-6 h-6 text-primary-600" />
        <h2 className="text-2xl font-bold text-gray-900">Optimized Projects</h2>
        <span className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-medium">
          {projects.length} {projects.length === 1 ? 'Project' : 'Projects'}
        </span>
      </div>

      {projects.map((project: any, index: number) => (
        <div key={index} className="card border-l-4 border-primary-500">
          {/* Project Header */}
          <div className="mb-4">
            <h3 className="text-xl font-bold text-gray-900 mb-2">{project.project_name}</h3>
            <p className="text-sm text-gray-600 mb-3">{project.relevance_reason}</p>
          </div>

          {/* Optimized Summary Bullets */}
          {project.optimized_version?.summary_bullets && (
            <div className="mb-6">
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

          {/* JD Keywords */}
          {project.optimized_version?.jd_keywords_highlighted && (
            <div className="mb-6">
              <h4 className="font-semibold text-gray-900 mb-3">JD Keywords Highlighted</h4>
              <div className="flex flex-wrap gap-2">
                {project.optimized_version.jd_keywords_highlighted.map((keyword: string, kwIndex: number) => (
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

          {/* Gaps Identified */}
          {project.gaps_identified && project.gaps_identified.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-orange-600" />
                Gaps Identified
              </h4>
              <div className="space-y-3">
                {project.gaps_identified.map((gap: any, gapIndex: number) => (
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
                      <span className="font-medium text-gray-900">{gap.item}</span>
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
                    <p className="text-sm text-gray-600">{gap.rationale}</p>
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
