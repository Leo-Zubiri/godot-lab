# rubrics/ — anchored scoring rubrics (versioned)

A rubric defines the scoring dimensions and **anchored** level criteria so scoring is reproducible and not a single
opaque number. The full default rubric is frozen in **P4**; this file fixes the schema.

## Rubric schema
```yaml
---
id: <rubric-id>
version: "<semver>"                 # bump on any criteria change; recorded in every result
created: <YYYY-MM-DD>
scale: [0, 1, 2, 3]                 # 0 wrong/absent · 1 major gaps · 2 minor issues · 3 fully correct
dimensions:
  - key: technical_correctness
    anchors: {0: "...", 1: "...", 2: "...", 3: "..."}
  - key: api_correctness
  - key: version_compatibility      # vs the declared Godot 4.7.2
  - key: architectural_quality      # human/rubric judgment — NEVER inferred from a passing test
  - key: requirement_fulfillment
  - key: source_quality
  - key: provenance
  - key: hallucinations             # reverse-scored (fewer = better)
  - key: practical_validity         # prefer the executable result over opinion
  - key: clarity
operational_costs:                  # recorded, NOT scored
  [input_tokens, output_tokens, retrieval_tokens, latency, exec_time, model_cost, research_cost, human_eval_time]
---
```

## Rules
- **No single opaque score** — report the per-dimension vector + A/A′/B deltas with variance.
- Missing/NA metrics recorded as `NA`, not `0`.
- Scoring is **blind** (condition hidden, outputs under randomized IDs, order shuffled) and done by a **different**
  evaluator model; outputs are **never rewritten/normalized**; score correctness & requirements, **not** verbosity/style.
- "Meaningful" improvement = B−A delta exceeds within-condition trial variance **and** holds on executable dimensions.
- **Passing tests ≠ architectural quality or completeness.**
