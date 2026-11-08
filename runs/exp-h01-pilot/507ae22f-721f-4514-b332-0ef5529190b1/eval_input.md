

```gdscript
extends Node

func _ready() -> void:
	# Creates a one-shot SceneTreeTimer and connects it so _on_timeout() runs once.
	get_tree().create_timer(1.0).timeout.connect(_on_timeout, CONNECT_ONE_SHOT)

func _on_timeout() -> void:
	print("Timeout fired after 1 second")
```

**Lifecycle**

- **Created:** `_ready()` runs once, after the node and its children have entered the tree. That is when `create_timer(1.0)` starts counting.
- **Callback:** After about 1 second, the timer emits `timeout` on a process frame, so the actual call can be up to one frame late. `_on_timeout()` runs once. `CONNECT_ONE_SHOT` also disconnects it after the first emission.
- **Cleanup:** The engine frees the SceneTreeTimer after it fires. If the node is freed before then, the connection is dropped and `_on_timeout()` is not called.
