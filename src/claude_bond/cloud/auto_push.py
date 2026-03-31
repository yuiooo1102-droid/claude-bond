"""Silent auto-push after bond modifications. Never raises, never blocks."""
from __future__ import annotations

from pathlib import Path

from rich.console import Console

from claude_bond.models.bond import BOND_DIR

console = Console()


def auto_push_if_configured(bond_dir: Path = BOND_DIR) -> None:
    """Push to cloud if configured. Silent on any failure."""
    try:
        from claude_bond.cloud.gist_sync import (
            load_cloud_config,
            has_gh_cli,
            check_gh_auth,
            cloud_push,
        )

        config = load_cloud_config(bond_dir)
        if not config.get("gist_id"):
            return

        if not has_gh_cli() or not check_gh_auth():
            return

        cloud_push(bond_dir, force=True)
        console.print("[dim]Cloud synced.[/dim]")
    except Exception:
        pass  # Silent - never disrupt the user's workflow
