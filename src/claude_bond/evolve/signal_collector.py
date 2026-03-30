from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from claude_bond.evolve.tacit import SessionSignal, save_signal
from claude_bond.models.bond import BOND_DIR


def collect_session_signal(
    bond_dir: Path = BOND_DIR,
    claude_dir: Path | None = None,
) -> SessionSignal | None:
    """Analyze ~/.claude/ changes to extract a tacit signal for this session."""
    if claude_dir is None:
        claude_dir = Path.home() / ".claude"

    snapshot_dir = bond_dir / ".snapshot"
    if not snapshot_dir.exists():
        return None

    # Gather new/changed content
    new_content = _collect_new_content(snapshot_dir, claude_dir)
    if not new_content:
        return None

    language = _detect_language(new_content)
    avg_length = _detect_response_length(new_content)
    topics = _extract_topics(new_content)
    corrections = _extract_corrections(new_content)

    signal = SessionSignal(
        date=date.today().isoformat(),
        avg_response_length=avg_length,
        language=language,
        topics=topics,
        corrections=corrections,
    )

    save_signal(signal, bond_dir)
    return signal


def _collect_new_content(snapshot_dir: Path, claude_dir: Path) -> str:
    """Get content that changed since snapshot."""
    parts: list[str] = []

    # Check CLAUDE.md changes
    old_claude = snapshot_dir / "CLAUDE.md"
    new_claude = claude_dir / "CLAUDE.md"
    if new_claude.exists():
        new_text = new_claude.read_text(encoding="utf-8")
        old_text = old_claude.read_text(encoding="utf-8") if old_claude.exists() else ""
        if new_text != old_text:
            # Only keep the diff (new lines)
            old_lines = set(old_text.splitlines())
            new_lines = [l for l in new_text.splitlines() if l not in old_lines]
            parts.extend(new_lines)

    # Check new/changed memory files
    old_mem = snapshot_dir / "memory"
    new_mem = claude_dir / "memory"
    if new_mem.is_dir():
        old_files = {f.name: f.read_text(encoding="utf-8") for f in old_mem.glob("*.md")} if old_mem.is_dir() else {}
        for f in new_mem.glob("*.md"):
            new_text = f.read_text(encoding="utf-8")
            old_text = old_files.get(f.name, "")
            if new_text != old_text:
                old_lines = set(old_text.splitlines())
                new_lines = [l for l in new_text.splitlines() if l not in old_lines]
                parts.extend(new_lines)

    return "\n".join(parts)


def _detect_language(text: str) -> str:
    """Simple heuristic language detection."""
    # Count CJK characters
    cjk_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    total_alpha = sum(1 for c in text if c.isalpha())

    if total_alpha == 0:
        return "unknown"

    cjk_ratio = cjk_count / total_alpha
    if cjk_ratio > 0.15:
        return "chinese"
    return "english"


def _detect_response_length(text: str) -> str:
    """Estimate typical response length from content."""
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return "short"

    avg_len = sum(len(l) for l in lines) / len(lines)
    if avg_len < 40:
        return "short"
    elif avg_len < 100:
        return "medium"
    return "long"


_TOPIC_PATTERNS = {
    "testing": re.compile(r"test|pytest|unittest|coverage|mock|assert", re.IGNORECASE),
    "debugging": re.compile(r"debug|error|fix|bug|issue|traceback|exception", re.IGNORECASE),
    "refactoring": re.compile(r"refactor|clean|reorganiz|restructur|simplif", re.IGNORECASE),
    "api": re.compile(r"api|endpoint|rest|graphql|grpc|request|response", re.IGNORECASE),
    "database": re.compile(r"database|sql|query|migration|schema|table|index", re.IGNORECASE),
    "frontend": re.compile(r"react|vue|css|html|component|render|dom|ui", re.IGNORECASE),
    "devops": re.compile(r"docker|deploy|ci|cd|pipeline|kubernetes|helm", re.IGNORECASE),
    "security": re.compile(r"auth|token|secret|encrypt|permission|csrf|xss", re.IGNORECASE),
}


def _extract_topics(text: str) -> list[str]:
    """Extract topic keywords from content."""
    topics: list[str] = []
    for topic, pattern in _TOPIC_PATTERNS.items():
        if pattern.search(text):
            topics.append(topic)
    return topics[:5]  # cap at 5


_CORRECTION_PATTERNS = [
    re.compile(r"(?:don'?t|do not|never|stop)\s+(.{10,60})", re.IGNORECASE),
    re.compile(r"(?:always|must|should)\s+(.{10,60})", re.IGNORECASE),
    re.compile(r"(?:prefer|instead)\s+(.{10,60})", re.IGNORECASE),
]


def _extract_corrections(text: str) -> list[str]:
    """Extract user corrections/preferences from content."""
    corrections: list[str] = []
    for pattern in _CORRECTION_PATTERNS:
        for match in pattern.finditer(text):
            correction = match.group(0).strip()
            if len(correction) > 15:
                corrections.append(correction[:80])
    return corrections[:5]  # cap at 5
