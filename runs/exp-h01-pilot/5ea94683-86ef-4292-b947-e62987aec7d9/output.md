The knowledge base at `/home/zub/.claude/jobs/895f8671/tmp/empty-knowledge` is empty: no AGENTS.md and no notes/, so I'm proceeding without it and cite no note ids.

**Lifecycle**

- **Created:** `_ready()` runs once, when the node enters the scene tree. It creates the `Timer`, configures it, and adds it as a child. Starting it there begins the 1-second countdown.
- **Ticking:** The SceneTree advances the timer each frame.
- **Callback:** After about 1 second (accurate to within one frame), the timer emits `timeout` on the main thread, which calls `_on_timeout()`. `one_shot` stops the timer after it fires, and `CONNECT_ONE_SHOT` disconnects the callback, so it runs only once even if the timer is restarted.
- **Cleanup:** The timer is a child of the node, so it is freed with the node. If the node is freed before 1 second, the callback never runs.

```gdscript
extends Node

var _timer: Timer

func _ready() -> void:
	_timer = Timer.new()
	_timer.one_shot = true
	_timer.wait_time = 1.0
	_timer.timeout.connect(_on_timeout, CONNECT_ONE_SHOT)
	add_child(_timer)
	_timer.start()

func _on_timeout() -> void:
	print("Timeout fired once")
```

I haven't run this in Godot 4.7.2 here; it's written against the Godot 4 API.
