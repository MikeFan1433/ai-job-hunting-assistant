"""Append user-message instructions so LLM JSON narrative matches UI language (en | zh)."""
from typing import Optional


def prefers_zh(preferred_lang: Optional[str]) -> bool:
    return (preferred_lang or "en").strip().lower().startswith("zh")


def output_language_suffix(preferred_lang: Optional[str]) -> str:
    if prefers_zh(preferred_lang):
        return (
            "\n\n=== 输出语言 ===\n"
            "所有面向用户的 JSON 字符串值（说明、分析、理由、列表项文本等）必须使用简体中文。\n"
            "JSON 的字段名必须与给定 schema 完全一致，不要翻译字段名。"
        )
    return (
        "\n\n=== OUTPUT LANGUAGE ===\n"
        "All user-facing string values in the JSON (descriptions, analyses, rationales, list item text, etc.) must be in English.\n"
        "Keep JSON property names exactly as in the schema; do not translate keys."
    )
