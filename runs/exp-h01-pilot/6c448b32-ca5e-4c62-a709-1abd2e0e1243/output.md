The knowledge base is usable. I read `AGENTS.md` and used these notes, all `status: proposed`:
- `node-lifecycle-callbacks`: `_ready` runs once, after the node and its children are in the tree.
- `gdscript-signals`: `.connect()` with a Callable, and `CONNECT_ONE_SHOT`.
- `godot-version-policy`: target Godot 4.7.2.

The KB does not cover `SceneTree.create_timer`, so that API comes from my own Godot 4 knowledge, not the KB. I could not parse-check the script because Bash was denied in this session.

**Lifecycle**
- **Created:** `_ready()` calls `create_timer(1.0)`. `_ready` runs once after this node and its children have entered the tree.
- **Ticking:** the timer starts when `create_timer` is called and is advanced by the SceneTree each frame.
- **Callback:** `_on_timeout()` runs once, about 1 second later. It runs when the timer's `timeout` signal fires during a frame, not synchronously. `CONNECT_ONE_SHOT` disconnects it after that single call.
- **Early free:** if the node is freed before 1 second elapses, the connection to the freed object should be dropped and the callback will not run. I believe Godot cleans up these connections automatically, but I have not verified it.

```gdscript
extends Node

func _ready() -> void:
	# One-shot: fires once after 1.0 s; CONNECT_ONE_SHOT disconnects after that call.
	get_tree().create_timer(1.0).timeout.connect(_on_timeout, CONNECT_ONE_SHOT)

func _on_timeout() -> void:
	print("1 second elapsed")
```
