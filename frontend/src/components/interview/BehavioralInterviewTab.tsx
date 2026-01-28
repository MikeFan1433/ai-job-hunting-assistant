import { User, BookOpen, HelpCircle } from 'lucide-react';

interface Props {
  data: any;
}

export default function BehavioralInterviewTab({ data }: Props) {
  if (!data) {
    return <div className="text-center py-12 text-gray-600">No behavioral interview data available</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3 mb-6">
        <User className="w-6 h-6 text-primary-600" />
        <h2 className="text-2xl font-bold text-gray-900">Behavioral Interview Preparation</h2>
      </div>

      {/* Self Introduction */}
      {data.self_introduction && (
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <User className="w-5 h-5 text-primary-600" />
            Self-Introduction
          </h3>
          <div className="card bg-blue-50 border-blue-200">
            {data.self_introduction.full_text ? (
              <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                {data.self_introduction.full_text}
              </p>
            ) : (
              <div className="space-y-3">
                {data.self_introduction.paragraph_1 && (
                  <p className="text-gray-700">{data.self_introduction.paragraph_1}</p>
                )}
                {data.self_introduction.paragraph_2 && (
                  <p className="text-gray-700">{data.self_introduction.paragraph_2}</p>
                )}
                {data.self_introduction.paragraph_3 && (
                  <p className="text-gray-700">{data.self_introduction.paragraph_3}</p>
                )}
              </div>
            )}
            {data.self_introduction.key_highlights && data.self_introduction.key_highlights.length > 0 && (
              <div className="mt-4 pt-4 border-t border-blue-300">
                <p className="text-sm font-semibold text-gray-900 mb-2">Key Highlights:</p>
                <ul className="space-y-1">
                  {data.self_introduction.key_highlights.map((highlight: string, index: number) => (
                    <li key={index} className="text-sm text-gray-700">• {highlight}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Storytelling Example */}
      {data.storytelling_example && (
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-primary-600" />
            Storytelling Answer Template
          </h3>
          <div className="card space-y-4">
            {data.storytelling_example.full_storytelling_answer ? (
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                  {data.storytelling_example.full_storytelling_answer}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {data.storytelling_example.hook && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Hook:</h4>
                    <p className="text-gray-700 bg-yellow-50 p-3 rounded-lg">{data.storytelling_example.hook}</p>
                  </div>
                )}
                {data.storytelling_example.emergency && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Emergency:</h4>
                    <p className="text-gray-700 bg-red-50 p-3 rounded-lg">{data.storytelling_example.emergency}</p>
                  </div>
                )}
                {data.storytelling_example.approach && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Approach:</h4>
                    <p className="text-gray-700 bg-blue-50 p-3 rounded-lg">{data.storytelling_example.approach}</p>
                  </div>
                )}
                {data.storytelling_example.action && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Action:</h4>
                    <p className="text-gray-700 bg-green-50 p-3 rounded-lg">{data.storytelling_example.action}</p>
                  </div>
                )}
                {data.storytelling_example.impact && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Impact:</h4>
                    <p className="text-gray-700 bg-purple-50 p-3 rounded-lg">{data.storytelling_example.impact}</p>
                  </div>
                )}
                {data.storytelling_example.reflection && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Reflection:</h4>
                    <p className="text-gray-700 bg-indigo-50 p-3 rounded-lg">{data.storytelling_example.reflection}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Top 10 Behavioral Questions */}
      {data.top_10_behavioral_questions && data.top_10_behavioral_questions.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-primary-600" />
            Top 10 Behavioral Questions
          </h3>
          <div className="space-y-6">
            {data.top_10_behavioral_questions.map((question: any, index: number) => (
              <div key={index} className="card border-l-4 border-primary-500">
                <div className="flex items-start justify-between mb-3">
                  <h4 className="text-lg font-semibold text-gray-900">
                    {index + 1}. {question.question}
                  </h4>
                </div>

                {question.why_they_ask_this && (
                  <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-sm font-semibold text-blue-900 mb-1">Why They Ask This:</p>
                    <p className="text-sm text-blue-800">{question.why_they_ask_this}</p>
                  </div>
                )}

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

                {question.key_points_to_emphasize && question.key_points_to_emphasize.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-gray-900 mb-2">Key Points to Emphasize:</p>
                    <ul className="space-y-1">
                      {question.key_points_to_emphasize.map((point: string, pointIndex: number) => (
                        <li key={pointIndex} className="text-sm text-gray-700 flex items-start gap-2">
                          <span className="text-primary-600 mt-1">•</span>
                          <span>{point}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {question.treat_principles_applied && (
                  <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
                    <p className="text-sm font-semibold text-green-900 mb-2">TREAT Principles Applied:</p>
                    <div className="space-y-1 text-sm text-green-800">
                      {Object.entries(question.treat_principles_applied).map(([key, value]: [string, any]) => (
                        <div key={key}>
                          <span className="font-semibold">{key}:</span> {value}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
