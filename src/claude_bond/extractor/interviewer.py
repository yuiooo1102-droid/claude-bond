from __future__ import annotations

from datetime import date

from claude_bond.models.bond import BondDimension, DIMENSIONS


def identify_gaps(classified: dict[str, list[str]]) -> dict[str, str]:
    gaps: dict[str, str] = {}
    for dim in DIMENSIONS:
        items = classified.get(dim, [])
        if len(items) == 0:
            gaps[dim] = "no data found"
    return gaps


def build_bond_from_classified(
    classified: dict[str, list[str]],
    sources: dict[str, list[str]] | None = None,
) -> list[BondDimension]:
    today = date.today().isoformat()
    if sources is None:
        sources = {dim: ["scan"] for dim in DIMENSIONS}

    dimensions: list[BondDimension] = []
    for dim in DIMENSIONS:
        items = classified.get(dim, [])
        content = "\n".join(f"- {item}" for item in items) if items else ""
        dimensions.append(
            BondDimension(
                name=dim,
                updated=today,
                source=sources.get(dim, ["scan"]),
                content=content,
            )
        )
    return dimensions
