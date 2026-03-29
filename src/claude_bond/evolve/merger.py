from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from claude_bond.models.bond import (
    BondDimension,
    load_dimension,
    load_meta,
    save_dimension,
)


@dataclass(frozen=True)
class PendingItem:
    dimension: str
    description: str
    action: str  # "new", "updated", "possible"
    confidence: str  # "high", "low"


_ITEM_RE = re.compile(r"^- \[(\w+)\]\s+(.+)$")


def parse_pending(content: str) -> list[PendingItem]:
    items: list[PendingItem] = []
    current_action = "new"
    current_confidence = "high"

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## New"):
            current_action = "new"
            current_confidence = "high"
        elif stripped.startswith("## Updated"):
            current_action = "updated"
            current_confidence = "high"
        elif stripped.startswith("## Possible"):
            current_action = "possible"
            current_confidence = "low"

        match = _ITEM_RE.match(stripped)
        if match:
            items.append(
                PendingItem(
                    dimension=match.group(1),
                    description=match.group(2),
                    action=current_action,
                    confidence=current_confidence,
                )
            )
    return items


def merge_items(items: list[PendingItem], bond_dir: Path) -> None:
    meta = load_meta(bond_dir)
    today = date.today().isoformat()

    by_dim: dict[str, list[PendingItem]] = {}
    for item in items:
        by_dim.setdefault(item.dimension, []).append(item)

    for dim_name, dim_items in by_dim.items():
        if dim_name not in meta.dimensions:
            continue
        try:
            dim = load_dimension(dim_name, bond_dir)
        except (FileNotFoundError, ValueError):
            dim = BondDimension(dim_name, today, ["evolve"], "")

        new_lines: list[str] = []
        for item in dim_items:
            new_lines.append(f"- {item.description}")

        updated_content = dim.content.rstrip()
        if updated_content:
            updated_content += "\n" + "\n".join(new_lines)
        else:
            updated_content = "\n".join(new_lines)

        updated_dim = BondDimension(
            name=dim_name,
            updated=today,
            source=list(set(dim.source + ["evolve"])),
            content=updated_content,
        )
        save_dimension(updated_dim, bond_dir)
