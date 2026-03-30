import tempfile
from pathlib import Path

from claude_bond.evolve.signal_collector import (
    collect_session_signal,
    _detect_language,
    _detect_response_length,
    _extract_topics,
    _extract_corrections,
    _collect_new_content,
)


def _setup_snapshot_and_claude(tmpdir: str):
    bond_dir = Path(tmpdir) / "bond"
    bond_dir.mkdir()
    snapshot = bond_dir / ".snapshot"
    snapshot.mkdir()
    (snapshot / "CLAUDE.md").write_text("# Rules\n- No emoji\n", encoding="utf-8")

    claude_dir = Path(tmpdir) / "claude"
    claude_dir.mkdir()

    return bond_dir, claude_dir


def test_detect_language_chinese():
    assert _detect_language("这是中文内容，用于测试语言检测") == "chinese"


def test_detect_language_english():
    assert _detect_language("This is English content for testing") == "english"


def test_detect_language_mixed():
    # Mostly Chinese
    text = "这是中文 with some English words 但主要是中文内容"
    assert _detect_language(text) == "chinese"


def test_detect_response_length():
    assert _detect_response_length("short line\nbrief") == "short"
    assert _detect_response_length("a" * 60 + "\n" + "b" * 80) == "medium"
    assert _detect_response_length("a" * 150 + "\n" + "b" * 200) == "long"


def test_extract_topics():
    text = "We need to fix the database migration and add more tests for the API endpoint"
    topics = _extract_topics(text)
    assert "database" in topics
    assert "testing" in topics
    assert "api" in topics


def test_extract_corrections():
    text = "don't use emoji in responses\nalways write tests first\nprefer immutable data structures"
    corrections = _extract_corrections(text)
    assert len(corrections) >= 2


def test_collect_new_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir, claude_dir = _setup_snapshot_and_claude(tmpdir)

        # Add new content
        (claude_dir / "CLAUDE.md").write_text("# Rules\n- No emoji\n- Be concise\n", encoding="utf-8")

        content = _collect_new_content(bond_dir / ".snapshot", claude_dir)
        assert "Be concise" in content
        assert "No emoji" not in content  # old line, not in diff


def test_collect_signal_no_changes():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir, claude_dir = _setup_snapshot_and_claude(tmpdir)
        (claude_dir / "CLAUDE.md").write_text("# Rules\n- No emoji\n", encoding="utf-8")

        signal = collect_session_signal(bond_dir=bond_dir, claude_dir=claude_dir)
        assert signal is None


def test_collect_signal_with_changes():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir, claude_dir = _setup_snapshot_and_claude(tmpdir)
        (claude_dir / "CLAUDE.md").write_text(
            "# Rules\n- No emoji\n- 使用中文回复\n- don't write trailing summaries\n",
            encoding="utf-8",
        )

        signal = collect_session_signal(bond_dir=bond_dir, claude_dir=claude_dir)
        assert signal is not None
        assert signal.language == "chinese"
        assert signal.date is not None
