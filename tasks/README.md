# tasks/ — the versioned task bank

Each task is a Markdown file with YAML frontmatter + the prompt + acceptance criteria. **Acceptance tests are written
BEFORE any run** and kept separate from implementation-specific assertions (don't assume one valid solution).

## Task schema
```yaml
---
id: <task-id>
category: <explain|architecture|codegen|debug|decision|...>
difficulty: <easy|intermediate|hard>
expected_to_help: <yes|no|mixed>    # declared up front (anti-bias); include negative controls
executable_validation: <none|parse|parse+test>
godot_version: "4.7.2-stable"
provenance: <authored|from-exploration:<exp-id>>   # for the leakage firewall
contributes_to_notes: []            # note ids this task helped create (NEVER benchmark those notes on this task)
created: <YYYY-MM-DD>
---

## Prompt
<the exact task given to the agent — identical across conditions>

## Acceptance criteria
<requirement-level checks, implementation-agnostic>

## Automated validation
<what parse/GUT/integration checks run; what each proves — and what it does NOT prove>
```

- [`holdout/`](holdout/) — **eval-only**; frozen before benchmark runs; never used to build/refine knowledge under test.
- [`exploration/`](exploration/) — free-form discovery; may *seed* notes, but a note is benchmarked only on holdout
  tasks that did **not** contribute to it.
