"""Handoff validation and context guardrails between search agent and orchestrator."""

import json
import re
import config

MAX_HANDOFF_CHARS = 8000
MAX_SUMMARY_WORDS = 80
TOOL_RESULT_MAX_CHARS = 3000


def truncate_tool_result(content: str, max_chars: int = TOOL_RESULT_MAX_CHARS) -> str:
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "\n...[truncated for context limit]"


def _trim_summary(summary: str) -> str:
    words = summary.split()
    if len(words) <= MAX_SUMMARY_WORDS:
        return summary
    return " ".join(words[:MAX_SUMMARY_WORDS]) + "..."


def parse_search_handoff(content: str) -> dict:
    """Extract JSON handoff from the search agent's final message."""
    if not content or not content.strip():
        raise ValueError("Empty search agent response")

    text = content.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in search agent response")

    return json.loads(text[start:end + 1])


def validate_and_trim_handoff(data: dict) -> dict:
    articles = data.get("articles")
    if not isinstance(articles, list):
        raise ValueError("Handoff must contain an 'articles' list")

    trimmed = []
    for article in articles[:config.MAX_ARTICLES]:
        if not isinstance(article, dict):
            continue
        title = str(article.get("title", "")).strip()
        summary = _trim_summary(str(article.get("summary", "")).strip())
        url = str(article.get("url", "")).strip()
        if title and summary and url:
            trimmed.append({"title": title, "summary": summary, "url": url})

    result = {"articles": trimmed}
    coverage_note = data.get("coverage_note")
    if coverage_note:
        result["coverage_note"] = str(coverage_note).strip()

    payload = json.dumps(result, ensure_ascii=False)
    if len(payload) > MAX_HANDOFF_CHARS:
        raise ValueError(f"Handoff exceeds {MAX_HANDOFF_CHARS} chars after trimming")

    return result
