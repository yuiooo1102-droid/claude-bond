#!/usr/bin/env bash
# Auto-apply bond at session start
if command -v bond &> /dev/null && [ -f "$HOME/.claude-bond/bond.yaml" ]; then
    bond apply 2>/dev/null
fi
