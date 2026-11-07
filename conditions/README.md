# conditions/ — experimental condition specs

Each condition is a reusable spec describing exactly how a run is set up. The **only intended difference** between them
is knowledge access; every other variable is held identical (see [`batch-config.md`](batch-config.md)).

- [`A.md`](A.md) — **baseline**: no knowledge, no retrieval instruction, knowledge repo absent from disk.
- [`A-prime.md`](A-prime.md) — **placebo**: retrieval instruction + an **empty** knowledge dir.
- [`B.md`](B.md) — **knowledge-assisted**: retrieval instruction + read-only `godot-knowledge`.

[`batch-config.md`](batch-config.md) is the locked batch configuration (the P0 decision record).
