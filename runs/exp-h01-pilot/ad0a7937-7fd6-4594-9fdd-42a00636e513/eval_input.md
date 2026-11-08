

**Lifecycle**
- **Creation:** the Timer is created and added in `_ready()`. That runs once, after the node and its children have entered the tree, so `add_child` and `start()` are safe there (`[ref-07]`).
- **Callback:** the timer counts down through the scene tree's per-frame processing. `_on_timeout()` runs on the main thread in the first frame after 1 second has elapsed, so it's close to 1 second but not exact.
- **Exactly once:** `one_shot = true` stops the timer after it fires, and `CONNECT_ONE_SHOT` disconnects the handler after the first emission (`[ref-02]`).
- **Cleanup:** the Timer is a child of the node, so if the node leaves the tree before 1 second, the Timer is freed and the callback never runs.

```gdscript
extends Node

var _timer: Timer

func _ready() -> void:
	_timer = Timer.new()
	_timer.one_shot = true
	_timer.wait_time = 1.0
	add_child(_timer)
	_timer.timeout.connect(_on_timeout, CONNECT_ONE_SHOT)
	_timer.start()

func _on_timeout() -> void:
	print("1 second elapsed: _on_timeout() called once")
```

Sources: `[ref-07]` and `[ref-02]`, both unverified in the reference material and cited against Godot 4.7. `[ref-03]` (tested on 4.7.2) supports the typed `-> void` signature. So check the signatures against the official 4.7 docs if it matters.
