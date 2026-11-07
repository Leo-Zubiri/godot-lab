---
id: h04-enter-tree-bug
category: debugging
difficulty: hard
expected_to_help: yes
executable_validation: parse+test
godot_version: "4.7.2-stable"
provenance: authored
contributes_to_notes: []
created: 2026-11-06
---

## Prompt
A developer reports that this Godot 4.7.2 script crashes with a "null instance" error. Diagnose the cause and provide a
corrected, parseable version, explaining the fix.

```gdscript
extends Node

func _enter_tree() -> void:
    $Label.text = "Hello"   # crashes here
```

(The node has a child `Label`.)

## Acceptance criteria (implementation-agnostic)
- Correctly identifies the cause: in `_enter_tree()` the node's **children are not guaranteed to be ready/available**, so
  `$Label` resolves to null; child access belongs in `_ready()` (which runs after all children have entered the tree).
- Provides a corrected script that accesses the child in `_ready()` (or otherwise guarantees the child exists).
- Corrected script parses cleanly for Godot 4.7.x.
- Explanation reflects the 4.7.x lifecycle ordering (`_enter_tree` top-down before children; `_ready` after children).

## Automated validation
- **parse:** `--check-only` on the corrected script must succeed.
- **test (GUT):** a small headless test instantiates the fixed scene/script and asserts the child is accessible and the
  text is set, without error. (A passing test confirms the fix runs; it does **not** grade the quality of the
  explanation — rubric does.)
