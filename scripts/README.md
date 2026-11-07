# scripts/ — thin local wrappers (NO infrastructure)

Small, optional helper scripts only — not a framework, service, database, or orchestration system.

- **P4/P5 (manual pipeline):** a headless-Godot validation wrapper (parse + GUT) that writes results into a run's
  `validation/` in the `runs/` schema.
- **P7 (only after the pipeline is proven):** a `claude -p` batch driver that loops task × condition × trial in fresh
  isolated sessions, randomizes order, and captures `--output-format stream-json` into the **same** run-record schema —
  no schema change.

Keep wrappers dependency-light and reproducible. Record every variable on the command line / in `config.yaml`. Never
embed secrets; read them from `.env` (gitignored).
