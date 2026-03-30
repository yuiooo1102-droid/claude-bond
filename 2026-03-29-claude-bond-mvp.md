# claude-bond MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI tool + Claude Code hooks that package the user-Claude relationship into portable Markdown files, enabling cross-device sync, export/import, and automatic evolution.

**Architecture:** Python CLI (Typer) with 5 modules: extractor (scan + interview), applier (bond -> claude config), evolve (detect + merge changes), sync (git-based), and pack (export/import .bond ZIP). Claude API handles intelligent extraction, classification, and merging.

**Tech Stack:** Python 3.11+, Typer, anthropic SDK, PyYAML, zipfile (stdlib), subprocess (git)

---

## File Map

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Project metadata, dependencies, `[project.scripts]` entry point |
| `src/claude_bond/__init__.py` | Package version |
| `src/claude_bond/cli.py` | Typer app, register all commands |
| `src/claude_bond/models/bond.py` | Bond dataclass, BondMeta, dimension file I/O |
| `src/claude_bond/utils/security.py` | Regex-based secret filtering |
| `src/claude_bond/utils/claude_api.py` | Thin wrapper: send prompt, get structured response |
| `src/claude_bond/extractor/scanner.py` | Walk ~/.claude/, read files, collect raw text per source |
| `src/claude_bond/extractor/interviewer.py` | Generate gap questions, parse answers, fill dimensions |
| `src/claude_bond/commands/init_cmd.py` | `bond init` orchestration |
| `src/claude_bond/applier/applier.py` | Read bond files, write CLAUDE.md section + memory files |
| `src/claude_bond/commands/apply_cmd.py` | `bond apply` orchestration |
| `src/claude_bond/commands/export_cmd.py` | ZIP pack ~/.claude-bond/ -> .bond |
| `src/claude_bond/commands/import_cmd.py` | Unpack .bond -> ~/.claude-bond/, call apply |
| `src/claude_bond/sync_engine/git_sync.py` | Git init/add/commit/pull/push, semantic merge |
| `src/claude_bond/commands/sync_cmd.py` | `bond sync` orchestration |
| `src/claude_bond/evolve/detector.py` | Snapshot diff, classify changes via Claude API |
| `src/claude_bond/evolve/merger.py` | Merge pending items into bond files |
| `src/claude_bond/commands/review_cmd.py` | `bond review` interactive TUI |
| `src/claude_bond/commands/auto_cmd.py` | `bond auto` toggle |
| `hooks/session-start.sh` | Shell hook calling `bond apply` |
| `hooks/session-end.sh` | Shell hook calling evolve detector |

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/claude_bond/__init__.py`
- Create: `src/claude_bond/cli.py`

- [ ] **Step 1: Create project directory and pyproject.toml**

```bash
mkdir -p /Users/wh/coding/claude-bond/src/claude_bond
mkdir -p /Users/wh/coding/claude-bond/tests
```

```toml
# /Users/wh/coding/claude-bond/pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "claude-bond"
version = "0.1.0"
description = "Package your relationship with Claude. Make Claude recognize you on any device."
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12.0",
    "anthropic>=0.40.0",
    "pyyaml>=6.0",
    "rich>=13.0",
]

[project.scripts]
bond = "claude_bond.cli:app"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 2: Create __init__.py**

```python
# src/claude_bond/__init__.py
__version__ = "0.1.0"
```

- [ ] **Step 3: Create CLI entry point with placeholder commands**

```python
# src/claude_bond/cli.py
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
```

- [ ] **Step 4: Initialize git repo and install in dev mode**

```bash
cd /Users/wh/coding/claude-bond
git init
pip install -e ".[dev]" 2>/dev/null || pip install -e .
```

- [ ] **Step 5: Verify CLI works**

Run: `bond --help`
Expected: Shows help text with all 7 commands listed.

Run: `bond init`
Expected: `bond init - not yet implemented`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/ tests/
git commit -m "feat: project scaffolding with CLI entry point"
```

---

### Task 2: Bond Data Model

**Files:**
- Create: `src/claude_bond/models/bond.py`
- Create: `tests/test_bond_model.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_bond_model.py
from pathlib import Path
import tempfile

from claude_bond.models.bond import (
    BondDimension,
    BondMeta,
    load_dimension,
    save_dimension,
    load_meta,
    save_meta,
    BOND_DIR,
)


def test_bond_dimension_from_markdown():
    md = """---
dimension: identity
updated: "2026-03-29"
source: [scan, interview]
---

- Data scientist focused on NLP
- Python as main language
"""
    dim = BondDimension.from_markdown(md)
    assert dim.name == "identity"
    assert dim.updated == "2026-03-29"
    assert dim.source == ["scan", "interview"]
    assert "Data scientist" in dim.content


def test_bond_dimension_to_markdown():
    dim = BondDimension(
        name="rules",
        updated="2026-03-29",
        source=["scan"],
        content="- No emoji in responses\n- No trailing summaries",
    )
    md = dim.to_markdown()
    assert "dimension: rules" in md
    assert "No emoji" in md


