import json
import tempfile
from pathlib import Path

from claude_bond.evolve.tacit import (
    SessionSignal,
    save_signal,
    load_signals,
    analyze_patterns,
    generate_tacit_pending,
)


def _create_signals(bond_dir: Path, count: int = 5) -> None:
    for i in range(count):
        signal = SessionSignal(
            date=f"2026-03-{20 + i:02d}",
            avg_response_length="short",
            language="chinese",
            topics=["claude-bond", "testing"],
            corrections=["don't use emoji"] if i % 2 == 0 else [],
        )
        save_signal(signal, bond_dir)


def test_save_and_load_signals():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        signal = SessionSignal(
            date="2026-03-30",
            avg_response_length="short",
            language="chinese",
            topics=["testing"],
            corrections=[],
        )
        save_signal(signal, bond_dir)
        loaded = load_signals(bond_dir)
        assert len(loaded) == 1
        assert loaded[0]["language"] == "chinese"


def test_analyze_patterns_needs_minimum_sessions():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        signal = SessionSignal("2026-03-30", "short", "chinese", [], [])
        save_signal(signal, bond_dir)
        patterns = analyze_patterns(bond_dir)
        assert patterns == []


def test_analyze_patterns_detects_language():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_signals(bond_dir, 5)
        patterns = analyze_patterns(bond_dir)
        language_patterns = [p for p in patterns if "language" in p["description"].lower()]
        assert len(language_patterns) >= 1
        assert "chinese" in language_patterns[0]["description"].lower()


def test_analyze_patterns_detects_response_length():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_signals(bond_dir, 5)
        patterns = analyze_patterns(bond_dir)
        length_patterns = [p for p in patterns if "short" in p["description"].lower()]
        assert len(length_patterns) >= 1


def test_analyze_patterns_detects_corrections():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_signals(bond_dir, 6)
        patterns = analyze_patterns(bond_dir)
        correction_patterns = [p for p in patterns if "emoji" in p["description"].lower()]
        assert len(correction_patterns) >= 1


def test_generate_tacit_pending():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        _create_signals(bond_dir, 5)
        result = generate_tacit_pending(bond_dir)
        assert result is not None
        assert "Possible" in result


def test_signals_capped_at_50():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        for i in range(60):
            signal = SessionSignal(f"2026-03-{i:02d}", "short", "en", [], [])
            save_signal(signal, bond_dir)
        loaded = load_signals(bond_dir)
        assert len(loaded) == 50
