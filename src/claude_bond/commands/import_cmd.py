from __future__ import annotations

import io
import zipfile
from pathlib import Path

from rich.console import Console

from claude_bond.models.bond import BOND_DIR

console = Console()


def run_import(
    file: Path,
    bond_dir: Path = BOND_DIR,
    auto_apply: bool = True,
    password: str | None = None,
) -> None:
    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise SystemExit(1)

    bond_dir.mkdir(parents=True, exist_ok=True)

    file_bytes = file.read_bytes()

    # Check if encrypted (starts with BOND magic)
    if file_bytes[:4] == b"BOND":
        if not password:
            console.print("[red]This file is encrypted. Use --password to provide the password.[/red]")
            raise SystemExit(1)
        from claude_bond.utils.crypto import decrypt_bytes

        file_bytes = decrypt_bytes(file_bytes, password)
        console.print("[dim]Decrypted successfully.[/dim]")

    with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as zf:
        zf.extractall(bond_dir)

    console.print(f"[bold green]Bond imported to {bond_dir}[/bold green]")

    if auto_apply:
        from claude_bond.commands.apply_cmd import run_apply

        run_apply(bond_dir=bond_dir)