def test_save_and_load_dimension():
    dim = BondDimension(
        name="style",
        updated="2026-03-29",
        source=["interview"],
        content="- Language: Chinese\n- Style: concise",
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        save_dimension(dim, Path(tmpdir))
        loaded = load_dimension("style", Path(tmpdir))
        assert loaded.name == "style"
        assert "Chinese" in loaded.content


def test_bond_meta_roundtrip():
    meta = BondMeta(
        version="0.1.0",
        created="2026-03-29",
        updated="2026-03-29",
        dimensions=["identity", "rules", "style", "memory"],
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        save_meta(meta, Path(tmpdir))
        loaded = load_meta(Path(tmpdir))
        assert loaded.version == "0.1.0"
        assert loaded.dimensions == ["identity", "rules", "style", "memory"]


def test_bond_dir_default():
    assert BOND_DIR == Path.home() / ".claude-bond"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_bond_model.py -v`
Expected: FAIL — `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Implement the Bond data model**

```python
# src/claude_bond/models/__init__.py
```

```python
# src/claude_bond/models/bond.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


BOND_DIR = Path.home() / ".claude-bond"
DIMENSIONS = ("identity", "rules", "style", "memory")


@dataclass(frozen=True)
class BondDimension:
    name: str
    updated: str
    source: list[str]
    content: str

    @classmethod
    def from_markdown(cls, text: str) -> BondDimension:
        parts = text.split("---", 2)
        if len(parts) < 3:
            raise ValueError("Invalid bond dimension: missing frontmatter")
        meta = yaml.safe_load(parts[1])
        content = parts[2].strip()
        return cls(
            name=meta["dimension"],
            updated=str(meta["updated"]),
            source=meta.get("source", []),
            content=content,
        )

    def to_markdown(self) -> str:
        meta = {
            "dimension": self.name,
            "updated": self.updated,
            "source": self.source,
        }
        header = yaml.dump(meta, default_flow_style=False, allow_unicode=True).strip()
        return f"---\n{header}\n---\n\n{self.content}\n"


@dataclass(frozen=True)
class BondMeta:
    version: str
    created: str
    updated: str
    dimensions: list[str] = field(default_factory=lambda: list(DIMENSIONS))


def save_dimension(dim: BondDimension, bond_dir: Path) -> Path:
    path = bond_dir / f"{dim.name}.md"
    path.write_text(dim.to_markdown(), encoding="utf-8")
    return path


def load_dimension(name: str, bond_dir: Path) -> BondDimension:
    path = bond_dir / f"{name}.md"
    return BondDimension.from_markdown(path.read_text(encoding="utf-8"))


def save_meta(meta: BondMeta, bond_dir: Path) -> Path:
    path = bond_dir / "bond.yaml"
    data = {
        "version": meta.version,
        "created": meta.created,
        "updated": meta.updated,
        "dimensions": meta.dimensions,
    }
    path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    return path


def load_meta(bond_dir: Path) -> BondMeta:
    path = bond_dir / "bond.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return BondMeta(
        version=data["version"],
        created=data["created"],
        updated=data["updated"],
        dimensions=data.get("dimensions", list(DIMENSIONS)),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_bond_model.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/claude_bond/models/ tests/test_bond_model.py
git commit -m "feat: bond data model with dimension and meta I/O"
```

---

### Task 3: Security Filter

**Files:**
- Create: `src/claude_bond/utils/security.py`
- Create: `tests/test_security.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_security.py
from claude_bond.utils.security import filter_secrets


def test_filters_api_keys():
    text = "My key is sk-ant-api03-abcdef123456 and also OPENAI_API_KEY=sk-proj-xyz"
    result = filter_secrets(text)
    assert "sk-ant-api03" not in result
    assert "sk-proj-xyz" not in result
    assert "[REDACTED]" in result


def test_filters_env_style_secrets():
    text = """
DATABASE_URL=postgres://user:pass@host/db
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
NORMAL_VAR=hello
"""
    result = filter_secrets(text)
    assert "postgres://user:pass" not in result
    assert "wJalrXUtnFEMI" not in result
    assert "NORMAL_VAR=hello" in result


def test_preserves_normal_content():
    text = "- I am a data scientist\n- I prefer Python\n- No emoji please"
    result = filter_secrets(text)
    assert result == text


def test_filters_bearer_tokens():
    text = 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc.def'
    result = filter_secrets(text)
    assert "eyJhbGci" not in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_security.py -v`
Expected: FAIL

- [ ] **Step 3: Implement secret filtering**

```python
# src/claude_bond/utils/__init__.py
```

```python
# src/claude_bond/utils/security.py
from __future__ import annotations

import re

_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("anthropic_key", re.compile(r"sk-ant-[\w-]{20,}")),
    ("openai_key", re.compile(r"sk-proj-[\w-]{20,}")),
    ("openai_key_old", re.compile(r"sk-[a-zA-Z0-9]{32,}")),
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)),
    ("database_url", re.compile(r"(postgres|mysql|mongodb)://\S+")),
    ("aws_secret", re.compile(r"(?:AWS_SECRET_ACCESS_KEY|aws_secret_access_key)\s*=\s*\S+")),
    ("generic_secret", re.compile(
        r"(?:SECRET|TOKEN|PASSWORD|PASSWD|API_KEY|APIKEY|ACCESS_KEY)"
        r"\s*=\s*\S+",
        re.IGNORECASE,
    )),
]


def filter_secrets(text: str) -> str:
    result = text
    for name, pattern in _SECRET_PATTERNS:
        result = pattern.sub(f"[REDACTED:{name}]", result)
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_security.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/claude_bond/utils/ tests/test_security.py
git commit -m "feat: secret filtering for bond extraction"
```

---

### Task 4: Claude API Wrapper

**Files:**
- Create: `src/claude_bond/utils/claude_api.py`
- Create: `tests/test_claude_api.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_claude_api.py
from unittest.mock import patch, MagicMock

from claude_bond.utils.claude_api import classify_content, generate_questions, ask_claude


def test_ask_claude_returns_text():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Hello from Claude")]
    )
    with patch("claude_bond.utils.claude_api._get_client", return_value=mock_client):
        result = ask_claude("Say hello")
        assert result == "Hello from Claude"


def test_classify_content_calls_api():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text='{"identity": ["I am a dev"], "rules": [], "style": [], "memory": []}')]
    )
    with patch("claude_bond.utils.claude_api._get_client", return_value=mock_client):
        result = classify_content("some raw text from scanning")
        assert "identity" in result
        assert isinstance(result["identity"], list)


def test_generate_questions_calls_api():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text='["What language do you prefer?", "Short or detailed replies?"]')]
    )
    with patch("claude_bond.utils.claude_api._get_client", return_value=mock_client):
        gaps = {"style": "insufficient data"}
        result = generate_questions(gaps)
        assert isinstance(result, list)
        assert len(result) >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_claude_api.py -v`
Expected: FAIL

- [ ] **Step 3: Implement Claude API wrapper**

```python
# src/claude_bond/utils/claude_api.py
from __future__ import annotations

import json
import os

from anthropic import Anthropic


_client: Anthropic | None = None

MODEL = "claude-sonnet-4-20250514"


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


def ask_claude(prompt: str, system: str = "") -> str:
    client = _get_client()
    messages = [{"role": "user", "content": prompt}]
    kwargs: dict = {"model": MODEL, "max_tokens": 4096, "messages": messages}
    if system:
        kwargs["system"] = system
    response = client.messages.create(**kwargs)
    return response.content[0].text


def classify_content(raw_text: str) -> dict[str, list[str]]:
    system = (
        "You classify raw text extracted from a user's Claude configuration into 4 dimensions: "
        "identity (who the user is), rules (behavioral preferences), "
        "style (communication preferences), memory (factual memories). "
        "Return valid JSON: {\"identity\": [...], \"rules\": [...], \"style\": [...], \"memory\": [...]}"
        " Each value is a list of concise bullet-point strings. "
        "If a dimension has no data, return an empty list."
    )
    result = ask_claude(f"Classify this content:\n\n{raw_text}", system=system)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        start = result.find("{")
        end = result.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(result[start:end])
        return {"identity": [], "rules": [], "style": [], "memory": []}


def generate_questions(gaps: dict[str, str]) -> list[str]:
    system = (
        "You generate 3-5 targeted questions to fill gaps in a user's bond profile. "
        "Return valid JSON: a list of question strings. "
        "Questions should be conversational and easy to answer."
    )
    prompt = f"These dimensions need more data:\n{json.dumps(gaps, ensure_ascii=False)}"
    result = ask_claude(prompt, system=system)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        start = result.find("[")
        end = result.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(result[start:end])
        return []


def analyze_changes(old_content: str, new_content: str) -> str:
    system = (
        "You analyze changes in a user's Claude configuration files and classify them as bond updates. "
        "For each change, output a line in this format:\n"
        "- [dimension] description\n"
        "Where dimension is one of: identity, rules, style, memory.\n"
        "Group into sections: ## New, ## Updated, ## Possible (low confidence).\n"
        "If no meaningful bond changes, return 'NO_CHANGES'."
    )
    prompt = f"OLD:\n{old_content}\n\nNEW:\n{new_content}"
    return ask_claude(prompt, system=system)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_claude_api.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/claude_bond/utils/claude_api.py tests/test_claude_api.py
git commit -m "feat: Claude API wrapper for classification, questions, and change analysis"
```

---

### Task 5: Scanner (Extract from ~/.claude/)

**Files:**
- Create: `src/claude_bond/extractor/__init__.py`
- Create: `src/claude_bond/extractor/scanner.py`
- Create: `tests/test_scanner.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_scanner.py
import tempfile
from pathlib import Path

from claude_bond.extractor.scanner import scan_claude_dir


def test_scan_reads_claude_md():
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir)
        (claude_dir / "CLAUDE.md").write_text("# Rules\n- No emoji\n- Be concise", encoding="utf-8")
        result = scan_claude_dir(claude_dir)
        assert "No emoji" in result["claude_md"]


def test_scan_reads_memory_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir)
        mem_dir = claude_dir / "memory"
        mem_dir.mkdir()
        (mem_dir / "user_role.md").write_text("User is a data scientist", encoding="utf-8")
        (mem_dir / "feedback_testing.md").write_text("Don't mock the database", encoding="utf-8")
        result = scan_claude_dir(claude_dir)
        assert len(result["memory_files"]) == 2
        assert any("data scientist" in m for m in result["memory_files"].values())


def test_scan_reads_settings():
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir)
        (claude_dir / "settings.json").write_text('{"language": "zh"}', encoding="utf-8")
        result = scan_claude_dir(claude_dir)
        assert "zh" in result["settings"]


def test_scan_handles_missing_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = scan_claude_dir(Path(tmpdir))
        assert result["claude_md"] == ""
        assert result["memory_files"] == {}
        assert result["settings"] == ""


def test_scan_filters_secrets():
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir)
        (claude_dir / "CLAUDE.md").write_text("API_KEY=sk-ant-api03-secretkey123456789", encoding="utf-8")
        result = scan_claude_dir(claude_dir)
        assert "sk-ant-api03" not in result["claude_md"]
        assert "REDACTED" in result["claude_md"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_scanner.py -v`
Expected: FAIL

- [ ] **Step 3: Implement scanner**

```python
# src/claude_bond/extractor/__init__.py
```

```python
# src/claude_bond/extractor/scanner.py
from __future__ import annotations

from pathlib import Path

from claude_bond.utils.security import filter_secrets


def scan_claude_dir(claude_dir: Path) -> dict[str, str | dict[str, str]]:
    result: dict[str, str | dict[str, str]] = {
        "claude_md": "",
        "memory_files": {},
        "settings": "",
        "project_claudes": {},
    }

    claude_md = claude_dir / "CLAUDE.md"
    if claude_md.exists():
        result["claude_md"] = filter_secrets(claude_md.read_text(encoding="utf-8"))

    memory_dir = claude_dir / "memory"
    if memory_dir.is_dir():
        mem_files: dict[str, str] = {}
        for f in sorted(memory_dir.glob("*.md")):
            mem_files[f.name] = filter_secrets(f.read_text(encoding="utf-8"))
        result["memory_files"] = mem_files

    settings_file = claude_dir / "settings.json"
    if settings_file.exists():
        result["settings"] = filter_secrets(settings_file.read_text(encoding="utf-8"))

    projects_dir = claude_dir / "projects"
    if projects_dir.is_dir():
        proj_claudes: dict[str, str] = {}
        for proj in projects_dir.iterdir():
            if proj.is_dir():
                proj_claude = proj / "CLAUDE.md"
                if proj_claude.exists():
                    proj_claudes[proj.name] = filter_secrets(
                        proj_claude.read_text(encoding="utf-8")
                    )
        result["project_claudes"] = proj_claudes

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_scanner.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/claude_bond/extractor/ tests/test_scanner.py
git commit -m "feat: scanner to extract data from ~/.claude/ directory"
```

---

### Task 6: Interviewer (AI Gap-Fill)

**Files:**
- Create: `src/claude_bond/extractor/interviewer.py`
- Create: `tests/test_interviewer.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_interviewer.py
from unittest.mock import patch

from claude_bond.extractor.interviewer import identify_gaps, build_bond_from_classified


def test_identify_gaps_finds_empty_dimensions():
    classified = {
        "identity": ["data scientist"],
        "rules": ["no emoji"],
        "style": [],
        "memory": ["works on NLP"],
    }
    gaps = identify_gaps(classified)
    assert "style" in gaps
    assert "identity" not in gaps


def test_identify_gaps_no_gaps():
    classified = {
        "identity": ["dev"],
        "rules": ["be concise"],
        "style": ["Chinese", "short replies"],
        "memory": ["project X"],
    }
    gaps = identify_gaps(classified)
    assert gaps == {}


def test_build_bond_from_classified():
    classified = {
        "identity": ["data scientist", "Python expert"],
        "rules": ["no emoji", "no summaries"],
        "style": ["Chinese", "concise"],
        "memory": ["working on claude-bond"],
    }
    dimensions = build_bond_from_classified(classified)
    assert len(dimensions) == 4
    names = {d.name for d in dimensions}
    assert names == {"identity", "rules", "style", "memory"}
    identity = next(d for d in dimensions if d.name == "identity")
    assert "data scientist" in identity.content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_interviewer.py -v`
Expected: FAIL

- [ ] **Step 3: Implement interviewer**

```python
# src/claude_bond/extractor/interviewer.py
from __future__ import annotations

from datetime import date

from claude_bond.models.bond import BondDimension, DIMENSIONS


def identify_gaps(classified: dict[str, list[str]]) -> dict[str, str]:
    gaps: dict[str, str] = {}
    for dim in DIMENSIONS:
        items = classified.get(dim, [])
        if len(items) == 0:
            gaps[dim] = "no data found"
        elif len(items) == 1 and dim in ("identity", "style"):
            gaps[dim] = "insufficient data (only 1 item)"
    return gaps


def build_bond_from_classified(
    classified: dict[str, list[str]],
    sources: dict[str, list[str]] | None = None,
) -> list[BondDimension]:
    today = date.today().isoformat()
    if sources is None:
        sources = {dim: ["scan"] for dim in DIMENSIONS}

    dimensions: list[BondDimension] = []
    for dim in DIMENSIONS:
        items = classified.get(dim, [])
        content = "\n".join(f"- {item}" for item in items) if items else ""
        dimensions.append(
            BondDimension(
                name=dim,
                updated=today,
                source=sources.get(dim, ["scan"]),
                content=content,
            )
        )
    return dimensions
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_interviewer.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/claude_bond/extractor/interviewer.py tests/test_interviewer.py
git commit -m "feat: interviewer for gap detection and bond construction"
```

---

### Task 7: bond init Command

**Files:**
- Create: `src/claude_bond/commands/__init__.py`
- Create: `src/claude_bond/commands/init_cmd.py`
- Modify: `src/claude_bond/cli.py`
- Create: `tests/test_init_cmd.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_init_cmd.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_init_cmd.py -v`
Expected: FAIL

- [ ] **Step 3: Implement init command**

```python
# src/claude_bond/commands/__init__.py
```

```python
# src/claude_bond/commands/init_cmd.py
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
            # Re-classify the answer and merge
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
```

- [ ] **Step 4: Wire init command into CLI**

Replace the `init` function in `src/claude_bond/cli.py`:

```python
# src/claude_bond/cli.py
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_init_cmd.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/claude_bond/commands/ src/claude_bond/cli.py tests/test_init_cmd.py
git commit -m "feat: bond init command with scan + AI classification"
```

---

### Task 8: Applier (bond apply)

**Files:**
- Create: `src/claude_bond/applier/__init__.py`
- Create: `src/claude_bond/applier/applier.py`
- Create: `src/claude_bond/commands/apply_cmd.py`
- Create: `tests/test_applier.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_applier.py
import tempfile
from pathlib import Path

from claude_bond.models.bond import BondDimension, BondMeta, save_dimension, save_meta
from claude_bond.applier.applier import apply_bond


def _create_test_bond(bond_dir: Path) -> None:
    dims = [
        BondDimension("identity", "2026-03-29", ["scan"], "- Data scientist\n- Python expert"),
        BondDimension("rules", "2026-03-29", ["scan"], "- No emoji\n- No trailing summaries"),
        BondDimension("style", "2026-03-29", ["interview"], "- Language: Chinese\n- Style: concise"),
        BondDimension("memory", "2026-03-29", ["scan"], "- Working on claude-bond project"),
    ]
    for d in dims:
        save_dimension(d, bond_dir)
    save_meta(BondMeta("0.1.0", "2026-03-29", "2026-03-29"), bond_dir)


def test_apply_creates_claude_md_section():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as claude_tmp:
        bond_dir = Path(bond_tmp)
        claude_dir = Path(claude_tmp)
        _create_test_bond(bond_dir)

        apply_bond(bond_dir=bond_dir, claude_dir=claude_dir)

        claude_md = (claude_dir / "CLAUDE.md").read_text(encoding="utf-8")
        assert "## Bond" in claude_md
        assert "No emoji" in claude_md


def test_apply_preserves_existing_claude_md():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as claude_tmp:
        bond_dir = Path(bond_tmp)
        claude_dir = Path(claude_tmp)
        _create_test_bond(bond_dir)

        (claude_dir / "CLAUDE.md").write_text("# My Existing Rules\n- Keep this\n", encoding="utf-8")

        apply_bond(bond_dir=bond_dir, claude_dir=claude_dir)

        claude_md = (claude_dir / "CLAUDE.md").read_text(encoding="utf-8")
        assert "Keep this" in claude_md
        assert "## Bond" in claude_md


def test_apply_writes_memory_files():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as claude_tmp:
        bond_dir = Path(bond_tmp)
        claude_dir = Path(claude_tmp)
        _create_test_bond(bond_dir)

        apply_bond(bond_dir=bond_dir, claude_dir=claude_dir)

        mem_dir = claude_dir / "memory"
        assert mem_dir.is_dir()
        bond_mem = mem_dir / "bond_memory.md"
        assert bond_mem.exists()
        assert "claude-bond" in bond_mem.read_text(encoding="utf-8")


def test_apply_creates_snapshot():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as claude_tmp:
        bond_dir = Path(bond_tmp)
        claude_dir = Path(claude_tmp)
        _create_test_bond(bond_dir)

        apply_bond(bond_dir=bond_dir, claude_dir=claude_dir)

        snapshot_dir = bond_dir / ".snapshot"
        assert snapshot_dir.is_dir()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_applier.py -v`
Expected: FAIL

- [ ] **Step 3: Implement applier**

```python
# src/claude_bond/applier/__init__.py
```

```python
# src/claude_bond/applier/applier.py
from __future__ import annotations

import shutil
from pathlib import Path

from claude_bond.models.bond import BOND_DIR, DIMENSIONS, load_dimension, load_meta


_BOND_SECTION_START = "<!-- bond:start -->"
_BOND_SECTION_END = "<!-- bond:end -->"


def apply_bond(
    bond_dir: Path = BOND_DIR,
    claude_dir: Path | None = None,
) -> None:
    if claude_dir is None:
        claude_dir = Path.home() / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)

    meta = load_meta(bond_dir)
    dims = {name: load_dimension(name, bond_dir) for name in meta.dimensions}

    # Build the bond section for CLAUDE.md
    bond_lines: list[str] = [_BOND_SECTION_START, "## Bond", ""]
    if "identity" in dims and dims["identity"].content:
        bond_lines.append("### Who I'm working with")
        bond_lines.append(dims["identity"].content)
        bond_lines.append("")
    if "rules" in dims and dims["rules"].content:
        bond_lines.append("### Behavioral rules")
        bond_lines.append(dims["rules"].content)
        bond_lines.append("")
    if "style" in dims and dims["style"].content:
        bond_lines.append("### Communication style")
        bond_lines.append(dims["style"].content)
        bond_lines.append("")
    bond_lines.append(_BOND_SECTION_END)
    bond_section = "\n".join(bond_lines)

    # Write CLAUDE.md (preserve existing content)
    claude_md_path = claude_dir / "CLAUDE.md"
    if claude_md_path.exists():
        existing = claude_md_path.read_text(encoding="utf-8")
        if _BOND_SECTION_START in existing:
            start = existing.index(_BOND_SECTION_START)
            end = existing.index(_BOND_SECTION_END) + len(_BOND_SECTION_END)
            new_content = existing[:start] + bond_section + existing[end:]
        else:
            new_content = existing.rstrip() + "\n\n" + bond_section + "\n"
    else:
        new_content = bond_section + "\n"
    claude_md_path.write_text(new_content, encoding="utf-8")

    # Write memory files
    if "memory" in dims and dims["memory"].content:
        mem_dir = claude_dir / "memory"
        mem_dir.mkdir(exist_ok=True)
        bond_mem_path = mem_dir / "bond_memory.md"
        bond_mem_path.write_text(
            f"---\nname: bond-memory\ndescription: Memories imported from claude-bond\ntype: project\n---\n\n{dims['memory'].content}\n",
            encoding="utf-8",
        )

    # Save snapshot for evolve detection
    snapshot_dir = bond_dir / ".snapshot"
    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)
    snapshot_dir.mkdir()

    if claude_md_path.exists():
        shutil.copy2(claude_md_path, snapshot_dir / "CLAUDE.md")
    mem_dir = claude_dir / "memory"
    if mem_dir.is_dir():
        snapshot_mem = snapshot_dir / "memory"
        snapshot_mem.mkdir()
        for f in mem_dir.glob("*.md"):
            shutil.copy2(f, snapshot_mem / f.name)
```

- [ ] **Step 4: Wire apply command into CLI**

```python
# src/claude_bond/commands/apply_cmd.py
from __future__ import annotations

from pathlib import Path

from rich.console import Console

from claude_bond.applier.applier import apply_bond
from claude_bond.models.bond import BOND_DIR

console = Console()


def run_apply(bond_dir: Path = BOND_DIR) -> None:
    if not (bond_dir / "bond.yaml").exists():
        console.print("[red]No bond found. Run 'bond init' first.[/red]")
        raise SystemExit(1)
    apply_bond(bond_dir=bond_dir)
    console.print("[bold green]Bond applied successfully.[/bold green]")
```

Update `src/claude_bond/cli.py` — replace the `apply` function:

```python
@app.command()
def apply() -> None:
    """Apply your bond to the current machine's ~/.claude/."""
    from claude_bond.commands.apply_cmd import run_apply
    run_apply()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_applier.py -v`
Expected: All 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/claude_bond/applier/ src/claude_bond/commands/apply_cmd.py src/claude_bond/cli.py tests/test_applier.py
git commit -m "feat: bond apply with CLAUDE.md section management and snapshot"
```

---

### Task 9: Export / Import

**Files:**
- Create: `src/claude_bond/commands/export_cmd.py`
- Create: `src/claude_bond/commands/import_cmd.py`
- Create: `tests/test_export_import.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_export_import.py
import tempfile
from pathlib import Path

from claude_bond.models.bond import BondDimension, BondMeta, save_dimension, save_meta
from claude_bond.commands.export_cmd import run_export
from claude_bond.commands.import_cmd import run_import


def _create_test_bond(bond_dir: Path) -> None:
    dims = [
        BondDimension("identity", "2026-03-29", ["scan"], "- Data scientist"),
        BondDimension("rules", "2026-03-29", ["scan"], "- No emoji"),
        BondDimension("style", "2026-03-29", ["interview"], "- Chinese"),
        BondDimension("memory", "2026-03-29", ["scan"], "- Project X"),
    ]
    for d in dims:
        save_dimension(d, bond_dir)
    save_meta(BondMeta("0.1.0", "2026-03-29", "2026-03-29"), bond_dir)


def test_export_creates_bond_file():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as out_tmp:
        bond_dir = Path(bond_tmp)
        _create_test_bond(bond_dir)
        output = Path(out_tmp) / "test.bond"
        run_export(bond_dir=bond_dir, output=output)
        assert output.exists()
        assert output.stat().st_size > 0


def test_import_restores_bond():
    with (
        tempfile.TemporaryDirectory() as src_tmp,
        tempfile.TemporaryDirectory() as out_tmp,
        tempfile.TemporaryDirectory() as dst_tmp,
    ):
        src_bond = Path(src_tmp)
        _create_test_bond(src_bond)

        bond_file = Path(out_tmp) / "test.bond"
        run_export(bond_dir=src_bond, output=bond_file)

        dst_bond = Path(dst_tmp)
        run_import(file=bond_file, bond_dir=dst_bond, auto_apply=False)

        assert (dst_bond / "identity.md").exists()
        assert (dst_bond / "bond.yaml").exists()
        content = (dst_bond / "identity.md").read_text(encoding="utf-8")
        assert "Data scientist" in content


def test_export_excludes_snapshot_and_pending():
    with tempfile.TemporaryDirectory() as bond_tmp, tempfile.TemporaryDirectory() as out_tmp:
        bond_dir = Path(bond_tmp)
        _create_test_bond(bond_dir)
        (bond_dir / ".snapshot").mkdir()
        (bond_dir / ".snapshot" / "CLAUDE.md").write_text("snapshot", encoding="utf-8")
        (bond_dir / "pending").mkdir()
        (bond_dir / "pending" / "2026-03-29.md").write_text("pending", encoding="utf-8")

        output = Path(out_tmp) / "test.bond"
        run_export(bond_dir=bond_dir, output=output)

        import zipfile
        with zipfile.ZipFile(output, "r") as zf:
            names = zf.namelist()
            assert not any(".snapshot" in n for n in names)
            assert not any("pending" in n for n in names)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_export_import.py -v`
Expected: FAIL

- [ ] **Step 3: Implement export**

```python
# src/claude_bond/commands/export_cmd.py
from __future__ import annotations

import zipfile
from pathlib import Path

from rich.console import Console

from claude_bond.models.bond import BOND_DIR

console = Console()

_EXCLUDE_DIRS = {".snapshot", "pending", ".git", "__pycache__"}


def run_export(bond_dir: Path = BOND_DIR, output: Path | None = None) -> Path:
    if not (bond_dir / "bond.yaml").exists():
        console.print("[red]No bond found. Run 'bond init' first.[/red]")
        raise SystemExit(1)

    if output is None:
        output = Path.cwd() / "my.bond"

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(bond_dir.rglob("*")):
            if file.is_file():
                rel = file.relative_to(bond_dir)
                if any(part in _EXCLUDE_DIRS for part in rel.parts):
                    continue
                zf.write(file, str(rel))

    console.print(f"[bold green]Bond exported to {output}[/bold green]")
    return output
```

- [ ] **Step 4: Implement import**

```python
# src/claude_bond/commands/import_cmd.py
from __future__ import annotations

import zipfile
from pathlib import Path

from rich.console import Console

from claude_bond.models.bond import BOND_DIR

console = Console()


def run_import(
    file: Path,
    bond_dir: Path = BOND_DIR,
    auto_apply: bool = True,
) -> None:
    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise SystemExit(1)

    bond_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(file, "r") as zf:
        zf.extractall(bond_dir)

    console.print(f"[bold green]Bond imported to {bond_dir}[/bold green]")

    if auto_apply:
        from claude_bond.commands.apply_cmd import run_apply
        run_apply(bond_dir=bond_dir)
```

- [ ] **Step 5: Wire into CLI**

Update `src/claude_bond/cli.py` — replace the `export` and `import_bond` functions:

```python
@app.command()
def export(
    output: str = typer.Option("my.bond", "--output", "-o", help="Output .bond file path"),
) -> None:
    """Export your bond as a portable .bond file."""
    from claude_bond.commands.export_cmd import run_export
    run_export(output=Path(output))


@app.command(name="import")
def import_bond(
    file: str = typer.Argument(help="Path to .bond file"),
) -> None:
    """Import a .bond file and apply it."""
    from claude_bond.commands.import_cmd import run_import
    run_import(file=Path(file))
```

Add `from pathlib import Path` to the top of cli.py.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_export_import.py -v`
Expected: All 3 tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/claude_bond/commands/export_cmd.py src/claude_bond/commands/import_cmd.py src/claude_bond/cli.py tests/test_export_import.py
git commit -m "feat: bond export/import with .bond ZIP format"
```

---

### Task 10: Git Sync

**Files:**
- Create: `src/claude_bond/sync_engine/__init__.py`
- Create: `src/claude_bond/sync_engine/git_sync.py`
- Create: `src/claude_bond/commands/sync_cmd.py`
- Create: `tests/test_git_sync.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_git_sync.py
import subprocess
import tempfile
from pathlib import Path

from claude_bond.sync_engine.git_sync import git_init, git_commit_all, is_git_repo


def test_git_init_creates_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        git_init(path)
        assert (path / ".git").is_dir()


def test_is_git_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        assert not is_git_repo(path)
        git_init(path)
        assert is_git_repo(path)


def test_git_commit_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        git_init(path)
        (path / "test.md").write_text("hello", encoding="utf-8")
        git_commit_all(path, "test commit")
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=path,
            capture_output=True,
            text=True,
        )
        assert "test commit" in result.stdout
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_git_sync.py -v`
Expected: FAIL

- [ ] **Step 3: Implement git sync**

```python
# src/claude_bond/sync_engine/__init__.py
```

```python
# src/claude_bond/sync_engine/git_sync.py
from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

from rich.console import Console

console = Console()


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def is_git_repo(path: Path) -> bool:
    result = _run_git(["rev-parse", "--is-inside-work-tree"], cwd=path)
    return result.returncode == 0


def git_init(path: Path) -> None:
    _run_git(["init"], cwd=path)
    _run_git(["config", "user.email", "bond@claude-bond.local"], cwd=path)
    _run_git(["config", "user.name", "claude-bond"], cwd=path)

    gitignore = path / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(".snapshot/\n*.bond\n__pycache__/\n", encoding="utf-8")
        _run_git(["add", ".gitignore"], cwd=path)
        _run_git(["commit", "-m", "chore: initial gitignore"], cwd=path)


def git_commit_all(path: Path, message: str | None = None) -> bool:
    _run_git(["add", "-A"], cwd=path)
    status = _run_git(["status", "--porcelain"], cwd=path)
    if not status.stdout.strip():
        return False
    if message is None:
        message = f"bond update {date.today().isoformat()}"
    _run_git(["commit", "-m", message], cwd=path)
    return True


def git_pull(path: Path) -> bool:
    result = _run_git(["pull", "--rebase"], cwd=path)
    return result.returncode == 0


def git_push(path: Path) -> bool:
    result = _run_git(["push"], cwd=path)
    return result.returncode == 0


def git_add_remote(path: Path, url: str) -> None:
    _run_git(["remote", "add", "origin", url], cwd=path)
    _run_git(["push", "-u", "origin", "main"], cwd=path)
```

```python
# src/claude_bond/commands/sync_cmd.py
from __future__ import annotations

from pathlib import Path

from rich.console import Console

from claude_bond.models.bond import BOND_DIR
from claude_bond.sync_engine.git_sync import (
    is_git_repo,
    git_init,
    git_commit_all,
    git_pull,
    git_push,
    git_add_remote,
)

console = Console()


def run_sync(bond_dir: Path = BOND_DIR, init_remote: str | None = None) -> None:
    if not (bond_dir / "bond.yaml").exists():
        console.print("[red]No bond found. Run 'bond init' first.[/red]")
        raise SystemExit(1)

    if not is_git_repo(bond_dir):
        git_init(bond_dir)
        console.print("[dim]Initialized git repo in bond directory.[/dim]")

    if init_remote:
        git_add_remote(bond_dir, init_remote)
        console.print(f"[dim]Added remote: {init_remote}[/dim]")
        console.print("[yellow]Please ensure this is a PRIVATE repository.[/yellow]")

    committed = git_commit_all(bond_dir)
    if committed:
        console.print("[dim]Committed local changes.[/dim]")

    has_remote = _has_remote(bond_dir)
    if has_remote:
        console.print("[dim]Pulling...[/dim]")
        git_pull(bond_dir)
        console.print("[dim]Pushing...[/dim]")
        git_push(bond_dir)
        console.print("[bold green]Bond synced.[/bold green]")
    else:
        console.print("[yellow]No remote configured. Use 'bond sync --init <url>' to set one.[/yellow]")


def _has_remote(bond_dir: Path) -> bool:
    import subprocess
    result = subprocess.run(
        ["git", "remote"],
        cwd=bond_dir,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())
```

- [ ] **Step 4: Wire into CLI**

Update `src/claude_bond/cli.py` — replace the `sync` function:

```python
@app.command()
def sync(
    init_remote: str = typer.Option(None, "--init", help="Initialize with git remote URL"),
) -> None:
    """Sync your bond via git."""
    from claude_bond.commands.sync_cmd import run_sync
    run_sync(init_remote=init_remote)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_git_sync.py -v`
Expected: All 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/claude_bond/sync_engine/ src/claude_bond/commands/sync_cmd.py src/claude_bond/cli.py tests/test_git_sync.py
git commit -m "feat: git-based bond sync"
```

---

### Task 11: Evolve Detector

**Files:**
- Create: `src/claude_bond/evolve/__init__.py`
- Create: `src/claude_bond/evolve/detector.py`
- Create: `tests/test_detector.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_detector.py
import tempfile
from pathlib import Path
from unittest.mock import patch

from claude_bond.evolve.detector import detect_changes, save_pending


def test_detect_no_changes_when_identical():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        snapshot_dir = bond_dir / ".snapshot"
        snapshot_dir.mkdir()
        (snapshot_dir / "CLAUDE.md").write_text("# Rules\n- No emoji", encoding="utf-8")

        claude_dir = Path(tmpdir) / "claude"
        claude_dir.mkdir()
        (claude_dir / "CLAUDE.md").write_text("# Rules\n- No emoji", encoding="utf-8")

        changes = detect_changes(bond_dir=bond_dir, claude_dir=claude_dir)
        assert changes is None


def test_detect_finds_changes():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir) / "bond"
        bond_dir.mkdir()
        snapshot_dir = bond_dir / ".snapshot"
        snapshot_dir.mkdir()
        (snapshot_dir / "CLAUDE.md").write_text("# Rules\n- No emoji", encoding="utf-8")

        claude_dir = Path(tmpdir) / "claude"
        claude_dir.mkdir()
        (claude_dir / "CLAUDE.md").write_text("# Rules\n- No emoji\n- Be concise", encoding="utf-8")

        mock_analysis = "## New\n\n- [rules] User added: Be concise"
        with patch("claude_bond.evolve.detector.analyze_changes", return_value=mock_analysis):
            changes = detect_changes(bond_dir=bond_dir, claude_dir=claude_dir)
            assert changes is not None
            assert "concise" in changes


def test_save_pending_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        (bond_dir / "pending").mkdir()

        save_pending(bond_dir, "## New\n\n- [rules] Be concise")

        pending_files = list((bond_dir / "pending").glob("*.md"))
        assert len(pending_files) == 1
        content = pending_files[0].read_text(encoding="utf-8")
        assert "concise" in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_detector.py -v`
Expected: FAIL

- [ ] **Step 3: Implement detector**

```python
# src/claude_bond/evolve/__init__.py
```

```python
# src/claude_bond/evolve/detector.py
from __future__ import annotations

from datetime import date
from pathlib import Path

from claude_bond.models.bond import BOND_DIR
from claude_bond.utils.claude_api import analyze_changes


def detect_changes(
    bond_dir: Path = BOND_DIR,
    claude_dir: Path | None = None,
) -> str | None:
    if claude_dir is None:
        claude_dir = Path.home() / ".claude"

    snapshot_dir = bond_dir / ".snapshot"
    if not snapshot_dir.exists():
        return None

    old_parts: list[str] = []
    new_parts: list[str] = []

    # Compare CLAUDE.md
    old_claude = snapshot_dir / "CLAUDE.md"
    new_claude = claude_dir / "CLAUDE.md"
    if old_claude.exists():
        old_parts.append(old_claude.read_text(encoding="utf-8"))
    if new_claude.exists():
        new_parts.append(new_claude.read_text(encoding="utf-8"))

    # Compare memory files
    old_mem = snapshot_dir / "memory"
    new_mem = claude_dir / "memory"
    if old_mem.is_dir():
        for f in sorted(old_mem.glob("*.md")):
            old_parts.append(f"[{f.name}]\n{f.read_text(encoding='utf-8')}")
    if new_mem.is_dir():
        for f in sorted(new_mem.glob("*.md")):
            new_parts.append(f"[{f.name}]\n{f.read_text(encoding='utf-8')}")

    old_text = "\n---\n".join(old_parts)
    new_text = "\n---\n".join(new_parts)

    if old_text.strip() == new_text.strip():
        return None

    result = analyze_changes(old_text, new_text)
    if result.strip() == "NO_CHANGES":
        return None
    return result


def save_pending(bond_dir: Path, changes: str) -> Path:
    pending_dir = bond_dir / "pending"
    pending_dir.mkdir(exist_ok=True)

    today = date.today().isoformat()
    path = pending_dir / f"{today}.md"

    header = f"---\ndate: {today}\n---\n\n"

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        content = existing + "\n" + changes
    else:
        content = header + changes

    path.write_text(content, encoding="utf-8")
    return path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_detector.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/claude_bond/evolve/ tests/test_detector.py
git commit -m "feat: evolve detector for session change tracking"
```

---

### Task 12: Review & Auto-Merge

**Files:**
- Create: `src/claude_bond/evolve/merger.py`
- Create: `src/claude_bond/commands/review_cmd.py`
- Create: `src/claude_bond/commands/auto_cmd.py`
- Create: `tests/test_merger.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_merger.py
import tempfile
from pathlib import Path

from claude_bond.models.bond import BondDimension, BondMeta, save_dimension, save_meta
from claude_bond.evolve.merger import parse_pending, merge_items


def test_parse_pending():
    content = """---
date: 2026-03-29
---

## New

- [rules] User said "don't write tests for me"
- [memory] deer-flow deployed

## Updated

- [identity] User switched to backend (was: data scientist)

## Possible (low confidence)

- [style] User prefers shorter replies
"""
    items = parse_pending(content)
    assert len(items) == 4
    assert items[0].dimension == "rules"
    assert items[0].action == "new"
    assert items[1].dimension == "memory"
    assert items[2].dimension == "identity"
    assert items[2].action == "updated"
    assert items[3].confidence == "low"


def test_merge_items_adds_to_dimension():
    with tempfile.TemporaryDirectory() as tmpdir:
        bond_dir = Path(tmpdir)
        save_dimension(
            BondDimension("rules", "2026-03-29", ["scan"], "- No emoji"),
            bond_dir,
        )
        save_meta(BondMeta("0.1.0", "2026-03-29", "2026-03-29"), bond_dir)

        items = parse_pending(
            "---\ndate: 2026-03-29\n---\n\n## New\n\n- [rules] Don't write tests for me\n"
        )
        merge_items(items, bond_dir)

        from claude_bond.models.bond import load_dimension
        rules = load_dimension("rules", bond_dir)
        assert "No emoji" in rules.content
        assert "Don't write tests" in rules.content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_merger.py -v`
Expected: FAIL

- [ ] **Step 3: Implement merger**

```python
# src/claude_bond/evolve/merger.py
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from claude_bond.models.bond import (
    BondDimension,
    load_dimension,
    load_meta,
    save_dimension,
)


@dataclass(frozen=True)
class PendingItem:
    dimension: str
    description: str
    action: str  # "new", "updated", "possible"
    confidence: str  # "high", "low"


_ITEM_RE = re.compile(r"^- \[(\w+)\]\s+(.+)$")


def parse_pending(content: str) -> list[PendingItem]:
    items: list[PendingItem] = []
    current_action = "new"
    current_confidence = "high"

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## New"):
            current_action = "new"
            current_confidence = "high"
        elif stripped.startswith("## Updated"):
            current_action = "updated"
            current_confidence = "high"
        elif stripped.startswith("## Possible"):
            current_action = "possible"
            current_confidence = "low"

        match = _ITEM_RE.match(stripped)
        if match:
            items.append(
                PendingItem(
                    dimension=match.group(1),
                    description=match.group(2),
                    action=current_action,
                    confidence=current_confidence,
                )
            )
    return items


def merge_items(items: list[PendingItem], bond_dir: Path) -> None:
    meta = load_meta(bond_dir)
    today = date.today().isoformat()

    by_dim: dict[str, list[PendingItem]] = {}
    for item in items:
        by_dim.setdefault(item.dimension, []).append(item)

    for dim_name, dim_items in by_dim.items():
        if dim_name not in meta.dimensions:
            continue
        try:
            dim = load_dimension(dim_name, bond_dir)
        except (FileNotFoundError, ValueError):
            dim = BondDimension(dim_name, today, ["evolve"], "")

        new_lines: list[str] = []
        for item in dim_items:
            new_lines.append(f"- {item.description}")

        updated_content = dim.content.rstrip()
        if updated_content:
            updated_content += "\n" + "\n".join(new_lines)
        else:
            updated_content = "\n".join(new_lines)

        updated_dim = BondDimension(
            name=dim_name,
            updated=today,
            source=list(set(dim.source + ["evolve"])),
            content=updated_content,
        )
        save_dimension(updated_dim, bond_dir)
```

- [ ] **Step 4: Implement review and auto commands**

```python
# src/claude_bond/commands/review_cmd.py
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from claude_bond.models.bond import BOND_DIR
from claude_bond.evolve.merger import parse_pending, merge_items, PendingItem

console = Console()


def run_review(bond_dir: Path = BOND_DIR) -> None:
    pending_dir = bond_dir / "pending"
    if not pending_dir.is_dir():
        console.print("[dim]No pending changes.[/dim]")
        return

    pending_files = sorted(pending_dir.glob("*.md"))
    if not pending_files:
        console.print("[dim]No pending changes.[/dim]")
        return

    accepted: list[PendingItem] = []

    for pf in pending_files:
        content = pf.read_text(encoding="utf-8")
        items = parse_pending(content)
        if not items:
            continue

        console.print(f"\n[bold]Changes from {pf.stem}:[/bold]")
        for item in items:
            confidence_tag = " [dim](low confidence)[/dim]" if item.confidence == "low" else ""
            console.print(f"  [{item.action}] [bold]{item.dimension}[/bold]: {item.description}{confidence_tag}")
            choice = typer.prompt("  Accept? (y/n)", default="y")
            if choice.lower() in ("y", "yes"):
                accepted.append(item)

        pf.unlink()

    if accepted:
        merge_items(accepted, bond_dir)
        console.print(f"\n[bold green]Merged {len(accepted)} changes into bond.[/bold green]")
    else:
        console.print("\n[dim]No changes accepted.[/dim]")
```

```python
# src/claude_bond/commands/auto_cmd.py
from __future__ import annotations

from pathlib import Path

from rich.console import Console

from claude_bond.models.bond import BOND_DIR
from claude_bond.evolve.merger import parse_pending, merge_items

console = Console()


def run_auto(bond_dir: Path = BOND_DIR, enable: bool = True) -> None:
    config_path = bond_dir / "bond.yaml"
    if not config_path.exists():
        console.print("[red]No bond found. Run 'bond init' first.[/red]")
        raise SystemExit(1)

    if enable:
        _auto_merge_pending(bond_dir)
    else:
        console.print("[dim]Auto-merge disabled. Use 'bond review' to review manually.[/dim]")


def _auto_merge_pending(bond_dir: Path) -> None:
    pending_dir = bond_dir / "pending"
    if not pending_dir.is_dir():
        console.print("[dim]No pending changes.[/dim]")
        return

    all_items = []
    for pf in sorted(pending_dir.glob("*.md")):
        items = parse_pending(pf.read_text(encoding="utf-8"))
        high_confidence = [i for i in items if i.confidence == "high"]
        all_items.extend(high_confidence)
        pf.unlink()

    if all_items:
        merge_items(all_items, bond_dir)
        console.print(f"[bold green]Auto-merged {len(all_items)} high-confidence changes.[/bold green]")
    else:
        console.print("[dim]No high-confidence changes to merge.[/dim]")
```

- [ ] **Step 5: Wire into CLI**

Update `src/claude_bond/cli.py` — replace `review` and `auto` functions:

```python
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
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_merger.py -v`
Expected: All 2 tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/claude_bond/evolve/merger.py src/claude_bond/commands/review_cmd.py src/claude_bond/commands/auto_cmd.py src/claude_bond/cli.py tests/test_merger.py
git commit -m "feat: review and auto-merge for pending bond changes"
```

---

### Task 13: Claude Code Hooks

**Files:**
- Create: `hooks/session-start.sh`
- Create: `hooks/session-end.sh`
- Create: `src/claude_bond/commands/hooks_cmd.py`

- [ ] **Step 1: Create session-start hook**

```bash
#!/usr/bin/env bash
# hooks/session-start.sh
# Auto-apply bond at session start
if command -v bond &> /dev/null && [ -f "$HOME/.claude-bond/bond.yaml" ]; then
    bond apply 2>/dev/null
fi
```

- [ ] **Step 2: Create session-end hook**

```bash
#!/usr/bin/env bash
# hooks/session-end.sh
# Detect bond evolution at session end
if command -v bond &> /dev/null && [ -f "$HOME/.claude-bond/bond.yaml" ]; then
    python -m claude_bond.evolve.run_detect 2>/dev/null
fi
```

- [ ] **Step 3: Create the evolve runner script**

```python
# src/claude_bond/evolve/run_detect.py
"""Standalone script for session-end hook to detect changes."""
from __future__ import annotations

from claude_bond.evolve.detector import detect_changes, save_pending
from claude_bond.models.bond import BOND_DIR


def main() -> None:
    if not (BOND_DIR / "bond.yaml").exists():
        return
    if not (BOND_DIR / ".snapshot").exists():
        return

    changes = detect_changes()
    if changes:
        save_pending(BOND_DIR, changes)

        # Auto-merge if enabled
        auto_config = BOND_DIR / ".auto"
        if auto_config.exists():
            from claude_bond.commands.auto_cmd import _auto_merge_pending
            _auto_merge_pending(BOND_DIR)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Make hooks executable**

```bash
chmod +x hooks/session-start.sh hooks/session-end.sh
```

- [ ] **Step 5: Commit**

```bash
git add hooks/ src/claude_bond/evolve/run_detect.py
git commit -m "feat: Claude Code session hooks for auto-apply and evolve"
```

---

### Task 14: Full Integration Test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_integration.py
"""End-to-end test: init → apply → export → import on a fresh machine."""
import tempfile
from pathlib import Path
from unittest.mock import patch

from claude_bond.commands.init_cmd import run_init
from claude_bond.commands.apply_cmd import run_apply
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
```

- [ ] **Step 2: Run integration test**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/test_integration.py -v`
Expected: PASS

- [ ] **Step 3: Run full test suite**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: full integration test for init → apply → export → import flow"
```

---

### Task 15: README and Final Polish

**Files:**
- Create: `README.md`
- Create: `LICENSE`

- [ ] **Step 1: Write README**

```markdown
# claude-bond

> Package your relationship with Claude. Make Claude recognize you on any device.

claude-bond captures the unique relationship between you and Claude — your identity, behavioral rules, communication style, and shared memories — into portable Markdown files that travel with you.

## Install

```bash
pip install claude-bond
```

## Quick Start

```bash
# 1. Initialize: scan your ~/.claude/ and answer a few questions
bond init

# 2. Apply to current machine
bond apply

# 3. Sync across devices (via git)
bond sync --init git@github.com:you/my-bond.git
bond sync

# 4. Export to share with someone
bond export -o my.bond

# 5. Import on a new machine
bond import my.bond
```

## How It Works

1. **`bond init`** scans your `~/.claude/` directory (CLAUDE.md, memory files, settings) and asks Claude to classify the data into 4 dimensions: identity, rules, style, and memory. If anything is missing, it asks you a few questions to fill the gaps.

2. **`bond apply`** takes your bond files and writes them into `~/.claude/CLAUDE.md` (as a managed section) and `~/.claude/memory/` so Claude Code picks them up automatically.

3. **Evolution**: A session-end hook detects changes in your `~/.claude/` after each Claude Code session and proposes updates to your bond. Use `bond review` to approve or `bond auto` to auto-merge.

## Bond Files

```
~/.claude-bond/
  ├── identity.md    # Who you are
  ├── rules.md       # What Claude should/shouldn't do
  ├── style.md       # How Claude should communicate
  ├── memory.md      # What Claude should remember
  ├── bond.yaml      # Metadata
  └── pending/       # Detected changes awaiting review
```

All files are human-readable Markdown. Edit them directly if you want.

## License

MIT
```

- [ ] **Step 2: Create LICENSE file**

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: Create .gitignore for the project repo**

```
# /Users/wh/coding/claude-bond/.gitignore
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.venv/
.pytest_cache/
*.bond
```

- [ ] **Step 4: Commit**

```bash
git add README.md LICENSE .gitignore
git commit -m "docs: README, LICENSE, and project gitignore"
```

- [ ] **Step 5: Final verification**

Run: `cd /Users/wh/coding/claude-bond && python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

Run: `bond --help`
Expected: All 7 commands listed with descriptions
