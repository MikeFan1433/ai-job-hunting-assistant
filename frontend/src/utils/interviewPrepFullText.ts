import type { getUiStrings } from '../i18n/uiStrings';

type Ui = ReturnType<typeof getUiStrings>;

/** Plain-text export of all interview prep sections as if every accordion were expanded. */
export function buildInterviewPrepFullExportText(data: any, ui: Ui): string {
  const out: string[] = [];
  const sep = () => out.push('');
  const behavioral = data.theme_1_behavioral_interview || {};
  const projectDeepDive = data.theme_2_project_deep_dive || {};
  const businessDomain = data.theme_3_business_domain || {};
  const summary = data.preparation_summary || {};

  const selfIntro = behavioral.self_introduction || {};
  const storytelling = behavioral.storytelling_example || {};
  const behavioralQs = behavioral.top_10_behavioral_questions || [];
  const projects = projectDeepDive.selected_projects || [];
  const businessQs = businessDomain.business_questions || [];

  out.push(ui.interview.selfIntro.toUpperCase());
  sep();
  if (selfIntro.full_text || selfIntro.paragraph_1) {
    const body =
      selfIntro.full_text ||
      [selfIntro.paragraph_1, selfIntro.paragraph_2, selfIntro.paragraph_3].filter(Boolean).join('\n\n');
    out.push(body);
    sep();
    if (selfIntro.key_highlights?.length) {
      out.push(ui.interview.highlights);
      selfIntro.key_highlights.forEach((h: string) => out.push(`• ${h}`));
      sep();
    }
  }

  if (storytelling.full_storytelling_answer || storytelling.hook) {
    const sub =
      storytelling.project_name || storytelling.selected_project?.project_name
        ? ` — ${storytelling.project_name || storytelling.selected_project?.project_name}`
        : '';
    out.push(`${ui.interview.storyTitle}${sub}`.toUpperCase());
    sep();
    if (storytelling.full_storytelling_answer) {
      out.push(storytelling.full_storytelling_answer);
    } else {
      if (storytelling.hook) {
        out.push(`${ui.interview.hook}\n${storytelling.hook}`);
      }
      if (storytelling.emergency) {
        out.push(`${ui.interview.emergency}\n${storytelling.emergency}`);
      }
      if (storytelling.approach) {
        out.push(`${ui.interview.approach}\n${storytelling.approach}`);
      }
      if (storytelling.action) {
        out.push(`${ui.interview.action}\n${storytelling.action}`);
      }
      if (storytelling.impact) {
        out.push(`${ui.interview.impact}\n${storytelling.impact}`);
      }
      if (storytelling.reflection) {
        out.push(`${ui.interview.reflection}\n${storytelling.reflection}`);
      }
    }
    sep();
    if (storytelling.jd_skills_demonstrated?.length) {
      out.push(storytelling.jd_skills_demonstrated.join(' · '));
      sep();
    }
  }

  if (behavioralQs.length > 0) {
    out.push(ui.interview.behavioralTitle(behavioralQs.length).toUpperCase());
    sep();
    behavioralQs.forEach((q: any, i: number) => {
      out.push(`Q${i + 1}: ${q.question || ''}`);
      if (q.why_they_ask_this) {
        out.push(`${ui.interview.whyAsk} ${q.why_they_ask_this}`);
      }
      if (q.answer_framework?.length) {
        out.push(ui.interview.framework);
        q.answer_framework.forEach((step: string, j: number) => out.push(`  ${j + 1}. ${step}`));
      } else if (q.sample_answer) {
        out.push(`${ui.interview.sampleAnswer}\n${q.sample_answer}`);
      }
      if (q.key_points_to_emphasize?.length) {
        out.push(ui.interview.keyPoints);
        q.key_points_to_emphasize.forEach((p: string) => out.push(`• ${p}`));
      }
      sep();
    });
  }

  if (projects.length > 0) {
    out.push(ui.interview.projectTitle(projects.length).toUpperCase());
    sep();
    projects.forEach((proj: any, pi: number) => {
      out.push(`=== ${proj.project_name || `Project ${pi + 1}`} ===`);
      const overview = proj.project_overview_star || {};
      const scenario = proj.answer_scenario || {};
      const whyJd = String(scenario.why_important_for_jd || '').trim();
      const whenTell = String(scenario.when_to_use_in_interview || '').trim();
      if (whyJd || whenTell) {
        out.push(ui.interview.answerScenarioTitle);
        if (whyJd) {
          out.push(`${ui.interview.whyImportantJd}\n${whyJd}`);
        }
        if (whenTell) {
          out.push(`${ui.interview.whenToTell}\n${whenTell}`);
        }
        sep();
      }
      const starBlocks = [
        { key: 'situation' as const, label: ui.interview.starSituation },
        { key: 'task' as const, label: ui.interview.starTask },
        { key: 'action' as const, label: ui.interview.starAction },
        { key: 'result' as const, label: ui.interview.starResult },
      ];
      const hasStarBody = starBlocks.some(({ key }) => String(overview[key] || '').trim());
      const legacyOverview = String(overview.full_overview_answer || proj.project_overview_answer || '').trim();
      if (hasStarBody) {
        starBlocks.forEach(({ key, label }) => {
          const text = String(overview[key] || '').trim();
          if (text) {
            out.push(`${label}\n${text}`);
            sep();
          }
        });
      } else if (legacyOverview) {
        out.push(`${ui.interview.starSummary}\n${legacyOverview}`);
        sep();
      }
      const questions = proj.technical_deep_dive_questions || proj.deep_dive_questions || [];
      questions.forEach((dq: any, qi: number) => {
        out.push(`Q${qi + 1}: ${dq.question || ''}`);
        if (dq.why_they_ask_this) {
          out.push(dq.why_they_ask_this);
        }
        if (dq.how_to_answer?.structure) {
          const arr = Array.isArray(dq.how_to_answer.structure)
            ? dq.how_to_answer.structure
            : [dq.how_to_answer.structure];
          out.push(ui.interview.answerStructure);
          arr.forEach((s: string, si: number) => out.push(`  ${si + 1}. ${s}`));
        }
        if (dq.how_to_answer?.key_points?.length) {
          out.push(ui.interview.points);
          dq.how_to_answer.key_points.forEach((p: string) => out.push(`• ${p}`));
        }
        sep();
      });
      if (proj.most_important_takeaways?.length) {
        out.push(ui.interview.corePoints);
        proj.most_important_takeaways.forEach((t: string) => out.push(`• ${t}`));
        sep();
      }
    });
  }

  if (businessQs.length > 0) {
    out.push(ui.interview.businessTitle(businessQs.length).toUpperCase());
    sep();
    businessQs.forEach((q: any, i: number) => {
      out.push(`Q${i + 1}: ${q.question || ''}`);
      if (q.why_they_ask_this) {
        out.push(q.why_they_ask_this);
      }
      if (q.how_to_answer?.structure) {
        const arr = Array.isArray(q.how_to_answer.structure)
          ? q.how_to_answer.structure
          : [q.how_to_answer.structure];
        out.push(ui.interview.answerStructure);
        arr.forEach((s: string, si: number) => out.push(`  ${si + 1}. ${s}`));
      }
      if (q.how_to_answer?.key_points?.length) {
        out.push(ui.interview.points);
        q.how_to_answer.key_points.forEach((p: string) => out.push(`• ${p}`));
      }
      sep();
    });
  }

  const rounds = data.theme_rounds || {};
  ['recruiter_round', 'hiring_manager_round', 'leader_round'].forEach((roundKey) => {
    const r = rounds[roundKey];
    if (!r?.typical_questions?.length) return;
    out.push(`=== ${r.round_name || roundKey} ===`);
    sep();
    r.typical_questions.forEach((tq: any, i: number) => {
      out.push(`Q${i + 1}: ${tq.question || ''}`);
      if (tq.why_asked) {
        out.push(`${ui.interview.whyAsk} ${tq.why_asked}`);
      }
      if (tq.answer_framework) {
        out.push(String(tq.answer_framework));
      }
      sep();
    });
  });

  if (summary.key_preparation_focus_areas?.length || summary.final_preparation_advice) {
    out.push(ui.interview.prepSummary.toUpperCase());
    sep();
    out.push(
      `${ui.interview.countBehavioral}: ${summary.total_behavioral_questions ?? 0} | ${ui.interview.countProject}: ${summary.total_projects_analyzed ?? 0} | ${ui.interview.countBusiness}: ${summary.total_business_questions ?? 0} | ${ui.interview.countTechnical}: ${summary.total_project_deep_dive_questions ?? summary.total_technical_questions ?? 0}`
    );
    sep();
    if (summary.key_preparation_focus_areas?.length) {
      out.push(ui.interview.focusAreas);
      summary.key_preparation_focus_areas.forEach((a: string) => out.push(`• ${a}`));
      sep();
    }
    if (summary.strongest_stories_to_lead_with?.length) {
      out.push(ui.interview.bestStory);
      summary.strongest_stories_to_lead_with.forEach((s: string) => out.push(`• ${s}`));
      sep();
    }
    if (summary.final_preparation_advice) {
      out.push(summary.final_preparation_advice);
    }
  }

  return out.join('\n').trim();
}
