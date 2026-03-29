import tempfile
from pathlib import Path

from claude_bond.models.bond import BondDimension, BondMeta, save_dimension, save_meta
from claude_bond.evolve.merger import parse_pending, merge_items


def test_parse_pending():
    content = """---
date: 2026-03-29
---

## New

- [rules] User said "don't write tests for me"
- [memory] deer-flow deployed

## Updated

- [identity] User switched to backend (was: data scientist)

## Possible (low confidence)

- [style] User prefers shorter replies
"""
    items = parse_pending(content)
    assert len(items) == 4
    assert items[0].dimension == "rules"
    assert items[0].action == "new"
    assert items[1].dimension == "memory"
    assert items[2].dimension == "identity"
    assert items[2].action == "updated"
    assert items[3].confidence == "low"


def test_merge_items_adds_to_dimension():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        save_dimension(
            BondDimension("rules", "2026-03-29", ["scan"], "- No emoji"),
            bond_dir,
        )
        save_meta(BondMeta("0.1.0", "2026-03-29", "2026-03-29"), bond_dir)

        items = parse_pending(
            "---\ndate: 2026-03-29\n---\n\n## New\n\n- [rules] Don't write tests for me\n"
        )
        merge_items(items, bond_dir)

        from claude_bond.models.bond import load_dimension
        rules = load_dimension("rules", bond_dir)
        assert "No emoji" in rules.content
        assert "Don't write tests" in rules.content
