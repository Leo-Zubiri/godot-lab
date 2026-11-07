# Condition B — knowledge-assisted

```yaml
condition: B
label: knowledge-assisted
knowledge_access: "read-only"       # read-only checkout/mount of godot-knowledge
retrieval_instruction: true         # identical instruction to A′
web_access: "off"                   # benchmark: only difference vs A/A′ is the curated content
enforcement:
  reachability: "additionalDirectories / --add-dir -> GODOT_KNOWLEDGE_RO_PATH"
  read_only: "OS-level read-only (chmod -R a-w / read-only mount)  # the hard boundary"
  harness_deny: "Edit(//abs/godot-knowledge/**)  # risk reduction only; does not stop Bash writes"
record:
  - knowledge_commit_sha            # git -C <knowledge> rev-parse HEAD (clean tree)
  - files_actually_read             # from tool_use events — the MEDIATOR evidence
  - retrieval_time_tokens
on_unavailable: "report 'knowledge could not be consulted', continue, FLAG the run (not counted as true B)"
notes: >
  The agent is instructed to read <knowledge>/AGENTS.md (added dirs are not auto-loaded) and follow its retrieval
  protocol: prefer verified, surface proposed with status, cite note ids. A B run that did not actually read any
  knowledge file is flagged and excluded from B aggregates.
```

Identical otherwise to [`batch-config.md`](batch-config.md).
