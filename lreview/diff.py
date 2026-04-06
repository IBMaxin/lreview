"""Git diff utilities and chunking."""
import subprocess
from dataclasses import dataclass


@dataclass
class DiffChunk:
    """A single file hunk from a git diff."""
    filename: str
    hunk: str
    token_estimate: int


def get_diff(base: str = "HEAD~1", staged: bool = False) -> str:
    """Run git diff and return raw unified diff string.

    Args:
        base: Git ref to diff against.
        staged: If True, diff only staged/cached changes.

    Returns:
        Unified diff string.

    Raises:
        subprocess.CalledProcessError: If git command fails.
    """
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--cached")
    else:
        cmd.append(base)
    return subprocess.check_output(cmd, text=True)


def chunk_diff(diff: str, max_tokens: int = 3000) -> list[DiffChunk]:
    """Split a unified diff into per-file chunks under the token limit.

    Args:
        diff: Raw unified diff string.
        max_tokens: Approx token ceiling per chunk (1 token ~= 4 chars).

    Returns:
        List of DiffChunk objects.
    """
    chunks: list[DiffChunk] = []
    current_file = "unknown"
    current_lines: list[str] = []

    def flush() -> None:
        if current_lines:
            hunk = "\n".join(current_lines)
            chunks.append(DiffChunk(
                filename=current_file,
                hunk=hunk,
                token_estimate=len(hunk) // 4,
            ))

    for line in diff.splitlines():
        if line.startswith("diff --git"):
            flush()
            current_file = line.split(" b/")[-1] if " b/" in line else line
            current_lines = [line]
        else:
            current_lines.append(line)
            if len("\n".join(current_lines)) // 4 >= max_tokens:
                flush()
                current_lines = []

    flush()
    return chunks
