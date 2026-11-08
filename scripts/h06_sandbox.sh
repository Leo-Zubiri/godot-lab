#!/usr/bin/env bash
# Root-free per-condition filesystem isolation for h06, via bubblewrap (user+mount namespaces).
# The knowledge appears ONLY at the fixed in-sandbox path /knowledge (the host path is never exposed), so A/A'
# cannot reach the real checkout through parent dirs, symlinks, env vars, or inherited mounts.
#
#   A        -> /knowledge NOT mounted (absent)
#   A_prime  -> /knowledge = read-only bind of a verified-empty dir
#   B        -> /knowledge = read-only bind of the pinned knowledge snapshot (cannot be modified)
#
# Network is kept (claude -p needs the API at execution); filesystem is isolated via the mount namespace.
# FAIL CLOSED: if bwrap or unprivileged namespaces are unavailable, exit 99 and run NOTHING (never fall back to chmod).
#
# Usage: [GODOT_KNOWLEDGE_RO=..] [APRIME_EMPTY=..] [H06_WORK=dir] h06_sandbox.sh <A|A_prime|B> -- <cmd...>
set -uo pipefail
COND="${1:?condition A|A_prime|B}"; shift
[ "${1:-}" = "--" ] && shift
RO="${GODOT_KNOWLEDGE_RO:-/home/zub/Documents/GODOT/godot-knowledge-ro-h06}"
EMPTY="${APRIME_EMPTY:-$HOME/.cache/h06-empty-knowledge}"

command -v bwrap >/dev/null || { echo "ISOLATION FAIL: bwrap not installed" >&2; exit 99; }
# Precheck: can we create an unprivileged user+mount namespace AND exec inside it? The exec needs the
# dynamic linker, so /lib64 etc. must be present — bind /usr and recreate Fedora's /lib*,/bin symlinks.
bwrap --unshare-user --unshare-pid --ro-bind /usr /usr \
      --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/lib64 /lib64 --symlink usr/sbin /sbin \
      --proc /proc --dev /dev --tmpfs /tmp -- /usr/bin/true 2>/dev/null \
  || { echo "ISOLATION FAIL: unprivileged namespaces unavailable; refusing to run unsandboxed" >&2; exit 99; }

# Base sandbox: clean env, read-only system, private /proc /dev /tmp. Fedora /bin,/lib,* are symlinks into /usr.
ARGS=(--unshare-user --unshare-pid --unshare-ipc --unshare-uts --unshare-cgroup --die-with-parent
      --clearenv --setenv PATH /usr/bin:/bin --setenv HOME /tmp
      --ro-bind /usr /usr --ro-bind-try /etc /etc --proc /proc --dev /dev --tmpfs /tmp)
for l in bin lib lib64 sbin; do [ -L "/$l" ] && ARGS+=(--symlink "usr/$l" "/$l"); done

case "$COND" in
  A)        : ;;                                            # no /knowledge
  A_prime)  [ -d "$EMPTY" ] || { echo "ISOLATION FAIL: empty dir $EMPTY missing" >&2; exit 98; }
            ARGS+=(--ro-bind "$EMPTY" /knowledge) ;;
  B)        [ -d "$RO" ] || { echo "ISOLATION FAIL: knowledge checkout $RO missing" >&2; exit 98; }
            ARGS+=(--ro-bind "$RO" /knowledge) ;;
  *) echo "bad condition: $COND" >&2; exit 2 ;;
esac

if [ -n "${H06_WORK:-}" ]; then
  [ -d "$H06_WORK" ] || { echo "ISOLATION FAIL: work dir $H06_WORK missing" >&2; exit 98; }
  ARGS+=(--bind "$H06_WORK" "$H06_WORK" --chdir "$H06_WORK")
fi

exec bwrap "${ARGS[@]}" -- "$@"
