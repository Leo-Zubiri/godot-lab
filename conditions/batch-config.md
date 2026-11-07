# Locked batch configuration (P0 decision record)

The frozen, approved configuration for the first experiment batch. Record the exact values in every run's
`config.yaml`. Change only by an explicit new decision (bump the version below).

```yaml
config_version: "0.1"
decided: 2026-11-06

# --- Environment ---
godot_version: "4.7.2-stable"      # pinned; record build hash per run
language: "gdscript"               # C# deferred (separate, justified phase)

# --- Generation (model under test) ---
gen_model_id: "claude-haiku-5-5"    # PILOT run: cheapest model for pipeline validation (switch to target model for real benchmarks)
gen_effort: "high"                  # pinned; fast mode OFF
sampling: "uncontrolled"            # temperature/top-p/seed NOT settable in Claude Code → repeats + variance
fallback_model: "unset"

# --- Conditions ---
conditions: [A, A_prime, B]         # A=baseline, A_prime=placebo(empty dir), B=knowledge
web_access: "off"                   # benchmark: deny WebSearch/WebFetch in ALL conditions
trials_per_condition: 3             # N=3 — PIPELINE VALIDATION ONLY, not a performance/statistical claim
order: "randomized"                 # fresh isolated session per run; no resume
session_isolation:                  # disable context/memory surprises
  - "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1"
  - "CLAUDE_CODE_DISABLE_CLAUDE_MDS=1 (or --bare)"
  - "--no-session-persistence"
  - "DISABLE_AUTOUPDATER=1"

# --- Knowledge access (the independent variable) ---
knowledge_repo: "Leo-Zubiri/godot-knowledge"
knowledge_commit_sha: "50cc03ab79ad448586f6dc0377202f3b2393c742"   # v0.1.0 (read-only checkout)
knowledge_access:
  A: "absent from filesystem"
  A_prime: "empty dir attached (record empty-dir detection)"
  B: "read-only (OS-level read-only checkout/mount) + Edit-deny; record files actually read"

# --- Validation ---
validation: "layered: godot --check-only (parse) -> GUT behavior tests -> integration checks"
gate_on: "parsed output (NOT exit code alone — headless can exit 0 on failure)"
acceptance_tests: "defined BEFORE running any condition; identical harness across A/A'/B"
failure_types_recorded: [parse, test, runtime, requirement]   # independently

# --- Evaluation ---
eval_model_id: "claude-sonnet-5-5"  # DIFFERENT from generator (claude-haiku-5-5), to curb self-agreement
eval_blind: true                    # randomized output IDs, shuffled order, condition hidden
eval_no_rewrite: true               # never rewrite/normalize outputs; score correctness+requirements, not verbosity/style
rubric_version: "<set when rubric frozen in P4>"
human_audit: "sample across ALL three conditions; review disagreements/suspicious/consequential"

# --- Holdout ---
holdout: "frozen BEFORE runs; balanced: code-gen, API-correctness, architecture, debugging, >=1 negative-control"
leakage_firewall: "a note is benchmarked only on holdout tasks that did NOT contribute to it"
```

## First-experiment objective (explicit)
Prove the **pipeline only**: (1) condition isolation (A has no knowledge on disk), (2) condition integrity (A/A′/B differ
only as intended), (3) knowledge-access mediation (B actually read files; A′ emptiness recorded), (4) reproducible
validation (same harness, deterministic parse/test), (5) reconstructable run records. **No** superiority or statistical
claim from N=3.

## Items to fill before the first run (P4/P5)
- `gen_model_id`, `eval_model_id` (distinct, pinned full IDs), `rubric_version`, `knowledge_commit_sha`, the frozen
  holdout list, and the Godot build hash.
