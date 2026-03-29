"""Offline keyword-based classifier for when no API key is available."""
from __future__ import annotations

import re

# Keyword patterns for each dimension
_IDENTITY_PATTERNS = re.compile(
    r"(role|developer|engineer|scientist|designer|manager|student|expert|senior|junior"
    r"|background|experience|profession|specializ|focus on|work(?:s|ing)?\s+(?:at|on|in|with))",
    re.IGNORECASE,
)
_RULES_PATTERNS = re.compile(
    r"(don'?t|do not|never|always|must|should|avoid|prefer|no\s+\w+|stop\s+\w+ing"
    r"|rule|convention|standard|require|forbid|important)",
    re.IGNORECASE,
)
_STYLE_PATTERNS = re.compile(
    r"(language|chinese|english|concise|verbose|brief|detailed|tone|formal|casual"
    r"|respond|reply|format|markdown|emoji|short|long|style|communicat)",
    re.IGNORECASE,
)
_MEMORY_PATTERNS = re.compile(
    r"(project|deploy|release|version|bug|feature|deadline|meeting|team|remember"
    r"|working on|launched|completed|started|migrat|refactor|incident)",
    re.IGNORECASE,
)


def classify_content_offline(raw_text: str) -> dict[str, list[str]]:
    """Classify raw text into bond dimensions using keyword matching."""
    result: dict[str, list[str]] = {
        "identity": [],
        "rules": [],
        "style": [],
        "memory": [],
    }

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    for line in lines:
        # Skip headers and frontmatter
        if line.startswith("#") or line.startswith("---") or line.startswith("```"):
            continue

        # Strip bullet prefix for cleaner output
        clean = re.sub(r"^[-*]\s*", "", line).strip()
        if not clean or len(clean) < 5:
            continue

        scores = {
            "identity": len(_IDENTITY_PATTERNS.findall(line)),
            "rules": len(_RULES_PATTERNS.findall(line)),
            "style": len(_STYLE_PATTERNS.findall(line)),
            "memory": len(_MEMORY_PATTERNS.findall(line)),
        }

        best = max(scores, key=scores.get)
        if scores[best] > 0:
            result[best].append(clean)

    return result
