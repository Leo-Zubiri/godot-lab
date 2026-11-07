---
id: h02-signal-oneshot-connect
category: api-correctness
difficulty: intermediate
expected_to_help: yes
executable_validation: parse
godot_version: "4.7.2-stable"
provenance: authored
contributes_to_notes: []
created: 2026-11-06
---

## Prompt
In Godot 4.7.2 (GDScript), declare a custom signal `died` on an `Enemy` node and connect it from another node so the
handler runs **only once** even if `died` were emitted multiple times. Show both the connect call and how you would
instead `await` the signal a single time. Explain the difference. Provide a parseable script.

## Acceptance criteria (implementation-agnostic)
- Valid Godot 4.7.x GDScript; parses cleanly.
- Declares a signal with `signal` and emits with `.emit()` (4.x), connects with a **Callable**.
- Achieves single-invocation via the correct one-shot mechanism (the `CONNECT_ONE_SHOT` connect flag) and separately
  shows `await enemy.died` as the one-time alternative.
- Correctly explains that `await` suspends the current function for one emission, whereas a one-shot connection
  auto-disconnects a persistent handler after the first emission.
- No Godot 3 signal idioms (e.g. string-based `connect("died", self, "_on_died")` as the only form).

## Automated validation
- **parse:** `--check-only` must succeed. (Parsing does not confirm the one-shot semantics — verify those against the
  rubric / the cited Godot docs.)
