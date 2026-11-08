### script
```gdscript
# player.gd
extends CharacterBody2D

const SPEED: float = 300.0
const JUMP_VELOCITY: float = -400.0


func _physics_process(delta: float) -> void:
	# Gravity only while airborne.
	if not is_on_floor():
		velocity += get_gravity() * delta

	# Jump only when grounded.
	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = JUMP_VELOCITY

	# Horizontal movement from the two actions (-1..1).
	var direction: float = Input.get_axis("move_left", "move_right")
	velocity.x = direction * SPEED

	move_and_slide()
```

```gdscript
# coin.gd
extends Area2D

signal collected

var _collected: bool = false


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	if _collected:
		return
	if not body.is_in_group("player"):
		return
	_collected = true
	# Stop further detection; deferred because we are inside a physics callback.
	set_deferred("monitoring", false)
	collected.emit()
	queue_free()
```

### explanation
**player.gd**
- All logic runs in `_physics_process(delta)`, the fixed-timestep callback appropriate for physics-driven movement.
- Gravity is not automatic on `CharacterBody2D`. It is added to the built-in `velocity` with `get_gravity() * delta` only when `is_on_floor()` is false. `get_gravity()` returns the project's 2D gravity.
- Jumping uses `Input.is_action_just_pressed("jump")` so it triggers once per press. It is gated by `is_on_floor()` and sets `velocity.y` to a negative value, because up is -Y in 2D.
- `Input.get_axis("move_left", "move_right")` gives -1..1 and is multiplied by `SPEED` to set `velocity.x`.
- `move_and_slide()` takes no arguments in Godot 4. It consumes `velocity`, resolves collisions and updates floor state. The floor check at the top of each frame therefore uses the result from the previous frame's move.

**coin.gd**
- `collected` is declared as a signal. `body_entered` is connected to a handler in `_ready()` using the Godot 4 `Callable` form.
- The handler ignores any body that is not in group `"player"`.
- The coin collects exactly once through three layers:
  - The `_collected` flag returns early on any repeat call. Several overlapping bodies, or several `body_entered` emissions in the same physics step, can reach the handler before the node is actually freed, because `queue_free()` is deferred to the end of the frame.
  - `set_deferred("monitoring", false)` stops further overlap detection. The change is deferred because changing monitoring during a physics callback is not allowed directly.
  - `queue_free()` then removes the node.
- Setting `_collected` before emitting means that if a `collected` listener somehow re-triggers the handler, it still cannot emit twice.
- The scene, collision shapes, layers and masks are assumed to be set up so that the coin's mask includes the player's layer.

### references
/knowledge/notes/characterbody2d-movement.md
/knowledge/notes/area2d-detection.md
/knowledge/notes/input-handling.md
/knowledge/sources/src-characterbody2d.md
/knowledge/sources/src-area2d.md