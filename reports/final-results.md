# H06 — Final results: does consulting `godot-knowledge` improve AI-generated Godot code?

**Experiment:** exp-h06-platformer-pickup (protocol v2) · **Task:** implement `player.gd` (CharacterBody2D) + `coin.gd`
(Area2D) for a 2D platformer pickup, Godot 4.7.2 GDScript.
**Design:** A (baseline, no knowledge) · A′ (placebo: told to retrieve, empty dir) · B (read-only `godot-knowledge`
@ `91250e6`). N=5 per condition, 15 generations total. Generator `claude-sonnet-5-5` (effort high, web off), each run
in its own bubblewrap sandbox (knowledge the only per-condition difference). Blind quality evaluator `claude-opus-5-5`.

> **N=5 is EXPLORATORY. No statistical significance is claimed, and nothing here generalizes beyond this one task.**
> Generator and evaluator are both Anthropic models (not provider-independent).

## Headline (read this first)
On this task, **the knowledge base did not produce a genuine quality improvement.** The one dramatic-looking result —
B passes the executable suite 5/5 while A passes 0/5 — is almost entirely an **artifact of a single shared magic
constant**, not better code:

- The GUT suite asserts `velocity.x == 300.0` (exact, ±1.0) for horizontal movement.
- The knowledge note `characterbody2d-movement.md` hard-codes `const SPEED := 300.0`, and the test's own reference
  implementation uses the same 300.
- **Every one of the 15 failures is that single assertion.** B runs copy `SPEED = 300` from the note → pass. A runs use
  `200` (one A′ used `160`) → fail only that assertion. **A speed of 200 is perfectly correct platformer code**; it just
  doesn't match an arbitrary constant the test and the note happen to share. This is textbook **benchmark leakage**.
- **Visual verification confirms it:** all 15 submissions — A, A′ and B — visibly run, jump, move, and **collect the coin**
  (coin removed) in the real engine. None is functionally "broken."

The blind quality evaluation (which never saw the test, the condition, or the speed) found **no meaningful separation**:
A′ ≈ B (2.42) with A marginally lower (2.29), inside the trial spread — and B scored **worse on hallucinations** than A.

## 1. Results kept strictly separate (per the approved design)

### 1a. Functional correctness — objective GUT (practical_validity)
| condition | GUT PASS | FAIL | practical_validity mean | sole failure cause |
|---|---|---|---|---|
| A | 0/5 | 5/5 | 0.0 | `velocity.x`=200, test wants exactly 300 |
| A′ | 3/5 | 2/5 | 1.8 | the 2 fails use 200 / 160 |
| B | 5/5 | 0/5 | 3.0 | all use 300 (from the note) |

All suites ran 6 tests; harness-sanity PASS; no crashes; no candidate parse errors; no harness errors. Verdicts use the
strict rule (PASS requires failures=0, skipped=0, risky=0, pending=0). **The A/B gap is entirely the speed constant.**

### 1b. Blind code/explanation quality — opus-5-5, condition- and test-blind (practical_validity excluded by design)
| dimension | A | A′ | B |
|---|---|---|---|
| technical_correctness | 2.6 | 3.0 | 3.0 |
| api_correctness | 3.0 | 3.0 | 3.0 |
| version_compatibility | 3.0 | 3.0 | 3.0 |
| architectural_quality | 2.4 | 2.6 | 2.8 |
| requirement_fulfillment | 2.6 | 2.8 | 3.0 |
| source_quality | 2.8 | 3.0 | 3.0 |
| provenance (as read by evaluator) | 3.0 | 3.0 | 3.0 |
| **hallucinations (reverse; 3=none)** | **3.0** | **2.6** | **2.0** |
| clarity | 3.0 | 3.0 | 3.0 |
| **overall mean** | **2.29** | **2.42** | **2.42** |
| overall median | 2.33 | 2.44 | 2.44 |
| overall range | 2.11–2.44 | 2.33–2.56 | 2.33–2.44 |

**Reading:** A′ and B tie; A is ~0.13 lower — well within the within-condition spread (~0.2–0.45), so not a
meaningful difference at N=5. The one consistent directional signal is **against** B: the blind evaluator flagged
**more hallucinated/over-asserted content in B** (2.0) than in A (3.0) — plausibly B importing extra claims from the notes.

### 1c. Provenance — separate references pass (objective existence + opus judgment)
| condition | runs citing refs | cited notes exist? | note |
|---|---|---|---|
| A | 3/5 | **no (existence 0–1)** | A **invented** citations despite having no knowledge — a contract violation + hallucination |
| A′ | 0/5 | — (NA) | correctly cited nothing (empty dir) |
| B | 5/5 | **yes (existence 3)** | cited real, relevant notes; claim↔source correspondence 2/3 (minor over-reach) |

This is the clearest **genuine** knowledge effect: B's citations are real and relevant; A fabricates references;
A′ honestly abstains. (Provenance scores are never combined with the quality vector.)

