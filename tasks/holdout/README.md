# tasks/holdout/ — evaluation-only tasks

The **frozen** benchmark set. Tasks here are used **only** to evaluate, **never** to build or refine the knowledge under
test. Freeze the set before a benchmark batch and record it in the experiment definition.

First holdout (frozen in P4) must be small and **balanced**: code generation, API correctness, architecture, debugging,
and **at least one negative-control** task (where the knowledge is expected not to help). See `tasks/README.md` for the
schema and the leakage firewall (`contributes_to_notes`).
