# experiments/ — experiment definitions

One subdirectory per experiment: `experiments/<exp-id>/definition.md`. The definition states *what* is being tested and
*how*, and points at tasks, conditions, and the rubric. It is frozen before runs.

## `definition.md` schema (YAML frontmatter + body)
```yaml
---
id: <exp-id>                        # stable slug, = dir name
status: draft                       # draft -> running -> scored -> concluded
created: <YYYY-MM-DD>
batch_config: ../../conditions/batch-config.md
conditions: [A, A_prime, B]
tasks:                              # holdout task ids under test
  - <task-id>
rubric: ../../rubrics/<rubric-id>.md
rubric_version: "<frozen version>"
trials_per_condition: 3            # pipeline-validation sample
hypothesis: >                       # a falsifiable statement; may be "no measurable difference"
  <what you expect, and explicitly what would count as the knowledge NOT helping>
expected_to_help: <yes|no|mixed>    # declare up front (anti-confirmation-bias)
---

## Purpose
<Why this experiment exists; what question it answers.>

## Method
<Any specifics beyond batch-config. Note acceptance tests are defined in the task files BEFORE runs.>

## Limits
<What this experiment can and cannot conclude (esp. at N=3).>
```

The first experiment's objective is **pipeline validation only** — see `conditions/batch-config.md`.
