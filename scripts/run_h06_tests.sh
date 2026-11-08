#!/usr/bin/env bash
# Deterministic h06 validation runner. Gates on PARSED GUT output + crash/error detection, NOT the exit code alone.
# Optionally swaps candidate scripts into under_test/ (for the A/A'/B matrix); defaults to whatever is there (reference).
# Usage: GODOT_BIN=/path/godot [CAND_PLAYER=..] [CAND_COIN=..] [OUT=run-dir] scripts/run_h06_tests.sh
set -uo pipefail
: "${GODOT_BIN:?set GODOT_BIN to the pinned Godot 4.7.2 binary}"
FIX="$(cd "$(dirname "$0")/../fixtures/h06" && pwd)"
OUT="${OUT:-}"
XML="$FIX/test_report.xml"
LOG="$(mktemp)"

[ -n "${CAND_PLAYER:-}" ] && cp -f "$CAND_PLAYER" "$FIX/under_test/player.gd"
[ -n "${CAND_COIN:-}" ]   && cp -f "$CAND_COIN"   "$FIX/under_test/coin.gd"

rm -f "$XML"                                   # avoid parsing a stale report after a crash
"$GODOT_BIN" --headless --path "$FIX" --import >/dev/null 2>&1
"$GODOT_BIN" --headless --path "$FIX" -s addons/gut/gut_cmdln.gd \
    -gdir=res://test -gjunit_xml_file=res://test_report.xml -gexit >"$LOG" 2>&1
rc=$?

# --- crash / script-error detection (exit code is unreliable in headless Godot 4) ---
crash=0;  grep -qiE 'handle_crash|signal 11|Program crashed' "$LOG" && crash=1
scripterr=$(grep -ciE 'SCRIPT ERROR|Parse Error' "$LOG")

# --- parse JUnit XML (missing => crash before write) ---
if [ -f "$XML" ]; then
  tests=$(grep -oE '<testsuites[^>]*>' "$XML" | grep -oE 'tests="[0-9]+"'    | grep -oE '[0-9]+' | head -1)
  fails=$(grep -oE '<testsuites[^>]*>' "$XML" | grep -oE 'failures="[0-9]+"' | grep -oE '[0-9]+' | head -1)
  skipped=$(grep -oE 'skipped="[0-9]+"' "$XML" | grep -oE '[0-9]+' | awk '{s+=$1} END{print s+0}')
else
  tests=0; fails="?"; skipped="?"
fi

verdict="FAIL"
if [ "$crash" = 0 ] && [ "$scripterr" = 0 ] && [ -f "$XML" ] && [ "${tests:-0}" -gt 0 ] && [ "${fails:-1}" = 0 ]; then
  verdict="PASS"
fi

echo "h06 validation: verdict=$verdict tests=${tests:-?} failures=${fails:-?} skipped=${skipped:-?} crash=$crash script_errors=$scripterr godot_rc=$rc"
if [ -n "$OUT" ]; then
  mkdir -p "$OUT/validation"
  cp -f "$XML" "$OUT/validation/gut_report.xml" 2>/dev/null
  { echo "verdict: $verdict"; echo "tests: ${tests:-?}"; echo "failures: ${fails:-?}"; echo "skipped: ${skipped:-?}";
    echo "crash: $crash"; echo "script_errors: $scripterr"; echo "godot_rc: $rc"; } > "$OUT/validation/h06.txt"
  tail -40 "$LOG" > "$OUT/validation/gut_stdout.txt"
fi
rm -f "$LOG"
[ "$verdict" = PASS ] && exit 0 || exit 1
