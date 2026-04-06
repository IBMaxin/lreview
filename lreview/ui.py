"""Rich-based terminal UI for issue display and selection."""
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from rich.syntax import Syntax
from .review import Issue

console = Console()

SEVERITY_COLOR = {
    "error": "bold red",
    "warning": "yellow",
    "info": "cyan",
}


def display_issues(issues: list[Issue]) -> None:
    """Render issues as a Rich table.

    Args:
        issues: List of Issue dataclasses from review pass.
    """
    if not issues:
        console.print("[green]No issues found.[/green]")
        return

    table = Table(title="Review Issues", show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Severity", width=9)
    table.add_column("File", style="cyan")
    table.add_column("Line", width=5)
    table.add_column("Issue")
    table.add_column("Suggestion")

    for i, issue in enumerate(issues):
        color = SEVERITY_COLOR.get(issue.severity, "white")
        table.add_row(
            str(i),
            f"[{color}]{issue.severity}[/{color}]",
            issue.file,
            str(issue.line or "-"),
            issue.issue,
            issue.suggestion,
        )
    console.print(table)


def select_issues(issues: list[Issue]) -> list[Issue]:
    """Prompt user to select which issues to patch.

    Args:
        issues: All reviewed issues.

    Returns:
        User-selected subset to generate patches for.
    """
    if not issues:
        return []

    console.print("\n[bold]Enter issue numbers to fix (comma-separated), or [cyan]all[/cyan]/[red]none[/red]:[/bold] ", end="")
    raw = input().strip().lower()

    if raw in ("none", ""):
        return []
    if raw == "all":
        return issues

    selected = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit() and int(part) < len(issues):
            selected.append(issues[int(part)])
    return selected


def show_patch(patch: str) -> bool:
    """Display a patch and ask for confirmation.

    Args:
        patch: Unified diff string.

    Returns:
        True if user confirms apply.
    """
    console.print(Syntax(patch, "diff", theme="monokai"))
    return Confirm.ask("[bold]Apply this patch?[/bold]")
