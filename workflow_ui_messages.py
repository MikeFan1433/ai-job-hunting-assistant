"""Bilingual workflow progress messages for SSE/polling (matches preferred_lang)."""
from typing import Optional

from llm_output_language import prefers_zh

_MESSAGES: dict[str, tuple[str, str]] = {
    # (English, Chinese)
    "startup": ("Validating input and starting analysis...", "正在校验输入并启动分析..."),
    "agent1_validate": ("Validating resume and inputs...", "正在校验简历与输入内容..."),
    "agent2_after_validation": ("Validation passed. Analyzing JD and resume...", "验证通过，正在分析 JD 与简历..."),
    "agent2_prep": ("Preparing JD analysis...", "正在准备 JD 分析..."),
    "agent2_analyzing": ("Analyzing job description and candidate fit...", "正在分析岗位描述与候选人匹配度..."),
    "agent2_done": ("JD analysis complete", "JD 分析完成"),
    "agent3_skip": ("No project materials; skipping project packaging...", "未提供项目材料，跳过项目包装..."),
    "agent3_skip_detail": (
        "Project supplement was empty; project packaging was skipped.",
        "未填写项目补充信息，已跳过项目包装",
    ),
    "agent3_running": ("Optimizing project descriptions...", "正在优化项目描述..."),
    "agent4_gen": ("Generating resume optimization suggestions...", "正在生成简历优化建议..."),
    "agent4_gap": ("Analyzing resume–role fit gaps...", "正在分析简历与岗位的匹配差距..."),
    "agent4_done": ("Resume optimization suggestions ready", "简历优化建议生成完成"),
    "resume_final": ("Generating optimized resume...", "正在生成优化后的简历..."),
    "agent5_gen": ("Generating interview preparation...", "正在生成面试准备材料..."),
    "agent5_analyze": ("Analyzing interview questions and answer strategies...", "正在分析面试问题与回答策略..."),
    "agent5_done": ("Interview preparation complete", "面试准备材料生成完成"),
    "workflow_done": ("All analysis complete!", "全部分析完成！"),
    "completed_poll": ("Workflow completed successfully!", "工作流已完成！"),
    "interview_prep": ("Preparing interview materials...", "正在准备面试材料..."),
    "interview_generating": ("Generating behavioral interview questions...", "正在生成行为面试题与策略..."),
    "interview_done": ("Interview preparation completed!", "面试准备已完成！"),
}


def workflow_progress_message(preferred_lang: Optional[str], key: str) -> str:
    pair = _MESSAGES.get(key)
    if not pair:
        return ""
    en, zh = pair
    return zh if prefers_zh(preferred_lang) else en
