import tempfile
from pathlib import Path
from unittest.mock import patch

from claude_bond.models.bond import BondDimension
from claude_bond.sync_engine.semantic_merge import (
    _naive_merge,
    _parse_conflict,
    semantic_merge_dimension,
)


def test_naive_merge_combines_unique_lines():
    ours = BondDimension("rules", "2026-03-29", ["scan"], "- No emoji\n- Be concise")
    theirs = BondDimension("rules", "2026-03-30", ["scan"], "- No emoji\n- Write tests first")

    merged = _naive_merge(ours, theirs)
    assert "No emoji" in merged.content
    assert "Be concise" in merged.content
    assert "Write tests first" in merged.content
    assert merged.updated == "2026-03-30"


def test_naive_merge_deduplicates():
    ours = BondDimension("style", "2026-03-29", ["scan"], "- Chinese\n- Concise")
    theirs = BondDimension("style", "2026-03-30", ["interview"], "- Chinese\n- Brief replies")

    merged = _naive_merge(ours, theirs)
    # "- Chinese" should appear only once
    assert merged.content.count("Chinese") == 1
    assert "scan" in merged.source
    assert "interview" in merged.source


def test_parse_conflict_markers():
    content = """---
dimension: rules
---

<<<<<<< HEAD
- No emoji
- Be concise
=======
- No emoji
- Write tests first
>>>>>>> origin/main
"""
    ours, theirs = _parse_conflict(content)
    assert "Be concise" in ours
    assert "Write tests first" in theirs


def test_semantic_merge_without_claude():
    """When Claude is unavailable, falls back to naive merge."""
    ours = BondDimension("memory", "2026-03-29", ["scan"], "- Project A\n- Uses Python")
    theirs = BondDimension("memory", "2026-03-30", ["scan"], "- Project A\n- Deployed v2")

    with patch("claude_bond.sync_engine.semantic_merge.can_use_claude", return_value=False):
        merged = semantic_merge_dimension(ours, theirs)

    assert "Project A" in merged.content
    assert "Uses Python" in merged.content
    assert "Deployed v2" in merged.content
