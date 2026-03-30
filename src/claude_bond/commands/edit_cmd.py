from __future__ import annotations

from datetime import date
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from claude_bond.models.bond import (
    BOND_DIR,
    DIMENSIONS,
    BondDimension,
    load_dimension,
    load_meta,
    save_dimension,
)

console = Console()

_DIM_LABELS = {
    "identity": "Who you are",
    "rules": "Behavioral rules",
    "style": "Communication style",
    "memory": "Memories",
    "tech_prefs": "Technical preferences",
    "work_context": "Work context",
    "toolchain": "Toolchain",
}


def run_edit(bond_dir: Path = BOND_DIR, dimension: str | None = None) -> None:
    if not (bond_dir / "bond.yaml").exists():
        console.print("[red]No bond found. Run 'bond init' first.[/red]")
        raise SystemExit(1)

    load_meta(bond_dir)

    if dimension:
        if dimension not in DIMENSIONS:
            console.print(f"[red]Unknown dimension: {dimension}[/red]")
            console.print(f"Available: {', '.join(DIMENSIONS)}")
            raise SystemExit(1)
        _edit_dimension(dimension, bond_dir)
        return

    # Interactive: show dimensions and let user pick
    _show_dimensions_menu(bond_dir)

    choice = typer.prompt(
        "\nEnter dimension name to edit (or 'q' to quit)",
        default="q",
    )

    if choice == "q":
        return

    if choice not in DIMENSIONS:
        console.print(f"[red]Unknown dimension: {choice}[/red]")
        return

    _edit_dimension(choice, bond_dir)


def _show_dimensions_menu(bond_dir: Path) -> None:
    console.print("\n[bold]Bond Dimensions[/bold]\n")

    table = Table()
    table.add_column("Dimension", style="bold")
    table.add_column("Description")
    table.add_column("Items", justify="right")

    for dim_name in DIMENSIONS:
        label = _DIM_LABELS.get(dim_name, dim_name)
        try:
            dim = load_dimension(dim_name, bond_dir)
            items = [line for line in dim.content.splitlines() if line.strip().startswith("-")]
            count = str(len(items))
        except (FileNotFoundError, ValueError):
            count = "0"
        table.add_row(dim_name, label, count)

    console.print(table)


def _edit_dimension(dim_name: str, bond_dir: Path) -> None:
    try:
        dim = load_dimension(dim_name, bond_dir)
    except (FileNotFoundError, ValueError):
        dim = BondDimension(dim_name, date.today().isoformat(), ["manual"], "")

    label = _DIM_LABELS.get(dim_name, dim_name)
    console.print(f"\n[bold]Editing: {label} ({dim_name})[/bold]")

    # Show current items
    items = _parse_items(dim.content)
    _show_items(items)

    while True:
        console.print("\n[dim]Commands: [a]dd, [d]elete <number>, [e]dit <number>, [q]uit[/dim]")
        cmd = typer.prompt("", default="q").strip()

        if cmd == "q":
            break
        elif cmd == "a":
            new_item = typer.prompt("New item")
            items.append(new_item.strip())
            _show_items(items)
        elif cmd.startswith("d"):
            _handle_delete(cmd, items)
            _show_items(items)
        elif cmd.startswith("e"):
            _handle_edit_item(cmd, items)
            _show_items(items)
        else:
            console.print("[dim]Unknown command.[/dim]")

    # Save
    new_content = "\n".join(f"- {item}" for item in items) if items else ""
    updated_dim = BondDimension(
        name=dim_name,
        updated=date.today().isoformat(),
        source=list(set(dim.source + ["manual"])),
        content=new_content,
    )
    save_dimension(updated_dim, bond_dir)
    console.print(f"[bold green]Saved {dim_name} ({len(items)} items).[/bold green]")


def _parse_items(content: str) -> list[str]:
    items: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:])
        elif stripped and not stripped.startswith("---"):
            items.append(stripped)
    return items


def _show_items(items: list[str]) -> None:
    if not items:
        console.print("  [dim](empty)[/dim]")
        return
    for i, item in enumerate(items, 1):
        console.print(f"  [bold]{i}.[/bold] {item}")


def _handle_delete(cmd: str, items: list[str]) -> None:
    parts = cmd.split(maxsplit=1)
    if len(parts) < 2:
        console.print("[red]Usage: d <number>[/red]")
        return
    try:
        idx = int(parts[1]) - 1
        if 0 <= idx < len(items):
            removed = items.pop(idx)
            console.print(f"[red]Deleted: {removed}[/red]")
        else:
            console.print("[red]Invalid number.[/red]")
    except ValueError:
        console.print("[red]Invalid number.[/red]")


def _handle_edit_item(cmd: str, items: list[str]) -> None:
    parts = cmd.split(maxsplit=1)
    if len(parts) < 2:
        console.print("[red]Usage: e <number>[/red]")
        return
    try:
        idx = int(parts[1]) - 1
        if 0 <= idx < len(items):
            console.print(f"  Current: {items[idx]}")
            new_val = typer.prompt("  New value", default=items[idx])
            items[idx] = new_val.strip()
        else:
            console.print("[red]Invalid number.[/red]")
    except ValueError:
        console.print("[red]Invalid number.[/red]")
