from pathlib import Path
import typer

from claude_bond.commands.init_cmd import run_init
from claude_bond.models.bond import BOND_DIR
from claude_bond.profile import get_bond_dir

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
    run_init(bond_dir=get_bond_dir(), interactive=not no_interview)


@app.command()
def apply() -> None:
    """Apply your bond to the current machine's ~/.claude/."""
    from claude_bond.commands.apply_cmd import run_apply
    run_apply(bond_dir=get_bond_dir())


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
    run_export(bond_dir=get_bond_dir(), output=Path(output), password=password)


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
    run_sync(bond_dir=get_bond_dir(), init_remote=init_remote)


@app.command()
def review() -> None:
    """Review pending bond changes."""
    from claude_bond.commands.review_cmd import run_review
    run_review(bond_dir=get_bond_dir())


@app.command()
def auto(
    enable: bool = typer.Option(True, help="Enable or disable auto-merge"),
) -> None:
    """Toggle automatic merging of pending changes."""
    from claude_bond.commands.auto_cmd import run_auto
    run_auto(bond_dir=get_bond_dir(), enable=enable)


@app.command()
def status() -> None:
    """Show current bond status and dimensions."""
    from claude_bond.commands.status_cmd import run_status
    run_status(bond_dir=get_bond_dir())


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
def diff() -> None:
    """Show diff between last snapshot and current ~/.claude/ state."""
    from claude_bond.commands.diff_cmd import run_diff
    run_diff(bond_dir=get_bond_dir())


@app.command()
def tacit() -> None:
    """Show tacit mode status and detected patterns."""
    from claude_bond.commands.tacit_cmd import run_tacit_status
    run_tacit_status(bond_dir=get_bond_dir())


@app.command()
def doctor() -> None:
    """Run health checks on the bond configuration."""
    from claude_bond.commands.doctor_cmd import run_doctor
    issues = run_doctor(bond_dir=get_bond_dir())
    has_errors = any(i["level"] == "error" for i in issues)
    if has_errors:
        raise SystemExit(1)


@app.command()
def edit(
    dimension: str = typer.Argument(None, help="Dimension to edit directly"),
) -> None:
    """Interactively edit bond dimensions."""
    from claude_bond.commands.edit_cmd import run_edit
    run_edit(bond_dir=get_bond_dir(), dimension=dimension)


@app.command()
def cloud(
    action: str = typer.Argument("sync", help="init, push, pull, status"),
    gist_id: str = typer.Option(None, "--id", help="Gist ID for first-time pull"),
) -> None:
    """Cloud sync via GitHub Gist."""
    from claude_bond.commands.cloud_cmd import (
        run_cloud_init,
        run_cloud_push,
        run_cloud_pull,
        run_cloud_sync,
        run_cloud_status,
    )
    if action == "init":
        run_cloud_init(bond_dir=get_bond_dir())
    elif action == "push":
        run_cloud_push(bond_dir=get_bond_dir())
    elif action == "pull":
        run_cloud_pull(bond_dir=get_bond_dir(), gist_id=gist_id)
    elif action == "status":
        run_cloud_status(bond_dir=get_bond_dir())
    elif action == "sync":
        run_cloud_sync(bond_dir=get_bond_dir())
    else:
        typer.echo(f"Unknown action: {action}. Use init, push, pull, status, or sync.")
        raise typer.Exit(1)


@app.command()
def profile(
    action: str = typer.Argument("list", help="list, use, create, delete, migrate"),
    name: str = typer.Argument(None, help="Profile name"),
    clone: str = typer.Option(None, "--clone", help="Clone from existing profile"),
) -> None:
    """Manage bond profiles (work, personal, etc.)."""
    from claude_bond.commands.profile_cmd import (
        run_profile_list,
        run_profile_use,
        run_profile_create,
        run_profile_delete,
        run_profile_migrate,
    )
    if action == "list":
        run_profile_list()
    elif action == "use":
        if not name:
            typer.echo("Usage: bond profile use <name>")
            raise typer.Exit(1)
        run_profile_use(name)
    elif action == "create":
        if not name:
            typer.echo("Usage: bond profile create <name>")
            raise typer.Exit(1)
        run_profile_create(name, clone_from=clone)
    elif action == "delete":
        if not name:
            typer.echo("Usage: bond profile delete <name>")
            raise typer.Exit(1)
        run_profile_delete(name)
    elif action == "migrate":
        run_profile_migrate()
    else:
        typer.echo(f"Unknown action: {action}. Use list, use, create, delete, or migrate.")
        raise typer.Exit(1)
