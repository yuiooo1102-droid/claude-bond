from pathlib import Path
import typer

from claude_bond.models.bond import BOND_DIR
from claude_bond.profile import get_bond_dir

app = typer.Typer(
    name="bond",
    help="Package your relationship with Claude.",
    invoke_without_command=True,
)


@app.callback()
def main(
    ctx: typer.Context,
    check: bool = typer.Option(False, "--check", help="Run health checks"),
    diff: bool = typer.Option(False, "--diff", help="Show changes since last apply"),
    tacit: bool = typer.Option(False, "--tacit", help="Show tacit mode patterns"),
    cloud: bool = typer.Option(False, "--cloud", help="Show cloud sync info"),
) -> None:
    """Package your relationship with Claude."""
    if ctx.invoked_subcommand is not None:
        return

    bond_dir = get_bond_dir()

    if check:
        from claude_bond.commands.doctor_cmd import run_doctor
        issues = run_doctor(bond_dir=bond_dir)
        if any(i["level"] == "error" for i in issues):
            raise SystemExit(1)
    elif diff:
        from claude_bond.commands.diff_cmd import run_diff
        run_diff(bond_dir=bond_dir)
    elif tacit:
        from claude_bond.commands.tacit_cmd import run_tacit_status
        run_tacit_status(bond_dir=bond_dir)
    elif cloud:
        from claude_bond.commands.cloud_cmd import run_cloud_status
        run_cloud_status(bond_dir=bond_dir)
    else:
        from claude_bond.commands.status_cmd import run_status
        run_status(bond_dir=bond_dir)


@app.command()
def init(
    no_interview: bool = typer.Option(False, "--no-interview", help="Skip interactive questions"),
) -> None:
    """Initialize bond: scan ~/.claude/, classify, interview, install hooks."""
    from claude_bond.commands.init_cmd import run_init
    from claude_bond.commands.hooks_cmd import run_hooks_install

    bond_dir = get_bond_dir()
    run_init(bond_dir=bond_dir, interactive=not no_interview)

    # Auto-install hooks
    try:
        run_hooks_install()
    except Exception:
        pass


@app.command()
def apply() -> None:
    """Apply bond to current machine's ~/.claude/."""
    from claude_bond.commands.apply_cmd import run_apply
    run_apply(bond_dir=get_bond_dir())


@app.command()
def sync(
    setup: bool = typer.Option(False, "--init", help="Initialize cloud sync (create private Gist)"),
    gist_id: str = typer.Option(None, "--id", help="Pull from a Gist ID (first-time on new device)"),
    force: bool = typer.Option(False, "--force", help="Force push (skip protection)"),
    git_remote: str = typer.Option(None, "--git", help="Use git repo sync instead of cloud"),
) -> None:
    """Sync bond to cloud (GitHub Gist)."""
    bond_dir = get_bond_dir()

    if git_remote:
        from claude_bond.commands.sync_cmd import run_sync
        run_sync(bond_dir=bond_dir, init_remote=git_remote)
        return

    from claude_bond.commands.cloud_cmd import (
        run_cloud_init,
        run_cloud_push,
        run_cloud_pull,
        run_cloud_sync,
    )

    if setup:
        run_cloud_init(bond_dir=bond_dir)
    elif gist_id:
        run_cloud_pull(bond_dir=bond_dir, gist_id=gist_id)
    elif force:
        run_cloud_push(bond_dir=bond_dir, force=True)
    else:
        run_cloud_sync(bond_dir=bond_dir)


@app.command()
def edit(
    dimension: str = typer.Argument(None, help="Dimension to edit directly"),
) -> None:
    """Interactively edit bond dimensions."""
    from claude_bond.commands.edit_cmd import run_edit
    run_edit(bond_dir=get_bond_dir(), dimension=dimension)


@app.command()
def review(
    auto: bool = typer.Option(False, "--auto", help="Auto-merge high-confidence changes"),
    disable: bool = typer.Option(False, "--disable", help="Disable auto-merge"),
) -> None:
    """Review pending changes. Use --auto to enable auto-merge."""
    bond_dir = get_bond_dir()
    if auto or disable:
        from claude_bond.commands.auto_cmd import run_auto
        run_auto(bond_dir=bond_dir, enable=auto)
    else:
        from claude_bond.commands.review_cmd import run_review
        run_review(bond_dir=bond_dir)


@app.command()
def export(
    output: str = typer.Option("my.bond", "--output", "-o", help="Output .bond file path"),
    encrypt: bool = typer.Option(False, "--encrypt", "-e", help="Encrypt with password"),
) -> None:
    """Export bond as a portable .bond file."""
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
