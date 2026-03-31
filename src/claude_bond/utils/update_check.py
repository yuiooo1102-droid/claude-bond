"""Silent version check against GitHub. At most once per day."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from claude_bond.models.bond import BOND_DIR


_CACHE_FILE = BOND_DIR / ".update_check"
_CHECK_INTERVAL = 86400  # 24 hours
_REPO = "yuiooo1102-droid/claude-bond"


def check_for_update() -> str | None:
    """Return latest version string if newer than local, else None. Silent on any error."""
    try:
        # Rate limit: at most once per day
        if _CACHE_FILE.exists():
            cache = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
            if time.time() - cache.get("checked_at", 0) < _CHECK_INTERVAL:
                return cache.get("new_version")

        from claude_bond import __version__ as local_version

        result = subprocess.run(
            ["gh", "api", f"repos/{_REPO}/releases/latest", "--jq", ".tag_name"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            # No releases yet, try tags
            result = subprocess.run(
                ["gh", "api", f"repos/{_REPO}/tags", "--jq", ".[0].name"],
                capture_output=True,
                text=True,
                timeout=5,
            )

        if result.returncode != 0 or not result.stdout.strip():
            _save_cache(None)
            return None

        remote_version = result.stdout.strip().lstrip("v")

        if _is_newer(remote_version, local_version):
            _save_cache(remote_version)
            return remote_version

        _save_cache(None)
        return None

    except Exception:
        return None


def _is_newer(remote: str, local: str) -> bool:
    """Compare semver strings."""
    try:
        remote_parts = [int(x) for x in remote.split(".")]
        local_parts = [int(x) for x in local.split(".")]
        return remote_parts > local_parts
    except (ValueError, AttributeError):
        return False


def _save_cache(new_version: str | None) -> None:
    try:
        BOND_DIR.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(
            json.dumps({"checked_at": time.time(), "new_version": new_version}),
            encoding="utf-8",
        )
    except Exception:
        pass
