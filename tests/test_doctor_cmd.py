import tempfile
from pathlib import Path

from claude_bond.models.bond import BondDimension, BondMeta, DIMENSIONS, save_dimension, save_meta
from claude_bond.commands.doctor_cmd import run_doctor


def _create_healthy_bond(bond_dir: Path) -> None:
    for dim_name in DIMENSIONS:
        save_dimension(
            BondDimension(dim_name, "2026-03-30", ["scan"], f"- {dim_name} item"),
            bond_dir,
        )
    save_meta(BondMeta("0.2.0", "2026-03-30", "2026-03-30"), bond_dir)
    (bond_dir / "pending").mkdir(exist_ok=True)
    snapshot = bond_dir / ".snapshot"
    snapshot.mkdir(exist_ok=True)
    (snapshot / "CLAUDE.md").write_text("placeholder", encoding="utf-8")


def test_doctor_healthy_bond():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_healthy_bond(bond_dir)
        issues = run_doctor(bond_dir=bond_dir)
        errors = [i for i in issues if i["level"] == "error"]
        assert len(errors) == 0


def test_doctor_missing_bond():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir) / "nonexistent"
        issues = run_doctor(bond_dir=bond_dir)
        assert len(issues) == 1
        assert issues[0]["level"] == "error"


def test_doctor_missing_dimension():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_healthy_bond(bond_dir)
        (bond_dir / "toolchain.md").unlink()
        issues = run_doctor(bond_dir=bond_dir)
        warnings = [i for i in issues if i["level"] == "warning"]
        assert any("toolchain" in w["msg"] for w in warnings)


def test_doctor_empty_dimension():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_healthy_bond(bond_dir)
        save_dimension(
            BondDimension("style", "2026-03-30", ["scan"], ""),
            bond_dir,
        )
        issues = run_doctor(bond_dir=bond_dir)
        infos = [i for i in issues if i["level"] == "info"]
        assert any("Empty" in i["msg"] and "style" in i["msg"] for i in infos)


def test_doctor_no_snapshot():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_healthy_bond(bond_dir)
        import shutil
        shutil.rmtree(bond_dir / ".snapshot")
        issues = run_doctor(bond_dir=bond_dir)
        warnings = [i for i in issues if i["level"] == "warning"]
        assert any("snapshot" in w["msg"].lower() for w in warnings)
