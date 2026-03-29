"""Standalone script for session-end hook to detect changes."""
from __future__ import annotations

from claude_bond.evolve.detector import detect_changes, save_pending
from claude_bond.models.bond import BOND_DIR


def main() -> None:
    if not (BOND_DIR / "bond.yaml").exists():
        return
    if not (BOND_DIR / ".snapshot").exists():
        return

    changes = detect_changes()
    if changes:
        save_pending(BOND_DIR, changes)

        # Auto-merge if enabled
        auto_config = BOND_DIR / ".auto"
        if auto_config.exists():
            from claude_bond.commands.auto_cmd import _auto_merge_pending
            _auto_merge_pending(BOND_DIR)


if __name__ == "__main__":
    main()
