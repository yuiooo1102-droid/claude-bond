"""Standalone script for session-end hook to detect changes."""
from __future__ import annotations

from claude_bond.evolve.detector import detect_changes, save_pending
from claude_bond.models.bond import BOND_DIR


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


if __name__ == "__main__":
    main()
