# fixtures/h06 — deterministic h06 validation project (Godot 4.7.2)

Self-contained Godot project that validates generated `player.gd` + `coin.gd` for the `h06-platformer-pickup`
experiment, with GUT behavior tests run headless. Used identically for conditions A / A′ / B.

## Layout
- `project.godot` — minimal 4.7 project (input actions are added at runtime by the test, for determinism).
- `under_test/player.gd`, `under_test/coin.gd` — the scripts being validated. **Committed = the reference
  (correct) implementation**; the matrix runner swaps in a candidate's scripts here per run.
- `test/test_h06.gd` — the fixed GUT suite (6 tests: gravity/landing, horizontal, jump, coin layer/mask negative
  control, coin collected exactly-once + no-repeat + freed). Builds the scene in code; steps physics by frames
  (no wall-clock); correct collision **bitmask** values (Ground 1, Player layer 2/mask 1, Coin layer 4/mask 2).
- `addons/gut/` — **not committed** (see below).

## GUT addon (fetch once; pinned)
GUT **9.6.1** (Godot 4.x). Fetch into `addons/gut/`:
```bash
git clone --branch 9.6.1 --depth 1 https://github.com/bitwes/Gut.git /tmp/gut \
  && cp -r /tmp/gut/addons/gut fixtures/h06/addons/gut
```

## Run
```bash
GODOT_BIN=/path/to/godot-4.7.2 scripts/run_h06_tests.sh
# PASS/FAIL is decided by the PARSED GUT report + crash/error detection, not the exit code alone.
```
First run auto-imports the project (GUT needs its class_names registered). Reference implementation → `PASS tests=6
failures=0`. Validated 2026-11-08 on Godot 4.7.2.stable.mono.
