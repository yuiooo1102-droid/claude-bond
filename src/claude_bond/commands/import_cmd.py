from __future__ import annotations

import zipfile
from pathlib import Path

from rich.console import Console

from claude_bond.models.bond import BOND_DIR

console = Console()


def run_import(
    file: Path,
    bond_dir: Path = BOND_DIR,
    auto_apply: bool = True,
) -> None:
    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise SystemExit(1)

    bond_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(file, "r") as zf:
        zf.extractall(bond_dir)

    console.print(f"[bold green]Bond imported to {bond_dir}[/bold green]")

    if auto_apply:
        from claude_bond.commands.apply_cmd import run_apply
        run_apply(bond_dir=bond_dir)
