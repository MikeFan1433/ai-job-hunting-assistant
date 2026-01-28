import { Briefcase, HelpCircle } from 'lucide-react';

interface Props {
  data: any;
}

export default function BusinessDomainTab({ data }: Props) {
  if (!data || !data.business_questions || data.business_questions.length === 0) {
    return <div className="text-center py-12 text-gray-600">No business domain questions available</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3 mb-6">
        <Briefcase className="w-6 h-6 text-primary-600" />
        <h2 className="text-2xl font-bold text-gray-900">Business Domain Questions</h2>
        <span className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-medium">
          {data.business_questions.length} Questions
        </span>
      </div>

      <div className="space-y-6">
        {data.business_questions.map((question: any, index: number) => (
          <div key={index} className="card border-l-4 border-indigo-500">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-indigo-600" />
                {index + 1}. {question.question}
              </h3>
              
              {question.why_they_ask_this && (
                <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-sm font-semibold text-blue-900 mb-1">Why They Ask This:</p>
                  <p className="text-sm text-blue-800">{question.why_they_ask_this}</p>
                </div>
              )}
            </div>

            {question.sample_answer && (
              <div className="mb-4">
                <p className="text-sm font-semibold text-gray-900 mb-2">Sample Answer:</p>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                    {question.sample_answer}
                  </p>
                </div>
              </div>
            )}

            {question.key_points && question.key_points.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-gray-900 mb-2">Key Points:</p>
                <ul className="space-y-1">
                  {question.key_points.map((point: string, pointIndex: number) => (
                    <li key={pointIndex} className="text-sm text-gray-700 flex items-start gap-2">
                      <span className="text-indigo-600 mt-1">•</span>
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {question.related_jd_requirements && question.related_jd_requirements.length > 0 && (
              <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
                <p className="text-sm font-semibold text-green-900 mb-2">Related JD Requirements:</p>
                <ul className="space-y-1">
                  {question.related_jd_requirements.map((req: string, reqIndex: number) => (
                    <li key={reqIndex} className="text-sm text-green-800">• {req}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
