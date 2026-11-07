# results/ — human-written analysis per experiment

One file per experiment: `results/<exp-id>.md`. Written by a human after runs are scored. Reports the **per-dimension**
A / A′ / B comparison (not a single number), across-trial **variance**, operational costs, any **regressions or negative
results**, and an honest **verdict** with its limits.

## Result schema (frontmatter + body)
```yaml
---
exp_id: <exp-id>
rubric_version: "<frozen>"
eval_model_id: "<different-from-generator>"
gen_model_id: "<...>"
knowledge_commit_sha: "<...>"
godot_version: "4.7.2-stable"
trials_per_condition: 3
verdict: <helped|no-effect|hurt|inconclusive>
claim_strength: pipeline-validation-only   # for the first batch; NOT a performance/statistical claim
---

## Per-dimension results (A vs A′ vs B, mean ± range over trials)
<table>

## Costs
<tokens / latency / exec time / human time>

## Observations
<mediator check (did B read knowledge?), A′ empty-dir detection, regressions, anything surprising>

## Limits
<explicitly what this can and cannot conclude at this N; leakage checks performed>
```
Prefer paired per-task comparison and sign tests over a single p-value; state uncertainty with every number.
