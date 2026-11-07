---
id: exp-h01-pilot
status: concluded
created: 2026-11-06
batch_config: ../../conditions/batch-config.md
conditions: [A, A_prime, B]
tasks:
  - h01-timer-oneshot
rubric: ../../rubrics/godot-eval-v0_1.md
rubric_version: "0.1.0"
trials_per_condition: 3
gen_model_id: claude-haiku-5-5
eval_model_id: claude-sonnet-5-5
knowledge_commit_sha: 50cc03ab79ad448586f6dc0377202f3b2393c742
hypothesis: >
  PIPELINE-VALIDATION ONLY. We make NO claim that B beats A/A′. We only check the machinery works end to end on one
  task: conditions are isolated and differ only as intended, B actually reads knowledge, A′ emptiness is recorded,
  validation is reproducible, and every run is reconstructable from its record.
expected_to_help: yes
---

## Purpose
First end-to-end exercise of the godot-lab pipeline on a single holdout task (`h01-timer-oneshot`). Proves the five
pipeline properties (see batch-config), **not** performance superiority.

## Method
- 1 task × {A, A′, B} × N=3 = 9 generations via fresh isolated `claude -p` sessions (Haiku 5.5, effort high), web OFF,
  randomized order, auto-memory/CLAUDE.md disabled, each in a neutral cwd.
- A: knowledge absent. A′: retrieval instruction + empty dir (record empty-dir detection). B: retrieval instruction +
  read-only `godot-knowledge` @ 50cc03a (record files read).
- Validation: `--check-only` parse of each produced script (parse-only for the pilot; GUT added next).
- Blind scoring: Sonnet 5.5, condition hidden, randomized IDs, outputs not rewritten; per-dimension + justification.

## Limits
N=3 on one task is a smoke test of the methodology. No statistical or superiority claim. Haiku 5.5 is a cost-minimizing
choice for pipeline validation, not the eventual target model.
