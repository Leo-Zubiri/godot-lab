#!/usr/bin/env bash
# Layered GDScript validation for a single generated script, for the godot-lab pipeline.
# Thin wrapper only (no infrastructure). Gates on PARSED output, not exit code alone
# (Godot 4 headless can exit 0 on failure; unknown flags are ignored silently).
#
# Usage:  GODOT_BIN=/path/to/godot-4.7.2 scripts/validate_gdscript.sh <script.gd> [run-out-dir]
# Writes a small result file (parse status) to <run-out-dir>/validation/ if provided.
set -uo pipefail

SCRIPT="${1:?usage: validate_gdscript.sh <script.gd> [out-dir]}"
OUT="${2:-}"
FIXTURE="$(cd "$(dirname "$0")/../fixtures/godot" && pwd)"
: "${GODOT_BIN:?set GODOT_BIN to the pinned Godot 4.7.2 binary (see .env.example)}"

[ -x "$GODOT_BIN" ] || { echo "ERROR: GODOT_BIN not executable: $GODOT_BIN" >&2; exit 2; }
[ -f "$SCRIPT" ]    || { echo "ERROR: script not found: $SCRIPT" >&2; exit 2; }

# Place the script inside the fixture project so res:// resolves, then parse-check it.
cp -f "$SCRIPT" "$FIXTURE/scripts/_under_test.gd"
LOG="$("$GODOT_BIN" --headless --path "$FIXTURE" --script res://scripts/_under_test.gd --check-only 2>&1)"
RC=$?

# Parse-gate: treat as PASS only if there is no error marker AND rc==0.
if echo "$LOG" | grep -qiE 'error|parse error|SCRIPT ERROR'; then PARSE="fail"; else [ "$RC" -eq 0 ] && PARSE="pass" || PARSE="fail"; fi

echo "parse=$PARSE rc=$RC"
echo "$LOG"

if [ -n "$OUT" ]; then
  mkdir -p "$OUT/validation"
  { echo "parse: $PARSE"; echo "exit_code: $RC"; echo "godot_bin: $GODOT_BIN"; echo "--- log ---"; echo "$LOG"; } \
    > "$OUT/validation/parse.txt"
fi

rm -f "$FIXTURE/scripts/_under_test.gd"
[ "$PARSE" = "pass" ] && exit 0 || exit 1
