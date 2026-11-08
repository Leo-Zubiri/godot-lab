---
exp_id: exp-h01-pilot
reeval: condition-leakage-audit
date: 2026-11-08
eval_model_id: claude-sonnet-5-5
rubric_version: "0.1.0"
input: normalized artifacts (eval_input.md)
supersedes_scoring_of: results/exp-h01-pilot.md
claim_strength: pipeline-validation-only
---

# exp-h01-pilot — blind re-evaluation after condition-leakage audit

The original pilot scoring (`results/exp-h01-pilot.md`) was **contaminated**: the evaluator saw the raw `output.md`, which
contained condition tells (process narration, repo note-ids, paths, `status: proposed`, A′'s "directory is empty"). This
document reports a **blind re-evaluation on normalized artifacts**. Original outputs, run records, and v1 scores are
**preserved and marked contaminated**, not overwritten.

## What changed
- **Deterministic normalizer** (`scripts/normalize_for_eval.py`): `output.md` → `eval_input.md` + `anon_map.json` +
  `normalize_log.json`. Code blocks kept **verbatim**; only prose normalized. Removes paths, repo/dir/file names, the
  "KB" abbreviation, process narration (consulting / emptiness / "not verified by a human" / tooling), and neutralizes
  `status: proposed` → `unverified` (keeps the justified uncertainty). **Anonymizes** repo note-ids → opaque `[ref-NN]`
  (correspondence in `anon_map.json`, which the evaluator never receives).
- **Evaluator input** is now exactly: the rubric + a random blind id + the normalized artifact. Nothing else.
- Scores recorded in `runs/<rid>/scores_v2.yaml` (new); originals in `scores.yaml` kept + marked `contaminated: true`.

## Verification tests (all passed)
| Test | Result |
|---|---|
| Determinism (normalize twice → identical) | **9/9 identical** ✓ |
| Script integrity (gdscript block byte-identical orig↔normalized) | **9/9 identical** ✓ |
| Leak audit (expanded forbidden-token grep incl. KB/proposed/is-empty/tooling/note-ids/paths/`the the`) | **clean** ✓ |
| Anonymization (repo note-ids → `[ref-NN]`, no raw ids remain) | ✓ |
| Content preservation (manual diff review: API names, lifecycle, typed signatures, justified uncertainty kept) | ✓ |

## Adversarial leakage test (req 8)
A separate Sonnet 5.5 classifier, given only the normalized artifact + the definitions of A/A′/B, guessed the condition:

- **Overall: 5/9 (55%)** vs chance 33%.
- **A′: 0/3** — now **indistinguishable from A** (the empty-dir / retrieval-instruction tell was fully removed). ✓
- **B: 3/3** — detectable **via the preserved `[ref-NN]` citations** (the traceability signal req 4 requires keeping).
- **A: 2/3.**

> **Honesty (req 8): N=9 cannot statistically demonstrate absence of leakage. A near-chance result is necessary, not
> sufficient. We do NOT claim perfect blinding.** The >chance overall is driven entirely by B, and B's detectability is
> inseparable from the thing being measured (knowledge → source-grounded answers).

## Scores: contaminated v1 vs blind v2 (mean over N=3; 0–3)
| Dimension | A v1 | A v2 | A′ v1 | A′ v2 | B v1 | B v2 |
|---|---|---|---|---|---|---|
| technical_correctness | 3 | 3 | 3 | 3 | 2.67 | 2.67 |
| api_correctness | 3 | 3 | 3 | 3 | 3 | 3 |
| version_compatibility | 3 | 3 | 3 | 3 | 3 | 3 |
| requirement_fulfillment | 3 | 3 | 3 | 3 | 3 | 3 |
| hallucinations (rev) | 2.67 | 3 | 3 | 3 | 2.67 | 2.67 |
| clarity | 3 | 3 | 3 | 3 | 2.67 | 2.0 |
| practical_validity (parse) | 3 | 3 | 3 | 3 | 3 | 3 |

**Reading (unchanged conclusion):** still at ceiling; **knowledge did not help** on this easy task. Differences are
**within N=3 noise**; the v2 B-clarity dip (2.67→2.0) is not evidence of anything and is **partly a normalization
artifact** (see residual #2). No performance or statistical claim.

## Residual limitations (req 10)
1. **B remains identifiable** via preserved anonymized citations + "reference material" mentions. This **cannot be
   removed without destroying the traceability signal** (req 4). It is arguably *signal* (the knowledge condition yields
   source-grounded answers), not a process tell — but it does mean the artifact-level blind is imperfect for B.
2. **Redaction artifacts bias clarity.** Deterministic redaction leaves mild awkwardness ("Per the reference guide and
   used these notes") **only in conditions that had tells (B/A′)**; A needed zero redaction. This can unfairly depress
   clarity for redacted conditions and may explain B's v2 clarity dip. Length/structure were intentionally **not**
   equalized (req 5), so this is not from padding.
3. **Deterministic phrase-redaction is brittle** to novel phrasings (whack-a-mole). It is audited clean for these 9
   outputs but is **not future-proof** for new tasks/models.
4. **N=9**: no statistical power for any blindness or performance claim.

## Recommended robust fix (OUT OF SCOPE here — needs separate authorization)
The limitations above are inherent to **post-hoc** redaction. The robust fix is to remove tells **at generation**: a
**structured output contract** (the generator emits only `{script, technical_explanation}`, no process narration),
optionally forbidding self-reference to tooling/sources, so artifacts are clean at the source and need no redaction
(eliminating residual #2 and most of #3). This **changes the generation design**, so per the audit's scope rule it is
presented for decision, not implemented here. Residual #1 (B cites sources) remains by design and is treated as signal.

## Integrity
Originals preserved: `output.md`, `*.jsonl` (gitignored), `scores.yaml` (marked `contaminated: true`, values intact),
`results/exp-h01-pilot.md` (banner added, body unchanged). New: `eval_input.md`, `anon_map.json`, `normalize_log.json`,
`scores_v2.yaml`, `adversarial/`, this file.
