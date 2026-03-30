from __future__ import annotations

import shutil
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


SYNC_BASE_DIR = ".sync_base"


def save_sync_base(bond_dir: Path) -> None:
    """Save current bond state as the sync base for future three-way merges."""
    base_dir = bond_dir / SYNC_BASE_DIR
    if base_dir.exists():
        shutil.rmtree(base_dir)
    base_dir.mkdir(parents=True)

    try:
        meta = load_meta(bond_dir)
    except (FileNotFoundError, Exception):
        return

    # Save meta
    save_meta(meta, base_dir)

    # Save each dimension
    for dim_name in meta.dimensions:
        try:
            dim = load_dimension(dim_name, bond_dir)
            save_dimension(dim, base_dir)
        except (FileNotFoundError, ValueError):
            pass


def load_sync_base(bond_dir: Path) -> dict[str, set[str]]:
    """Load sync base as dimension -> set of content lines."""
    base_dir = bond_dir / SYNC_BASE_DIR
    return _load_dimensions_as_sets(base_dir)


def has_sync_base(bond_dir: Path) -> bool:
    """Check if a sync base exists."""
    base_dir = bond_dir / SYNC_BASE_DIR
    return base_dir.exists() and (base_dir / "bond.yaml").exists()


def load_local_state(bond_dir: Path) -> dict[str, set[str]]:
    """Load current local bond as dimension -> set of content lines."""
    return _load_dimensions_as_sets(bond_dir)


def parse_remote_state(remote_data: dict) -> dict[str, set[str]]:
    """Parse remote JSON data as dimension -> set of content lines."""
    result: dict[str, set[str]] = {}
    for dim_name, dim_data in remote_data.get("dimensions", {}).items():
        lines = set()
        for line in dim_data.get("content", "").splitlines():
            stripped = line.strip()
            if stripped:
                lines.add(stripped)
        result[dim_name] = lines
    return result


def three_way_merge(
    base: dict[str, set[str]],
    local: dict[str, set[str]],
    remote: dict[str, set[str]],
) -> dict[str, set[str]]:
    """Perform three-way merge across all dimensions.

    Returns merged state as dimension -> set of content lines.
    """
    all_dims = set(base.keys()) | set(local.keys()) | set(remote.keys())
    merged: dict[str, set[str]] = {}

    for dim in all_dims:
        base_items = base.get(dim, set())
        local_items = local.get(dim, set())
        remote_items = remote.get(dim, set())

        merged[dim] = _merge_dimension_items(base_items, local_items, remote_items)

    return merged


def _merge_dimension_items(
    base: set[str],
    local: set[str],
    remote: set[str],
) -> set[str]:
    """Three-way merge for a single dimension's items."""
    result: set[str] = set()

    all_items = base | local | remote

    for item in all_items:
        in_base = item in base
        in_local = item in local
        in_remote = item in remote

        if in_base and in_local and in_remote:
            # All three have it: keep
            result.add(item)
        elif in_base and not in_local and in_remote:
            # Local deleted it: respect deletion
            pass
        elif in_base and in_local and not in_remote:
            # Remote deleted it: respect deletion
            pass
        elif in_base and not in_local and not in_remote:
            # Both deleted: gone
            pass
        elif not in_base and in_local and not in_remote:
            # Local added: keep
            result.add(item)
        elif not in_base and not in_local and in_remote:
            # Remote added: keep
            result.add(item)
        elif not in_base and in_local and in_remote:
            # Both added same item: keep
            result.add(item)

    return result


def apply_merged_state(
    merged: dict[str, set[str]],
    bond_dir: Path,
    remote_data: dict,
) -> None:
    """Write merged state back to bond files."""
    from datetime import date

    today = date.today().isoformat()

    # Determine dimensions list
    try:
        meta = load_meta(bond_dir)
        dim_list = list(meta.dimensions)
    except (FileNotFoundError, Exception):
        dim_list = list(DIMENSIONS)

    # Add any new dimensions from merged state
    for dim_name in merged:
        if dim_name not in dim_list:
            dim_list.append(dim_name)

    # Write each dimension
    for dim_name, items in merged.items():
        content = "\n".join(sorted(items)) if items else ""

        # Try to preserve source info from local or remote
        source = ["sync"]
        try:
            existing = load_dimension(dim_name, bond_dir)
            source = list(set(existing.source + ["sync"]))
        except (FileNotFoundError, ValueError):
            remote_dims = remote_data.get("dimensions", {})
            if dim_name in remote_dims:
                source = list(set(remote_dims[dim_name].get("source", []) + ["sync"]))

        dim = BondDimension(
            name=dim_name,
            updated=today,
            source=source,
            content=content,
        )
        save_dimension(dim, bond_dir)

    # Update meta
    new_meta = BondMeta(
        version=remote_data.get("version", "0.2.0"),
        created=remote_data.get("created", today),
        updated=today,
        dimensions=dim_list,
    )
    save_meta(new_meta, bond_dir)


def count_items(bond_dir: Path) -> int:
    """Count total items across all dimensions."""
    total = 0
    try:
        meta = load_meta(bond_dir)
        for dim_name in meta.dimensions:
            try:
                dim = load_dimension(dim_name, bond_dir)
                lines = [line for line in dim.content.splitlines() if line.strip()]
                total += len(lines)
            except (FileNotFoundError, ValueError):
                pass
    except (FileNotFoundError, Exception):
        pass
    return total


def _load_dimensions_as_sets(dir_path: Path) -> dict[str, set[str]]:
    """Load all dimensions from a directory as sets of content lines."""
    result: dict[str, set[str]] = {}
    try:
        meta = load_meta(dir_path)
    except (FileNotFoundError, Exception):
        return result

    for dim_name in meta.dimensions:
        try:
            dim = load_dimension(dim_name, dir_path)
            lines = set()
            for line in dim.content.splitlines():
                stripped = line.strip()
                if stripped:
                    lines.add(stripped)
            result[dim_name] = lines
        except (FileNotFoundError, ValueError):
            pass

    return result
