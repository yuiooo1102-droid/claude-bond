import tempfile
from pathlib import Path
from unittest.mock import patch

from claude_bond.evolve.detector import detect_changes, save_pending


def test_detect_no_changes_when_identical():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        snapshot_dir = bond_dir / ".snapshot"
        snapshot_dir.mkdir()
        (snapshot_dir / "CLAUDE.md").write_text("# Rules\n- No emoji", encoding="utf-8")

        claude_dir = Path(tmpdir) / "claude"
        claude_dir.mkdir()
        (claude_dir / "CLAUDE.md").write_text("# Rules\n- No emoji", encoding="utf-8")

        changes = detect_changes(bond_dir=bond_dir, claude_dir=claude_dir)
        assert changes is None


def test_detect_finds_changes():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir) / "bond"
        bond_dir.mkdir()
        snapshot_dir = bond_dir / ".snapshot"
        snapshot_dir.mkdir()
        (snapshot_dir / "CLAUDE.md").write_text("# Rules\n- No emoji", encoding="utf-8")

        claude_dir = Path(tmpdir) / "claude"
        claude_dir.mkdir()
        (claude_dir / "CLAUDE.md").write_text("# Rules\n- No emoji\n- Be concise", encoding="utf-8")

        mock_analysis = "## New\n\n- [rules] User added: Be concise"
        with patch("claude_bond.evolve.detector.analyze_changes", return_value=mock_analysis):
            changes = detect_changes(bond_dir=bond_dir, claude_dir=claude_dir)
            assert changes is not None
            assert "concise" in changes


def test_save_pending_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        (bond_dir / "pending").mkdir()

        save_pending(bond_dir, "## New\n\n- [rules] Be concise")

        pending_files = list((bond_dir / "pending").glob("*.md"))
        assert len(pending_files) == 1
        content = pending_files[0].read_text(encoding="utf-8")
        assert "concise" in content
