# Condition A′ — placebo (instruction + empty directory)

```yaml
condition: A_prime
label: placebo
knowledge_access: "empty-dir"       # same attach mechanism as B, but an EMPTY/irrelevant directory
retrieval_instruction: true         # identical retrieval instruction to B
web_access: "off"
record:                             # A' is an IMPERFECT placebo — capture these every run:
  - retrieval_attempts
  - files_accessed                  # expected: none meaningful
  - retrieval_time_tokens
  - empty_dir_detected              # did the agent notice the dir was empty?
notes: >
  Isolates the effect of the *instruction to retrieve* (A vs A′) from the effect of the *actual content* (A′ vs B).
  The empty dir must NOT reach cached/global/previously-loaded knowledge. Do not interpret A′−A as a pure instruction
  effect without reporting the fields above (an agent that detects emptiness and gives up is not a clean control).
```

Identical otherwise to [`batch-config.md`](batch-config.md).
