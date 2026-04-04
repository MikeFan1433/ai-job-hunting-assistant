import { useMemo } from 'react';
import { User, Briefcase, Code, Users, Award } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { getUiStrings } from '../../i18n/uiStrings';

interface Props {
  data: any;
}

type SkillRow = { skill: string; why_critical?: string };

function normalizeSkillRows(raw: unknown): SkillRow[] {
  if (!Array.isArray(raw)) return [];
  const out: SkillRow[] = [];
  for (const x of raw) {
    if (typeof x === 'string' && x.trim()) {
      out.push({ skill: x.trim() });
      continue;
    }
    if (x && typeof x === 'object') {
      const o = x as Record<string, unknown>;
      const skill = String(o.skill ?? '').trim();
      if (!skill) continue;
      let why = o.why_critical ?? o.details ?? o.importance;
      let wc = typeof why === 'string' ? why.trim() : '';
      if (!wc && typeof o.manifestation === 'string') wc = o.manifestation.trim();
      out.push({ skill, why_critical: wc });
    }
  }
  return out;
}

function hardSkillsFromProfile(profile: Record<string, unknown>): SkillRow[] {
  const top = normalizeSkillRows(profile.hard_skills_top5);
  if (top.length > 0) return top.slice(0, 5);
  const must = (profile.hard_skills as { must_have?: unknown } | undefined)?.must_have;
  return normalizeSkillRows(must).slice(0, 5);
}

export default function CandidateProfileTab({ data }: Props) {
  const lang = useAppStore((s) => s.inputs.preferred_lang);
  const ui = getUiStrings(lang);
  const profile = data?.ideal_candidate_profile || {};

  const hardSkillsTop5 = useMemo(
    () => hardSkillsFromProfile(profile as Record<string, unknown>),
    [profile]
  );
  const softSkillsTop5 = useMemo(
    () => normalizeSkillRows((profile as Record<string, unknown>).soft_skills_top5).slice(0, 5),
    [profile]
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <User className="w-6 h-6 text-primary-600" />
        <h2 className="text-2xl font-bold text-gray-900">{ui.candidateProfile.title}</h2>
      </div>

      {/* Overall Experience & Traits */}
      {profile.overall_experience_traits && (
        <div className="card">
          <div className="flex items-center gap-2 mb-3">
            <Award className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900">{ui.candidateProfile.overall}</h3>
          </div>
          <p className="text-gray-700 leading-relaxed">{profile.overall_experience_traits}</p>
        </div>
      )}

      {/* Industry Experience */}
      {profile.industry_experience && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Briefcase className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900">{ui.candidateProfile.industry}</h3>
          </div>
          {profile.industry_experience.industry_background && (
            <div className="mb-4">
              <h4 className="font-medium text-gray-900 mb-2">{ui.candidateProfile.industryBg}</h4>
              <div className="space-y-2">
                {(Array.isArray(profile.industry_experience.industry_background) ? profile.industry_experience.industry_background : []).map((item: string, index: number) => (
                  <div key={index} className="flex items-start gap-2 p-2 bg-blue-50 rounded border border-blue-200">
                    <div className="w-1.5 h-1.5 bg-blue-600 rounded-full mt-1.5 flex-shrink-0" />
                    <p className="text-sm text-gray-700">{item}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          {profile.industry_experience.customer_business_context && (
            <div className="mb-4">
              <h4 className="font-medium text-gray-900 mb-2">{ui.candidateProfile.customerCtx}</h4>
              <div className="space-y-2">
                {(Array.isArray(profile.industry_experience.customer_business_context) ? profile.industry_experience.customer_business_context : []).map((item: string, index: number) => (
                  <div key={index} className="flex items-start gap-2 p-2 bg-green-50 rounded border border-green-200">
                    <div className="w-1.5 h-1.5 bg-green-600 rounded-full mt-1.5 flex-shrink-0" />
                    <p className="text-sm text-gray-700">{item}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          {profile.industry_experience.business_model_familiarity && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">{ui.candidateProfile.businessModel}</h4>
              <div className="space-y-2">
                {(Array.isArray(profile.industry_experience.business_model_familiarity) ? profile.industry_experience.business_model_familiarity : []).map((item: string, index: number) => (
                  <div key={index} className="flex items-start gap-2 p-2 bg-purple-50 rounded border border-purple-200">
                    <div className="w-1.5 h-1.5 bg-purple-600 rounded-full mt-1.5 flex-shrink-0" />
                    <p className="text-sm text-gray-700">{item}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Hard Skills Top 5 */}
      {hardSkillsTop5.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Code className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900">{ui.candidateProfile.hardTop5}</h3>
          </div>
          <div className="space-y-4">
            {hardSkillsTop5.map((skill: any, index: number) => (
              <div key={index} className="p-4 bg-gradient-to-r from-red-50 to-orange-50 rounded-lg border border-red-200">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-red-600 text-white rounded-full flex items-center justify-center font-bold">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 mb-2">{skill.skill}</h4>
                    {skill.why_critical && (
                      <p className="text-sm text-gray-700">
                        {skill.why_critical}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Soft Skills Top 5 */}
      {softSkillsTop5.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900">{ui.candidateProfile.softTop5}</h3>
          </div>
          <div className="space-y-4">
            {softSkillsTop5.map((skill: any, index: number) => (
              <div key={index} className="p-4 bg-gradient-to-r from-primary-50 to-blue-50 rounded-lg border border-primary-200">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 mb-2">{skill.skill}</h4>
                    {skill.why_critical ? (
                      <p className="text-sm text-gray-700">{skill.why_critical}</p>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fallback for legacy format */}
      {!profile.overall_experience_traits && !profile.industry_experience && (
        <>
          {profile.required_experience && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Required Experience</h3>
              <p className="text-gray-700 whitespace-pre-wrap">{profile.required_experience}</p>
            </div>
          )}

          {profile.required_skills && profile.required_skills.length > 0 && (
            <div className="card">
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
        </>
      )}
    </div>
  );
}
