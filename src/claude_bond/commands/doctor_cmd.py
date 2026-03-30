from __future__ import annotations

from pathlib import Path

from rich.console import Console

from claude_bond.models.bond import BOND_DIR, DIMENSIONS, load_dimension, load_meta

console = Console()


def run_doctor(bond_dir: Path = BOND_DIR) -> list[dict]:
    """Run health checks. Returns list of issues found."""
    issues: list[dict] = []

    console.print("\n[bold]Bond Doctor[/bold]\n")

    # Check 1: Bond directory exists
    if not bond_dir.exists():
        issues.append({"level": "error", "msg": "Bond directory not found. Run 'bond init'."})
        _print_issue("error", "Bond directory not found. Run 'bond init'.")
        _print_summary(issues)
        return issues
    _print_ok("Bond directory exists")

    # Check 2: bond.yaml exists and is valid
    try:
        meta = load_meta(bond_dir)
        _print_ok(f"bond.yaml valid (v{meta.version})")
    except (FileNotFoundError, Exception) as e:
        issues.append({"level": "error", "msg": f"bond.yaml invalid: {e}"})
        _print_issue("error", f"bond.yaml invalid: {e}")
        _print_summary(issues)
        return issues

    # Check 3: All dimension files exist
    for dim_name in DIMENSIONS:
        dim_path = bond_dir / f"{dim_name}.md"
        if not dim_path.exists():
            issues.append({"level": "warning", "msg": f"Missing dimension file: {dim_name}.md"})
            _print_issue("warning", f"Missing dimension file: {dim_name}.md")
        else:
            try:
                dim = load_dimension(dim_name, bond_dir)
                if not dim.content.strip():
                    issues.append({"level": "info", "msg": f"Empty dimension: {dim_name}"})
                    _print_issue("info", f"Empty dimension: {dim_name}")
                else:
                    items = [l for l in dim.content.splitlines() if l.strip().startswith("-")]
                    _print_ok(f"{dim_name}.md ({len(items)} items)")
            except Exception as e:
                issues.append({"level": "error", "msg": f"Invalid {dim_name}.md: {e}"})
                _print_issue("error", f"Invalid {dim_name}.md: {e}")

    # Check 4: Meta dimensions match DIMENSIONS
    if set(meta.dimensions) != set(DIMENSIONS):
        missing = set(DIMENSIONS) - set(meta.dimensions)
        extra = set(meta.dimensions) - set(DIMENSIONS)
        if missing:
            issues.append({"level": "warning", "msg": f"bond.yaml missing dimensions: {missing}"})
            _print_issue("warning", f"bond.yaml missing dimensions: {missing}")
        if extra:
            issues.append({"level": "info", "msg": f"bond.yaml has extra dimensions: {extra}"})
            _print_issue("info", f"bond.yaml has extra dimensions: {extra}")
    else:
        _print_ok(f"Dimensions consistent ({len(DIMENSIONS)} registered)")

    # Check 5: Pending directory
    pending_dir = bond_dir / "pending"
    if not pending_dir.exists():
        issues.append({"level": "info", "msg": "pending/ directory missing"})
        _print_issue("info", "pending/ directory missing (will be created on next init)")
    else:
        pending_count = len(list(pending_dir.glob("*.md")))
        if pending_count > 0:
            _print_issue("info", f"{pending_count} pending change(s) awaiting review")
        else:
            _print_ok("No pending changes")

    # Check 6: Snapshot exists
    snapshot_dir = bond_dir / ".snapshot"
    if not snapshot_dir.exists():
        issues.append({"level": "warning", "msg": "No snapshot. Run 'bond apply' to enable change detection."})
        _print_issue("warning", "No snapshot. Run 'bond apply' to enable change detection.")
    else:
        _print_ok("Snapshot exists (evolve detection active)")

    # Check 7: Claude directory accessible
    claude_dir = Path.home() / ".claude"
    if not claude_dir.exists():
        issues.append({"level": "warning", "msg": "~/.claude/ not found. Claude Code may not be installed."})
        _print_issue("warning", "~/.claude/ not found. Claude Code may not be installed.")
    else:
        claude_md = claude_dir / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text(encoding="utf-8")
            if "<!-- bond:start -->" in content:
                _print_ok("Bond section found in ~/.claude/CLAUDE.md")
            else:
                issues.append({"level": "info", "msg": "Bond not applied to CLAUDE.md yet. Run 'bond apply'."})
                _print_issue("info", "Bond not applied to CLAUDE.md yet. Run 'bond apply'.")
        else:
            _print_issue("info", "~/.claude/CLAUDE.md not found")

    # Check 8: Tacit signals
    tacit_path = bond_dir / "tacit_signals.json"
    if tacit_path.exists():
        import json
        try:
            signals = json.loads(tacit_path.read_text(encoding="utf-8"))
            _print_ok(f"Tacit mode: {len(signals)} session(s) tracked")
        except Exception:
            issues.append({"level": "warning", "msg": "tacit_signals.json corrupted"})
            _print_issue("warning", "tacit_signals.json corrupted")
    else:
        _print_ok("Tacit mode: no signals yet (normal for new bond)")

    _print_summary(issues)
    return issues


def _print_ok(msg: str) -> None:
    console.print(f"  [green]✓[/green] {msg}")


def _print_issue(level: str, msg: str) -> None:
    icons = {"error": "[red]✗[/red]", "warning": "[yellow]![/yellow]", "info": "[dim]·[/dim]"}
    icon = icons.get(level, "[dim]?[/dim]")
    console.print(f"  {icon} {msg}")


def _print_summary(issues: list[dict]) -> None:
    errors = sum(1 for i in issues if i["level"] == "error")
    warnings = sum(1 for i in issues if i["level"] == "warning")
    infos = sum(1 for i in issues if i["level"] == "info")

    console.print()
    if errors:
        console.print(f"  [red bold]{errors} error(s)[/red bold]", end="")
    if warnings:
        console.print(f"  [yellow]{warnings} warning(s)[/yellow]", end="")
    if infos:
        console.print(f"  [dim]{infos} info(s)[/dim]", end="")
    if not issues:
        console.print("  [bold green]All checks passed![/bold green]", end="")
    console.print("\n")
