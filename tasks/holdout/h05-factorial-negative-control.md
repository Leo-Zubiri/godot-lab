---
id: h05-factorial-negative-control
category: codegen
difficulty: easy
expected_to_help: no
executable_validation: parse+test
godot_version: "4.7.2-stable"
provenance: authored
contributes_to_notes: []
created: 2026-11-06
---

## Prompt
In GDScript (Godot 4.7.2), write an iterative function `factorial(n: int) -> int` that returns n! for n >= 0, returning
1 for n == 0. Provide a complete, parseable script.

## Acceptance criteria (implementation-agnostic)
- Valid, parseable GDScript.
- `factorial(0) == 1`, `factorial(1) == 1`, `factorial(5) == 120`.
- Iterative (not the point to enforce recursion vs iteration beyond "iterative" as asked); uses basic language features
  only.

## Automated validation
- **parse:** `--check-only` must succeed.
- **test (GUT):** assert the three values above.

## Why this is a NEGATIVE CONTROL
This is answerable from the base model's general programming + GDScript syntax knowledge; the `godot-knowledge` base has
**no** factorial/looping note and should add nothing. `expected_to_help: no`. If Condition B shows a large advantage
here, that is a **red flag** for a confound (e.g. prompt/instruction effect rather than content) — exactly what A′ helps
diagnose. Report it rather than hide it.
