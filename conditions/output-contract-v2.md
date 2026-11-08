# Generation output contract — protocol v2

Introduced for protocol **v2** (h06 onward) to fix the v1 condition-leakage residuals at the **source** (no post-hoc
redaction of process narration). The **same contract, task, instructions, budgets and acceptance criteria apply to A, A′
and B** — only knowledge availability differs.

The generator must return exactly these three sections and nothing else (no process narration — no "I read…", no tool
remarks):

```
### script
<one or more ```gdscript code blocks — the deliverable files, e.g. player.gd and coin.gd>

### explanation
<technical explanation of the solution: behavior, APIs, lifecycle. No narration about tools, retrieval, or the author's process.>

### references
<the references actually used, one per line, or the single word: none>
```

Rules:
- **`references` may be empty** (write `none`). Conditions A/A′ have nothing to cite — **do not invent references**.
- Condition B lists the references it actually used — **do not strip real references**.
- **No process narration** anywhere in `script`/`explanation` (that was the v1 leak + redaction-artifact source).

## Evaluation separation (v2)
- **Blind quality evaluation** receives ONLY: `script` + `explanation` (passed through `scripts/normalize_for_eval.py`
  as a safety net), a **random blind ID**, and the identical rubric. It never receives `references`, condition labels,
  knowledge mappings, or experiment metadata.
- **Provenance evaluation** is a **separate** pass over `references` only: existence, relevance, claim-to-source
  correspondence, correctness of attribution. **Provenance scores are never combined with blind quality scores.**
- Original structured outputs are preserved untouched; normalized artifacts and both evaluations are stored separately.
- Reuse the leakage-audit tooling from `fe9d1eb` **without modifying** historical v1/v2 (pilot) results.
