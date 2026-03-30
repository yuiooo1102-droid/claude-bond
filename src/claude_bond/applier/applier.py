from __future__ import annotations

import shutil
from pathlib import Path

from claude_bond.models.bond import BOND_DIR, DIMENSIONS, load_dimension, load_meta


_BOND_SECTION_START = "<!-- bond:start -->"
_BOND_SECTION_END = "<!-- bond:end -->"


def apply_bond(
    bond_dir: Path = BOND_DIR,
    claude_dir: Path | None = None,
) -> None:
    if claude_dir is None:
        claude_dir = Path.home() / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)

    meta = load_meta(bond_dir)
    dims = {name: load_dimension(name, bond_dir) for name in meta.dimensions}

    # Build the bond section for CLAUDE.md
    bond_lines: list[str] = [_BOND_SECTION_START, "## Bond", ""]
    if "identity" in dims and dims["identity"].content:
        bond_lines.append("### Who I'm working with")
        bond_lines.append(dims["identity"].content)
        bond_lines.append("")
    if "rules" in dims and dims["rules"].content:
        bond_lines.append("### Behavioral rules")
        bond_lines.append(dims["rules"].content)
        bond_lines.append("")
    if "style" in dims and dims["style"].content:
        bond_lines.append("### Communication style")
        bond_lines.append(dims["style"].content)
        bond_lines.append("")
    if "tech_prefs" in dims and dims["tech_prefs"].content:
        bond_lines.append("### Technical preferences")
        bond_lines.append(dims["tech_prefs"].content)
        bond_lines.append("")
    if "work_context" in dims and dims["work_context"].content:
        bond_lines.append("### Work context")
        bond_lines.append(dims["work_context"].content)
        bond_lines.append("")
    if "toolchain" in dims and dims["toolchain"].content:
        bond_lines.append("### Toolchain")
        bond_lines.append(dims["toolchain"].content)
        bond_lines.append("")
    bond_lines.append(_BOND_SECTION_END)
    bond_section = "\n".join(bond_lines)

    # Write CLAUDE.md (preserve existing content)
    claude_md_path = claude_dir / "CLAUDE.md"
    if claude_md_path.exists():
        existing = claude_md_path.read_text(encoding="utf-8")
        if _BOND_SECTION_START in existing:
            start = existing.index(_BOND_SECTION_START)
            end = existing.index(_BOND_SECTION_END) + len(_BOND_SECTION_END)
            new_content = existing[:start] + bond_section + existing[end:]
        else:
            new_content = existing.rstrip() + "\n\n" + bond_section + "\n"
    else:
        new_content = bond_section + "\n"
    claude_md_path.write_text(new_content, encoding="utf-8")

    # Write memory files
    if "memory" in dims and dims["memory"].content:
        mem_dir = claude_dir / "memory"
        mem_dir.mkdir(exist_ok=True)
        bond_mem_path = mem_dir / "bond_memory.md"
        bond_mem_path.write_text(
            f"---\nname: bond-memory\ndescription: Memories imported from claude-bond\ntype: project\n---\n\n{dims['memory'].content}\n",
            encoding="utf-8",
        )

    # Save snapshot for evolve detection
    snapshot_dir = bond_dir / ".snapshot"
    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)
    snapshot_dir.mkdir()

    if claude_md_path.exists():
        shutil.copy2(claude_md_path, snapshot_dir / "CLAUDE.md")
    mem_dir = claude_dir / "memory"
    if mem_dir.is_dir():
        snapshot_mem = snapshot_dir / "memory"
        snapshot_mem.mkdir()
        for f in mem_dir.glob("*.md"):
            shutil.copy2(f, snapshot_mem / f.name)
