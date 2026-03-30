from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

from claude_bond.models.bond import BOND_DIR
from claude_bond.evolve.tacit import load_signals, analyze_patterns

console = Console()


def run_tacit_status(bond_dir: Path = BOND_DIR) -> None:
    signals = load_signals(bond_dir)
    console.print(f"\n[bold]Tacit Mode[/bold]")
    console.print(f"  Sessions tracked: {len(signals)}")

    if len(signals) < 3:
        console.print(f"  [dim]Need at least 3 sessions to detect patterns (have {len(signals)})[/dim]\n")
        return

    patterns = analyze_patterns(bond_dir)
    if not patterns:
        console.print("  [dim]No patterns detected yet.[/dim]\n")
        return

    table = Table(title="Detected Patterns")
    table.add_column("Dimension", style="bold")
    table.add_column("Pattern")
    table.add_column("Confidence", justify="right")
    table.add_column("Evidence")

    for p in patterns:
        conf_str = f"{int(p['confidence'] * 100)}%"
        style = "green" if p["confidence"] >= 0.8 else "yellow" if p["confidence"] >= 0.6 else "dim"
        table.add_row(
            p["dimension"],
            p["description"],
            f"[{style}]{conf_str}[/{style}]",
            p["evidence"],
        )

    console.print(table)
    console.print()
