# claude-bond

> Package your relationship with Claude. Make Claude recognize you on any device.

claude-bond captures the unique relationship between you and Claude -- your identity, behavioral rules, communication style, and shared memories -- into portable Markdown files that travel with you.

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

## Commands

| Command | Description |
|---------|-------------|
| `bond init` | Initialize bond by scanning ~/.claude/ |
| `bond apply` | Apply bond to current machine |
| `bond export` | Export as portable .bond file |
| `bond import <file>` | Import and apply a .bond file |
| `bond sync` | Sync via git |
| `bond review` | Review pending changes |
| `bond auto` | Auto-merge high-confidence changes |

## License

MIT
