#!/usr/bin/env bash
# Detect bond evolution at session end
if command -v bond &> /dev/null && [ -f "$HOME/.claude-bond/bond.yaml" ]; then
    python3 -m claude_bond.evolve.run_detect 2>/dev/null
fi
