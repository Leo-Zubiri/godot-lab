---
id: h01-timer-oneshot
category: codegen
difficulty: easy
expected_to_help: yes
executable_validation: parse
godot_version: "4.7.2-stable"
provenance: authored
contributes_to_notes: []
created: 2026-11-06
---

## Prompt
In Godot 4.7.2 (GDScript), write a short script for a `Node` that, when it is ready, waits 1 second and then calls a
method `_on_timeout()` exactly once. Briefly explain the lifecycle (when your timer is created and when the callback
runs). Provide a complete, parseable script.

## Acceptance criteria (implementation-agnostic)
- The script is valid GDScript for Godot 4.7.x and parses with no errors.
- A one-second delay occurs after the node is ready, and the one-shot action happens **exactly once** (not every frame,
  not repeatedly).
- The explanation correctly identifies where the wait is set up (node ready) and that the callback fires once.
- Uses a 4.x-correct mechanism (e.g. `await get_tree().create_timer(1.0).timeout`, or a `Timer` with `one_shot = true`
  connected via a Callable) — **not** a Godot 3 idiom (`yield(...)`).

## Automated validation
- **parse:** `godot --headless --script res://h01.gd --check-only` must succeed (syntax/parse only — does NOT prove the
  timing behaves at runtime).
- A green parse proves the code compiles, **not** that the lifecycle explanation is correct — score those on the rubric.
