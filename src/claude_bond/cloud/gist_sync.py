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
from claude_bond.cloud.three_way_merge import (
    save_sync_base,
    load_sync_base,
    has_sync_base,
    load_local_state,
    parse_remote_state,
    three_way_merge,
    apply_merged_state,
    count_items,
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
    bond_dir.mkdir(parents=True, exist_ok=True)
    path = bond_dir / CLOUD_CONFIG
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cloud_init(bond_dir: Path = BOND_DIR) -> str:
    """Create a private gist and save its ID. Returns gist ID."""
    if not has_gh_cli():
        raise RuntimeError("gh CLI not found. Install: https://cli.github.com")

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

    save_sync_base(bond_dir)

    return gist_id


def cloud_push(bond_dir: Path = BOND_DIR, force: bool = False) -> None:
    """Push local bond to gist. Protected against accidental overwrites."""
    config = load_cloud_config(bond_dir)
    gist_id = config.get("gist_id")
    if not gist_id:
        raise RuntimeError("Cloud not initialized. Run 'bond cloud init' first.")

    if not check_gh_auth():
        raise RuntimeError("GitHub 未登录。请先运行: gh auth login")

    # Push protection: require sync base (means we've pulled at least once)
    if not force and not has_sync_base(bond_dir):
        # Check if this is the device that did cloud init (has gist_url in config)
        if not config.get("gist_url"):
            raise RuntimeError(
                "从未同步过。请先运行 bond cloud pull 拉取云端数据。\n"
                "如确定要覆盖云端，使用 bond cloud push --force"
            )

    # Push protection: warn if local has significantly fewer items than remote
    if not force:
        try:
            remote_data = _fetch_remote(gist_id)
            if remote_data:
                remote_count = sum(
                    len([l for l in d.get("content", "").splitlines() if l.strip()])
                    for d in remote_data.get("dimensions", {}).values()
                )
                local_count = count_items(bond_dir)
                if remote_count > 0 and local_count < remote_count * 0.5:
                    raise RuntimeError(
                        f"⚠ 本地 {local_count} 条，云端 {remote_count} 条。\n"
                        f"  这看起来像是新设备，建议先 bond cloud pull。\n"
                        f"  确定要覆盖？使用 bond cloud push --force"
                    )
        except json.JSONDecodeError:
            pass  # Remote empty or invalid, safe to push

    bond_data = _serialize_bond(bond_dir)
    _upload_to_gist(gist_id, bond_data, bond_dir)

    # Update sync base after successful push
    save_sync_base(bond_dir)

    config["last_push"] = datetime.now().isoformat()
    save_cloud_config(config, bond_dir)


def cloud_pull(bond_dir: Path = BOND_DIR) -> dict:
    """Pull bond from gist with three-way merge."""
    config = load_cloud_config(bond_dir)
    gist_id = config.get("gist_id")
    if not gist_id:
        raise RuntimeError("Cloud not initialized. Run 'bond cloud init' first.")

    if not check_gh_auth():
        raise RuntimeError("GitHub 未登录。请先运行: gh auth login")

    remote_data = _fetch_remote(gist_id)
    if not remote_data:
        raise RuntimeError("Failed to fetch remote data.")

    if has_sync_base(bond_dir):
        # Three-way merge
        base = load_sync_base(bond_dir)
        local = load_local_state(bond_dir)
        remote = parse_remote_state(remote_data)
        merged = three_way_merge(base, local, remote)
        apply_merged_state(merged, bond_dir, remote_data)
    else:
        # First pull: no base, just write remote data
        _deserialize_bond(remote_data, bond_dir)

    # Save sync base after pull
    save_sync_base(bond_dir)

    config["last_pull"] = datetime.now().isoformat()
    save_cloud_config(config, bond_dir)

    return remote_data


def cloud_sync(bond_dir: Path = BOND_DIR) -> None:
    """Smart sync: three-way merge pull, then push."""
    config = load_cloud_config(bond_dir)
    gist_id = config.get("gist_id")
    if not gist_id:
        raise RuntimeError("Cloud not initialized. Run 'bond cloud init' first.")

    # Pull with three-way merge
    try:
        cloud_pull(bond_dir)
    except RuntimeError:
        pass  # Remote might be empty on first sync

    # Push merged result (force=True since we just merged)
    cloud_push(bond_dir, force=True)


def cloud_status(bond_dir: Path = BOND_DIR) -> dict | None:
    """Get cloud sync status."""
    config = load_cloud_config(bond_dir)
    if not config.get("gist_id"):
        return None
    return config


def _fetch_remote(gist_id: str) -> dict | None:
    """Fetch remote bond data from gist."""
    result = _run_gh(["gist", "view", gist_id, "-f", "_bond_cloud.json", "--raw"])
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _upload_to_gist(gist_id: str, bond_data: dict, bond_dir: Path) -> None:
    """Upload bond data to gist."""
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
        raise RuntimeError(f"Failed to upload to gist: {result.stderr}")


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
