from __future__ import annotations

import difflib
from pathlib import Path

from rich.console import Console

from claude_bond.models.bond import BOND_DIR

console = Console()


def run_diff(bond_dir: Path = BOND_DIR, claude_dir: Path | None = None) -> bool:
    """Show diff between snapshot and current ~/.claude/. Returns True if changes found."""
    if claude_dir is None:
        claude_dir = Path.home() / ".claude"

    snapshot_dir = bond_dir / ".snapshot"
    if not snapshot_dir.exists():
        console.print("[yellow]No snapshot found. Run 'bond apply' first to create a baseline.[/yellow]")
        return False

    has_changes = False

    # Compare CLAUDE.md
    old_claude = snapshot_dir / "CLAUDE.md"
    new_claude = claude_dir / "CLAUDE.md"
    changed = _diff_file(old_claude, new_claude, "CLAUDE.md")
    if changed:
        has_changes = True

    # Compare memory files
    old_mem = snapshot_dir / "memory"
    new_mem = claude_dir / "memory"

    old_files = set(f.name for f in old_mem.glob("*.md")) if old_mem.is_dir() else set()
    new_files = set(f.name for f in new_mem.glob("*.md")) if new_mem.is_dir() else set()

    # New files
    for name in sorted(new_files - old_files):
        console.print(f"\n[green]+ New file: memory/{name}[/green]")
        content = (new_mem / name).read_text(encoding="utf-8")
        _print_added(content)
        has_changes = True

    # Deleted files
    for name in sorted(old_files - new_files):
        console.print(f"\n[red]- Deleted file: memory/{name}[/red]")
        has_changes = True

    # Modified files
    for name in sorted(old_files & new_files):
        old_path = old_mem / name
        new_path = new_mem / name
        changed = _diff_file(old_path, new_path, f"memory/{name}")
        if changed:
            has_changes = True

    if not has_changes:
        console.print("[dim]No changes since last apply.[/dim]")

    return has_changes


def _diff_file(old_path: Path, new_path: Path, label: str) -> bool:
    """Show unified diff between two files. Returns True if different."""
    old_text = old_path.read_text(encoding="utf-8") if old_path.exists() else ""
    new_text = new_path.read_text(encoding="utf-8") if new_path.exists() else ""

    if old_text == new_text:
        return False

    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"snapshot/{label}",
        tofile=f"current/{label}",
        lineterm="",
    ))

    if not diff:
        return False

    console.print(f"\n[bold]Changes in {label}:[/bold]")
    for line in diff:
        line = line.rstrip("\n")
        if line.startswith("+") and not line.startswith("+++"):
            console.print(f"[green]{line}[/green]")
        elif line.startswith("-") and not line.startswith("---"):
            console.print(f"[red]{line}[/red]")
        elif line.startswith("@@"):
            console.print(f"[cyan]{line}[/cyan]")
        else:
            console.print(line)

    return True


def _print_added(content: str) -> None:
    """Print content as all-new lines."""
    for line in content.splitlines():
        console.print(f"[green]+ {line}[/green]")
