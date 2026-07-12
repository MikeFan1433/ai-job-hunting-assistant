"""Offer-toolkit skill frameworks as executable prompt fragments."""

from skill_frameworks.global_principles import GLOBAL_PRINCIPLES_PROMPT
from skill_frameworks.jd_decode import JD_DECODE_PROMPT
from skill_frameworks.match_rubric import MATCH_RUBRIC_PROMPT
from skill_frameworks.go_no_go import GO_NO_GO_PROMPT
from skill_frameworks.org_salary import ORG_SALARY_PROMPT
from skill_frameworks.resume_tailoring import RESUME_TAILORING_PROMPT
from skill_frameworks.bq_prep import BQ_PREP_PROMPT, BQ_ANSWER_PROMPT
from skill_frameworks.interview_predict import (
    INTERVIEW_PREDICT_BEHAVIOR_PROMPT,
    INTERVIEW_PREDICT_TOP10_PROMPT,
)

__all__ = [
    "GLOBAL_PRINCIPLES_PROMPT",
    "JD_DECODE_PROMPT",
    "MATCH_RUBRIC_PROMPT",
    "GO_NO_GO_PROMPT",
    "ORG_SALARY_PROMPT",
    "RESUME_TAILORING_PROMPT",
    "BQ_PREP_PROMPT",
    "BQ_ANSWER_PROMPT",
    "INTERVIEW_PREDICT_BEHAVIOR_PROMPT",
    "INTERVIEW_PREDICT_TOP10_PROMPT",
]
