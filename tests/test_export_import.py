import tempfile
import zipfile
from pathlib import Path

from claude_bond.models.bond import BondDimension, BondMeta, save_dimension, save_meta
from claude_bond.commands.export_cmd import run_export
from claude_bond.commands.import_cmd import run_import


def _create_test_bond(bond_dir: Path) -> None:
    dims = [
        BondDimension("identity", "2026-03-29", ["scan"], "- Data scientist"),
        BondDimension("rules", "2026-03-29", ["scan"], "- No emoji"),
        BondDimension("style", "2026-03-29", ["interview"], "- Chinese"),
        BondDimension("memory", "2026-03-29", ["scan"], "- Project X"),
    ]
    for d in dims:
        save_dimension(d, bond_dir)
    save_meta(BondMeta("0.1.0", "2026-03-29", "2026-03-29"), bond_dir)


def test_export_creates_bond_file():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as out_tmp:
        bond_dir = Path(bond_tmp)
        _create_test_bond(bond_dir)
        output = Path(out_tmp) / "test.bond"
        run_export(bond_dir=bond_dir, output=output)
        assert output.exists()
        assert output.stat().st_size > 0


def test_import_restores_bond():
    with (
        tempfile.TemporaryDirectory() as src_tmp,
        tempfile.TemporaryDirectory() as out_tmp,
        tempfile.TemporaryDirectory() as dst_tmp,
    ):
        src_bond = Path(src_tmp)
        _create_test_bond(src_bond)

        bond_file = Path(out_tmp) / "test.bond"
        run_export(bond_dir=src_bond, output=bond_file)

        dst_bond = Path(dst_tmp)
        run_import(file=bond_file, bond_dir=dst_bond, auto_apply=False)

        assert (dst_bond / "identity.md").exists()
        assert (dst_bond / "bond.yaml").exists()
        content = (dst_bond / "identity.md").read_text(encoding="utf-8")
        assert "Data scientist" in content


def test_encrypted_export_import():
    with (
        tempfile.TemporaryDirectory() as bond_tmp,
        tempfile.TemporaryDirectory() as out_tmp,
        tempfile.TemporaryDirectory() as dst_tmp,
    ):
        src_bond = Path(bond_tmp)
        _create_test_bond(src_bond)

        bond_file = Path(out_tmp) / "encrypted.bond"
        run_export(bond_dir=src_bond, output=bond_file, password="test123")

        # Verify it's encrypted (starts with BOND magic)
        assert bond_file.read_bytes()[:4] == b"BOND"

        dst_bond = Path(dst_tmp)
        run_import(file=bond_file, bond_dir=dst_bond, auto_apply=False, password="test123")

        assert (dst_bond / "identity.md").exists()
        content = (dst_bond / "identity.md").read_text(encoding="utf-8")
        assert "Data scientist" in content


def test_export_excludes_snapshot_and_pending():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as out_tmp:
        bond_dir = Path(bond_tmp)
        _create_test_bond(bond_dir)
        (bond_dir / ".snapshot").mkdir()
        (bond_dir / ".snapshot" / "CLAUDE.md").write_text("snapshot", encoding="utf-8")
        (bond_dir / "pending").mkdir()
        (bond_dir / "pending" / "2026-03-29.md").write_text("pending", encoding="utf-8")

        output = Path(out_tmp) / "test.bond"
        run_export(bond_dir=bond_dir, output=output)

        with zipfile.ZipFile(output, "r") as zf:
            names = zf.namelist()
            assert not any(".snapshot" in n for n in names)
            assert not any("pending" in n for n in names)
