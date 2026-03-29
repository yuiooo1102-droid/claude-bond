"""End-to-end test: init -> apply -> export -> import on a fresh machine."""
import tempfile
from pathlib import Path
from unittest.mock import patch

from claude_bond.commands.init_cmd import run_init
from claude_bond.commands.export_cmd import run_export
from claude_bond.commands.import_cmd import run_import


def test_full_flow():
    mock_classified = {
        "identity": ["senior Python developer", "works at startup"],
        "rules": ["no emoji", "no trailing summaries", "one PR for refactors"],
        "style": ["Chinese language", "concise replies", "code over explanation"],
        "memory": ["working on claude-bond", "girlfriend also uses Claude"],
    }

    with (
        tempfile.TemporaryDirectory() as device_a_claude,
        tempfile.TemporaryDirectory() as device_a_bond,
        tempfile.TemporaryDirectory() as export_dir,
        tempfile.TemporaryDirectory() as device_b_bond,
        tempfile.TemporaryDirectory() as device_b_claude,
    ):
        device_a_claude = Path(device_a_claude)
        device_a_bond = Path(device_a_bond)
        device_b_bond = Path(device_b_bond)
        device_b_claude = Path(device_b_claude)

        # Setup device A: create some Claude config
        (device_a_claude / "CLAUDE.md").write_text("# My Rules\n- Existing rule\n", encoding="utf-8")
        mem_dir = device_a_claude / "memory"
        mem_dir.mkdir()
        (mem_dir / "user.md").write_text(
            "---\nname: user\ndescription: user info\ntype: user\n---\n\nSenior Python developer",
            encoding="utf-8",
        )

        # Step 1: Init on device A
        with patch("claude_bond.commands.init_cmd.has_api_key", return_value=True):
            with patch("claude_bond.commands.init_cmd.classify_content", return_value=mock_classified):
                with patch("claude_bond.commands.init_cmd.generate_questions", return_value=[]):
                    run_init(claude_dir=device_a_claude, bond_dir=device_a_bond, interactive=False)

        assert (device_a_bond / "identity.md").exists()
        assert (device_a_bond / "bond.yaml").exists()

        # Step 2: Apply on device A
        from claude_bond.applier.applier import apply_bond
        apply_bond(bond_dir=device_a_bond, claude_dir=device_a_claude)
        claude_md = (device_a_claude / "CLAUDE.md").read_text(encoding="utf-8")
        assert "Existing rule" in claude_md  # preserved
        assert "Bond" in claude_md  # bond section added

        # Step 3: Export
        bond_file = Path(export_dir) / "my.bond"
        run_export(bond_dir=device_a_bond, output=bond_file)
        assert bond_file.exists()

        # Step 4: Import on device B
        run_import(file=bond_file, bond_dir=device_b_bond, auto_apply=False)
        assert (device_b_bond / "identity.md").exists()
        identity = (device_b_bond / "identity.md").read_text(encoding="utf-8")
        assert "Python developer" in identity

        # Step 5: Apply on device B
        apply_bond(bond_dir=device_b_bond, claude_dir=device_b_claude)
        device_b_md = (device_b_claude / "CLAUDE.md").read_text(encoding="utf-8")
        assert "no emoji" in device_b_md
        assert "Bond" in device_b_md
