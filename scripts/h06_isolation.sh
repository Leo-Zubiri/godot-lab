#!/usr/bin/env bash
# h06 per-condition knowledge isolation: SET UP + VERIFY. Never uses sudo; documents the root requirement for a hard
# guarantee and STOPS for intervention rather than silently weakening isolation.
#
#   A        -> NO knowledge dir attached, NO retrieval instruction, neutral cwd (knowledge absent from the run's set).
#   A_prime  -> a FRESH, genuinely EMPTY knowledge dir (verified: no files, incl. hidden/notes/index/metadata).
#   B        -> ONLY the read-only checkout at the pinned SHA (chmod a-w), attached via --add-dir to B alone.
#
# The B path / condition label are NEVER passed to A or A'.
set -uo pipefail
RO="${GODOT_KNOWLEDGE_RO:-/home/zub/Documents/GODOT/godot-knowledge-ro-h06}"
EMPTY="${APRIME_EMPTY:-$HOME/.cache/h06-empty-knowledge}"
PIN="91250e6b2bd9e3966e7b22be94dea9bc2c263fae"
fail=0

echo "=== A' empty dir: (re)create fresh and verify genuinely empty ==="
rm -rf "$EMPTY"; mkdir -p "$EMPTY"
n=$(find "$EMPTY" -mindepth 1 2>/dev/null | wc -l)
if [ "$n" -eq 0 ]; then echo "OK  $EMPTY is empty (0 entries incl. hidden)"; else echo "FAIL $EMPTY not empty ($n)"; fail=1; fi

echo "=== B read-only checkout: verify pin + write-blocked ==="
if [ ! -d "$RO/.git" ]; then echo "FAIL $RO missing"; fail=1;
else
  head=$(git -C "$RO" rev-parse HEAD 2>/dev/null)
  [ "$head" = "$PIN" ] && echo "OK  HEAD == pin $PIN" || { echo "FAIL HEAD=$head != $PIN"; fail=1; }
  if (touch "$RO/.__wtest" 2>/dev/null); then echo "FAIL write succeeded (not read-only)"; rm -f "$RO/.__wtest"; fail=1; else echo "OK  write blocked (chmod a-w)"; fi
fi

cat <<'NOTE'

=== ISOLATION STRENGTH — READ ===
`chmod a-w` prevents accidental writes but is NOT a hard guarantee that condition A/A' cannot READ the B checkout
via an absolute path from Bash. A hard guarantee requires OS-level isolation that needs ROOT or manual setup:
  (1) a read-only bind mount visible only to B's run, or
  (2) running B inside a container / mount namespace (e.g. bwrap/unshare) that excludes the path from A/A'.
Example (ROOT required — DO NOT let the agent run this; operator runs it):
  sudo mount --bind <ro> <mnt> && sudo mount -o remount,ro,bind <mnt>
Until such isolation is provided, the practical controls are: attach the path ONLY to B (--add-dir), neutral cwd for
A/A', deny web + restrict Bash in generation, and never leak the path/label to A/A'. The matrix runner enforces the
practical controls; the HARD guarantee is an OPEN ITEM requiring operator intervention.
NOTE
[ "$fail" = 0 ] && echo "ISOLATION SETUP: OK (practical controls ready; hard-mount = open item)" || { echo "ISOLATION SETUP: PROBLEMS ABOVE"; exit 1; }
