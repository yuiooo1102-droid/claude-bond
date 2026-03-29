import subprocess
import tempfile
from pathlib import Path

from claude_bond.sync_engine.git_sync import git_init, git_commit_all, is_git_repo


def test_git_init_creates_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        git_init(path)
        assert (path / ".git").is_dir()


def test_is_git_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        assert not is_git_repo(path)
        git_init(path)
        assert is_git_repo(path)


def test_git_commit_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        git_init(path)
        (path / "test.md").write_text("hello", encoding="utf-8")
        git_commit_all(path, "test commit")
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=path,
            capture_output=True,
            text=True,
        )
        assert "test commit" in result.stdout
