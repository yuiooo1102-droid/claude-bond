import tempfile
from pathlib import Path

from claude_bond.models.bond import BondDimension, BondMeta, save_dimension, save_meta
from claude_bond.commands.status_cmd import run_status


def _create_test_bond(bond_dir: Path) -> None:
    dims = [
        BondDimension("identity", "2026-03-29", ["scan"], "- Data scientist\n- Python expert"),
        BondDimension("rules", "2026-03-29", ["scan"], "- No emoji\n- No trailing summaries"),
        BondDimension("style", "2026-03-29", ["interview"], "- Chinese\n- Concise"),
        BondDimension("memory", "2026-03-29", ["scan"], "- Working on claude-bond"),
    ]
    for d in dims:
        save_dimension(d, bond_dir)
    save_meta(BondMeta("0.1.0", "2026-03-29", "2026-03-29"), bond_dir)


def test_status_shows_dimensions(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_test_bond(bond_dir)
        run_status(bond_dir=bond_dir)
        output = capsys.readouterr().out
        assert "identity" in output
        assert "rules" in output
        assert "style" in output
        assert "memory" in output


def test_status_shows_item_counts(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_test_bond(bond_dir)
        run_status(bond_dir=bond_dir)
        output = capsys.readouterr().out
        assert "7" in output  # total items


def test_status_shows_pending(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_test_bond(bond_dir)
        pending = bond_dir / "pending"
        pending.mkdir()
        (pending / "2026-03-29.md").write_text("- [rules] new rule", encoding="utf-8")
        run_status(bond_dir=bond_dir)
        output = capsys.readouterr().out
        assert "Pending" in output or "pending" in output


def test_status_no_bond():
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            run_status(bond_dir=Path(tmpdir))
            assert False, "Should have raised SystemExit"
        except SystemExit:
            pass
