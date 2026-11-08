#!/usr/bin/env bash
# Deterministic h06 validation runner (STRICT). Gates on the PARSED GUT report + crash/error detection, never the exit
# code alone. Emits PASS / FAIL / INVALID with a recorded reason, and reports the harness-sanity suite SEPARATELY
# (excluded from the candidate verdict). Optionally swaps candidate scripts into under_test/ for the A/A'/B matrix.
#
# Usage: GODOT_BIN=/path/godot [CAND_PLAYER=..] [CAND_COIN=..] [OUT=run-dir] scripts/run_h06_tests.sh
# Exit: 0 only on candidate PASS; 1 on FAIL; 2 on INVALID/ERROR.
set -uo pipefail
: "${GODOT_BIN:?set GODOT_BIN to the pinned Godot 4.7.2 binary}"
FIX="$(cd "$(dirname "$0")/../fixtures/h06" && pwd)"
OUT="${OUT:-}"; XML="$FIX/test_report.xml"; LOG="$(mktemp)"

[ -n "${CAND_PLAYER:-}" ] && cp -f "$CAND_PLAYER" "$FIX/under_test/player.gd"
[ -n "${CAND_COIN:-}" ]   && cp -f "$CAND_COIN"   "$FIX/under_test/coin.gd"

rm -f "$XML"
"$GODOT_BIN" --headless --path "$FIX" --import >/dev/null 2>&1
"$GODOT_BIN" --headless --path "$FIX" -s addons/gut/gut_cmdln.gd \
    -gdir=res://test -gjunit_xml_file=res://test_report.xml -gexit >"$LOG" 2>&1
rc=$?

# --- classify engine/script errors ---
crash=0;       grep -qiE 'handle_crash|signal 11|Program crashed' "$LOG" && crash=1
harness_err=$(grep -iE 'SCRIPT ERROR|Parse Error' "$LOG" | grep -cE 'res://test/|res://addons/')
cand_err=$(grep -iE 'SCRIPT ERROR|Parse Error' "$LOG" | grep -cE 'res://under_test/')
risky=$(grep -oiE 'risky[^0-9]*[0-9]+' "$LOG" | grep -oE '[0-9]+' | awk '{s+=$1} END{print s+0}')
pending=$(grep -oiE 'pending[^0-9]*[0-9]+' "$LOG" | grep -oE '[0-9]+' | awk '{s+=$1} END{print s+0}')

_attr() { # $1=suite-file-substring -> echo "tests failures skipped" (or "NA NA NA")
	local line; line=$(grep -oE "<testsuite [^>]*name=\"[^\"]*$1\"[^>]*>" "$XML" 2>/dev/null | head -1)
	if [ -z "$line" ]; then echo "NA NA NA"; return; fi
	echo "$(echo "$line" | grep -oE 'tests="[0-9]+"' | grep -oE '[0-9]+') \
	      $(echo "$line" | grep -oE 'failures="[0-9]+"' | grep -oE '[0-9]+') \
	      $(echo "$line" | grep -oE 'skipped="[0-9]+"' | grep -oE '[0-9]+')"
}

if [ -f "$XML" ]; then read -r c_tests c_fails c_skip <<<"$(_attr test_h06.gd)"; read -r s_tests s_fails s_skip <<<"$(_attr test_harness_sanity.gd)"
else c_tests=NA; c_fails=NA; c_skip=NA; s_tests=NA; s_fails=NA; s_skip=NA; fi

# --- CANDIDATE verdict (harness_sanity excluded) ---
verdict="INVALID"; reason=""
if [ "$crash" = 1 ]; then reason="engine crash"
elif [ "$harness_err" -gt 0 ]; then reason="harness script error (test/ or addons/)"
elif [ ! -f "$XML" ]; then reason="no JUnit report (crash/early exit)"
elif [ "$c_tests" = "NA" ] || [ "${c_tests:-0}" -eq 0 ]; then reason="candidate testsuite missing or empty"
else
	if [ "${c_fails:-1}" -gt 0 ]; then verdict="FAIL"; reason="candidate test failures=$c_fails"
	elif [ "${c_skip:-0}" -gt 0 ] || [ "${risky:-0}" -gt 0 ] || [ "${pending:-0}" -gt 0 ]; then
		verdict="FAIL"; reason="skipped=$c_skip risky=$risky pending=$pending (not allowed)"
	else verdict="PASS"; reason="all candidate tests passed"; fi
fi

# --- harness sanity (reported separately) ---
san="INVALID"
if [ -f "$XML" ] && [ "$s_tests" != "NA" ] && [ "${s_tests:-0}" -gt 0 ] && [ "${s_fails:-1}" -eq 0 ] && [ "${s_skip:-1}" -eq 0 ]; then san="PASS"
elif [ "$s_tests" != "NA" ] && [ "${s_fails:-0}" -gt 0 ]; then san="FAIL"; fi

echo "CANDIDATE: verdict=$verdict reason=\"$reason\" tests=$c_tests failures=$c_fails skipped=$c_skip risky=$risky pending=$pending crash=$crash harness_err=$harness_err cand_err=$cand_err godot_rc=$rc"
echo "HARNESS_SANITY: verdict=$san tests=$s_tests failures=$s_fails skipped=$s_skip"

if [ -n "$OUT" ]; then
	mkdir -p "$OUT/validation"; cp -f "$XML" "$OUT/validation/gut_report.xml" 2>/dev/null; tail -60 "$LOG" > "$OUT/validation/gut_stdout.txt"
	{ echo "candidate_verdict: $verdict"; echo "reason: \"$reason\""; echo "tests: $c_tests"; echo "failures: $c_fails";
	  echo "skipped: $c_skip"; echo "risky: $risky"; echo "pending: $pending"; echo "crash: $crash";
	  echo "harness_err: $harness_err"; echo "cand_err: $cand_err"; echo "godot_rc: $rc";
	  echo "harness_sanity_verdict: $san"; } > "$OUT/validation/h06.yaml"
fi
rm -f "$LOG"
case "$verdict" in PASS) exit 0;; FAIL) exit 1;; *) exit 2;; esac
