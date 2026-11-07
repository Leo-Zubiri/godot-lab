---
id: h03-cross-scene-state
category: architecture
difficulty: intermediate
expected_to_help: yes
executable_validation: none
godot_version: "4.7.2-stable"
provenance: authored
contributes_to_notes: []
created: 2026-11-06
---

## Prompt
In a Godot 4.7.2 game, the player's progress (coins, unlocked levels) must persist as the player moves between scenes.
Recommend where this state should live — a Node in the scene, a custom Resource, or an Autoload singleton — and justify
the choice, including trade-offs and at least one case where a different option would be better.

## Acceptance criteria (implementation-agnostic)
- Correctly explains the relevant Godot options (Node vs Resource vs Autoload) and what each is for in 4.7.x.
- Recommends a defensible option for **cross-scene persistence** (an Autoload is the idiomatic fit for live cross-scene
  state; a Resource is defensible for the serializable data it holds) and **justifies** it.
- Names concrete **trade-offs** (e.g. global coupling of autoloads; shared-by-reference caveat of Resources).
- Acknowledges when the alternative is better (shows it is not a one-size answer).
- Does not recommend putting everything in one global ("god autoload") without caveats.

## Automated validation
- **none** (architecture/judgment task). Score entirely on the rubric; `practical_validity` = NA.
- This is deliberately a non-executable task to test whether knowledge helps on **design reasoning**, not just code.
