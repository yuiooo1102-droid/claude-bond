from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

from claude_bond.models.bond import BOND_DIR, DIMENSIONS, load_dimension, load_meta


console = Console()


def run_status(bond_dir: Path = BOND_DIR) -> None:
    if not (bond_dir / "bond.yaml").exists():
        console.print("[red]No bond found. Run 'bond init' first.[/red]")
        raise SystemExit(1)

    meta = load_meta(bond_dir)

    console.print(f"\n[bold]Bond v{meta.version}[/bold]")
    console.print(f"  Created: {meta.created}")
    console.print(f"  Updated: {meta.updated}")
    console.print(f"  Location: {bond_dir}\n")

    # Dimensions table
    table = Table(title="Dimensions")
    table.add_column("Dimension", style="bold")
    table.add_column("Items", justify="right")
    table.add_column("Source")
    table.add_column("Updated")

    total_items = 0
    for dim_name in DIMENSIONS:
        try:
            dim = load_dimension(dim_name, bond_dir)
            items = [line for line in dim.content.splitlines() if line.strip().startswith("-")]
            count = len(items)
            total_items += count
            source = ", ".join(dim.source)
            updated = dim.updated
            style = "green" if count > 0 else "dim"
            table.add_row(f"[{style}]{dim_name}[/{style}]", str(count), source, updated)
        except (FileNotFoundError, ValueError):
            table.add_row(f"[red]{dim_name}[/red]", "0", "-", "-")

    console.print(table)
    console.print(f"\n  Total: [bold]{total_items}[/bold] items across {len(DIMENSIONS)} dimensions")

    # Pending changes
    pending_dir = bond_dir / "pending"
    if pending_dir.is_dir():
        pending_files = list(pending_dir.glob("*.md"))
        if pending_files:
            console.print(f"\n  [yellow]Pending changes: {len(pending_files)} file(s)[/yellow]")
            console.print("  Run [bold]bond review[/bold] to review them.")
        else:
            console.print("\n  [dim]No pending changes.[/dim]")

    # Snapshot status
    snapshot_dir = bond_dir / ".snapshot"
    if snapshot_dir.exists():
        console.print("  [dim]Snapshot: active (evolve detection enabled)[/dim]")
    else:
        console.print("  [dim]Snapshot: none (run 'bond apply' to enable evolve detection)[/dim]")

    # Sync status
    git_dir = bond_dir / ".git"
    if git_dir.is_dir():
        import subprocess
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=bond_dir,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            remote_line = result.stdout.splitlines()[0]
            console.print(f"  [dim]Sync: {remote_line}[/dim]")
        else:
            console.print("  [dim]Sync: git initialized, no remote[/dim]")
    else:
        console.print("  [dim]Sync: not configured[/dim]")

    # Update check
    from claude_bond.utils.update_check import check_for_update
    new_version = check_for_update()
    if new_version:
        console.print(f"  [yellow bold]⬆ New version available: {new_version}[/yellow bold]")
        console.print(f"    pip install --upgrade claude-bond")

    console.print()
