"""Standalone script for session-end hook to detect changes."""
from __future__ import annotations

import json
import time
from pathlib import Path

from claude_bond.evolve.detector import detect_changes, save_pending
from claude_bond.models.bond import BOND_DIR


_SYNC_COOLDOWN = 300  # 5 minutes
_COOLDOWN_FILE = BOND_DIR / ".last_sync"


def main() -> None:
    if not (BOND_DIR / "bond.yaml").exists():
        return
    if not (BOND_DIR / ".snapshot").exists():
        return

    # Collect tacit signal from this session's changes
    from claude_bond.evolve.signal_collector import collect_session_signal
    collect_session_signal()

    # Explicit change detection
    changes = detect_changes()
    if changes:
        save_pending(BOND_DIR, changes)

    # Tacit pattern analysis (across accumulated signals)
    from claude_bond.evolve.tacit import generate_tacit_pending
    tacit_changes = generate_tacit_pending(BOND_DIR)
    if tacit_changes:
        save_pending(BOND_DIR, tacit_changes)

    # Auto-merge if enabled
    auto_config = BOND_DIR / ".auto"
    if auto_config.exists():
        from claude_bond.commands.auto_cmd import _auto_merge_pending
        _auto_merge_pending(BOND_DIR)

    # Cloud sync (pull + merge + push) with cooldown
    _auto_cloud_sync()


def _auto_cloud_sync() -> None:
    """Pull + merge + push to cloud. Respects 5-minute cooldown."""
    try:
        # Cooldown check
        if _COOLDOWN_FILE.exists():
            last_sync = json.loads(_COOLDOWN_FILE.read_text(encoding="utf-8")).get("ts", 0)
            if time.time() - last_sync < _SYNC_COOLDOWN:
                return

        from claude_bond.cloud.gist_sync import load_cloud_config, has_gh_cli, check_gh_auth, cloud_sync

        config = load_cloud_config(BOND_DIR)
        if not config.get("gist_id"):
            return

        if not has_gh_cli() or not check_gh_auth():
            return

        cloud_sync(BOND_DIR)

        # Record sync time
        BOND_DIR.mkdir(parents=True, exist_ok=True)
        _COOLDOWN_FILE.write_text(json.dumps({"ts": time.time()}), encoding="utf-8")
    except Exception:
        pass  # Silent - never break session end


if __name__ == "__main__":
    main()
