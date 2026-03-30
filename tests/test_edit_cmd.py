import tempfile
from pathlib import Path

from claude_bond.models.bond import (
    BondDimension,
    BondMeta,
    DIMENSIONS,
    save_dimension,
    save_meta,
    load_dimension,
)
from claude_bond.commands.edit_cmd import _parse_items, _show_dimensions_menu


def _create_test_bond(bond_dir: Path) -> None:
    for dim_name in DIMENSIONS:
        save_dimension(
            BondDimension(dim_name, "2026-03-30", ["scan"], f"- {dim_name} item 1\n- {dim_name} item 2"),
            bond_dir,
        )
    save_meta(BondMeta("0.2.0", "2026-03-30", "2026-03-30"), bond_dir)


def test_parse_items_from_content():
    content = "- No emoji\n- Be concise\n- Write tests first"
    items = _parse_items(content)
    assert len(items) == 3
    assert items[0] == "No emoji"
    assert items[2] == "Write tests first"


def test_parse_items_empty():
    assert _parse_items("") == []
    assert _parse_items("\n\n") == []


def test_parse_items_mixed_format():
    content = "- Bullet item\nPlain text item\n---\n- Another bullet"
    items = _parse_items(content)
    assert len(items) == 3
    assert "Plain text item" in items


def test_show_dimensions_menu(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_test_bond(bond_dir)
        _show_dimensions_menu(bond_dir)
        output = capsys.readouterr().out
        assert "identity" in output
        assert "rules" in output


def test_edit_saves_dimension():
    """Test that editing a dimension saves correctly (non-interactive)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_test_bond(bond_dir)

        # Simulate what _edit_dimension does internally
        dim = load_dimension("rules", bond_dir)
        items = _parse_items(dim.content)
        items.append("New manual rule")

        from datetime import date
        new_content = "\n".join(f"- {item}" for item in items)
        updated = BondDimension(
            name="rules",
            updated=date.today().isoformat(),
            source=list(set(dim.source + ["manual"])),
            content=new_content,
        )
        save_dimension(updated, bond_dir)

        reloaded = load_dimension("rules", bond_dir)
        assert "New manual rule" in reloaded.content
        assert "manual" in reloaded.source
