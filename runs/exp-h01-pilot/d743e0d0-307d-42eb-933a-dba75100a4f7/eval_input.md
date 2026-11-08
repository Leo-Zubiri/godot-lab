Lifecycle, from the `[ref-07]` note (`_ready` runs once, after the node and its children are in the tree):

- **Created:** the `Timer` is built in `_ready()`, configured, added as a child, and started there. The 1-second countdown begins at that moment.
- **Callback:** `_on_timeout()` runs once, about 1 second later, when the timer's `timeout` signal fires during normal frame processing. It can land a frame or so late, not at exactly 1.000 s. `one_shot = true` stops the timer after that single emission. The signal wiring follows the `[ref-02]` note.
- **Cleanup:** the timer is a child of the node, so if the node is freed first, the callback never runs.

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

Cited notes: `[ref-07]`, `[ref-02]`, `[ref-06]` (4.7 scoping). Both lifecycle and signals notes are unverified, so treat them as unverified. I did not run this in Godot 4.7.
