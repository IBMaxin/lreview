"""LLM review pass - returns structured issues from a diff chunk."""
import json
import logging
from dataclasses import dataclass

import ollama

logger = logging.getLogger(__name__)

REVIEW_SYSTEM = """You are a senior code reviewer. Analyze the git diff and return ONLY a JSON array.
Each element must have these exact keys:
  file (str), line (int or null), severity (\"error\"|\"warning\"|\"info\"),
  issue (str, <=120 chars), suggestion (str, <=200 chars)
Return [] if no issues. No markdown fences, no explanation - raw JSON only."""


@dataclass
class Issue:
    """A single code review issue."""
    file: str
    line: int | None
    severity: str
    issue: str
    suggestion: str


def review_chunk(
    chunk_hunk: str,
    model: str,
    temperature: float = 0.2,
    timeout: int = 60,
) -> list[Issue]:
    """Send a diff chunk to the LLM and parse structured issues.

    Args:
        chunk_hunk: Unified diff string for one file/hunk.
        model: Ollama model name.
        temperature: Sampling temperature.
        timeout: Request timeout in seconds.

    Returns:
        List of Issue dataclasses.
    """
    prompt = f"Review this diff:\n\n{chunk_hunk}"
    try:
        resp = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": REVIEW_SYSTEM},
                {"role": "user", "content": prompt + " /no_think"},
            ],
            options={"temperature": temperature},
        )
        raw = resp["message"]["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        return [Issue(**item) for item in data]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.warning("Failed to parse review response: %s", exc)
        return []
    except Exception as exc:
        logger.error("LLM review error: %s", exc)
        return []
