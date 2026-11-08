The script creates a one-shot `SceneTreeTimer` in `_ready()` and connects its `timeout` signal to `_on_timeout()`.

```gdscript
extends Node

func _ready() -> void:
	var timer: SceneTreeTimer = get_tree().create_timer(1.0)
	timer.timeout.connect(_on_timeout, CONNECT_ONE_SHOT)

func _on_timeout() -> void:
	print("Timeout fired")
```

**Lifecycle**
- **Creation:** `_ready()` runs once, when the node has entered the tree and its children are ready. `create_timer(1.0)` creates the timer at that moment and returns immediately; nothing blocks.
- **Waiting:** The timer is owned by the `SceneTree`, not by this node. It counts down over frames (idle time by default).
- **Callback:** After about 1 second, the timer emits `timeout` once on the main thread, which calls `_on_timeout()`. The timer is then released. `CONNECT_ONE_SHOT` also ensures the connection is removed after the first call.
- **Early removal:** If this node is freed before the timer elapses, Godot drops the connection automatically, so `_on_timeout()` is not called on a freed object.

I have not run this in Godot 4.7.2 here.
