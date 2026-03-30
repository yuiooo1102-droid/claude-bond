from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console

from claude_bond.models.bond import BOND_DIR
from claude_bond.sync_engine.git_sync import (
    is_git_repo,
    git_init,
    git_commit_all,
    git_pull,
    git_push,
    git_add_remote,
)

console = Console()


def run_sync(bond_dir: Path = BOND_DIR, init_remote: str | None = None) -> None:
    if not (bond_dir / "bond.yaml").exists():
        console.print("[red]No bond found. Run 'bond init' first.[/red]")
        raise SystemExit(1)

    if not is_git_repo(bond_dir):
        git_init(bond_dir)
        console.print("[dim]Initialized git repo in bond directory.[/dim]")

    if init_remote:
        git_add_remote(bond_dir, init_remote)
        console.print(f"[dim]Added remote: {init_remote}[/dim]")
        console.print("[yellow]Please ensure this is a PRIVATE repository.[/yellow]")

    committed = git_commit_all(bond_dir)
    if committed:
        console.print("[dim]Committed local changes.[/dim]")

    has_remote = _has_remote(bond_dir)
    if has_remote:
        console.print("[dim]Pulling...[/dim]")
        pulled = git_pull(bond_dir)

        if not pulled:
            # Pull failed, likely merge conflict
            from claude_bond.sync_engine.semantic_merge import resolve_sync_conflicts
            console.print("[yellow]Merge conflict detected, resolving semantically...[/yellow]")
            resolved = resolve_sync_conflicts(bond_dir)
            if resolved:
                console.print(f"[green]Resolved conflicts in: {', '.join(resolved)}[/green]")
                git_commit_all(bond_dir, "bond: semantic merge resolution")
            else:
                console.print("[red]Could not resolve conflicts automatically. Please resolve manually.[/red]")
                return

        console.print("[dim]Pushing...[/dim]")
        git_push(bond_dir)
        console.print("[bold green]Bond synced.[/bold green]")
    else:
        console.print("[yellow]No remote configured. Use 'bond sync --init <url>' to set one.[/yellow]")


def _has_remote(bond_dir: Path) -> bool:
    result = subprocess.run(
        ["git", "remote"],
        cwd=bond_dir,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())
