import tempfile
from pathlib import Path

from claude_bond.models.bond import BondDimension, BondMeta, DIMENSIONS, save_dimension, save_meta, load_dimension
from claude_bond.cloud.three_way_merge import (
    three_way_merge,
    _merge_dimension_items,
    save_sync_base,
    load_sync_base,
    has_sync_base,
    parse_remote_state,
    apply_merged_state,
    count_items,
)


def _create_bond(bond_dir: Path, rules_content: str = "- No emoji\n- Be concise") -> None:
    bond_dir.mkdir(parents=True, exist_ok=True)
    save_dimension(BondDimension("rules", "2026-03-30", ["scan"], rules_content), bond_dir)
    save_dimension(BondDimension("style", "2026-03-30", ["scan"], "- Chinese"), bond_dir)
    save_meta(BondMeta("0.2.0", "2026-03-30", "2026-03-30"), bond_dir)


# --- Item-level merge tests ---

def test_both_keep_unchanged():
    base = {"- No emoji", "- Be concise"}
    local = {"- No emoji", "- Be concise"}
    remote = {"- No emoji", "- Be concise"}
    result = _merge_dimension_items(base, local, remote)
    assert result == {"- No emoji", "- Be concise"}


def test_local_added():
    base = {"- No emoji"}
    local = {"- No emoji", "- Be concise"}
    remote = {"- No emoji"}
    result = _merge_dimension_items(base, local, remote)
    assert "- Be concise" in result
    assert "- No emoji" in result


def test_remote_added():
    base = {"- No emoji"}
    local = {"- No emoji"}
    remote = {"- No emoji", "- Write tests"}
    result = _merge_dimension_items(base, local, remote)
    assert "- Write tests" in result


def test_local_deleted():
    base = {"- No emoji", "- Use tabs"}
    local = {"- No emoji"}  # deleted "Use tabs"
    remote = {"- No emoji", "- Use tabs"}
    result = _merge_dimension_items(base, local, remote)
    assert "- Use tabs" not in result  # deletion respected
    assert "- No emoji" in result


def test_remote_deleted():
    base = {"- No emoji", "- Use tabs"}
    local = {"- No emoji", "- Use tabs"}
    remote = {"- No emoji"}  # deleted "Use tabs"
    result = _merge_dimension_items(base, local, remote)
    assert "- Use tabs" not in result


def test_both_deleted():
    base = {"- No emoji", "- Use tabs"}
    local = {"- No emoji"}
    remote = {"- No emoji"}
    result = _merge_dimension_items(base, local, remote)
    assert result == {"- No emoji"}


def test_both_added_same():
    base = {"- No emoji"}
    local = {"- No emoji", "- Be concise"}
    remote = {"- No emoji", "- Be concise"}
    result = _merge_dimension_items(base, local, remote)
    assert result == {"- No emoji", "- Be concise"}


def test_both_added_different():
    base = {"- No emoji"}
    local = {"- No emoji", "- Be concise"}
    remote = {"- No emoji", "- Write tests"}
    result = _merge_dimension_items(base, local, remote)
    assert result == {"- No emoji", "- Be concise", "- Write tests"}


def test_cross_changes():
    """Local adds + remote deletes different items."""
    base = {"- No emoji", "- Use tabs"}
    local = {"- No emoji", "- Use tabs", "- Be concise"}  # added concise
    remote = {"- No emoji"}  # deleted Use tabs
    result = _merge_dimension_items(base, local, remote)
    assert "- No emoji" in result
    assert "- Be concise" in result  # local add kept
    assert "- Use tabs" not in result  # remote delete respected


# --- Dimension-level merge tests ---

def test_three_way_merge_multiple_dimensions():
    base = {"rules": {"- No emoji"}, "style": {"- Chinese"}}
    local = {"rules": {"- No emoji", "- Be concise"}, "style": {"- Chinese"}}
    remote = {"rules": {"- No emoji"}, "style": {"- Chinese", "- Brief"}}

    merged = three_way_merge(base, local, remote)
    assert "- Be concise" in merged["rules"]
    assert "- Brief" in merged["style"]


def test_three_way_merge_new_dimension():
    base = {"rules": {"- No emoji"}}
    local = {"rules": {"- No emoji"}}
    remote = {"rules": {"- No emoji"}, "memory": {"- Project X"}}

    merged = three_way_merge(base, local, remote)
    assert "- Project X" in merged["memory"]


# --- Sync base tests ---

def test_save_and_load_sync_base():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_bond(bond_dir)

        save_sync_base(bond_dir)
        assert has_sync_base(bond_dir)

        base = load_sync_base(bond_dir)
        assert "- No emoji" in base["rules"]
        assert "- Chinese" in base["style"]


def test_has_sync_base_false():
    with tempfile.TemporaryDirectory() as tmpdir:
        assert not has_sync_base(Path(tmpdir))


def test_count_items():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_bond(bond_dir)
        assert count_items(bond_dir) == 3  # No emoji, Be concise, Chinese


# --- Parse remote ---

def test_parse_remote_state():
    remote_data = {
        "dimensions": {
            "rules": {"content": "- No emoji\n- Write tests", "source": ["scan"], "updated": "2026-03-30"},
        }
    }
    state = parse_remote_state(remote_data)
    assert "- No emoji" in state["rules"]
    assert "- Write tests" in state["rules"]


# --- Full integration ---

def test_apply_merged_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_bond(bond_dir)

        merged = {"rules": {"- No emoji", "- Be concise", "- Write tests"}, "style": {"- Chinese"}}
        remote_data = {"version": "0.2.0", "created": "2026-03-30", "updated": "2026-03-30", "dimensions": {}}

        apply_merged_state(merged, bond_dir, remote_data)

        rules = load_dimension("rules", bond_dir)
        assert "No emoji" in rules.content
        assert "Write tests" in rules.content
