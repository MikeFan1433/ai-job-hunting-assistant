import { Briefcase, Clock, Users, Target } from 'lucide-react';

interface Props {
  data: any;
}

export default function WorkScenarioTab({ data }: Props) {
  const analysis = data?.job_role_team_analysis || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <Briefcase className="w-6 h-6 text-primary-600" />
        <h2 className="text-2xl font-bold text-gray-900">Work Scenario Analysis</h2>
      </div>

      {/* Daily Activities */}
      {analysis.daily_activities && analysis.daily_activities.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Clock className="w-5 h-5 text-primary-600" />
            Daily Activities
          </h3>
          <div className="space-y-3">
            {analysis.daily_activities.map((activity: string, index: number) => (
              <div key={index} className="card">
                <p className="text-gray-700">{activity}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Work Scenarios */}
      {analysis.work_scenarios && analysis.work_scenarios.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-primary-600" />
            Typical Work Scenarios
          </h3>
          <div className="space-y-4">
            {analysis.work_scenarios.map((scenario: string, index: number) => (
              <div key={index} className="card border-l-4 border-primary-500">
                <p className="text-gray-700">{scenario}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Project Types */}
      {analysis.project_types && analysis.project_types.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Project Types</h3>
          <div className="flex flex-wrap gap-2">
            {analysis.project_types.map((type: string, index: number) => (
              <span
                key={index}
                className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
              >
                {type}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Methods & Tools */}
      {analysis.methods && analysis.methods.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Methods & Tools</h3>
          <div className="flex flex-wrap gap-2">
            {analysis.methods.map((method: string, index: number) => (
              <span
                key={index}
                className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium"
              >
                {method}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* KPIs */}
      {analysis.kpis && analysis.kpis.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Target className="w-5 h-5 text-primary-600" />
            Key Performance Indicators (KPIs)
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {analysis.kpis.map((kpi: string, index: number) => (
              <div key={index} className="card bg-yellow-50 border-yellow-200">
                <p className="text-gray-700 font-medium">{kpi}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Team Objectives */}
      {analysis.team_objectives && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Users className="w-5 h-5 text-primary-600" />
            Team Objectives
          </h3>
          <div className="card">
            <p className="text-gray-700 whitespace-pre-wrap">{analysis.team_objectives}</p>
          </div>
        </div>
      )}
    </div>
  );
}
