from __future__ import annotations

import json
import os
import shutil
import subprocess


MODEL = "claude-sonnet-4-20250514"

_client = None


def has_api_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def has_claude_cli() -> bool:
    return shutil.which("claude") is not None


def _get_client():
    global _client
    if _client is None:
        from anthropic import Anthropic
        _client = Anthropic()
    return _client


def _ask_via_cli(prompt: str, system: str = "") -> str:
    """Use the claude CLI (Max/subscription) to get a response."""
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    cmd = ["claude", "-p", full_prompt]
    if system:
        cmd.extend(["--append-system-prompt", system])
        cmd = ["claude", "-p", prompt, "--append-system-prompt", system]
    else:
        cmd = ["claude", "-p", full_prompt]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {result.stderr}")
    return result.stdout.strip()


def _ask_via_api(prompt: str, system: str = "") -> str:
    """Use the Anthropic API (requires ANTHROPIC_API_KEY)."""
    client = _get_client()
    messages = [{"role": "user", "content": prompt}]
    kwargs: dict = {"model": MODEL, "max_tokens": 4096, "messages": messages}
    if system:
        kwargs["system"] = system
    response = client.messages.create(**kwargs)
    return response.content[0].text


def ask_claude(prompt: str, system: str = "") -> str:
    """Ask Claude via CLI (preferred) or API (fallback)."""
    if has_claude_cli():
        return _ask_via_cli(prompt, system)
    if has_api_key():
        return _ask_via_api(prompt, system)
    raise RuntimeError(
        "No Claude backend available. Install Claude Code CLI or set ANTHROPIC_API_KEY."
    )


def can_use_claude() -> bool:
    """Check if any Claude backend is available."""
    return has_claude_cli() or has_api_key()


def classify_content(raw_text: str) -> dict[str, list[str]]:
    system = (
        "You classify raw text extracted from a user's Claude configuration into 4 dimensions: "
        "identity (who the user is), rules (behavioral preferences), "
        "style (communication preferences), memory (factual memories). "
        'Return valid JSON: {"identity": [...], "rules": [...], "style": [...], "memory": [...]}'
        " Each value is a list of concise bullet-point strings. "
        "If a dimension has no data, return an empty list."
    )
    result = ask_claude(f"Classify this content:\n\n{raw_text}", system=system)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        start = result.find("{")
        end = result.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(result[start:end])
        return {"identity": [], "rules": [], "style": [], "memory": []}


def generate_questions(gaps: dict[str, str]) -> list[str]:
    system = (
        "You generate 3-5 targeted questions to fill gaps in a user's bond profile. "
        "Return valid JSON: a list of question strings. "
        "Questions should be conversational and easy to answer."
    )
    prompt = f"These dimensions need more data:\n{json.dumps(gaps, ensure_ascii=False)}"
    result = ask_claude(prompt, system=system)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        start = result.find("[")
        end = result.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(result[start:end])
        return []


def analyze_changes(old_content: str, new_content: str) -> str:
    system = (
        "You analyze changes in a user's Claude configuration files and classify them as bond updates. "
        "For each change, output a line in this format:\n"
        "- [dimension] description\n"
        "Where dimension is one of: identity, rules, style, memory.\n"
        "Group into sections: ## New, ## Updated, ## Possible (low confidence).\n"
        "If no meaningful bond changes, return 'NO_CHANGES'."
    )
    prompt = f"OLD:\n{old_content}\n\nNEW:\n{new_content}"
    return ask_claude(prompt, system=system)
