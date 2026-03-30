from pathlib import Path
import typer

from claude_bond.commands.init_cmd import run_init
from claude_bond.models.bond import BOND_DIR

app = typer.Typer(
    name="bond",
    help="Package your relationship with Claude.",
    no_args_is_help=True,
)


@app.command()
def init(
    no_interview: bool = typer.Option(False, "--no-interview", help="Skip interactive questions"),
) -> None:
    """Initialize your bond by scanning ~/.claude/ and interviewing you."""
    run_init(interactive=not no_interview)


@app.command()
def apply() -> None:
    """Apply your bond to the current machine's ~/.claude/."""
    from claude_bond.commands.apply_cmd import run_apply
    run_apply()


@app.command()
def export(
    output: str = typer.Option("my.bond", "--output", "-o", help="Output .bond file path"),
    encrypt: bool = typer.Option(False, "--encrypt", "-e", help="Encrypt with password"),
) -> None:
    """Export your bond as a portable .bond file."""
    from claude_bond.commands.export_cmd import run_export

    password = None
    if encrypt:
        password = typer.prompt("Enter encryption password", hide_input=True)
        confirm = typer.prompt("Confirm password", hide_input=True)
        if password != confirm:
            typer.echo("Passwords don't match.")
            raise typer.Exit(1)
    run_export(output=Path(output), password=password)


@app.command(name="import")
def import_bond(
    file: str = typer.Argument(help="Path to .bond file"),
    password: str = typer.Option(None, "--password", "-p", help="Decryption password"),
) -> None:
    """Import a .bond file and apply it."""
    from claude_bond.commands.import_cmd import run_import

    run_import(file=Path(file), password=password)


@app.command()
def sync(
    init_remote: str = typer.Option(None, "--init", help="Initialize with git remote URL"),
) -> None:
    """Sync your bond via git."""
    from claude_bond.commands.sync_cmd import run_sync
    run_sync(init_remote=init_remote)


@app.command()
def review() -> None:
    """Review pending bond changes."""
    from claude_bond.commands.review_cmd import run_review
    run_review()


@app.command()
def auto(
    enable: bool = typer.Option(True, help="Enable or disable auto-merge"),
) -> None:
    """Toggle automatic merging of pending changes."""
    from claude_bond.commands.auto_cmd import run_auto
    run_auto(enable=enable)


@app.command()
def status() -> None:
    """Show current bond status and dimensions."""
    from claude_bond.commands.status_cmd import run_status
    run_status()


@app.command()
def hooks(
    install: bool = typer.Option(False, "--install", help="Install Claude Code hooks"),
    uninstall: bool = typer.Option(False, "--uninstall", help="Remove Claude Code hooks"),
) -> None:
    """Manage Claude Code session hooks."""
    from claude_bond.commands.hooks_cmd import (
        run_hooks_install,
        run_hooks_uninstall,
        run_hooks_status,
    )
    if install:
        run_hooks_install()
    elif uninstall:
        run_hooks_uninstall()
    else:
        run_hooks_status()


@app.command()
def tacit() -> None:
    """Show tacit mode status and detected patterns."""
    from claude_bond.commands.tacit_cmd import run_tacit_status
    run_tacit_status()
