# AGENTS.md — godot-lab (experimental lab)

This is the **canonical entry point for agents** working in `godot-lab`. Read it first.

`godot-lab` is an **experimental harness**, not a knowledge base. Its job is to **measure whether consulting the shared
`godot-knowledge` repository actually improves** AI-generated Godot answers, decisions, and code — rigorously and
reproducibly, without tuning the design to make the knowledge condition win. It must **never become a second knowledge
repository**; durable, reusable Godot knowledge lives only in `godot-knowledge`.

> **Prime directives.**
> 1. **Read-only to knowledge.** Never write to `godot-knowledge` from here. Reusable findings are **staged** in
>    [`knowledge-outbox/`](knowledge-outbox/) and ingested by a *separate, authorized* pass — never by a dev/experiment run.
> 2. **Never promote to `verified`.** Agents may only *propose*; humans verify, in `godot-knowledge`'s Git-governed lifecycle.
> 3. **Measure honestly.** No performance-superiority or statistical claims from the first N=3 runs — they validate the
>    *pipeline* only. Report negative results and regressions.

## What lives where
- [`tasks/`](tasks/) — the versioned task bank. [`tasks/holdout/`](tasks/holdout/) = eval-only tasks (never used to build
  or refine the knowledge under test). [`tasks/exploration/`](tasks/exploration/) = free-form discovery tasks.
- [`conditions/`](conditions/) — condition specs **A**, **A′**, **B** (config templates; see below).
- [`rubrics/`](rubrics/) — anchored scoring rubrics (versioned).
- [`experiments/`](experiments/) — one dir per experiment: `definition.md` (what/why/tasks/conditions).
- [`runs/`](runs/) — immutable per-run records (config + output + validation + scores).
- [`results/`](results/) — human-written analysis per experiment (A vs A′ vs B, variance, honest verdict).
- [`fixtures/godot/`](fixtures/godot/) — minimal headless Godot project(s) for executable validation.
- [`knowledge-outbox/`](knowledge-outbox/) — staged candidate findings for ingestion into `godot-knowledge`.
- [`scripts/`](scripts/) — thin local wrappers (headless Godot, later a `claude -p` batch driver). **No infrastructure.**
- [`conditions/batch-config.md`](conditions/batch-config.md) — the **locked batch configuration** (the P0 decision record).

## Consuming `godot-knowledge` (read-only) — the cross-repo pattern
This uses the Knowledge Repository Template v1.0.0 cross-repo-consumption pattern.

- **Reachability:** attach a checkout of `godot-knowledge` via Claude Code `additionalDirectories` / `--add-dir`
  (path in `.env` → `GODOT_KNOWLEDGE_RO_PATH`). **Reachability is not read-only.**
- **Read-only boundary (enforced, not assumed):** the attached checkout must be **OS-level read-only** (a read-only
  copy/mount; e.g. `chmod -R a-w`) — the robust guarantee. A Claude Code `Edit(//.../godot-knowledge/**)` deny rule is
  only harness-level risk reduction and does not stop `Bash` writes. **Condition A must not have the knowledge repo on
  disk at all.**
- **Load its instructions explicitly:** an `AGENTS.md` in an added dir is **not** auto-loaded — so, when a task calls for
  it, **read `<GODOT_KNOWLEDGE_RO_PATH>/AGENTS.md`** and follow its retrieval protocol: prefer `verified`, surface
  `proposed` with its status, cite note `id`s, keep context small.
- **If unavailable** (path missing/unreadable): **report that knowledge could not be consulted and continue** — do not
  block; a Condition-B run that couldn't consult is flagged, not silently counted as B.

## Experimental conditions (the only intended difference is knowledge access)
- **A — baseline:** task + shared instructions; **no** knowledge access and **no** retrieval instruction; knowledge repo
  **absent from disk**.
- **A′ — placebo:** same retrieval instruction as B, pointed at an **empty** dir. Record retrieval attempts, files
  accessed, time/tokens, and **whether the agent detected the dir was empty**. A′ is an imperfect placebo — do not read
  A′−A as a pure instruction effect without these.
- **B — knowledge-assisted:** same retrieval instruction + read-only `godot-knowledge`. Record **which files were
  actually read** (the mediator).

Hold everything else identical and recorded: pinned full model id (no alias), effort, identical prompt (except the
knowledge clause), **web OFF in benchmark** (deny `WebSearch`/`WebFetch`), pinned Godot 4.7.2, time/token budget,
**knowledge commit SHA**, fresh isolated session per run (`claude -p`, unique `--session-id`, no resume; auto-memory &
CLAUDE.md disabled). Temperature/seed are **not controllable** → repeat N times and report variance.

## Validation & scoring discipline
- Define **acceptance tests before** running any condition; apply the **identical harness** to A/A′/B; record parse /
  test / runtime / requirement failures **independently**; preserve raw output + exit codes.
- **Automated tests prove only what they test** — keep executable correctness separate from architecture/design quality
  (human/rubric judgment). Godot headless can exit 0 on failure → gate on parsed output, not exit code alone.
- **Blind evaluation:** a **different** evaluator model (pinned id), blind to condition (randomized output IDs, shuffled
  order), **without rewriting/normalizing outputs**, scoring **correctness & requirements, not verbosity/style**;
  per-dimension scores + justifications; **human audit a sample across all three conditions**.

## Modes
- **Exploration:** web ON, free-form; generates candidates → `knowledge-outbox/`; **no measured-improvement claims**.
- **Benchmark:** frozen holdout tasks, controlled conditions, web OFF, repeated trials, blind scoring, reproducible
  `results/`. **Leakage firewall:** a note may be benchmarked only on holdout tasks that did **not** contribute to it.

## Governance & secrets
- Independent Git history from `godot-knowledge`; **no submodule**. Branches + human review; knowledge contributions land
  in `godot-knowledge` as reviewed PRs (separate from this repo).
- **Never commit** API keys, tokens, private prompts, PII, or provider credentials. `.env` is gitignored; `.env.example`
  holds references only.
- **No databases/embeddings/MCP/RAG or permanent multi-agent orchestration** unless a measured need justifies it.
