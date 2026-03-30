from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

console = Console()

CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"

BOND_HOOK_MARKER = "claude-bond"

APPLY_HOOK = {
    "matcher": "",
    "hooks": [
        {
            "type": "command",
            "command": "bond apply 2>/dev/null",
        }
    ],
}

EVOLVE_HOOK = {
    "matcher": "",
    "hooks": [
        {
            "type": "command",
            "command": "python3 -m claude_bond.evolve.run_detect 2>/dev/null",
        }
    ],
}


def _load_settings(settings_path: Path) -> dict:
    if settings_path.exists():
        return json.loads(settings_path.read_text(encoding="utf-8"))
    return {}


def _save_settings(settings: dict, settings_path: Path) -> None:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _has_bond_hook(hooks_list: list[dict]) -> bool:
    for hook_group in hooks_list:
        for hook in hook_group.get("hooks", []):
            cmd = hook.get("command", "")
            if "claude_bond" in cmd or "bond apply" in cmd:
                return True
    return False


def run_hooks_install(settings_path: Path = CLAUDE_SETTINGS) -> None:
    settings = _load_settings(settings_path)

    if "hooks" not in settings:
        settings["hooks"] = {}

    hooks = settings["hooks"]
    changed = False

    # Install PreToolUse hook for session-start apply
    if "PreToolUse" not in hooks:
        hooks["PreToolUse"] = []

    if not _has_bond_hook(hooks["PreToolUse"]):
        hooks["PreToolUse"].append(APPLY_HOOK)
        changed = True
        console.print("[green]Installed session-start hook (PreToolUse → bond apply)[/green]")
    else:
        console.print("[dim]Session-start hook already installed.[/dim]")

    # Install Stop hook for evolve detection
    if "Stop" not in hooks:
        hooks["Stop"] = []

    if not _has_bond_hook(hooks["Stop"]):
        hooks["Stop"].append(EVOLVE_HOOK)
        changed = True
        console.print("[green]Installed session-end hook (Stop → evolve detect)[/green]")
    else:
        console.print("[dim]Session-end hook already installed.[/dim]")

    if changed:
        _save_settings(settings, settings_path)
        console.print("[bold green]Hooks installed successfully.[/bold green]")
    else:
        console.print("[dim]No changes needed.[/dim]")


def run_hooks_uninstall(settings_path: Path = CLAUDE_SETTINGS) -> None:
    settings = _load_settings(settings_path)
    hooks = settings.get("hooks", {})
    changed = False

    for event_type in list(hooks.keys()):
        original_len = len(hooks[event_type])
        hooks[event_type] = [
            hg for hg in hooks[event_type]
            if not any(
                "claude_bond" in h.get("command", "") or "bond apply" in h.get("command", "")
                for h in hg.get("hooks", [])
            )
        ]
        if len(hooks[event_type]) < original_len:
            changed = True
        if not hooks[event_type]:
            del hooks[event_type]

    if not hooks:
        settings.pop("hooks", None)

    if changed:
        _save_settings(settings, settings_path)
        console.print("[bold green]Bond hooks removed.[/bold green]")
    else:
        console.print("[dim]No bond hooks found to remove.[/dim]")


def run_hooks_status(settings_path: Path = CLAUDE_SETTINGS) -> None:
    settings = _load_settings(settings_path)
    hooks = settings.get("hooks", {})

    found = False
    for event_type, hook_groups in hooks.items():
        for hg in hook_groups:
            for hook in hg.get("hooks", []):
                cmd = hook.get("command", "")
                if "claude_bond" in cmd or "bond apply" in cmd:
                    console.print(f"  [green]✓[/green] {event_type}: {cmd}")
                    found = True

    if not found:
        console.print("[dim]No bond hooks installed.[/dim]")
        console.print("Run [bold]bond hooks --install[/bold] to install them.")
