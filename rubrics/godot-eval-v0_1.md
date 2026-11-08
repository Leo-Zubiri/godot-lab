---
id: godot-eval-v0_1
version: "0.1.0"
created: 2026-11-06
scale: [0, 1, 2, 3]
dimensions:
  - key: technical_correctness
  - key: api_correctness
  - key: version_compatibility
  - key: architectural_quality
  - key: requirement_fulfillment
  - key: source_quality
  - key: provenance
  - key: hallucinations
  - key: practical_validity
  - key: clarity
operational_costs: [input_tokens, output_tokens, retrieval_tokens, latency, exec_time, model_cost, research_cost, human_eval_time]
---

# Godot evaluation rubric v0.1.0

Blind, per-dimension scoring for A / A′ / B outputs. **No single opaque score** — report the full vector + deltas with
variance. Score **correctness and requirements, not verbosity or style**. Outputs are scored **as written** (never
rewritten/normalized). Missing/NA → `NA`, not `0`. `hallucinations` is **reverse-scored** (3 = none).

Anchors (0 = absent/wrong · 1 = major gaps · 2 = minor issues · 3 = fully correct):

| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| **technical_correctness** | fundamentally wrong | several substantive errors | mostly right, minor errors | correct |
| **api_correctness** | invented/wrong Godot APIs | some wrong signatures/usage | mostly valid, small slips | all APIs valid for the task |
| **version_compatibility** | wrong for 4.7.2 (e.g. Godot 3 idioms) | some version-inappropriate bits | minor version slips | correct for declared 4.7.2 |
| **architectural_quality** | poor coupling/responsibilities | notable design issues | reasonable, minor concerns | clean, maintainable, extensible |
| **requirement_fulfillment** | task not done | partial | mostly complete | all stated requirements met |
| **source_quality** | no/irrelevant support | weak/loose support | adequate support | claims backed by appropriate sources |
| **provenance** | unattributable claims | vague references | mostly traceable | key claims traceable to evidence |
| **hallucinations** (reverse) | pervasive invented behavior | several invented items | one minor invention | none |
| **practical_validity** | does not parse/run | parses but likely wrong at runtime | runs with caveats | **passes the task's executable validation** |
| **clarity** | unintelligible | hard to follow | mostly clear | clear and actionable |

## Scoring rules
- **`practical_validity` is measured OBJECTIVELY by the GUT/parse harness, OUTSIDE the blind quality evaluator, and is
  stored separately.** The blind quality evaluator is **NOT** given the GUT/validation result (feeding it back would
  leak signal and risk condition identification); the evaluator scores the other dimensions from the submission alone.
  Aggregation may merge the objective `practical_validity` with the blind dimensions for analysis, but the two are kept
  as **separate scores** and the GUT result is **never** fed back into the blind quality evaluator.
- **`architectural_quality` is a human/rubric judgment** and must **not** be inferred from a passing test.
- Evaluator: a **different** model from the generator (pinned id, recorded). Blind to condition (randomized output IDs,
  shuffled order). Provide **a one-line justification per dimension**.
- "Meaningful" improvement = B−A delta exceeds within-condition trial variance **and** holds on executable dimensions.
- Human audits a sample across **all three** conditions; human reviews major disagreements and consequential claims.
