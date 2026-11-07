# runs/ — immutable per-run records

One directory per run: `runs/<exp-id>/<run-id>/`. A run = one (task × condition × trial). Records are **append-only /
immutable** once written; they must let a run be reconstructed. The schema is **automation-compatible** (identical shape
whether produced manually in P5 or by the `claude -p` driver in P7).

```
runs/<exp-id>/<run-id>/
  config.yaml        # see below
  prompt.txt         # the exact prompt sent (shared task + condition clause)
  output.md          # the model's raw output, UNMODIFIED (never normalized/rewritten)
  validation/        # executable-validation artifacts: parse/test logs, exit codes, per-failure-type results
  mediator.yaml      # retrieval evidence (files read, attempts, time/tokens, empty-dir detection for A′)
  usage.yaml         # tokens (input/output/cache), latency, cost ($ cautiously), from stream-json
  scores.yaml        # blind evaluator per-dimension scores + justifications (added at scoring time)
```

## `config.yaml` (reconstructability)
```yaml
exp_id: <exp-id>
run_id: <uuid>
task_id: <task-id>
condition: <A|A_prime|B>
trial: <n>
gen_model_id: <full id>            # resolved, from system/init
gen_effort: <level>
godot_version: "4.7.2-stable"
godot_build_hash: <hash>
knowledge_commit_sha: <sha|null>   # null for A
web_access: off
session_id: <uuid>                 # fresh, no resume
settings_sha256: <hash>
claude_version: <x.y.z>
order_index: <n>                   # position in the randomized order
timestamp: <iso8601>
```

Raw transcripts (`*.jsonl`, `raw/`) are gitignored by default; the curated record above is committed.
