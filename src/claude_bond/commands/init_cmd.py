from __future__ import annotations

from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from claude_bond.models.bond import (
    BOND_DIR,
    BondMeta,
    save_dimension,
    save_meta,
)
from claude_bond.extractor.scanner import scan_claude_dir
from claude_bond.extractor.interviewer import (
    identify_gaps,
    build_bond_from_classified,
)
from claude_bond.utils.claude_api import classify_content, generate_questions

console = Console()
CLAUDE_DIR = Path.home() / ".claude"


def run_init(
    claude_dir: Path = CLAUDE_DIR,
    bond_dir: Path = BOND_DIR,
    interactive: bool = True,
) -> None:
    bond_dir.mkdir(parents=True, exist_ok=True)
    (bond_dir / "pending").mkdir(exist_ok=True)

    # Step 1: Scan
    console.print("\n[bold]Scanning ~/.claude/ ...[/bold]")
    raw = scan_claude_dir(claude_dir)

    raw_text_parts: list[str] = []
    if raw["claude_md"]:
        raw_text_parts.append(f"## CLAUDE.md\n{raw['claude_md']}")
    for name, content in raw.get("memory_files", {}).items():
        raw_text_parts.append(f"## Memory: {name}\n{content}")
    if raw["settings"]:
        raw_text_parts.append(f"## Settings\n{raw['settings']}")
    for proj, content in raw.get("project_claudes", {}).items():
        raw_text_parts.append(f"## Project {proj}\n{content}")

    raw_text = "\n\n".join(raw_text_parts)

    if not raw_text.strip():
        console.print("[yellow]No Claude configuration found. Starting from scratch.[/yellow]")
        classified: dict[str, list[str]] = {
            "identity": [],
            "rules": [],
            "style": [],
            "memory": [],
        }
    else:
        console.print("[bold]Asking Claude to classify extracted data...[/bold]")
        classified = classify_content(raw_text)

    # Display extraction summary
    for dim, items in classified.items():
        marker = "[green]✓[/green]" if items else "[red]✗[/red]"
        console.print(f"  {marker} {dim} — {len(items)} items")

    # Step 2: Interview for gaps
    sources: dict[str, list[str]] = {dim: ["scan"] for dim in classified}
    gaps = identify_gaps(classified)

    if gaps and interactive:
        console.print(f"\n[bold]Found gaps in {len(gaps)} dimensions. Let me ask a few questions...[/bold]\n")
        questions = generate_questions(gaps)
        for q in questions:
            answer = typer.prompt(q)
            supplement = classify_content(f"User answered: {answer}")
            for dim, items in supplement.items():
                classified[dim] = classified.get(dim, []) + items
                if items and dim in sources:
                    sources[dim] = list(set(sources[dim] + ["interview"]))

    # Step 3: Build and save
    dimensions = build_bond_from_classified(classified, sources)
    for dim in dimensions:
        save_dimension(dim, bond_dir)

    today = date.today().isoformat()
    meta = BondMeta(version="0.1.0", created=today, updated=today)
    save_meta(meta, bond_dir)

    console.print(f"\n[bold green]Bond initialized at {bond_dir}[/bold green]")
    console.print("Run [bold]bond apply[/bold] to apply it to this machine.")
