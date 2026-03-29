from __future__ import annotations

import zipfile
from pathlib import Path

from rich.console import Console

from claude_bond.models.bond import BOND_DIR

console = Console()

_EXCLUDE_DIRS = {".snapshot", "pending", ".git", "__pycache__"}


def run_export(bond_dir: Path = BOND_DIR, output: Path | None = None) -> Path:
    if not (bond_dir / "bond.yaml").exists():
        console.print("[red]No bond found. Run 'bond init' first.[/red]")
        raise SystemExit(1)

    if output is None:
        output = Path.cwd() / "my.bond"

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(bond_dir.rglob("*")):
            if file.is_file():
                rel = file.relative_to(bond_dir)
                if any(part in _EXCLUDE_DIRS for part in rel.parts):
                    continue
                zf.write(file, str(rel))

    console.print(f"[bold green]Bond exported to {output}[/bold green]")
    return output
