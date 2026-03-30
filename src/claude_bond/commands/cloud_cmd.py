from __future__ import annotations

from pathlib import Path

from rich.console import Console

from claude_bond.models.bond import BOND_DIR

console = Console()


def run_cloud_init(bond_dir: Path = BOND_DIR) -> None:
    from claude_bond.cloud.gist_sync import cloud_init, has_gh_cli, check_gh_auth

    if not has_gh_cli():
        console.print("[red]gh CLI not found.[/red]")
        console.print("Install: https://cli.github.com")
        raise SystemExit(1)

    if not check_gh_auth():
        console.print("[red]GitHub not logged in.[/red]")
        console.print("Run: [bold]gh auth login[/bold]")
        raise SystemExit(1)

    if not (bond_dir / "bond.yaml").exists():
        console.print("[red]No bond found. Run 'bond init' first.[/red]")
        raise SystemExit(1)

    try:
        gist_id = cloud_init(bond_dir)
        console.print("[bold green]Cloud initialized![/bold green]")
        console.print(f"  Gist ID: {gist_id}")
        console.print("  Your bond is now synced to a private GitHub Gist.")
        console.print(f"\n  To sync on another device:")
        console.print(f"  [bold]bond cloud pull --id {gist_id}[/bold]")
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        raise SystemExit(1)


def run_cloud_push(bond_dir: Path = BOND_DIR) -> None:
    from claude_bond.cloud.gist_sync import cloud_push

    try:
        cloud_push(bond_dir)
        console.print("[bold green]Bond pushed to cloud.[/bold green]")
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        raise SystemExit(1)


def run_cloud_pull(bond_dir: Path = BOND_DIR, gist_id: str | None = None) -> None:
    from claude_bond.cloud.gist_sync import cloud_pull, load_cloud_config, save_cloud_config

    # Fix #2: ensure bond_dir exists before saving config
    bond_dir.mkdir(parents=True, exist_ok=True)

    if gist_id:
        config = load_cloud_config(bond_dir)
        config["gist_id"] = gist_id
        save_cloud_config(config, bond_dir)

    try:
        cloud_pull(bond_dir)
        console.print("[bold green]Bond pulled from cloud.[/bold green]")
        console.print("Run [bold]bond apply[/bold] to apply it.")
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        raise SystemExit(1)


def run_cloud_sync(bond_dir: Path = BOND_DIR) -> None:
    from claude_bond.cloud.gist_sync import cloud_sync, load_cloud_config

    config = load_cloud_config(bond_dir)
    if not config.get("gist_id"):
        console.print("[yellow]Cloud not initialized. Run 'bond cloud init' first.[/yellow]")
        raise SystemExit(1)

    try:
        console.print("[dim]Syncing...[/dim]")
        cloud_sync(bond_dir)
        console.print("[bold green]Cloud sync complete.[/bold green]")
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        raise SystemExit(1)


def run_cloud_status(bond_dir: Path = BOND_DIR) -> None:
    from claude_bond.cloud.gist_sync import cloud_status

    status = cloud_status(bond_dir)
    if not status:
        console.print("[dim]Cloud not configured. Run 'bond cloud init' to set up.[/dim]")
        return

    console.print("\n[bold]Cloud Sync[/bold]")
    console.print(f"  Gist ID:    {status.get('gist_id', 'unknown')}")
    console.print(f"  Gist URL:   {status.get('gist_url', 'unknown')}")
    if status.get("last_push"):
        console.print(f"  Last push:  {status['last_push']}")
    if status.get("last_pull"):
        console.print(f"  Last pull:  {status['last_pull']}")
    console.print()
