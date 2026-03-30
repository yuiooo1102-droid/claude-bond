import json
import tempfile
from pathlib import Path

from claude_bond.commands.hooks_cmd import (
    run_hooks_install,
    run_hooks_uninstall,
    run_hooks_status,
    _has_bond_hook,
)


def test_install_creates_hook():
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_path = Path(tmpdir) / "settings.json"
        run_hooks_install(settings_path=settings_path)

        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        assert "hooks" in settings
        assert "Stop" in settings["hooks"]
        assert len(settings["hooks"]["Stop"]) == 1
        cmd = settings["hooks"]["Stop"][0]["hooks"][0]["command"]
        assert "claude_bond" in cmd


def test_install_idempotent():
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_path = Path(tmpdir) / "settings.json"
        run_hooks_install(settings_path=settings_path)
        run_hooks_install(settings_path=settings_path)

        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        assert len(settings["hooks"]["Stop"]) == 1  # not duplicated


def test_install_preserves_existing_settings():
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_path = Path(tmpdir) / "settings.json"
        settings_path.write_text('{"theme": "dark", "hooks": {}}', encoding="utf-8")

        run_hooks_install(settings_path=settings_path)

        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        assert settings["theme"] == "dark"
        assert "Stop" in settings["hooks"]


def test_uninstall_removes_hook():
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_path = Path(tmpdir) / "settings.json"
        run_hooks_install(settings_path=settings_path)
        run_hooks_uninstall(settings_path=settings_path)

        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        assert "hooks" not in settings or "Stop" not in settings.get("hooks", {})


def test_has_bond_hook_detection():
    hooks = [{"hooks": [{"type": "command", "command": "python3 -m claude_bond.evolve.run_detect"}]}]
    assert _has_bond_hook(hooks) is True

    hooks = [{"hooks": [{"type": "command", "command": "echo hello"}]}]
    assert _has_bond_hook(hooks) is False
