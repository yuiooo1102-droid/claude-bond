from __future__ import annotations

from pathlib import Path

from rich.console import Console

from claude_bond.applier.applier import apply_bond
from claude_bond.models.bond import BOND_DIR

console = Console()


def run_apply(bond_dir: Path = BOND_DIR) -> None:
    if not (bond_dir / "bond.yaml").exists():
        console.print("[red]No bond found. Run 'bond init' first.[/red]")
        raise SystemExit(1)

    # No cloud pull here - apply is local-only for zero latency.
    # Cloud pull happens at session-end (run_detect.py).
    apply_bond(bond_dir=bond_dir)
    console.print("[bold green]Bond applied successfully.[/bold green]")
