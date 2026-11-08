# h06 visual verification — AUXILIARY evidence

**This is auxiliary evidence of engine execution, NOT a correctness oracle.** The authoritative functional verdict is
the headless GUT suite (`evidence/godot-execution/`). A screenshot shows that Godot *loaded and ran* a candidate and what
it rendered; it does **not** prove correctness, and a passing GUT test does **not** prove the visual presentation. The
three evidence kinds are kept distinct:

1. **Engine execution** — Godot 4.7.2-mono actually loads/executes each candidate (this dir + GUT logs).
2. **Behavioral evidence** — the GUT suite asserts the mechanics (`evidence/godot-execution/`).
3. **Visual evidence** — genuine engine screenshots, here.

## How these screenshots were produced
- Harness: `scripts/h06_visual_proj/` (an **isolated auxiliary** Godot project) + `scripts/h06_visual.py`.
- For each run, the **original** `player.gd`/`coin.gd` are extracted from the preserved `output.md` and copied, **unmodified**,
  into the aux project's `under_test/`. The SHA-256 is recorded **before and after** the run (`manifest.json → unmodified`),
  proving the run never altered the submission. The experiment's own run artifacts are never touched.
- The engine runs in a real window on an **isolated Xvfb display** (`xvfb-run`), not the desktop. No system packages were
  installed and no sandbox was weakened.
- Input actions (`move_left/move_right/jump`) and collision layers mirror the GUT harness exactly
  (ground=1/mask0, player=2/mask1 + group `"player"`, coin=4/mask2). Visuals (blue rect = player, gold circle = coin,
  green bar = ground) are rendering aids added by the aux harness only; they are not part of any submission.
- Screenshots are captured from the live viewport (`get_viewport().get_texture().get_image().save_png()`).

## States captured per run
`01_initial` (player spawned, coin to the right) · `02_grounded` (resting on floor) · `03_jump` (airborne) ·
`04_approach` (moving right toward the coin) · `05_collected` (after overlap; coin removed).

## Honest caveats
- Visual success ≠ correctness. In particular, the sole GUT failure on this task is an **exact-speed assertion**
  (`velocity.x == 300`); a candidate using a different speed still **looks** like a correct platformer in these
  screenshots while **failing** GUT. Do not read "the game runs" as "the code is correct."
- `manifest.json` records, per run: run_id, condition, candidate SHA-256 (before/after), Godot version, each screenshot's
  caption, the engine state at capture, and whether it is an actual running-engine screenshot (all are).
- Directories: `A/`, `A-prime/`, `B/` each contain `<run_id>/` with the PNGs, the engine-state manifest, and Godot logs.
