import tempfile
from pathlib import Path

from claude_bond.models.bond import (
    DIMENSIONS,
    BondDimension,
    BondMeta,
    save_dimension,
    save_meta,
    load_dimension,
)
from claude_bond.applier.applier import apply_bond


def test_dimensions_include_v2():
    assert "tech_prefs" in DIMENSIONS
    assert "work_context" in DIMENSIONS
    assert "toolchain" in DIMENSIONS
    assert len(DIMENSIONS) == 7


def test_save_load_v2_dimension():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        dim = BondDimension(
            name="tech_prefs",
            updated="2026-03-30",
            source=["scan"],
            content="- Prefer pytest over unittest\n- Use black formatter",
        )
        save_dimension(dim, bond_dir)
        loaded = load_dimension("tech_prefs", bond_dir)
        assert loaded.name == "tech_prefs"
        assert "pytest" in loaded.content


def test_apply_includes_v2_sections():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as claude_tmp:
        bond_dir = Path(bond_tmp)
        claude_dir = Path(claude_tmp)

        dims = [
            BondDimension("identity", "2026-03-30", ["scan"], "- Developer"),
            BondDimension("rules", "2026-03-30", ["scan"], "- No emoji"),
            BondDimension("style", "2026-03-30", ["scan"], "- Chinese"),
            BondDimension("memory", "2026-03-30", ["scan"], "- Project X"),
            BondDimension("tech_prefs", "2026-03-30", ["scan"], "- Prefer pytest\n- Use black"),
            BondDimension("work_context", "2026-03-30", ["scan"], "- Building claude-bond"),
            BondDimension("toolchain", "2026-03-30", ["scan"], "- VS Code\n- MCP servers"),
        ]
        for d in dims:
            save_dimension(d, bond_dir)
        save_meta(BondMeta("0.2.0", "2026-03-30", "2026-03-30"), bond_dir)

        apply_bond(bond_dir=bond_dir, claude_dir=claude_dir)

        claude_md = (claude_dir / "CLAUDE.md").read_text(encoding="utf-8")
        assert "Technical preferences" in claude_md
        assert "pytest" in claude_md
        assert "Work context" in claude_md
        assert "claude-bond" in claude_md
        assert "Toolchain" in claude_md
        assert "VS Code" in claude_md
