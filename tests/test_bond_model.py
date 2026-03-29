from pathlib import Path
import tempfile

from claude_bond.models.bond import (
    BondDimension,
    BondMeta,
    load_dimension,
    save_dimension,
    load_meta,
    save_meta,
    BOND_DIR,
)


def test_bond_dimension_from_markdown():
    md = """---
dimension: identity
updated: "2026-03-29"
source: [scan, interview]
---

- Data scientist focused on NLP
- Python as main language
"""
    dim = BondDimension.from_markdown(md)
    assert dim.name == "identity"
    assert dim.updated == "2026-03-29"
    assert dim.source == ["scan", "interview"]
    assert "Data scientist" in dim.content


def test_bond_dimension_to_markdown():
    dim = BondDimension(
        name="rules",
        updated="2026-03-29",
        source=["scan"],
        content="- No emoji in responses\n- No trailing summaries",
    )
    md = dim.to_markdown()
    assert "dimension: rules" in md
    assert "No emoji" in md


def test_save_and_load_dimension():
    dim = BondDimension(
        name="style",
        updated="2026-03-29",
        source=["interview"],
        content="- Language: Chinese\n- Style: concise",
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        save_dimension(dim, Path(tmpdir))
        loaded = load_dimension("style", Path(tmpdir))
        assert loaded.name == "style"
        assert "Chinese" in loaded.content


def test_bond_meta_roundtrip():
    meta = BondMeta(
        version="0.1.0",
        created="2026-03-29",
        updated="2026-03-29",
        dimensions=["identity", "rules", "style", "memory"],
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        save_meta(meta, Path(tmpdir))
        loaded = load_meta(Path(tmpdir))
        assert loaded.version == "0.1.0"
        assert loaded.dimensions == ["identity", "rules", "style", "memory"]


def test_bond_dir_default():
    assert BOND_DIR == Path.home() / ".claude-bond"
