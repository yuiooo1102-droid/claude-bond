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
_TECH_PREFS_PATTERNS = re.compile(
    r"(framework|library|pattern|architect|pytest|unittest|dataclass|typing|async"
    r"|react|vue|django|flask|fastapi|pep\s*8|black|ruff|isort|mypy|type.?hint)",
    re.IGNORECASE,
)
_WORK_CONTEXT_PATTERNS = re.compile(
    r"(team|sprint|milestone|roadmap|deadline|initiative|stakeholder|review|pr\b|pull.?request"
    r"|jira|linear|ticket|epic|story|backlog|kanban|standup)",
    re.IGNORECASE,
)
_TOOLCHAIN_PATTERNS = re.compile(
    r"(mcp|hook|skill|plugin|extension|ide|vscode|vim|neovim|jetbrains|terminal"
    r"|docker|kubernetes|ci/?cd|github.?action|jenkins|formatter|linter)",
    re.IGNORECASE,
)


def classify_content_offline(raw_text: str) -> dict[str, list[str]]:
    """Classify raw text into bond dimensions using keyword matching."""
    result: dict[str, list[str]] = {
        "identity": [],
        "rules": [],
        "style": [],
        "memory": [],
        "tech_prefs": [],
        "work_context": [],
        "toolchain": [],
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
            "tech_prefs": len(_TECH_PREFS_PATTERNS.findall(line)),
            "work_context": len(_WORK_CONTEXT_PATTERNS.findall(line)),
            "toolchain": len(_TOOLCHAIN_PATTERNS.findall(line)),
        }

        best = max(scores, key=scores.get)
        if scores[best] > 0:
            result[best].append(clean)

    return result
