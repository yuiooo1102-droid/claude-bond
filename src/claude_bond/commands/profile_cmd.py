from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console
from rich.table import Table

from claude_bond.models.bond import BOND_DIR, DIMENSIONS, load_meta, load_dimension
from claude_bond.profile import (
    get_active_profile,
    set_active_profile,
    get_profile_dir,
    list_profiles,
    profile_exists,
    migrate_to_profiles,
    PROFILES_DIR,
)

console = Console()


def run_profile_list() -> None:
    profiles = list_profiles()
    active = get_active_profile()

    if not profiles:
        console.print("[dim]No profiles found. Run 'bond profile create <name>' to create one.[/dim]")
        return

    table = Table(title="Bond Profiles")
    table.add_column("Profile", style="bold")
    table.add_column("Dimensions", justify="right")
    table.add_column("Active")

    for name in profiles:
        profile_dir = get_profile_dir(name)
        try:
            meta = load_meta(profile_dir)
            dim_count = len(meta.dimensions)
        except Exception:
            dim_count = 0

        marker = "[green]★[/green]" if name == active else ""
        table.add_row(name, str(dim_count), marker)

    console.print(table)


def run_profile_use(name: str) -> None:
    if not profile_exists(name):
        console.print(f"[red]Profile '{name}' not found.[/red]")
        console.print(f"Available: {', '.join(list_profiles()) or 'none'}")
        raise SystemExit(1)

    set_active_profile(name)
    console.print(f"[bold green]Switched to profile: {name}[/bold green]")
    console.print("Run [bold]bond apply[/bold] to apply this profile.")


def run_profile_create(name: str, clone_from: str | None = None) -> None:
    profile_dir = get_profile_dir(name)
    if profile_dir.exists():
        console.print(f"[red]Profile '{name}' already exists.[/red]")
        raise SystemExit(1)

    if clone_from:
        source = get_profile_dir(clone_from)
        if not source.exists():
            console.print(f"[red]Source profile '{clone_from}' not found.[/red]")
            raise SystemExit(1)
        shutil.copytree(source, profile_dir)
        console.print(f"[bold green]Profile '{name}' created (cloned from '{clone_from}').[/bold green]")
    else:
        profile_dir.mkdir(parents=True)
        console.print(f"[bold green]Profile '{name}' created (empty).[/bold green]")
        console.print(f"Run [bold]bond profile use {name}[/bold] then [bold]bond init[/bold] to set it up.")


def run_profile_delete(name: str) -> None:
    if name == get_active_profile():
        console.print("[red]Cannot delete the active profile. Switch first.[/red]")
        raise SystemExit(1)

    profile_dir = get_profile_dir(name)
    if not profile_dir.exists():
        console.print(f"[red]Profile '{name}' not found.[/red]")
        raise SystemExit(1)

    shutil.rmtree(profile_dir)
    console.print(f"[bold green]Profile '{name}' deleted.[/bold green]")


def run_profile_migrate() -> None:
    if migrate_to_profiles():
        console.print("[bold green]Migrated to profile-based layout. Active profile: default[/bold green]")
    else:
        console.print("[dim]Already using profile layout or no bond to migrate.[/dim]")
