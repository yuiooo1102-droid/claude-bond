import tempfile
from pathlib import Path

from claude_bond.models.bond import BondDimension, BondMeta, DIMENSIONS, save_dimension, save_meta, load_dimension, load_meta
from claude_bond.cloud.gist_sync import (
    _serialize_bond,
    _deserialize_bond,
    _merge_bond_data,
    load_cloud_config,
    save_cloud_config,
)


def _create_test_bond(bond_dir: Path) -> None:
    for dim_name in DIMENSIONS:
        save_dimension(
            BondDimension(dim_name, "2026-03-30", ["scan"], f"- {dim_name} item 1\n- {dim_name} item 2"),
            bond_dir,
        )
    save_meta(BondMeta("0.2.0", "2026-03-30", "2026-03-30"), bond_dir)


def test_serialize_roundtrip():
    with tempfile.TemporaryDirectory() as src_tmp, tempfile.TemporaryDirectory() as dst_tmp:
        src = Path(src_tmp)
        dst = Path(dst_tmp)
        _create_test_bond(src)

        data = _serialize_bond(src)
        _deserialize_bond(data, dst)

        # Verify meta
        meta = load_meta(dst)
        assert meta.version == "0.2.0"
        assert len(meta.dimensions) == 7

        # Verify dimensions
        for dim_name in DIMENSIONS:
            dim = load_dimension(dim_name, dst)
            assert f"{dim_name} item 1" in dim.content
            assert f"{dim_name} item 2" in dim.content


def test_serialize_preserves_sources():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        save_dimension(
            BondDimension("rules", "2026-03-30", ["scan", "interview"], "- No emoji"),
            bond_dir,
        )
        save_meta(BondMeta("0.2.0", "2026-03-30", "2026-03-30"), bond_dir)

        data = _serialize_bond(bond_dir)
        assert "scan" in data["dimensions"]["rules"]["source"]
        assert "interview" in data["dimensions"]["rules"]["source"]


def test_cloud_config_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        config = {"gist_id": "abc123", "gist_url": "https://gist.github.com/abc123"}
        save_cloud_config(config, bond_dir)

        loaded = load_cloud_config(bond_dir)
        assert loaded["gist_id"] == "abc123"


def test_cloud_config_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = load_cloud_config(Path(tmpdir))
        assert config == {}


def test_deserialize_creates_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        dst = Path(tmpdir) / "new_bond"
        data = {
            "version": "0.2.0",
            "created": "2026-03-30",
            "updated": "2026-03-30",
            "dimensions_list": ["identity", "rules"],
            "dimensions": {
                "identity": {"updated": "2026-03-30", "source": ["cloud"], "content": "- Developer"},
                "rules": {"updated": "2026-03-30", "source": ["cloud"], "content": "- No emoji"},
            },
        }
        _deserialize_bond(data, dst)
        assert (dst / "bond.yaml").exists()
        assert (dst / "identity.md").exists()
        dim = load_dimension("identity", dst)
        assert "Developer" in dim.content


def test_merge_keeps_both_unique_items():
    local = {
        "version": "0.2.0",
        "created": "2026-03-29",
        "updated": "2026-03-30",
        "dimensions_list": ["rules"],
        "dimensions": {
            "rules": {
                "updated": "2026-03-30",
                "source": ["scan"],
                "content": "- No emoji\n- Be concise",
            },
        },
    }
    remote = {
        "version": "0.2.0",
        "created": "2026-03-29",
        "updated": "2026-03-30",
        "dimensions_list": ["rules"],
        "dimensions": {
            "rules": {
                "updated": "2026-03-30",
                "source": ["scan"],
                "content": "- No emoji\n- Write tests first",
            },
        },
    }
    merged = _merge_bond_data(local, remote)
    content = merged["dimensions"]["rules"]["content"]
    assert "No emoji" in content
    assert "Be concise" in content
    assert "Write tests first" in content


def test_merge_deduplicates():
    local = {
        "version": "0.2.0", "created": "2026-03-29", "updated": "2026-03-30",
        "dimensions_list": ["style"],
        "dimensions": {"style": {"updated": "2026-03-30", "source": ["scan"], "content": "- Chinese"}},
    }
    remote = {
        "version": "0.2.0", "created": "2026-03-29", "updated": "2026-03-30",
        "dimensions_list": ["style"],
        "dimensions": {"style": {"updated": "2026-03-30", "source": ["scan"], "content": "- Chinese"}},
    }
    merged = _merge_bond_data(local, remote)
    assert merged["dimensions"]["style"]["content"].count("Chinese") == 1


def test_merge_handles_one_side_missing_dim():
    local = {
        "version": "0.2.0", "created": "2026-03-29", "updated": "2026-03-30",
        "dimensions_list": ["rules"],
        "dimensions": {"rules": {"updated": "2026-03-30", "source": ["scan"], "content": "- No emoji"}},
    }
    remote = {
        "version": "0.2.0", "created": "2026-03-29", "updated": "2026-03-30",
        "dimensions_list": ["memory"],
        "dimensions": {"memory": {"updated": "2026-03-30", "source": ["scan"], "content": "- Project X"}},
    }
    merged = _merge_bond_data(local, remote)
    assert "rules" in merged["dimensions"]
    assert "memory" in merged["dimensions"]
    assert "No emoji" in merged["dimensions"]["rules"]["content"]
    assert "Project X" in merged["dimensions"]["memory"]["content"]


def test_save_cloud_config_creates_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir) / "nonexistent" / "subdir"
        config = {"gist_id": "test123"}
        save_cloud_config(config, bond_dir)
        assert (bond_dir / "cloud.json").exists()
