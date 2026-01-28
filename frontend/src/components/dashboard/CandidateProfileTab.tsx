import { User } from 'lucide-react';

interface Props {
  data: any;
}

export default function CandidateProfileTab({ data }: Props) {
  const profile = data?.ideal_candidate_profile || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <User className="w-6 h-6 text-primary-600" />
        <h2 className="text-2xl font-bold text-gray-900">Ideal Candidate Profile</h2>
      </div>

      {/* Required Experience */}
      {profile.required_experience && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Required Experience</h3>
          <div className="card">
            <p className="text-gray-700 whitespace-pre-wrap">{profile.required_experience}</p>
          </div>
        </div>
      )}

      {/* Required Skills */}
      {profile.required_skills && profile.required_skills.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Required Skills</h3>
          <div className="flex flex-wrap gap-2">
            {profile.required_skills.map((skill: string, index: number) => (
              <span
                key={index}
                className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-medium"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Preferred Project Portfolio */}
      {profile.preferred_project_portfolio && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Preferred Project Portfolio</h3>
          <div className="card">
            <p className="text-gray-700 whitespace-pre-wrap">
              {profile.preferred_project_portfolio}
            </p>
          </div>
        </div>
      )}

      {/* Industry Experience */}
      {profile.industry_experience && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Industry Experience</h3>
          <div className="card">
            <p className="text-gray-700 whitespace-pre-wrap">{profile.industry_experience}</p>
          </div>
        </div>
      )}

      {/* Education & Certifications */}
      {profile.education_certifications && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Education & Certifications</h3>
          <div className="card">
            <p className="text-gray-700 whitespace-pre-wrap">
              {profile.education_certifications}
            </p>
          </div>
        </div>
      )}

      {/* Soft Skills */}
      {profile.soft_skills && profile.soft_skills.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Soft Skills</h3>
          <div className="flex flex-wrap gap-2">
            {profile.soft_skills.map((skill: string, index: number) => (
              <span
                key={index}
                className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
