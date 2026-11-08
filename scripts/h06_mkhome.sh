#!/usr/bin/env bash
# Make an ephemeral, minimal HOME for a single sandboxed generation: only the OAuth credential is copied in, so the
# run authenticates but inherits NO project history, memory, CLAUDE.md, or settings (fresh session). Prints the path.
set -euo pipefail
dst="$(mktemp -d "${TMPDIR:-/tmp}/h06-home.XXXXXX")"
mkdir -p "$dst/.claude"
cp "$HOME/.claude/.credentials.json" "$dst/.claude/.credentials.json"
chmod 700 "$dst/.claude"; chmod 600 "$dst/.claude/.credentials.json"
echo "$dst"
