from __future__ import annotations

from pathlib import Path

from rich.console import Console

from claude_bond.applier.applier import apply_bond
from claude_bond.models.bond import BOND_DIR

console = Console()


def _auto_pull_if_configured(bond_dir: Path) -> None:
    """Pull latest from cloud before applying. Silent on failure."""
    try:
        from claude_bond.cloud.gist_sync import load_cloud_config, has_gh_cli, check_gh_auth, cloud_pull

        config = load_cloud_config(bond_dir)
        if not config.get("gist_id"):
            return

        if not has_gh_cli() or not check_gh_auth():
            return

        cloud_pull(bond_dir)
    except Exception:
        pass  # Silent - don't block apply if cloud is unreachable


def run_apply(bond_dir: Path = BOND_DIR) -> None:
    if not (bond_dir / "bond.yaml").exists():
        console.print("[red]No bond found. Run 'bond init' first.[/red]")
        raise SystemExit(1)

    # Pull latest from cloud first (soul lives in the cloud)
    _auto_pull_if_configured(bond_dir)

    apply_bond(bond_dir=bond_dir)
    console.print("[bold green]Bond applied successfully.[/bold green]")
