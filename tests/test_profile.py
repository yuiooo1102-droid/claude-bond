import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from claude_bond.models.bond import BondDimension, BondMeta, DIMENSIONS, save_dimension, save_meta
from claude_bond.profile import (
    get_active_profile,
    set_active_profile,
    get_profile_dir,
    list_profiles,
    profile_exists,
    migrate_to_profiles,
    PROFILES_DIR,
    ACTIVE_FILE,
    DEFAULT_PROFILE,
)


def _create_bond_in(bond_dir: Path) -> None:
    bond_dir.mkdir(parents=True, exist_ok=True)
    for dim_name in DIMENSIONS:
        save_dimension(
            BondDimension(dim_name, "2026-03-30", ["scan"], f"- {dim_name} data"),
            bond_dir,
        )
    save_meta(BondMeta("0.2.0", "2026-03-30", "2026-03-30"), bond_dir)


def test_get_active_profile_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("claude_bond.profile.ACTIVE_FILE", Path(tmpdir) / "active_profile"):
            result = get_active_profile()
            assert result == DEFAULT_PROFILE


def test_set_and_get_active_profile():
    with tempfile.TemporaryDirectory() as tmpdir:
        active_file = Path(tmpdir) / "active_profile"
        bond_dir = Path(tmpdir)
        with patch("claude_bond.profile.ACTIVE_FILE", active_file), \
             patch("claude_bond.profile.BOND_DIR", bond_dir):
            set_active_profile("work")
            with patch("claude_bond.profile.ACTIVE_FILE", active_file):
                assert get_active_profile() == "work"


def test_list_profiles():
    with tempfile.TemporaryDirectory() as tmpdir:
        profiles_dir = Path(tmpdir) / "profiles"
        _create_bond_in(profiles_dir / "default")
        _create_bond_in(profiles_dir / "work")

        with patch("claude_bond.profile.PROFILES_DIR", profiles_dir):
            result = list_profiles()
            assert "default" in result
            assert "work" in result
            assert len(result) == 2


def test_profile_exists():
    with tempfile.TemporaryDirectory() as tmpdir:
        profiles_dir = Path(tmpdir) / "profiles"
        _create_bond_in(profiles_dir / "work")

        with patch("claude_bond.profile.PROFILES_DIR", profiles_dir):
            assert profile_exists("work") is True
            assert profile_exists("personal") is False


def test_migrate_to_profiles():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        profiles_dir = bond_dir / "profiles"
        active_file = bond_dir / "active_profile"

        # Create legacy flat layout
        _create_bond_in(bond_dir)
        (bond_dir / "pending").mkdir()

        with patch("claude_bond.profile.BOND_DIR", bond_dir), \
             patch("claude_bond.profile.PROFILES_DIR", profiles_dir), \
             patch("claude_bond.profile.ACTIVE_FILE", active_file):
            result = migrate_to_profiles()

        assert result is True
        assert (profiles_dir / "default" / "bond.yaml").exists()
        assert (profiles_dir / "default" / "identity.md").exists()
        assert (profiles_dir / "default" / "pending").is_dir()
        assert not (bond_dir / "bond.yaml").exists()  # moved out


def test_migrate_idempotent():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        profiles_dir = bond_dir / "profiles"
        profiles_dir.mkdir(parents=True)

        with patch("claude_bond.profile.BOND_DIR", bond_dir), \
             patch("claude_bond.profile.PROFILES_DIR", profiles_dir):
            result = migrate_to_profiles()

        assert result is False  # already has profiles dir
