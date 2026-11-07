# fixtures/godot/ — minimal headless Godot project(s) for executable validation

A minimal Godot **4.7.2** project used to validate generated GDScript objectively. The actual fixture is built in **P4**.

## Plan
- Minimal project = `project.godot` (`config_version=5`) + `.gd` scripts (+ optional `.tscn`). No binary assets needed to
  validate GDScript.
- **Layered validation** (see `../../AGENTS.md`):
  1. `godot --headless --script res://<file>.gd --check-only` → parse/syntax (no execution).
  2. **GUT** behavior tests (addon under `addons/gut/`), run headless via its cmdline runner; exit codes 0/1.
  3. Integration checks for scene/node/signal/Resource/runtime tasks.
- **Gate on parsed output**, not the exit code alone (Godot 4 headless can exit 0 on failure; unknown flags are ignored
  silently).
- **git hygiene:** ignore `.godot/` and `*.translation` (already in `../../.gitignore`); commit `project.godot`, scripts,
  and `.import` sidecars.
- Keep the harness **modular** so gdUnit4 could replace GUT later without restructuring.

Reference: `~/Documents/GODOT/godot-learning` is an existing minimal Godot project to copy structure from.
*Verify at build time: the exact Godot 4.7.2 binary path (`$GODOT_BIN`) and GUT's current CLI flags.*
