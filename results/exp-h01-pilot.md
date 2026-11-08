---
exp_id: exp-h01-pilot
rubric_version: "0.1.0"
eval_model_id: claude-sonnet-5-5
gen_model_id: claude-haiku-5-5
knowledge_commit_sha: 50cc03ab79ad448586f6dc0377202f3b2393c742
godot_version: "4.7.2-stable"
trials_per_condition: 3
verdict: inconclusive
claim_strength: pipeline-validation-only
---

# Results — exp-h01-pilot (PIPELINE VALIDATION ONLY)

> ⚠️ **Scoring below is CONTAMINATED and SUPERSEDED (condition-leakage audit, 2026-11-08).** The evaluator saw raw
> outputs containing condition tells (process narration, note-ids, paths, `status: proposed`, A′'s "empty directory").
> The blind re-evaluation on normalized artifacts is in **[`exp-h01-pilot-reeval.md`](exp-h01-pilot-reeval.md)**. The
> pipeline-validation evidence (isolation, mediation, reproducible validation, reconstructable records) remains valid;
> only the per-dimension **scores** are superseded. Original scores are preserved and marked `contaminated: true`.

**This run makes NO performance-superiority or statistical claim.** It is a smoke test of the whole godot-lab pipeline
on one easy holdout task (`h01-timer-oneshot`), 1 task × {A, A′, B} × N=3 = 9 generations (Haiku 5.5) + 9 blind
evaluations (Sonnet 5.5).

## Pipeline properties — all demonstrated ✓
1. **Condition isolation:** Condition A ran with the knowledge repo **absent from disk**; it read nothing (kb_reads=0).
2. **Condition integrity:** A / A′ / B differed only as intended (A no instruction+no repo; A′ instruction+empty dir;
   B instruction+read-only repo). Identical model, effort, prompt (minus the knowledge clause), web OFF, fresh isolated
   sessions, randomized order.
3. **Knowledge-access mediation:** all 3 **B** runs actually read the knowledge (kb_reads = 2, 6, 2) — via `Bash cat` of
   the read-only checkout — and **cited note ids** (`node-lifecycle-callbacks`, `gdscript-signals`,
   `godot-version-policy`, …), noting their `status: proposed`. All 3 **A′** runs **detected the empty dir** ("empty").
4. **Reproducible validation:** the identical harness parse-checked every output with Godot 4.7.2 (`--check-only`,
   gated on parsed output). **9/9 parse = pass.**
5. **Reconstructable records:** every run has a `config.yaml` (model, effort, Godot, knowledge SHA, order, session id,
   tokens, cost, parse, kb_reads) + `output.md` + `output.gd` + `validation/parse.txt` + `scores.yaml`.

## Per-dimension blind scores (mean over N=3; 0–3, higher better; hallucinations reverse-scored)
| Dimension | A (baseline) | A′ (placebo) | B (knowledge) |
|---|---|---|---|
| technical_correctness | 3 | 3 | 2.67 |
| api_correctness | 3 | 3 | 3 |
| version_compatibility | 3 | 3 | 3 |
| requirement_fulfillment | 3 | 3 | 3 |
| hallucinations | 2.67 | 3 | 2.67 |
| clarity | 3 | 3 | 2.67 |
| practical_validity (from parse) | 3 | 3 | 3 |

**Reading (honest):** on this easy, ceiling-effect task the three conditions are essentially tied, and **B is if
anything marginally lower** on technical_correctness and clarity. **Knowledge did not help here** — the expected result
for a trivial task, and a useful check that we are **not** tuning the setup to make B win. A plausible cause of B's small
dip is that B outputs carried extra process narration ("I read the KB…"), which the blind evaluator judged slightly less
clean. No conclusion about knowledge value should be drawn from this.

## Operational costs (recorded)
- Generation (USD, sum over 3 trials): A ≈ 0.0065, A′ ≈ 0.0068, **B ≈ 0.0149** (~2× — B reads knowledge). Output tokens:
  A ≈ 1.1k, A′ ≈ 1.5–1.8k (instruction effect, empty dir), B ≈ 1.6–3.0k.
- Pilot total (gen + eval) is well under ~$0.1. Token counts are the primary metric (subscription $ ≠ billing).

## Limitations (why no conclusions)
- **N=3, one easy task, ceiling effects** → no statistical power; no superiority claim.
- **Condition leakage into outputs:** generated answers contained condition "tells" (B: "I consulted the knowledge
  base"; A′: "the directory is empty"). The evaluator was blind to the *label* and instructed to score the technical
  answer and ignore process narration, but the tells are not fully removable without changing the generator prompt
  (e.g., instruct generators not to narrate process) or scoring only the extracted script. **Fix before any real
  benchmark.**
- **Haiku 5.5** was a cost-minimizing pilot generator, **not** the eventual target model; **parse-only** validation
  (GUT behavior tests not yet wired); **A′ agents detected emptiness**, so A′−A is not a clean pure-instruction contrast.

## What this unblocks
The machinery (isolation → mediated consultation → reproducible validation → blind scoring → reconstructable records)
works end to end. Next: address output leakage, add GUT behavior tests, pick the real target model, expand the holdout,
and raise N before making any measured claim.
