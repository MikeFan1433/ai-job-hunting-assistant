import { BarChart3, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';

interface Props {
  data: any;
}

export default function MatchAnalysisTab({ data }: Props) {
  const matchAssessment = data?.match_assessment || {};
  const overallScore = parseFloat(matchAssessment.overall_match_score || '0');
  const experienceScore = parseFloat(matchAssessment.experience_match_score || '0');
  const skillsScore = parseFloat(matchAssessment.skills_match_score || '0');
  const educationScore = parseFloat(matchAssessment.education_match_score || '0');

  const getScoreColor = (score: number) => {
    if (score >= 4) return 'text-green-600';
    if (score >= 3) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 4) return 'bg-green-100';
    if (score >= 3) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <BarChart3 className="w-6 h-6 text-primary-600" />
        <h2 className="text-2xl font-bold text-gray-900">Match Analysis</h2>
      </div>

      {/* Overall Score */}
      <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-lg p-6 border border-primary-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Overall Match Score</h3>
          <div className={`text-4xl font-bold ${getScoreColor(overallScore)}`}>
            {overallScore.toFixed(1)} / 5.0
          </div>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4">
          <div
            className={`h-4 rounded-full transition-all ${getScoreBgColor(overallScore)}`}
            style={{ width: `${(overallScore / 5) * 100}%` }}
          />
        </div>
        <p className="text-sm text-gray-600 mt-2">
          {matchAssessment.match_level || 'Moderate match'}
        </p>
      </div>

      {/* Detailed Scores */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Experience</span>
            <span className={`text-lg font-bold ${getScoreColor(experienceScore)}`}>
              {experienceScore.toFixed(1)}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${getScoreBgColor(experienceScore)}`}
              style={{ width: `${(experienceScore / 5) * 100}%` }}
            />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Skills</span>
            <span className={`text-lg font-bold ${getScoreColor(skillsScore)}`}>
              {skillsScore.toFixed(1)}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${getScoreBgColor(skillsScore)}`}
              style={{ width: `${(skillsScore / 5) * 100}%` }}
            />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Education</span>
            <span className={`text-lg font-bold ${getScoreColor(educationScore)}`}>
              {educationScore.toFixed(1)}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${getScoreBgColor(educationScore)}`}
              style={{ width: `${(educationScore / 5) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Strengths */}
      {matchAssessment.strengths && matchAssessment.strengths.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-600" />
            Strengths
          </h3>
          <div className="space-y-2">
            {matchAssessment.strengths.map((strength: string, index: number) => (
              <div key={index} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="w-2 h-2 bg-green-600 rounded-full mt-2 flex-shrink-0" />
                <p className="text-gray-700">{strength}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Gaps */}
      {matchAssessment.gaps && matchAssessment.gaps.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <TrendingDown className="w-5 h-5 text-orange-600" />
            Gaps & Improvement Areas
          </h3>
          <div className="space-y-2">
            {matchAssessment.gaps.map((gap: string, index: number) => (
              <div key={index} className="flex items-start gap-3 p-3 bg-orange-50 rounded-lg border border-orange-200">
                <AlertCircle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                <p className="text-gray-700">{gap}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Competitive Analysis */}
      {matchAssessment.competitive_advantages && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Competitive Advantages</h3>
          <div className="space-y-2">
            {matchAssessment.competitive_advantages.map((advantage: string, index: number) => (
              <div key={index} className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-gray-700">{advantage}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
