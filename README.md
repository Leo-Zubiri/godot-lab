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
