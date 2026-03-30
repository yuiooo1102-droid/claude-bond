import tempfile
from pathlib import Path

from claude_bond.models.bond import BondDimension, BondMeta, save_dimension, save_meta
from claude_bond.applier.applier import apply_bond


def _create_test_bond(bond_dir: Path) -> None:
    dims = [
        BondDimension("identity", "2026-03-29", ["scan"], "- Data scientist\n- Python expert"),
        BondDimension("rules", "2026-03-29", ["scan"], "- No emoji\n- No trailing summaries"),
        BondDimension("style", "2026-03-29", ["interview"], "- Language: Chinese\n- Style: concise"),
        BondDimension("memory", "2026-03-29", ["scan"], "- Working on claude-bond project"),
        BondDimension("tech_prefs", "2026-03-29", ["scan"], ""),
        BondDimension("work_context", "2026-03-29", ["scan"], ""),
        BondDimension("toolchain", "2026-03-29", ["scan"], ""),
    ]
    for d in dims:
        save_dimension(d, bond_dir)
    save_meta(BondMeta("0.1.0", "2026-03-29", "2026-03-29"), bond_dir)


def test_apply_creates_claude_md_section():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as claude_tmp:
        bond_dir = Path(bond_tmp)
        claude_dir = Path(claude_tmp)
        _create_test_bond(bond_dir)

        apply_bond(bond_dir=bond_dir, claude_dir=claude_dir)

        claude_md = (claude_dir / "CLAUDE.md").read_text(encoding="utf-8")
        assert "## Bond" in claude_md
        assert "No emoji" in claude_md


def test_apply_preserves_existing_claude_md():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as claude_tmp:
        bond_dir = Path(bond_tmp)
        claude_dir = Path(claude_tmp)
        _create_test_bond(bond_dir)

        (claude_dir / "CLAUDE.md").write_text("# My Existing Rules\n- Keep this\n", encoding="utf-8")

        apply_bond(bond_dir=bond_dir, claude_dir=claude_dir)

        claude_md = (claude_dir / "CLAUDE.md").read_text(encoding="utf-8")
        assert "Keep this" in claude_md
        assert "## Bond" in claude_md


def test_apply_writes_memory_files():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as claude_tmp:
        bond_dir = Path(bond_tmp)
        claude_dir = Path(claude_tmp)
        _create_test_bond(bond_dir)

        apply_bond(bond_dir=bond_dir, claude_dir=claude_dir)

        mem_dir = claude_dir / "memory"
        assert mem_dir.is_dir()
        bond_mem = mem_dir / "bond_memory.md"
        assert bond_mem.exists()
        assert "claude-bond" in bond_mem.read_text(encoding="utf-8")


def test_apply_creates_snapshot():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as claude_tmp:
        bond_dir = Path(bond_tmp)
        claude_dir = Path(claude_tmp)
        _create_test_bond(bond_dir)

        apply_bond(bond_dir=bond_dir, claude_dir=claude_dir)

        snapshot_dir = bond_dir / ".snapshot"
        assert snapshot_dir.is_dir()
