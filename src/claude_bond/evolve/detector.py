from __future__ import annotations

from datetime import date
from pathlib import Path

from claude_bond.models.bond import BOND_DIR
from claude_bond.utils.claude_api import analyze_changes


def detect_changes(
    bond_dir: Path = BOND_DIR,
    claude_dir: Path | None = None,
) -> str | None:
    if claude_dir is None:
        claude_dir = Path.home() / ".claude"

    snapshot_dir = bond_dir / ".snapshot"
    if not snapshot_dir.exists():
        return None

    old_parts: list[str] = []
    new_parts: list[str] = []

    # Compare CLAUDE.md
    old_claude = snapshot_dir / "CLAUDE.md"
    new_claude = claude_dir / "CLAUDE.md"
    if old_claude.exists():
        old_parts.append(old_claude.read_text(encoding="utf-8"))
    if new_claude.exists():
        new_parts.append(new_claude.read_text(encoding="utf-8"))

    # Compare memory files
    old_mem = snapshot_dir / "memory"
    new_mem = claude_dir / "memory"
    if old_mem.is_dir():
        for f in sorted(old_mem.glob("*.md")):
            old_parts.append(f"[{f.name}]\n{f.read_text(encoding='utf-8')}")
    if new_mem.is_dir():
        for f in sorted(new_mem.glob("*.md")):
            new_parts.append(f"[{f.name}]\n{f.read_text(encoding='utf-8')}")

    old_text = "\n---\n".join(old_parts)
    new_text = "\n---\n".join(new_parts)

    if old_text.strip() == new_text.strip():
        return None

    result = analyze_changes(old_text, new_text)
    if result.strip() == "NO_CHANGES":
        return None
    return result


def save_pending(bond_dir: Path, changes: str) -> Path:
    pending_dir = bond_dir / "pending"
    pending_dir.mkdir(exist_ok=True)

    today = date.today().isoformat()
    path = pending_dir / f"{today}.md"

    header = f"---\ndate: {today}\n---\n\n"

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        content = existing + "\n" + changes
    else:
        content = header + changes

    path.write_text(content, encoding="utf-8")
    return path
