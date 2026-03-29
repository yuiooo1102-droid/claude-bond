from __future__ import annotations

import re

_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("anthropic_key", re.compile(r"sk-ant-[\w-]{10,}")),
    ("openai_key", re.compile(r"sk-proj-[\w-]{3,}")),
    ("openai_key_old", re.compile(r"sk-[a-zA-Z0-9]{20,}")),
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)),
    ("database_url", re.compile(r"(postgres|mysql|mongodb)://\S+")),
    ("aws_secret", re.compile(r"(?:AWS_SECRET_ACCESS_KEY|aws_secret_access_key)\s*=\s*\S+")),
    ("generic_secret", re.compile(
        r"(?:SECRET|TOKEN|PASSWORD|PASSWD|API_KEY|APIKEY|ACCESS_KEY)"
        r"\s*=\s*\S+",
        re.IGNORECASE,
    )),
]


def filter_secrets(text: str) -> str:
    result = text
    for name, pattern in _SECRET_PATTERNS:
        result = pattern.sub(f"[REDACTED:{name}]", result)
    return result
