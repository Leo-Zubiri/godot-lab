#!/usr/bin/env bash
# Filesystem-isolation tests for the h06 bwrap sandbox (A/A'/B) + adversarial escape attempts.
# No model calls. Run: scripts/test_isolation.sh
#
# Design: every assertion runs a command that prints a SENTINEL only if the sandbox actually executes,
# then asserts on that sentinel. A broken/fail-closed sandbox prints nothing and therefore FAILS the
# test (it is never silently counted as an isolation "pass"). A positive control proves the sandbox runs.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SB="$HERE/h06_sandbox.sh"
RO="${GODOT_KNOWLEDGE_RO:-/home/zub/Documents/GODOT/godot-knowledge-ro-h06}"
EMPTY="${APRIME_EMPTY:-$HOME/.cache/h06-empty-knowledge}"
NOTE="/knowledge/notes/characterbody2d-movement.md"
NOTEBASE="characterbody2d-movement.md"
P=0; F=0
ok(){ P=$((P+1)); echo "  PASS  $1"; }
no(){ F=$((F+1)); echo "  FAIL  $1  ${2:+(got: '$2')}"; }
eq(){ [ "$1" = "$2" ] && ok "$3" || no "$3" "$1"; }   # eq EXPECT GOT LABEL

rm -rf "$EMPTY"; mkdir -p "$EMPTY"                         # fresh verified-empty A' dir
WORK="$(mktemp -d)"; ln -s "$RO" "$WORK/link_to_knowledge" # adversarial symlink -> host checkout
echo "host-secret" > "$WORK/work_marker"                  # a real file so the work dir is non-empty

# run <cond> -- cmd... ; prints the command's STDOUT (stderr suppressed). Empty output == sandbox did not run it.
run(){ local c="$1"; shift; [ "${1:-}" = "--" ] && shift
  H06_WORK="$WORK" GODOT_KNOWLEDGE_RO="$RO" APRIME_EMPTY="$EMPTY" bash "$SB" "$c" -- "$@" 2>/dev/null; }

echo "== positive control: the sandbox can execute at all =="
eq RUNS "$(run A -- sh -c 'echo RUNS')" "A: sandbox executes a command"
eq RUNS "$(run B -- sh -c 'echo RUNS')" "B: sandbox executes a command"
eq RUNS "$(run A_prime -- sh -c 'echo RUNS')" "A': sandbox executes a command"
# equal tool access: a core tool present in every condition
eq YES "$(run A -- sh -c '[ -x /usr/bin/python3 ] && echo YES')" "A: python3 available (equal tool access)"
eq YES "$(run B -- sh -c '[ -x /usr/bin/python3 ] && echo YES')" "B: python3 available (equal tool access)"
eq YES "$(run A_prime -- sh -c '[ -x /usr/bin/python3 ] && echo YES')" "A': python3 available (equal tool access)"

echo "== A: knowledge absent, host unreachable =="
eq ABSENT  "$(run A -- sh -c '[ -e /knowledge ] && echo PRESENT || echo ABSENT')"              "A: /knowledge absent"
eq ABSENT  "$(run A -- sh -c "[ -e '$RO' ] && echo PRESENT || echo ABSENT")"                   "A: host checkout path absent in sandbox"
eq ABSENT  "$(run A -- sh -c '[ -e /home/zub ] && echo PRESENT || echo ABSENT')"               "A: /home/zub not inherited"

echo "== A' : only a verified-empty /knowledge =="
eq EMPTY   "$(run A_prime -- sh -c '[ -z "$(ls -A /knowledge 2>/dev/null)" ] && echo EMPTY || echo NONEMPTY')" "A': /knowledge is empty"
eq ABSENT  "$(run A_prime -- sh -c "[ -e '$NOTE' ] && echo PRESENT || echo ABSENT")"           "A': no inherited notes"
eq ABSENT  "$(run A_prime -- sh -c "[ -e '$RO' ] && echo PRESENT || echo ABSENT")"             "A': host checkout path absent"

echo "== B: read-only snapshot =="
eq READ    "$(run B -- sh -c "cat '$NOTE' >/dev/null 2>&1 && echo READ || echo NOREAD")"       "B: can READ the pinned note"
eq RO      "$(run B -- sh -c 'touch /knowledge/__wtest 2>/dev/null && echo WROTE || echo RO')" "B: cannot WRITE into /knowledge (read-only bind)"
eq RO      "$(run B -- sh -c "rm -f '$NOTE' 2>/dev/null && echo DELETED || echo RO")" "B: cannot DELETE a pinned note"
# the host checkout is untouched after write attempts
[ -f "$RO/notes/$NOTEBASE" ] && [ ! -e "$RO/__wtest" ] && ok "B: host checkout unmodified after write attempts" || no "B: host checkout changed!"

echo "== adversarial escape attempts =="
# parent-directory traversal (B): /knowledge/../<host path> must not resolve to the host checkout
eq BLOCKED "$(run B -- sh -c "cat '/knowledge/../$RO/notes/$NOTEBASE' >/dev/null 2>&1 && echo ESCAPED || echo BLOCKED")" "B: parent-dir traversal blocked"
# symlink in the (bound, writable) work dir pointing at the host checkout -> must not resolve inside A
eq BLOCKED "$(run A -- sh -c "cat '$WORK/link_to_knowledge/notes/$NOTEBASE' >/dev/null 2>&1 && echo ESCAPED || echo BLOCKED")" "A: symlink-to-host does not resolve"
eq BLOCKED "$(run A_prime -- sh -c "cat '$WORK/link_to_knowledge/notes/$NOTEBASE' >/dev/null 2>&1 && echo ESCAPED || echo BLOCKED")" "A': symlink-to-host does not resolve"
# environment leakage: no knowledge path anywhere in A's env (--clearenv)
LEAK="$(run A -- env | grep -iE 'godot-knowledge|/knowledge' || true)"
[ -z "$LEAK" ] && ok "A: env has no knowledge path (--clearenv)" || no "A: env leaks a knowledge path" "$LEAK"
# inherited mounts: /proc/mounts inside A must not reference the host checkout
MNT="$(run A -- cat /proc/mounts | grep 'godot-knowledge-ro-h06' || true)"
[ -z "$MNT" ] && ok "A: no inherited mount of the checkout" || no "A: inherited mount exposes checkout" "$MNT"
# /proc/mounts inside A' / B must not reveal the HOST path of the knowledge (only the in-sandbox /knowledge)
MNT2="$(run B -- cat /proc/mounts | grep "$RO" || true)"
[ -z "$MNT2" ] && ok "B: mount table hides host checkout path" || no "B: mount table leaks host path" "$MNT2"

rm -rf "$WORK"
echo ""; echo "ISOLATION TESTS: $P passed, $F failed"
[ "$F" -eq 0 ] || exit 1
