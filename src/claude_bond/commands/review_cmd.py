from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from claude_bond.models.bond import BOND_DIR
from claude_bond.evolve.merger import parse_pending, merge_items, PendingItem

console = Console()


def run_review(bond_dir: Path = BOND_DIR) -> None:
    pending_dir = bond_dir / "pending"
    if not pending_dir.is_dir():
        console.print("[dim]No pending changes.[/dim]")
        return

    pending_files = sorted(pending_dir.glob("*.md"))
    if not pending_files:
        console.print("[dim]No pending changes.[/dim]")
        return

    accepted: list[PendingItem] = []

    for pf in pending_files:
        content = pf.read_text(encoding="utf-8")
        items = parse_pending(content)
        if not items:
            continue

        console.print(f"\n[bold]Changes from {pf.stem}:[/bold]")
        for item in items:
            confidence_tag = " [dim](low confidence)[/dim]" if item.confidence == "low" else ""
            console.print(f"  [{item.action}] [bold]{item.dimension}[/bold]: {item.description}{confidence_tag}")
            choice = typer.prompt("  Accept? (y/n)", default="y")
            if choice.lower() in ("y", "yes"):
                accepted.append(item)

        pf.unlink()

    if accepted:
        merge_items(accepted, bond_dir)
        console.print(f"\n[bold green]Merged {len(accepted)} changes into bond.[/bold green]")

        from claude_bond.cloud.auto_push import auto_push_if_configured
        auto_push_if_configured(bond_dir)
    else:
        console.print("\n[dim]No changes accepted.[/dim]")
