---
id: exp-h06-platformer-pickup
protocol: v2
status: designed            # harness built + validated on the reference; matrix NOT yet run
created: 2026-11-08
batch_config: ../../conditions/batch-config.md
output_contract: ../../conditions/output-contract-v2.md
task: ../../tasks/holdout/h06-platformer-pickup.md
rubric: ../../rubrics/godot-eval-v0_1.md
conditions: [A, A_prime, B]
trials_per_condition: 5     # N=5 is EXPLORATORY — cannot establish statistical significance
gen_model_id: claude-sonnet-5-5          # exact resolved version recorded per run (system/init) at matrix time; fixed across all conditions
eval_model_id: claude-opus-5-5           # APPROVED evaluator (!= generator)
eval_provider_note: "generator (Sonnet) and evaluator (Opus) are BOTH Anthropic models; different models from the SAME provider do NOT establish provider-independent evaluation (shared lineage => possibly correlated biases)."
knowledge_pin: "godot-knowledge@91250e6b2bd9e3966e7b22be94dea9bc2c263fae"   # branch knowledge/batch-01-2d-entity
knowledge_status_note: "the 3 cited notes are PROPOSED (agent-authored), NOT verified"
expected_to_help: mixed
---

## Purpose
First **practical** cross-repo experiment: does read-only access to `godot-knowledge` (the CharacterBody2D / Area2D /
input notes) change the quality of a non-trivial generated 2D-platformer-pickup implementation? Exploratory only.

## Protocol v2 (vs the pilot's v1)
- **Structured output contract** (`### script / ### explanation / ### references`) — no process narration ⇒ removes the
  v1 leak + redaction-artifact source at the source. See `output-contract-v2.md`.
- **Evaluation separation:** blind quality (script+explanation only, normalized, random blind id, identical rubric) vs a
  separate provenance pass over `references`. Scores never combined. Condition mapping kept out of evaluator inputs.
- **Deterministic executable validation** via the fixed GUT harness (`fixtures/h06/`, `scripts/run_h06_tests.sh`),
  gating on the parsed report + crash/error detection.
- Original outputs preserved; reuse `fe9d1eb` tooling without touching historical v1/v2 (pilot) results. Protocol
  **versioned v2** so pilot (v1) and h06 (v2) remain distinguishable.

## Conditions (only knowledge availability differs)
- **A** — baseline: no knowledge on disk, no retrieval instruction.
- **A′** — placebo: retrieval instruction + an empty knowledge dir.
- **B** — read-only `godot-knowledge` checked out at the pinned SHA above (OS-level read-only), with the retrieval
  instruction. Record which notes were actually read (mediator).

Identical for all: generator model+version, effort, task prompt, output contract, token budget, acceptance criteria,
web OFF, fresh isolated sessions. **Randomize generation order; blind evaluation order; keep condition mappings outside
evaluator inputs.**

## Validation status (this checkpoint)
Harness built and **validated on a reference implementation: 6/6 GUT tests pass, deterministic, no crash** (see
`runs/exp-h06-platformer-pickup/reference/`). The runner also correctly reports **FAIL** on a deliberately broken
candidate. **The 15-generation matrix has NOT been run** — awaiting review/authorization.

## Limits
N=5 is exploratory; **a small score delta is not proof** of knowledge effectiveness. The B notes are `proposed`, not
verified. Headless physics is made deterministic by fixed-frame stepping, but results still reflect one machine/build.
