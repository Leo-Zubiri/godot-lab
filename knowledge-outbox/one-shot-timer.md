---
id: one-shot-timer
status: staged
discovered_in: exp-h01-pilot
general_or_specific: general
reusable_why: "Any Godot project needs a short one-off delay; SceneTree.create_timer + await/one-shot connect is the idiomatic 4.x way and is not yet in godot-knowledge."
source_lead: https://docs.godotengine.org/en/4.7/classes/class_scenetree.html  (create_timer -> SceneTreeTimer.timeout); also class_timer.html (Timer node one_shot)
godot_version: "4.7.2-stable"
created: 2026-11-06
---

## Finding
A common one-off delay in Godot 4.7 is done without a Timer node: `await get_tree().create_timer(1.0).timeout`
(suspends the current function ~1s), or connect `get_tree().create_timer(1.0).timeout.connect(cb, CONNECT_ONE_SHOT)`.
For a reusable node-based timer, a `Timer` with `one_shot = true` emits `timeout` once. During exp-h01-pilot the B agent
noted the knowledge base does **not** cover `create_timer`, so it fell back to its own knowledge — a genuine gap.

## Evidence lead (to preserve/verify during ingestion — NOT yet verified)
- `SceneTree.create_timer(time_sec)` returns a `SceneTreeTimer` whose `timeout` signal fires once after the delay:
  https://docs.godotengine.org/en/4.7/classes/class_scenetree.html and class_scenetreetimer.html
- `Timer` node `one_shot`: https://docs.godotengine.org/en/4.7/classes/class_timer.html

## Routing note
General, engine-level, source-backed → belongs in **godot-knowledge** (not experiment/project-specific). Relates to the
existing `node-lifecycle-callbacks` and `gdscript-signals` notes. **Leakage firewall:** discovered via task `h01`, so a
resulting note must NOT be benchmarked on h01 — use other holdout tasks.
