from __future__ import annotations

from pathlib import Path

from claude_bond.utils.security import filter_secrets


def scan_claude_dir(claude_dir: Path) -> dict[str, str | dict[str, str]]:
    result: dict[str, str | dict[str, str]] = {
        "claude_md": "",
        "memory_files": {},
        "settings": "",
        "project_claudes": {},
    }

    claude_md = claude_dir / "CLAUDE.md"
    if claude_md.exists():
        result["claude_md"] = filter_secrets(claude_md.read_text(encoding="utf-8"))

    memory_dir = claude_dir / "memory"
    if memory_dir.is_dir():
        mem_files: dict[str, str] = {}
        for f in sorted(memory_dir.glob("*.md")):
            mem_files[f.name] = filter_secrets(f.read_text(encoding="utf-8"))
        result["memory_files"] = mem_files

    settings_file = claude_dir / "settings.json"
    if settings_file.exists():
        result["settings"] = filter_secrets(settings_file.read_text(encoding="utf-8"))

    projects_dir = claude_dir / "projects"
    if projects_dir.is_dir():
        proj_claudes: dict[str, str] = {}
        for proj in projects_dir.iterdir():
            if proj.is_dir():
                proj_claude = proj / "CLAUDE.md"
                if proj_claude.exists():
                    proj_claudes[proj.name] = filter_secrets(
                        proj_claude.read_text(encoding="utf-8")
                    )
        result["project_claudes"] = proj_claudes

    return result
