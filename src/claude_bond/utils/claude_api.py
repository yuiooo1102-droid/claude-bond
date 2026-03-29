from __future__ import annotations

import json
import os

from anthropic import Anthropic


_client: Anthropic | None = None

MODEL = "claude-sonnet-4-20250514"


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


def ask_claude(prompt: str, system: str = "") -> str:
    client = _get_client()
    messages = [{"role": "user", "content": prompt}]
    kwargs: dict = {"model": MODEL, "max_tokens": 4096, "messages": messages}
    if system:
        kwargs["system"] = system
    response = client.messages.create(**kwargs)
    return response.content[0].text


def classify_content(raw_text: str) -> dict[str, list[str]]:
    system = (
        "You classify raw text extracted from a user's Claude configuration into 4 dimensions: "
        "identity (who the user is), rules (behavioral preferences), "
        "style (communication preferences), memory (factual memories). "
        "Return valid JSON: {\"identity\": [...], \"rules\": [...], \"style\": [...], \"memory\": [...]}"
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
