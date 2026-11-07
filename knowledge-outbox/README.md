# knowledge-outbox/ — staged candidate findings (consumer side)

Reusable Godot findings discovered during experiments/exploration are **staged here as raw candidates** — never written
directly into `godot-knowledge`. A **separate, authorized ingestion pass** (human, with write access to the knowledge
repo) later runs the template intake loop (search → dedupe → contradiction-check → preserve source → synthesize
`proposed` note → human review → `verified`). This is a *delivery mechanism*, not knowledge; candidates are never cited.

## Candidate schema
```yaml
---
id: <candidate-slug>
status: staged                      # staged -> ingested -> (proposed note in godot-knowledge) | discarded
discovered_in: <exp-id|exploration-task-id>
general_or_specific: general        # ONLY general, source-backed, reusable findings proceed to the knowledge base
reusable_why: <one line: why another Godot project benefits unchanged>
source_lead: <official doc URL / reproducible test that would back it>
godot_version: "4.7.2-stable"
created: <YYYY-MM-DD>
---

## Finding
<the candidate claim, in brief>

## Evidence lead
<what to preserve/verify during ingestion — NOT an assertion that it's verified>

## Routing note
<why this is general (belongs in godot-knowledge) and not experiment/project-specific>
```

**Guards:** an AI answer is not a source; an experiment is evidence only for what it tested; a **failed experiment can be
a valuable (anti-pattern/negative) finding**; a finding that only helps one benchmark is **overfit** — require it to
generalize.
