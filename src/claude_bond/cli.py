import typer

app = typer.Typer(
    name="bond",
    help="Package your relationship with Claude.",
    no_args_is_help=True,
)


@app.command()
def init() -> None:
    """Initialize your bond by scanning ~/.claude/ and interviewing you."""
    typer.echo("bond init - not yet implemented")


@app.command()
def apply() -> None:
    """Apply your bond to the current machine's ~/.claude/."""
    typer.echo("bond apply - not yet implemented")


@app.command()
def export(
    output: str = typer.Option("my.bond", "--output", "-o", help="Output .bond file path"),
) -> None:
    """Export your bond as a portable .bond file."""
    typer.echo("bond export - not yet implemented")


@app.command(name="import")
def import_bond(
    file: str = typer.Argument(help="Path to .bond file"),
) -> None:
    """Import a .bond file and apply it."""
    typer.echo("bond import - not yet implemented")


@app.command()
def sync(
    init_remote: str = typer.Option(None, "--init", help="Initialize with git remote URL"),
) -> None:
    """Sync your bond via git."""
    typer.echo("bond sync - not yet implemented")


@app.command()
def review() -> None:
    """Review pending bond changes."""
    typer.echo("bond review - not yet implemented")


@app.command()
def auto(
    enable: bool = typer.Option(True, help="Enable or disable auto-merge"),
) -> None:
    """Toggle automatic merging of pending changes."""
    typer.echo("bond auto - not yet implemented")
