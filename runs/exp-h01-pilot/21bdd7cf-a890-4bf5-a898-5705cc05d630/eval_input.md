```gdscript
extends Node

func _ready() -> void:
	# create_timer() returns a one-shot SceneTreeTimer. It emits "timeout" once after 1.0 s and then frees itself.
	get_tree().create_timer(1.0).timeout.connect(_on_timeout)

func _on_timeout() -> void:
	print("Timeout fired once")
```

**Lifecycle:**
- **Created:** `_ready()` runs once, after the node and its children have entered the tree. That is when the timer is created and the connection is made.
- **Counting:** The SceneTree counts down the 1.0 s on each frame. By default it ticks even while the tree is paused and respects `Engine.time_scale`.
- **Callback:** When the time elapses, `timeout` emits during a process frame and `_on_timeout()` runs. The timer is one-shot, so it cannot fire again.
- **Early free:** If the node is freed before the timer elapses, the connection is dropped and the callback never runs.

I haven't run this in Godot 4.7.
