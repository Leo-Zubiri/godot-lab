# godot-lab — does consulting `godot-knowledge` actually help?

An **experimental laboratory** that measures whether giving an AI agent read-only access to the
[`godot-knowledge`](https://github.com/Leo-Zubiri/godot-knowledge) base **measurably and reproducibly improves** its
Godot answers, decisions, and code — compared to a baseline with no knowledge access.

It is **not** a knowledge base and must never become one. It consumes `godot-knowledge` **read-only** and feeds
validated, reusable findings back through that repo's human-governed intake. The two repos stay independent (no
submodule, no copy). Agents working here: start with [`AGENTS.md`](AGENTS.md).

## The experiment, in one line
Run identical Godot tasks under three conditions and score them blind:
- **A** — baseline (no knowledge, no retrieval instruction).
- **A′** — placebo (told to retrieve, but an empty knowledge dir).
- **B** — knowledge-assisted (told to retrieve + read-only `godot-knowledge`).

The only intended difference is knowledge access; everything else is controlled or recorded. **A vs A′** isolates the
*instruction to retrieve*; **A′ vs B** isolates the *actual curated content*.

## Results so far — H06 *platformer-pickup* (A/A′/B × N=5) · **EXPLORATORY**
> N=5 per condition is a pipeline/exploratory run: **no statistical significance, no generalization**. Generator
> (`claude-sonnet-5-5`) and blind evaluator (`claude-opus-5-5`) are both Anthropic models (not provider-independent).

**Headline — on this task, the knowledge base did *not* produce a genuine quality improvement.** The one dramatic number
(B passes the executable suite 5/5 vs A's 0/5) is a **benchmark-leakage artifact**, not better code: the GUT test asserts
`velocity.x == 300` *exactly*, and the knowledge note hard-codes `SPEED := 300`. B copies that constant and passes; A
uses an equally-valid `200` and fails only that one assertion. All 15 submissions (A/A′/B) **visibly run and collect the
coin** in the real Godot engine.

| metric (kept separate) | A | A′ | B |
|---|---|---|---|
| GUT PASS (functional) | 0/5 | 3/5 | 5/5 ← artifact (shared `SPEED=300`) |
| Blind quality mean (opus, test-blind) | 2.29 | 2.42 | 2.42 ← no real separation |
| Hallucinations (3 = none) | 3.0 | 2.6 | **2.0** ← B slightly worse |
| Provenance | **fabricated** refs in 3/5 | cited nothing (correct) | **real, relevant** citations |
| Knowledge reads (mediator) | 0 | 0 (+1 turn placebo) | 3.2 (read in 4/5) |

**The one genuine knowledge effect:** B grounds its claims in *real* sources, while the baseline *fabricates* references.
Full write-up → [`results/final-results.md`](results/final-results.md) · per-run data →
[`results/comparisons.csv`](results/comparisons.csv) · engine/GUT + 75 real screenshots →
[`experiments/exp-h06-platformer-pickup/evidence/`](experiments/exp-h06-platformer-pickup/evidence/).

### Did it generate knowledge?
Yes — H06 fed the cross-repo lifecycle (`lab → source → synthesized notes`) into
[`godot-knowledge`](https://github.com/Leo-Zubiri/godot-knowledge), all **`status: proposed`** (awaiting human
verification — agents never self-promote to `verified`):
- `sources/src-h06-platformer-experiment.md` — the experiment preserved as evidence (pins `godot-lab@9aa96dd`).
- `notes/benchmark-leakage-assertions.md` — anti-pattern: exact-constant assertions that also live in the knowledge leak the answer.
- `notes/knowledge-availability-vs-application.md` — concept: available ≠ retrieved ≠ better code; provenance can improve while quality doesn't.

**Does this justify a larger experiment? Not as-is** — first fix the methodology (assert *behavior*, not magic
constants; guarantee holdout independence). The pipeline itself (isolation, blinding, mediation, objective + visual
evidence, provenance) worked and *caught* the artifact.

## Layout
| Dir | Purpose |
|---|---|
| [`tasks/`](tasks/) | versioned task bank — `holdout/` (eval-only) and `exploration/` |
| [`conditions/`](conditions/) | condition specs A / A′ / B + the locked [`batch-config.md`](conditions/batch-config.md) |
| [`rubrics/`](rubrics/) | anchored 0–3 scoring rubric (versioned) |
| [`experiments/`](experiments/) | one dir per experiment (`definition.md`) |
| [`runs/`](runs/) | immutable per-run records (config + output + validation + scores) |
| [`results/`](results/) | human analysis per experiment (A/A′/B deltas, variance, verdict) |
| [`fixtures/godot/`](fixtures/godot/) | minimal headless Godot 4.7.2 project for executable validation |
| [`knowledge-outbox/`](knowledge-outbox/) | staged candidate findings for ingestion into `godot-knowledge` |
| [`scripts/`](scripts/) | thin local wrappers (no infrastructure) |

## Ground rules
- **Read-only to knowledge** (OS-enforced); findings are staged, never written directly to `godot-knowledge`.
- **Never promote to `verified`** — humans do that in `godot-knowledge`.
- **First N=3 runs validate the pipeline only** — no performance-superiority or statistical claims.
- **No secrets in git**; no DB/embeddings/MCP/RAG or permanent multi-agent infra.
- Environment pinned to **Godot 4.7.2 (stable), GDScript-first**.

## License
MIT — © 2026 Leo Zubiri (see [`LICENSE`](LICENSE)). Independent of, but designed to interoperate with, the Knowledge
Repository Template v1.0.0 cross-repo-consumption pattern.
