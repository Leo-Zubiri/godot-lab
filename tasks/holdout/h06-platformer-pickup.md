---
id: h06-platformer-pickup
category: codegen+architecture
difficulty: intermediate
expected_to_help: mixed
executable_validation: parse+test
godot_version: "4.7.2-stable"
provenance: authored
contributes_to_notes: []          # eval-only holdout; must not be used to build the knowledge under test
protocol: v2
created: 2026-11-08
---

## Prompt (identical across conditions A / A′ / B)
In **Godot 4.7.2 (GDScript)**, implement a minimal 2D platformer pickup. Produce **two scripts** following the output
contract (`### script` / `### explanation` / `### references`):

- **`player.gd`** — attached to a `CharacterBody2D`. Apply gravity each physics frame while airborne; move left/right
  using the input actions **`move_left`**/**`move_right`**; **jump** (upward velocity) on the **`jump`** action only when
  on the floor; use `move_and_slide()`.
- **`coin.gd`** — attached to an `Area2D`. Declare a signal **`collected`**. When a node in group **`"player"`** overlaps
  the coin, emit `collected` and remove the coin with `queue_free()` — **exactly once** (never collect twice).

Assume the scene, collision shapes, collision layers/masks, the `"player"` group, and the input actions are provided by
the project/harness. Do not add process narration to the deliverable.

## Acceptance criteria (implementation-agnostic; identical across conditions)
- Both scripts **parse** under Godot 4.7.2.
- **Gravity & landing:** an airborne player accelerates downward and comes to rest on the floor (`is_on_floor()`).
- **Horizontal movement:** holding `move_right` moves the player right at its configured speed.
- **Jump:** pressing `jump` while on the floor produces upward velocity and leaves the floor.
- **Coin detection:** a body in group `"player"` overlapping the coin triggers collection; a body the coin's
  layer/mask does **not** cover does **not**.
- **Exactly once + removal:** `collected` fires once, the counter increments once, the coin is freed, and **no repeated
  collection** occurs on subsequent physics frames.

## Validation harness (fixed; identical across conditions)
`fixtures/h06/` (Godot 4.7.2 project + GUT 9.6.1) with `test/test_h06.gd`, run via `scripts/run_h06_tests.sh`
(deterministic physics-frame stepping; **gates on the parsed GUT report + crash/error detection, not the exit code**).
Collision config uses **bitmask values**: Ground layer idx1=value 1; Player layer idx2=value 2, mask value 1; Coin
layer idx3=**value 4**, mask value **2** (scans the player layer). The harness places the candidate's `player.gd`/`coin.gd`
into `under_test/` and runs the same 6 tests for every condition.

## Component vs integration
- **Component:** gravity-in-air, lands-on-floor, horizontal, jump, coin layer/mask (incl. the negative control).
- **Integration:** coin collected exactly once (full scene, stepped physics).
