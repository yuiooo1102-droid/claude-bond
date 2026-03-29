import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from claude_bond.commands.init_cmd import run_init


def test_run_init_creates_bond_files():
    mock_classified = {
        "identity": ["data scientist"],
        "rules": ["no emoji"],
        "style": ["Chinese", "concise"],
        "memory": ["working on project X"],
    }
    with tempfile.TemporaryDirectory() as claude_tmp, tempfile.TemporaryDirectory() as bond_tmp:
        claude_dir = Path(claude_tmp)
        bond_dir = Path(bond_tmp)

        # Create a minimal ~/.claude/ to scan
        (claude_dir / "CLAUDE.md").write_text("# Rules\n- No emoji", encoding="utf-8")
        mem_dir = claude_dir / "memory"
        mem_dir.mkdir()
        (mem_dir / "user.md").write_text("User is a data scientist", encoding="utf-8")

        with patch("claude_bond.commands.init_cmd.classify_content", return_value=mock_classified):
            with patch("claude_bond.commands.init_cmd.generate_questions", return_value=[]):
                run_init(claude_dir=claude_dir, bond_dir=bond_dir, interactive=False)

        assert (bond_dir / "identity.md").exists()
        assert (bond_dir / "rules.md").exists()
        assert (bond_dir / "style.md").exists()
        assert (bond_dir / "memory.md").exists()
        assert (bond_dir / "bond.yaml").exists()
