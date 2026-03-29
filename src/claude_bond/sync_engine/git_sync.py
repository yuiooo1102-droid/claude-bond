from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

from rich.console import Console

console = Console()


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def is_git_repo(path: Path) -> bool:
    result = _run_git(["rev-parse", "--is-inside-work-tree"], cwd=path)
    return result.returncode == 0


def git_init(path: Path) -> None:
    _run_git(["init"], cwd=path)
    _run_git(["config", "user.email", "bond@claude-bond.local"], cwd=path)
    _run_git(["config", "user.name", "claude-bond"], cwd=path)

    gitignore = path / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(".snapshot/\n*.bond\n__pycache__/\n", encoding="utf-8")
        _run_git(["add", ".gitignore"], cwd=path)
        _run_git(["commit", "-m", "chore: initial gitignore"], cwd=path)


def git_commit_all(path: Path, message: str | None = None) -> bool:
    _run_git(["add", "-A"], cwd=path)
    status = _run_git(["status", "--porcelain"], cwd=path)
    if not status.stdout.strip():
        return False
    if message is None:
        message = f"bond update {date.today().isoformat()}"
    _run_git(["commit", "-m", message], cwd=path)
    return True


def git_pull(path: Path) -> bool:
    result = _run_git(["pull", "--rebase"], cwd=path)
    return result.returncode == 0


def git_push(path: Path) -> bool:
    result = _run_git(["push"], cwd=path)
    return result.returncode == 0


def git_add_remote(path: Path, url: str) -> None:
    _run_git(["remote", "add", "origin", url], cwd=path)
    _run_git(["push", "-u", "origin", "main"], cwd=path)
