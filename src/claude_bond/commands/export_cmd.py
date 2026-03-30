from __future__ import annotations

import io
import zipfile
from pathlib import Path

from rich.console import Console

from claude_bond.models.bond import BOND_DIR

console = Console()

_EXCLUDE_DIRS = {".snapshot", "pending", ".git", "__pycache__"}


def run_export(
    bond_dir: Path = BOND_DIR,
    output: Path | None = None,
    password: str | None = None,
) -> Path:
    if not (bond_dir / "bond.yaml").exists():
        console.print("[red]No bond found. Run 'bond init' first.[/red]")
        raise SystemExit(1)

    if output is None:
        output = Path.cwd() / "my.bond"

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(bond_dir.rglob("*")):
            if file.is_file():
                rel = file.relative_to(bond_dir)
                if any(part in _EXCLUDE_DIRS for part in rel.parts):
                    continue
                zf.write(file, str(rel))

    zip_bytes = zip_buffer.getvalue()

    if password:
        from claude_bond.utils.crypto import encrypt_bytes

        zip_bytes = encrypt_bytes(zip_bytes, password)
        console.print("[dim]Encrypted with AES-256.[/dim]")

    output.write_bytes(zip_bytes)
    console.print(f"[bold green]Bond exported to {output}[/bold green]")
    return output
