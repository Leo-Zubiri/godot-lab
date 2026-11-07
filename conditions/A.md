# Condition A — baseline

```yaml
condition: A
label: baseline
knowledge_access: "absent"          # godot-knowledge NOT on the filesystem (separate dir/container)
retrieval_instruction: false        # the prompt does NOT tell the agent to retrieve external knowledge
web_access: "off"                   # benchmark
notes: >
  The control. The generation prompt is the shared task + shared general instructions + constraints only.
  Because `--add-dir` grants read+edit and deny/Bash rules are leaky, the knowledge repo must be truly absent
  from the run's filesystem — not merely permission-denied.
```

Everything else (model id, effort, Godot version, tools, budgets, isolation) is identical to the other conditions and
taken from [`batch-config.md`](batch-config.md).
