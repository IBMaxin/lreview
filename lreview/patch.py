"""Patch generation, dry-run validation, apply, and rollback."""
import logging
import subprocess

import ollama

logger = logging.getLogger(__name__)

PATCH_SYSTEM = """You are a code repair tool. Given a diff hunk and an issue description,
output ONLY a valid unified diff patch that fixes the issue.
No explanation. No markdown. Raw unified diff starting with --- and +++."""


def generate_patch(hunk: str, issue_desc: str, suggestion: str, model: str, temperature: float = 0.15) -> str | None:
    """Generate a unified diff patch for a specific issue.

    Args:
        hunk: The original diff hunk context.
        issue_desc: Short description of the issue.
        suggestion: LLM suggestion from review pass.
        model: Ollama patch model name.
        temperature: Sampling temperature.

    Returns:
        Unified diff string or None on failure.
    """
    prompt = (
        f"Diff context:\n{hunk}\n\n"
        f"Issue: {issue_desc}\n"
        f"Suggested fix: {suggestion}\n\n"
        "Output the patch to fix this issue as a unified diff."
    )
    try:
        resp = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": PATCH_SYSTEM},
                {"role": "user", "content": prompt + " /no_think"},
            ],
            options={"temperature": temperature},
        )
        return resp["message"]["content"].strip()
    except Exception as exc:
        logger.error("Patch generation failed: %s", exc)
        return None


def dry_run_patch(patch: str) -> bool:
    """Check if a patch applies cleanly without writing files.

    Args:
        patch: Unified diff string.

    Returns:
        True if patch applies cleanly.
    """
    result = subprocess.run(
        ["git", "apply", "--check", "-"],
        input=patch,
        text=True,
        capture_output=True,
    )
    return result.returncode == 0


def apply_patch(patch: str) -> bool:
    """Apply a patch to the working tree.

    Args:
        patch: Unified diff string.

    Returns:
        True on success.
    """
    result = subprocess.run(
        ["git", "apply", "-"],
        input=patch,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        logger.error("git apply failed: %s", result.stderr)
    return result.returncode == 0


def rollback_patch(patch: str) -> bool:
    """Reverse-apply a patch (rollback).

    Args:
        patch: Previously applied unified diff string.

    Returns:
        True on success.
    """
    result = subprocess.run(
        ["git", "apply", "-R", "-"],
        input=patch,
        text=True,
        capture_output=True,
    )
    return result.returncode == 0


def run_tests(test_cmd: str) -> bool:
    """Run test command and return True if it passes.

    Args:
        test_cmd: Shell command string, e.g. 'pytest -x'.

    Returns:
        True if exit code is 0.
    """
    result = subprocess.run(test_cmd, shell=True)
    return result.returncode == 0
