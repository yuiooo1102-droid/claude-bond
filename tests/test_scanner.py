import tempfile
from pathlib import Path

from claude_bond.extractor.scanner import scan_claude_dir


def test_scan_reads_claude_md():
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir)
        (claude_dir / "CLAUDE.md").write_text("# Rules\n- No emoji\n- Be concise", encoding="utf-8")
        result = scan_claude_dir(claude_dir)
        assert "No emoji" in result["claude_md"]


def test_scan_reads_memory_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir)
        mem_dir = claude_dir / "memory"
        mem_dir.mkdir()
        (mem_dir / "user_role.md").write_text("User is a data scientist", encoding="utf-8")
        (mem_dir / "feedback_testing.md").write_text("Don't mock the database", encoding="utf-8")
        result = scan_claude_dir(claude_dir)
        assert len(result["memory_files"]) == 2
        assert any("data scientist" in m for m in result["memory_files"].values())


def test_scan_reads_settings():
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir)
        (claude_dir / "settings.json").write_text('{"language": "zh"}', encoding="utf-8")
        result = scan_claude_dir(claude_dir)
        assert "zh" in result["settings"]


def test_scan_handles_missing_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = scan_claude_dir(Path(tmpdir))
        assert result["claude_md"] == ""
        assert result["memory_files"] == {}
        assert result["settings"] == ""


def test_scan_filters_secrets():
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir)
        (claude_dir / "CLAUDE.md").write_text("API_KEY=sk-ant-api03-secretkey123456789", encoding="utf-8")
        result = scan_claude_dir(claude_dir)
        assert "sk-ant-api03" not in result["claude_md"]
        assert "REDACTED" in result["claude_md"]
