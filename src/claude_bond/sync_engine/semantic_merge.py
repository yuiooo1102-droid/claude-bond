from __future__ import annotations

import subprocess
from pathlib import Path

from claude_bond.models.bond import BondDimension, save_dimension
from claude_bond.utils.claude_api import ask_claude, can_use_claude


def semantic_merge_dimension(
    ours: BondDimension,
    theirs: BondDimension,
) -> BondDimension:
    """Merge two versions of a dimension using Claude for semantic understanding."""
    if not can_use_claude():
        return _naive_merge(ours, theirs)

    system = (
        "You are merging two versions of a user's bond profile dimension. "
        "Both versions may have unique items that should be kept, or overlapping items that should be deduplicated.\n\n"
        "Rules:\n"
        "1. Keep ALL unique items from both versions.\n"
        "2. Deduplicate: if both versions say the same thing differently, keep the more recent/specific one.\n"
        "3. If items conflict (e.g., 'prefers Python' vs 'switched to Go'), keep the THEIRS version (newer device).\n"
        "4. Output ONLY the merged content as bullet points, one per line. No explanation.\n"
        "5. Each line starts with '- '"
    )
    prompt = (
        f"Dimension: {ours.name}\n\n"
        f"VERSION A (ours):\n{ours.content}\n\n"
        f"VERSION B (theirs - more recent):\n{theirs.content}\n\n"
        "Merge these into a single deduplicated list:"
    )

    merged_content = ask_claude(prompt, system=system)

    updated = max(ours.updated, theirs.updated)
    sources = list(set(ours.source + theirs.source))

    return BondDimension(
        name=ours.name,
        updated=updated,
        source=sources,
        content=merged_content.strip(),
    )


def _naive_merge(ours: BondDimension, theirs: BondDimension) -> BondDimension:
    """Fallback merge without Claude: combine all unique lines."""
    ours_lines = set(line.strip() for line in ours.content.splitlines() if line.strip())
    theirs_lines = set(line.strip() for line in theirs.content.splitlines() if line.strip())
    all_lines = sorted(ours_lines | theirs_lines)

    updated = max(ours.updated, theirs.updated)
    sources = list(set(ours.source + theirs.source))

    return BondDimension(
        name=ours.name,
        updated=updated,
        source=sources,
        content="\n".join(all_lines),
    )


def resolve_sync_conflicts(bond_dir: Path) -> list[str]:
    """Check for git conflict markers in dimension files and resolve them semantically."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=U"],
        cwd=bond_dir,
        capture_output=True,
        text=True,
    )

    if not result.stdout.strip():
        return []

    resolved: list[str] = []
    conflict_files = result.stdout.strip().splitlines()

    for filename in conflict_files:
        if not filename.endswith(".md"):
            continue

        filepath = bond_dir / filename
        content = filepath.read_text(encoding="utf-8")

        if "<<<<<<< " not in content:
            continue

        dim_name = filename.replace(".md", "")
        ours_content, theirs_content = _parse_conflict(content)

        ours = BondDimension(dim_name, "unknown", ["sync"], ours_content)
        theirs = BondDimension(dim_name, "unknown", ["sync"], theirs_content)

        merged = semantic_merge_dimension(ours, theirs)
        save_dimension(merged, bond_dir)

        subprocess.run(["git", "add", filename], cwd=bond_dir)
        resolved.append(dim_name)

    return resolved


def _parse_conflict(content: str) -> tuple[str, str]:
    """Extract ours and theirs content from git conflict markers."""
    ours_lines: list[str] = []
    theirs_lines: list[str] = []
    state = "before"

    for line in content.splitlines():
        if line.startswith("<<<<<<< "):
            state = "ours"
        elif line.startswith("======="):
            state = "theirs"
        elif line.startswith(">>>>>>> "):
            state = "after"
        elif state == "ours":
            ours_lines.append(line)
        elif state == "theirs":
            theirs_lines.append(line)

    return "\n".join(ours_lines), "\n".join(theirs_lines)
