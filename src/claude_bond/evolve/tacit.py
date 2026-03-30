from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from claude_bond.models.bond import BOND_DIR


@dataclass(frozen=True)
class SessionSignal:
    date: str
    avg_response_length: str  # "short", "medium", "long"
    language: str  # detected language
    topics: list[str]  # detected topics
    corrections: list[str]  # user corrections detected


SIGNALS_FILE = "tacit_signals.json"


def load_signals(bond_dir: Path = BOND_DIR) -> list[dict]:
    path = bond_dir / SIGNALS_FILE
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_signal(signal: SessionSignal, bond_dir: Path = BOND_DIR) -> None:
    signals = load_signals(bond_dir)
    signals.append({
        "date": signal.date,
        "avg_response_length": signal.avg_response_length,
        "language": signal.language,
        "topics": signal.topics,
        "corrections": signal.corrections,
    })
    # Keep last 50 sessions
    signals = signals[-50:]
    path = bond_dir / SIGNALS_FILE
    path.write_text(json.dumps(signals, ensure_ascii=False, indent=2), encoding="utf-8")


def analyze_patterns(bond_dir: Path = BOND_DIR) -> list[dict]:
    """Analyze accumulated signals to detect implicit preferences."""
    signals = load_signals(bond_dir)
    if len(signals) < 3:
        return []

    patterns: list[dict] = []

    # Pattern 1: Consistent response length preference
    lengths = [s["avg_response_length"] for s in signals[-10:]]
    if lengths:
        from collections import Counter
        length_counts = Counter(lengths)
        dominant, count = length_counts.most_common(1)[0]
        if count >= len(lengths) * 0.7:
            patterns.append({
                "dimension": "style",
                "description": f"Prefers {dominant} responses",
                "confidence": round(count / len(lengths), 2),
                "evidence": f"{count}/{len(lengths)} recent sessions used {dominant} responses",
            })

    # Pattern 2: Consistent language usage
    languages = [s["language"] for s in signals[-10:]]
    if languages:
        from collections import Counter
        lang_counts = Counter(languages)
        dominant, count = lang_counts.most_common(1)[0]
        if count >= len(languages) * 0.8 and dominant != "unknown":
            patterns.append({
                "dimension": "style",
                "description": f"Primary language: {dominant}",
                "confidence": round(count / len(languages), 2),
                "evidence": f"{count}/{len(languages)} recent sessions in {dominant}",
            })

    # Pattern 3: Repeated corrections → rules
    all_corrections: list[str] = []
    for s in signals[-20:]:
        all_corrections.extend(s.get("corrections", []))
    if all_corrections:
        from collections import Counter
        correction_counts = Counter(all_corrections)
        for correction, count in correction_counts.most_common(5):
            if count >= 2:
                patterns.append({
                    "dimension": "rules",
                    "description": correction,
                    "confidence": min(0.5 + count * 0.1, 0.95),
                    "evidence": f"User corrected this {count} times",
                })

    # Pattern 4: Frequent topics → work_context
    all_topics: list[str] = []
    for s in signals[-10:]:
        all_topics.extend(s.get("topics", []))
    if all_topics:
        from collections import Counter
        topic_counts = Counter(all_topics)
        for topic, count in topic_counts.most_common(3):
            if count >= 3:
                patterns.append({
                    "dimension": "work_context",
                    "description": f"Frequently works on: {topic}",
                    "confidence": round(min(count / len(signals[-10:]), 0.95), 2),
                    "evidence": f"Mentioned in {count}/{len(signals[-10:])} recent sessions",
                })

    return patterns


def generate_tacit_pending(bond_dir: Path = BOND_DIR) -> str | None:
    """Generate pending items from tacit patterns."""
    patterns = analyze_patterns(bond_dir)
    if not patterns:
        return None

    lines = ["## Possible (low confidence)", ""]
    for p in patterns:
        conf_pct = int(p["confidence"] * 100)
        lines.append(f"- [{p['dimension']}] {p['description']} ({conf_pct}% confidence: {p['evidence']})")

    return "\n".join(lines)
