from __future__ import annotations

import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from claude_bond.models.bond import (
    BOND_DIR,
    DIMENSIONS,
    BondDimension,
    BondMeta,
    load_dimension,
    load_meta,
    save_dimension,
    save_meta,
)


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


def check_gh_auth() -> bool:
    """Check if gh CLI is authenticated."""
    result = _run_gh(["auth", "status"])
    return result.returncode == 0


def load_cloud_config(bond_dir: Path = BOND_DIR) -> dict:
    path = bond_dir / CLOUD_CONFIG
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cloud_config(config: dict, bond_dir: Path = BOND_DIR) -> None:
    bond_dir.mkdir(parents=True, exist_ok=True)  # Fix #2: ensure dir exists
    path = bond_dir / CLOUD_CONFIG
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cloud_init(bond_dir: Path = BOND_DIR) -> str:
    """Create a private gist and save its ID. Returns gist ID."""
    if not has_gh_cli():
        raise RuntimeError("gh CLI not found. Install: https://cli.github.com")

    # Fix #6: friendly auth check
    if not check_gh_auth():
        raise RuntimeError(
            "GitHub 未登录。请先运行: gh auth login"
        )

    config = load_cloud_config(bond_dir)
    if config.get("gist_id"):
        raise RuntimeError(
            f"Cloud already initialized (gist: {config['gist_id']}). "
            "Use 'bond cloud push' to sync."
        )

    bond_data = _serialize_bond(bond_dir)

    # Fix #3: use tempfile for safe cleanup
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        prefix="bond_cloud_",
        delete=False,
        encoding="utf-8",
    ) as f:
        json.dump(bond_data, f, ensure_ascii=False, indent=2)
        tmp_path = Path(f.name)

    try:
        # Fix #1: gh gist create takes file path directly
        result = _run_gh([
            "gist", "create",
            "--public=false",
            "-d", "claude-bond cloud sync",
            "-f", "_bond_cloud.json",
            str(tmp_path),
        ])
    finally:
        tmp_path.unlink(missing_ok=True)

    if result.returncode != 0:
        raise RuntimeError(f"Failed to create gist: {result.stderr}")

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

    if not check_gh_auth():
        raise RuntimeError("GitHub 未登录。请先运行: gh auth login")

    bond_data = _serialize_bond(bond_dir)

    # Fix #1 & #3: use tempfile, correct gh gist edit usage
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        prefix="bond_cloud_",
        delete=False,
        encoding="utf-8",
    ) as f:
        json.dump(bond_data, f, ensure_ascii=False, indent=2)
        tmp_path = Path(f.name)

    try:
        result = _run_gh(["gist", "edit", gist_id, "-f", "_bond_cloud.json", str(tmp_path)])
    finally:
        tmp_path.unlink(missing_ok=True)

    if result.returncode != 0:
        raise RuntimeError(f"Failed to push to gist: {result.stderr}")

    # Update last push timestamp
    config["last_push"] = datetime.now().isoformat()
    save_cloud_config(config, bond_dir)


def cloud_pull(bond_dir: Path = BOND_DIR) -> dict:
    """Pull bond from gist. Returns the pulled data dict."""
    config = load_cloud_config(bond_dir)
    gist_id = config.get("gist_id")
    if not gist_id:
        raise RuntimeError("Cloud not initialized. Run 'bond cloud init' first.")

    if not check_gh_auth():
        raise RuntimeError("GitHub 未登录。请先运行: gh auth login")

    result = _run_gh(["gist", "view", gist_id, "-f", "_bond_cloud.json", "--raw"])
    if result.returncode != 0:
        raise RuntimeError(f"Failed to pull from gist: {result.stderr}")

    bond_data = json.loads(result.stdout)
    _deserialize_bond(bond_data, bond_dir)

    config["last_pull"] = datetime.now().isoformat()
    save_cloud_config(config, bond_dir)

    return bond_data


def cloud_sync(bond_dir: Path = BOND_DIR) -> None:
    """Smart sync: merge remote and local, then push."""
    config = load_cloud_config(bond_dir)
    gist_id = config.get("gist_id")
    if not gist_id:
        raise RuntimeError("Cloud not initialized. Run 'bond cloud init' first.")

    # Fix #4: smart merge instead of blind overwrite
    # Step 1: serialize local state BEFORE pulling
    local_data = _serialize_bond(bond_dir)

    # Step 2: pull remote
    result = _run_gh(["gist", "view", gist_id, "-f", "_bond_cloud.json", "--raw"])
    if result.returncode == 0:
        remote_data = json.loads(result.stdout)
        # Step 3: merge remote into local
        merged_data = _merge_bond_data(local_data, remote_data)
        _deserialize_bond(merged_data, bond_dir)
    # If pull fails (no remote yet), just use local

    # Step 4: push merged result
    cloud_push(bond_dir)


def cloud_status(bond_dir: Path = BOND_DIR) -> dict | None:
    """Get cloud sync status."""
    config = load_cloud_config(bond_dir)
    if not config.get("gist_id"):
        return None
    return config


def _merge_bond_data(local: dict, remote: dict) -> dict:
    """Fix #4: merge two bond data dicts, keeping unique items from both."""
    merged = {
        "version": max(local.get("version", "0"), remote.get("version", "0")),
        "created": min(local.get("created", ""), remote.get("created", "")),
        "updated": max(local.get("updated", ""), remote.get("updated", "")),
        "dimensions_list": local.get("dimensions_list", list(DIMENSIONS)),
    }

    # Merge dimensions
    local_dims = local.get("dimensions", {})
    remote_dims = remote.get("dimensions", {})
    all_dim_names = set(local_dims.keys()) | set(remote_dims.keys())

    merged_dims: dict = {}
    for dim_name in all_dim_names:
        local_dim = local_dims.get(dim_name)
        remote_dim = remote_dims.get(dim_name)

        if local_dim and not remote_dim:
            merged_dims[dim_name] = local_dim
        elif remote_dim and not local_dim:
            merged_dims[dim_name] = remote_dim
        elif local_dim and remote_dim:
            # Both have it: merge content lines
            local_lines = set(
                line.strip() for line in local_dim["content"].splitlines() if line.strip()
            )
            remote_lines = set(
                line.strip() for line in remote_dim["content"].splitlines() if line.strip()
            )
            all_lines = sorted(local_lines | remote_lines)
            merged_dims[dim_name] = {
                "updated": max(local_dim["updated"], remote_dim["updated"]),
                "source": sorted(set(local_dim["source"] + remote_dim["source"])),
                "content": "\n".join(all_lines),
            }

    merged["dimensions"] = merged_dims

    # Ensure dimensions_list covers all merged dims
    dim_list = list(merged["dimensions_list"])
    for name in merged_dims:
        if name not in dim_list:
            dim_list.append(name)
    merged["dimensions_list"] = dim_list

    return merged


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
