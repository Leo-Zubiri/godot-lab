

```gdscript
extends Node

func _ready() -> void:
	var timer := get_tree().create_timer(1.0)
	timer.timeout.connect(_on_timeout, CONNECT_ONE_SHOT)

func _on_timeout() -> void:
	pass # Runs exactly once, 1 second after _ready().
```

**Lifecycle**
- **Creation:** `_ready()` runs once when the node enters the scene tree. That is when `create_timer(1.0)` starts counting.
- **Callback:** after about 1 second of ticks, the timer emits `timeout` on the main thread, which calls `_on_timeout()`. `CONNECT_ONE_SHOT` disconnects after the first emission. The `SceneTreeTimer` frees itself after it fires, so no reference needs to be kept.
- **Pause:** `create_timer` defaults to `process_always = true`, so the countdown continues while the tree is paused.

I did not run this in Godot 4.7.2, since no Godot binary was checked. It uses only standard Godot 4 APIs (`create_timer`, typed `:=`, `connect` with `CONNECT_ONE_SHOT`).
