The timer is created in `_ready()`, which runs once the node enters the scene tree. `start()` begins the 1-second countdown there. Godot processes the timer each frame, and when it expires, `timeout` emits and calls `_on_timeout()` on the main thread. `one_shot = true` makes it fire only once, and the timer is freed with the node.

```gdscript
extends Node

var _timer: Timer

func _ready() -> void:
	_timer = Timer.new()
	_timer.one_shot = true
	_timer.wait_time = 1.0
	_timer.timeout.connect(_on_timeout)
	add_child(_timer)
	_timer.start()

func _on_timeout() -> void:
	print("Timeout fired once")
```

I haven't run this in Godot 4.7.2 here. It uses only standard Godot 4 APIs (`Timer`, `timeout.connect`, typed `func` signatures), so it should parse as written.
