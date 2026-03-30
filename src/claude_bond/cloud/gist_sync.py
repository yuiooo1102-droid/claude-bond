from __future__ import annotations

import json
import subprocess
from pathlib import Path

from claude_bond.models.bond import BOND_DIR, DIMENSIONS, load_dimension, load_meta, save_dimension, save_meta, BondDimension, BondMeta


CLOUD_CONFIG = "cloud.json"


def _run_gh(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
    )


def has_gh_cli() -> bool:
    import shutil
    return shutil.which("gh") is not None


def load_cloud_config(bond_dir: Path = BOND_DIR) -> dict:
    path = bond_dir / CLOUD_CONFIG
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cloud_config(config: dict, bond_dir: Path = BOND_DIR) -> None:
    path = bond_dir / CLOUD_CONFIG
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cloud_init(bond_dir: Path = BOND_DIR) -> str:
    """Create a private gist and save its ID. Returns gist ID."""
    if not has_gh_cli():
        raise RuntimeError("gh CLI not found. Install: https://cli.github.com")

    config = load_cloud_config(bond_dir)
    if config.get("gist_id"):
        raise RuntimeError(f"Cloud already initialized (gist: {config['gist_id']}). Use 'bond cloud push' to sync.")

    # Create initial content
    bond_data = _serialize_bond(bond_dir)

    # Write temp file for gist creation
    tmp_file = bond_dir / "_bond_cloud.json"
    tmp_file.write_text(json.dumps(bond_data, ensure_ascii=False, indent=2), encoding="utf-8")

    result = _run_gh(["gist", "create", "--public=false", "-d", "claude-bond cloud sync", str(tmp_file)])
    tmp_file.unlink()

    if result.returncode != 0:
        raise RuntimeError(f"Failed to create gist: {result.stderr}")

    # Extract gist ID from URL
    gist_url = result.stdout.strip()
    gist_id = gist_url.rstrip("/").split("/")[-1]

    config["gist_id"] = gist_id
    config["gist_url"] = gist_url
    save_cloud_config(config, bond_dir)

    return gist_id


def cloud_push(bond_dir: Path = BOND_DIR) -> None:
    """Push local bond to gist."""
    config = load_cloud_config(bond_dir)
    gist_id = config.get("gist_id")
    if not gist_id:
        raise RuntimeError("Cloud not initialized. Run 'bond cloud init' first.")

    bond_data = _serialize_bond(bond_dir)

    tmp_file = bond_dir / "_bond_cloud.json"
    tmp_file.write_text(json.dumps(bond_data, ensure_ascii=False, indent=2), encoding="utf-8")

    result = _run_gh(["gist", "edit", gist_id, "-f", "_bond_cloud.json", str(tmp_file)])
    tmp_file.unlink()

    if result.returncode != 0:
        raise RuntimeError(f"Failed to push to gist: {result.stderr}")


def cloud_pull(bond_dir: Path = BOND_DIR) -> None:
    """Pull bond from gist and write to local files."""
    config = load_cloud_config(bond_dir)
    gist_id = config.get("gist_id")
    if not gist_id:
        raise RuntimeError("Cloud not initialized. Run 'bond cloud init' first.")

    result = _run_gh(["gist", "view", gist_id, "-f", "_bond_cloud.json", "--raw"])
    if result.returncode != 0:
        raise RuntimeError(f"Failed to pull from gist: {result.stderr}")

    bond_data = json.loads(result.stdout)
    _deserialize_bond(bond_data, bond_dir)


def cloud_status(bond_dir: Path = BOND_DIR) -> dict | None:
    """Get cloud sync status."""
    config = load_cloud_config(bond_dir)
    if not config.get("gist_id"):
        return None
    return config


def _serialize_bond(bond_dir: Path) -> dict:
    """Serialize all bond files to a dict."""
    meta = load_meta(bond_dir)
    dimensions = {}
    for dim_name in meta.dimensions:
        try:
            dim = load_dimension(dim_name, bond_dir)
            dimensions[dim_name] = {
                "updated": dim.updated,
                "source": dim.source,
                "content": dim.content,
            }
        except (FileNotFoundError, ValueError):
            pass

    return {
        "version": meta.version,
        "created": meta.created,
        "updated": meta.updated,
        "dimensions_list": meta.dimensions,
        "dimensions": dimensions,
    }


def _deserialize_bond(data: dict, bond_dir: Path) -> None:
    """Deserialize dict to bond files."""
    bond_dir.mkdir(parents=True, exist_ok=True)

    meta = BondMeta(
        version=data["version"],
        created=data["created"],
        updated=data["updated"],
        dimensions=data.get("dimensions_list", list(DIMENSIONS)),
    )
    save_meta(meta, bond_dir)

    for dim_name, dim_data in data.get("dimensions", {}).items():
        dim = BondDimension(
            name=dim_name,
            updated=dim_data["updated"],
            source=dim_data["source"],
            content=dim_data["content"],
        )
        save_dimension(dim, bond_dir)