## 2. Condition contrasts
- **A vs A′ (instruction-to-retrieve effect):** A′ > A on GUT (3 vs 0 PASS) and marginally on blind quality (2.42 vs
  2.29). Both driven by the same thing: being *told* to retrieve nudged 3/5 A′ runs toward the conventional `SPEED=300`,
  and A′ stopped fabricating references. **A′ never actually read files** (empty dir; mean knowledge reads = 0) and took
  2 turns vs A's 1 — the "looked, found nothing, proceeded" signature. So A′−A is an instruction/anchoring effect, not content.
- **B vs A:** large on GUT (5 vs 0) but **artifactual** (speed constant); negligible and mixed on blind quality (B not
  better; worse on hallucinations); B clearly better on provenance (real vs fabricated citations).
- **B vs A′:** **tied** on blind quality (2.42 = 2.42); B higher on GUT only via the shared constant; B cites real
  sources where A′ cites none. Net: the *actual curated content* (A′→B) produced **no measurable code-quality gain** here.

## 3. Mediation (did B actually use the knowledge?)
Mean knowledge file-reads: A=0, A′=0, **B=3.2**. B read `/knowledge` in **4/5** runs (1–6 reads: AGENTS.md + notes).
**Anomaly:** B run `9e367447` shows 0 recorded reads yet cited 5 real notes — it most likely listed the notes via a
glob/dir listing the mediator under-counts (the mediator captures `Read/Glob/Grep` paths containing `/knowledge`; a
bare directory glob can evade it). That run is a weaker "true B". This nuance is recorded, not hidden.

## 4. Visual evidence
All 15 runs rendered in the real Godot 4.7.2-mono engine (isolated Xvfb; candidate SHA-256 identical before/after —
submissions unmodified). Each produced 5 genuine screenshots (initial, grounded, jump, approach, collected). **In every
condition all 5/5 runs collected the coin on screen.** See `evidence/visual/` (per-run manifests + SHAs) and its README.
**Caveat:** visual success ≠ correctness — the A runs look like fully working platformers while failing the exact-speed
assertion. Three evidence kinds are kept distinct: engine execution, GUT behavioral tests, and visual screenshots.

## 5. Anomalies & deviations
- **Benchmark leakage (major):** the holdout test asserts an exact `SPEED` that the knowledge note supplies — the task
  is not a clean independent holdout for the `practical_validity` dimension. Fix before any larger run (below).
- **A fabricated references** in 3/5 runs (hallucinated provenance).
- **B hallucination score worse** than A on the blind rubric.
- **One B run** did not measurably read knowledge yet cited notes (mediator under-count).

## 6. Limitations
- N=5 per condition — exploratory; **no significance, no generalization** beyond this single intermediate task.
- Generator and evaluator are both Anthropic models → shared-provider bias; not provider-independent.
- The executable signal was dominated by **one over-specified assertion**; GUT here measures constant-matching more than
  correctness. Blind quality (the cleaner signal) showed no B advantage.
- A′ is an instruction+empty-dir placebo, not a perfect one (recorded: 0 reads, +1 turn vs A).

## 7. Does this justify a larger experiment?
**Not as-is.** First fix the methodology, then scale:
1. **Remove magic-constant coupling:** tests should assert *behavioral properties* (moves right, speed > 0, monotonic
   progress), not an exact `SPEED`; or randomize the required constant per run so it can't be memorized from a note.
2. **Guarantee holdout independence:** ensure no test asserts a literal that appears in the knowledge under test.
3. **Weight the blind/behavioral signal** over exact-match executable checks; treat `practical_validity` as behavioral.
4. Only then raise N (≥20–30/condition), add tasks across difficulty, and keep a provider-independent evaluator in view.
The pipeline itself (isolation, blinding, mediation, objective validation, provenance, visual evidence) **worked and
caught the artifact** — that is the main positive outcome of this run.

## 8. Evidence package
- `evidence/godot-execution/` — `environment.json`, `runs.json` (per-run SHA-256, versions, command, exit code, counts,
  verdict), `gut-reports/`, `logs/`.
- `evidence/visual/` — `A/`, `A-prime/`, `B/` screenshots + per-run engine-state manifests, `manifest.json`, `README.md`.
- `evidence/evaluation/` — blind quality `payload.json` (proving `{blind_id,rubric,submission}` only) + `scores.json`;
  separate `provenance/`.
- `results/` — `exp-h06-platformer-pickup-matrix.{json,md}` (aggregates), `comparisons.csv` (per-run), this report.
- Raw preserved runs: `runs/exp-h06-platformer-pickup/{matrix,blind_quality,provenance}/` (every attempt kept).

## Reproducibility
Knowledge pin `91250e6b2bd9e3966e7b22be94dea9bc2c263fae`; Godot `4.7.2.stable.mono`; GUT `9.6.1`; generator
`claude-sonnet-5-5`; evaluator `claude-opus-5-5`. Total generation cost ≈ $0.94; blind+provenance ≈ a few $ (opus).
Re-run: `scripts/h06_matrix.py --execute` → `h06_validate.py` → `h06_blind_eval.py --execute` →
`h06_provenance_eval.py --execute` → `h06_aggregate.py` (+ `h06_visual.py` for screenshots).
