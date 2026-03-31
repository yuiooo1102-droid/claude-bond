from __future__ import annotations

from pathlib import Path

from rich.console import Console

from claude_bond.models.bond import BOND_DIR
from claude_bond.evolve.merger import parse_pending, merge_items

console = Console()


def run_auto(bond_dir: Path = BOND_DIR, enable: bool = True) -> None:
    config_path = bond_dir / "bond.yaml"
    if not config_path.exists():
        console.print("[red]No bond found. Run 'bond init' first.[/red]")
        raise SystemExit(1)

    auto_flag = bond_dir / ".auto"
    if enable:
        auto_flag.touch()
        console.print("[bold green]Auto-merge enabled.[/bold green]")
        _auto_merge_pending(bond_dir)
    else:
        auto_flag.unlink(missing_ok=True)
        console.print("[dim]Auto-merge disabled. Use 'bond review' to review manually.[/dim]")


def _auto_merge_pending(bond_dir: Path) -> None:
    pending_dir = bond_dir / "pending"
    if not pending_dir.is_dir():
        console.print("[dim]No pending changes.[/dim]")
        return

    all_items = []
    for pf in sorted(pending_dir.glob("*.md")):
        items = parse_pending(pf.read_text(encoding="utf-8"))
        high_confidence = [i for i in items if i.confidence == "high"]
        all_items.extend(high_confidence)
        pf.unlink()

    if all_items:
        merge_items(all_items, bond_dir)
        console.print(f"[bold green]Auto-merged {len(all_items)} high-confidence changes.[/bold green]")

        from claude_bond.cloud.auto_push import auto_push_if_configured
        auto_push_if_configured(bond_dir)
    else:
        console.print("[dim]No high-confidence changes to merge.[/dim]")
