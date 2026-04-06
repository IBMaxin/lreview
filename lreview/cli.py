"""lreview CLI entry point."""
import json
import logging
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .config import load_config
from .diff import get_diff, chunk_diff
from .review import review_chunk
from .patch import dry_run_patch, apply_patch, rollback_patch, run_tests, generate_patch
from .ui import display_issues, select_issues, show_patch

app = typer.Typer(help="Local AI code review with staged patch apply.")
console = Console()
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


class OutputFormat(str, Enum):
    text = "text"
    json = "json"


@app.command()
def review(
    diff_base: str = typer.Argument(default="", help="Git ref to diff against, e.g. HEAD~2"),
    staged: bool = typer.Option(False, "--staged", "-s", help="Review staged changes only"),
    test_cmd: Optional[str] = typer.Option(None, "--test-cmd", "-t", help="Run after patch, rollback on fail"),
    output: OutputFormat = typer.Option(OutputFormat.text, "--output", "-o"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c"),
    review_model: Optional[str] = typer.Option(None, "--review-model"),
    patch_model: Optional[str] = typer.Option(None, "--patch-model"),
) -> None:
    """Review a git diff with a local Ollama model and optionally apply fixes."""
    cfg = load_config(config_path)
    rm = review_model or cfg.models.review_model
    pm = patch_model or cfg.models.patch_model
    base = diff_base or cfg.git.default_diff_base

    console.print(f"[dim]review={rm}  patch={pm}[/dim]")

    try:
        diff = get_diff(base=base, staged=staged)
    except Exception as exc:
        console.print(f"[red]git diff failed: {exc}[/red]")
        raise typer.Exit(1)

    if not diff.strip():
        console.print("[yellow]No changes detected.[/yellow]")
        raise typer.Exit()

    chunks = chunk_diff(diff, max_tokens=cfg.limits.max_diff_tokens)
    console.print(f"[cyan]Reviewing {len(chunks)} file chunk(s)...[/cyan]")

    all_issues = []
    for chunk in chunks:
        console.print(f"  [dim]-> {chunk.filename}[/dim]")
        issues = review_chunk(
            chunk.hunk,
            model=rm,
            temperature=cfg.limits.temperature,
            timeout=cfg.limits.review_timeout,
        )
        for issue in issues:
            issue.file = issue.file or chunk.filename
        all_issues.extend(issues)

    if output == OutputFormat.json:
        print(json.dumps([vars(i) for i in all_issues], indent=2))
        raise typer.Exit()

    display_issues(all_issues)

    if not all_issues:
        raise typer.Exit()

    selected = select_issues(all_issues)
    if not selected:
        console.print("[dim]No fixes selected. Done.[/dim]")
        raise typer.Exit()

    chunk_map = {c.filename: c for c in chunks}

    for issue in selected:
        hunk = chunk_map.get(issue.file, chunks[0]).hunk
        console.print(f"\n[bold cyan]Generating patch for:[/bold cyan] {issue.issue}")
        patch = generate_patch(hunk, issue.issue, issue.suggestion, pm, cfg.limits.temperature)

        if not patch:
            console.print("[red]Patch generation failed, skipping.[/red]")
            continue

        if not dry_run_patch(patch):
            console.print("[red]Patch does not apply cleanly, skipping.[/red]")
            continue

        if not show_patch(patch):
            continue

        if apply_patch(patch):
            console.print("[green]Patch applied.[/green]")
            if test_cmd:
                console.print(f"[dim]Running: {test_cmd}[/dim]")
                if not run_tests(test_cmd):
                    console.print("[red]Tests failed - rolling back.[/red]")
                    rollback_patch(patch)
                else:
                    console.print("[green]Tests passed.[/green]")
        else:
            console.print("[red]Apply failed.[/red]")

    console.print("\n[bold green]lreview done.[/bold green]")


def main() -> None:
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
