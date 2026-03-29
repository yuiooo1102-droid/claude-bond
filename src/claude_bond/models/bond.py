from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


BOND_DIR = Path.home() / ".claude-bond"
DIMENSIONS = ("identity", "rules", "style", "memory")


@dataclass(frozen=True)
class BondDimension:
    name: str
    updated: str
    source: list[str]
    content: str

    @classmethod
    def from_markdown(cls, text: str) -> BondDimension:
        parts = text.split("---", 2)
        if len(parts) < 3:
            raise ValueError("Invalid bond dimension: missing frontmatter")
        meta = yaml.safe_load(parts[1])
        content = parts[2].strip()
        return cls(
            name=meta["dimension"],
            updated=str(meta["updated"]),
            source=meta.get("source", []),
            content=content,
        )

    def to_markdown(self) -> str:
        meta = {
            "dimension": self.name,
            "updated": self.updated,
            "source": self.source,
        }
        header = yaml.dump(meta, default_flow_style=False, allow_unicode=True).strip()
        return f"---\n{header}\n---\n\n{self.content}\n"


@dataclass(frozen=True)
class BondMeta:
    version: str
    created: str
    updated: str
    dimensions: list[str] = field(default_factory=lambda: list(DIMENSIONS))


def save_dimension(dim: BondDimension, bond_dir: Path) -> Path:
    path = bond_dir / f"{dim.name}.md"
    path.write_text(dim.to_markdown(), encoding="utf-8")
    return path


def load_dimension(name: str, bond_dir: Path) -> BondDimension:
    path = bond_dir / f"{name}.md"
    return BondDimension.from_markdown(path.read_text(encoding="utf-8"))


def save_meta(meta: BondMeta, bond_dir: Path) -> Path:
    path = bond_dir / "bond.yaml"
    data = {
        "version": meta.version,
        "created": meta.created,
        "updated": meta.updated,
        "dimensions": meta.dimensions,
    }
    path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    return path


def load_meta(bond_dir: Path) -> BondMeta:
    path = bond_dir / "bond.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return BondMeta(
        version=data["version"],
        created=data["created"],
        updated=data["updated"],
        dimensions=data.get("dimensions", list(DIMENSIONS)),
    )
