from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess


MODEL = "claude-sonnet-4-20250514"

_client = None

_IS_WINDOWS = platform.system() == "Windows"


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
    cmd = ["claude", "-p", "-"]
    if system:
        cmd.extend(["--append-system-prompt", system])
    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=120,
        # On Windows, claude is installed as a .cmd script via npm.
        # subprocess cannot find .cmd files without shell=True.
        shell=_IS_WINDOWS,
        # Windows defaults to the system locale (e.g. GBK) for subprocess
        # I/O, which fails on UTF-8 content from Claude. Force UTF-8.
        encoding="utf-8",
        errors="replace",
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
        "You are extracting a user's Claude bond profile from their configuration files. "
        "Classify ALL relevant information into exactly 7 dimensions. Be thorough - extract every piece of useful info.\n\n"
        "Dimensions:\n"
        "- identity: Who the user is. Role, job title, expertise, experience level, team, company, interests.\n"
        "  Examples: 'Senior Python developer', 'Works on NLP projects', 'Familiar with Go and React'\n"
        "- rules: Behavioral preferences the user has set. Things Claude should/shouldn't do.\n"
        "  Examples: 'No emoji in responses', 'Always write tests first', 'Use immutable data structures'\n"
        "- style: Communication preferences. Language, tone, verbosity, formatting.\n"
        "  Examples: 'Respond in Chinese', 'Be concise', 'Code over explanation'\n"
        "- memory: Factual memories, ongoing work, relationships, events.\n"
        "  Examples: 'Working on claude-bond project', 'Mock only in offline tests'\n"
        "- tech_prefs: Technical preferences. Frameworks, libraries, code style, architecture patterns.\n"
        "  Examples: 'Prefer pytest over unittest', 'Use Typer for CLI', 'Follow PEP 8', 'Prefer dataclasses(frozen=True)'\n"
        "- work_context: Current projects, team info, deadlines, ongoing initiatives.\n"
        "  Examples: 'Building claude-bond CLI tool', 'Team uses GitHub for PRs', 'Deadline: end of March'\n"
        "- toolchain: Development tools, MCP servers, hooks, IDE config, skills.\n"
        "  Examples: 'Uses VS Code', 'Has MCP servers configured', 'Uses black + ruff for formatting'\n\n"
        "Rules:\n"
        "1. Extract ALL items, not just a few. Be comprehensive.\n"
        "2. Each item should be a concise phrase (not a full sentence).\n"
        "3. Deduplicate: don't repeat the same info in different words.\n"
        "4. If content spans multiple files, merge related items.\n"
        "5. Return ONLY valid JSON, no markdown fences or explanation.\n\n"
        'Return format: {"identity": [...], "rules": [...], "style": [...], "memory": [...], "tech_prefs": [...], "work_context": [...], "toolchain": [...]}'
    )
    result = ask_claude(f"Classify this content:\n\n{raw_text}", system=system)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        start = result.find("{")
        end = result.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(result[start:end])
        return {
            "identity": [], "rules": [], "style": [], "memory": [],
            "tech_prefs": [], "work_context": [], "toolchain": [],
        }


def generate_questions(gaps: dict[str, str]) -> list[str]:
    system = (
        "You generate 3-5 targeted questions to fill gaps in a user's bond profile. "
        "Ask in Chinese. Be conversational and specific.\n"
        "Return ONLY valid JSON: a list of question strings, no markdown fences.\n"
        "Example: [\"你主要用什么编程语言？\", \"你希望我回复用中文还是英文？\"]"
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
        "Where dimension is one of: identity, rules, style, memory, tech_prefs, work_context, toolchain.\n"
        "Group into sections: ## New, ## Updated, ## Possible (low confidence).\n"
        "If no meaningful bond changes, return 'NO_CHANGES'."
    )
    prompt = f"OLD:\n{old_content}\n\nNEW:\n{new_content}"
    return ask_claude(prompt, system=system)
