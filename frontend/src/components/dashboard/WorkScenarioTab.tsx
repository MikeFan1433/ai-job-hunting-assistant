import { Briefcase, Target, AlertTriangle, FileText, Code } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { getUiStrings } from '../../i18n/uiStrings';

interface Props {
  data: any;
}

export default function WorkScenarioTab({ data }: Props) {
  const lang = useAppStore((s) => s.inputs.preferred_lang);
  const ui = getUiStrings(lang);
  const analysis = data?.job_role_team_analysis || {};

  const challenges = analysis.challenges || [];
  const workScenarios = analysis.work_scenarios || [];
  const projectTypes = analysis.project_types || [];
  const methodsTech = analysis.methods_technologies || [];

  const hasContent =
    analysis.team_objectives ||
    challenges.length > 0 ||
    workScenarios.length > 0 ||
    projectTypes.length > 0 ||
    methodsTech.length > 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <Briefcase className="w-6 h-6 text-primary-600" />
        <h2 className="text-2xl font-bold text-gray-900">{ui.workScenario.title}</h2>
      </div>

      {/* 1. Team Objectives */}
      {analysis.team_objectives && (
        <div className="card">
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900">{ui.workScenario.teamObjectives}</h3>
          </div>
          <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{analysis.team_objectives}</p>
        </div>
      )}

      {/* 2. Challenges */}
      {challenges.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <h3 className="text-lg font-semibold text-gray-900">{ui.workScenario.challenges}</h3>
          </div>
          <div className="space-y-3">
            {challenges.map((item: string, index: number) => (
              <div key={index} className="flex items-start gap-3 p-4 bg-amber-50 rounded-lg border-l-4 border-amber-400">
                <div className="flex-shrink-0 w-6 h-6 bg-amber-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  {index + 1}
                </div>
                <p className="text-gray-700 leading-relaxed flex-1">{item}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Work Scenarios */}
      {workScenarios.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Briefcase className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900">{ui.workScenario.scenarios}</h3>
          </div>
          <div className="space-y-3">
            {workScenarios.map((scenario: string, index: number) => (
              <div key={index} className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border-l-4 border-primary-500">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                    {index + 1}
                  </div>
                  <p className="text-gray-700 leading-relaxed flex-1">{scenario}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Project Types */}
      {projectTypes.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <FileText className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900">{ui.workScenario.projectTypes}</h3>
          </div>
          <div className="space-y-3">
            {projectTypes.map((type: string, index: number) => (
              <div key={index} className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                <p className="text-gray-700">{type}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. Methods & Technologies */}
      {methodsTech.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Code className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900">{ui.workScenario.methodsTech}</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {methodsTech.map((method: string, index: number) => (
              <span
                key={index}
                className="px-3 py-1.5 bg-green-100 text-green-800 rounded-full text-sm font-medium"
              >
                {method}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!hasContent && (
        <div className="text-center py-12">
          <Briefcase className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">{ui.workScenario.empty}</p>
        </div>
      )}
    </div>
  );
}
