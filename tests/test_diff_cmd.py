import tempfile
from pathlib import Path

from claude_bond.commands.diff_cmd import run_diff


def _setup_snapshot(bond_dir: Path, claude_dir: Path) -> None:
    """Create a snapshot matching claude_dir."""
    snapshot = bond_dir / ".snapshot"
    snapshot.mkdir(parents=True)
    (snapshot / "CLAUDE.md").write_text("# Rules\n- No emoji\n", encoding="utf-8")
    mem = snapshot / "memory"
    mem.mkdir()
    (mem / "user.md").write_text("User is a developer", encoding="utf-8")

    (claude_dir / "CLAUDE.md").write_text("# Rules\n- No emoji\n", encoding="utf-8")
    mem2 = claude_dir / "memory"
    mem2.mkdir()
    (mem2 / "user.md").write_text("User is a developer", encoding="utf-8")


def test_diff_no_changes():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as claude_tmp:
        bond_dir = Path(bond_tmp)
        claude_dir = Path(claude_tmp)
        _setup_snapshot(bond_dir, claude_dir)

        has_changes = run_diff(bond_dir=bond_dir, claude_dir=claude_dir)
        assert has_changes is False


def test_diff_detects_claude_md_change():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as claude_tmp:
        bond_dir = Path(bond_tmp)
        claude_dir = Path(claude_tmp)
        _setup_snapshot(bond_dir, claude_dir)

        # Modify CLAUDE.md
        (claude_dir / "CLAUDE.md").write_text("# Rules\n- No emoji\n- Be concise\n", encoding="utf-8")

        has_changes = run_diff(bond_dir=bond_dir, claude_dir=claude_dir)
        assert has_changes is True


def test_diff_detects_new_memory_file():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as claude_tmp:
        bond_dir = Path(bond_tmp)
        claude_dir = Path(claude_tmp)
        _setup_snapshot(bond_dir, claude_dir)

        # Add new memory file
        (claude_dir / "memory" / "new_project.md").write_text("New project info", encoding="utf-8")

        has_changes = run_diff(bond_dir=bond_dir, claude_dir=claude_dir)
        assert has_changes is True


def test_diff_detects_deleted_memory_file():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as claude_tmp:
        bond_dir = Path(bond_tmp)
        claude_dir = Path(claude_tmp)
        _setup_snapshot(bond_dir, claude_dir)

        # Delete memory file
        (claude_dir / "memory" / "user.md").unlink()

        has_changes = run_diff(bond_dir=bond_dir, claude_dir=claude_dir)
        assert has_changes is True


def test_diff_no_snapshot():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as claude_tmp:
        has_changes = run_diff(bond_dir=Path(bond_tmp), claude_dir=Path(claude_tmp))
        assert has_changes is False
