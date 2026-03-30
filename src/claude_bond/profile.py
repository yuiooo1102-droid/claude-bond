from __future__ import annotations

from pathlib import Path

from claude_bond.models.bond import BOND_DIR


PROFILES_DIR = BOND_DIR / "profiles"
ACTIVE_FILE = BOND_DIR / "active_profile"
DEFAULT_PROFILE = "default"


def get_active_profile() -> str:
    if ACTIVE_FILE.exists():
        return ACTIVE_FILE.read_text(encoding="utf-8").strip()
    return DEFAULT_PROFILE


def set_active_profile(name: str) -> None:
    BOND_DIR.mkdir(parents=True, exist_ok=True)
    ACTIVE_FILE.write_text(name, encoding="utf-8")


def get_profile_dir(name: str | None = None) -> Path:
    if name is None:
        name = get_active_profile()
    return PROFILES_DIR / name


def list_profiles() -> list[str]:
    if not PROFILES_DIR.exists():
        return []
    return sorted(
        d.name for d in PROFILES_DIR.iterdir()
        if d.is_dir() and (d / "bond.yaml").exists()
    )


def profile_exists(name: str) -> bool:
    return (PROFILES_DIR / name / "bond.yaml").exists()


def get_bond_dir() -> Path:
    """Get the bond_dir for the active profile. Falls back to BOND_DIR for legacy layout."""
    profile_dir = get_profile_dir()
    if profile_dir.exists() and (profile_dir / "bond.yaml").exists():
        return profile_dir
    # Legacy: bond files directly in BOND_DIR
    if (BOND_DIR / "bond.yaml").exists():
        return BOND_DIR
    return profile_dir


def migrate_to_profiles() -> bool:
    """Migrate legacy flat layout to profile-based layout. Returns True if migrated."""
    if PROFILES_DIR.exists():
        return False
    if not (BOND_DIR / "bond.yaml").exists():
        return False

    import shutil
    default_dir = PROFILES_DIR / DEFAULT_PROFILE
    default_dir.mkdir(parents=True)

    # Move bond files to default profile
    for item in BOND_DIR.iterdir():
        if item.name in ("profiles", "active_profile", "tacit_signals.json", ".snapshot"):
            continue
        if item.name.startswith("."):
            continue
        if item.is_file():
            shutil.move(str(item), str(default_dir / item.name))
        elif item.is_dir() and item.name in ("pending",):
            shutil.move(str(item), str(default_dir / item.name))

    set_active_profile(DEFAULT_PROFILE)
    return True
