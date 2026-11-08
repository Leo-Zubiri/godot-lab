### script
```gdscript
# player.gd
extends CharacterBody2D

const SPEED: float = 300.0
const JUMP_VELOCITY: float = -400.0


func _physics_process(delta: float) -> void:
	# Gravity is not automatic: apply it only while airborne.
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

var _is_collected: bool = false


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	if _is_collected:
		return
	if not body.is_in_group("player"):
		return
	_is_collected = true
	# Stop further overlap reports (deferred: physics state can't be changed mid-callback).
	set_deferred("monitoring", false)
	collected.emit()
	queue_free()
```

### explanation
**player.gd**
- All movement runs in `_physics_process`, so it uses the fixed timestep.
- Gravity is added to `velocity` only when `is_on_floor()` is false. `get_gravity()` returns the project's default 2D gravity vector, so it is multiplied by `delta`.
- The jump sets `velocity.y` to a negative value, because up is negative y in 2D. It checks `Input.is_action_just_pressed("jump")` and `is_on_floor()`, so holding the button doesn't re-trigger it and it can't fire in mid-air.
- `Input.get_axis("move_left", "move_right")` gives a value from -1 to 1, which is scaled by `SPEED` and written to `velocity.x`.
- `move_and_slide()` takes no arguments in Godot 4. It uses the `velocity` property and updates the floor state.
- `is_on_floor()` therefore reflects the previous frame's slide when it is read. This is the standard pattern.

**coin.gd**
- `collected` is declared as a signal. The `body_entered` signal is connected with the Godot 4 Callable form in `_ready()`.
- The handler returns early if the coin was already collected or if the body isn't in the `"player"` group.
- Collection happens exactly once because of three things:
  - The `_is_collected` flag is set before anything else happens, so a second `body_entered` in the same physics step is ignored.
  - `monitoring` is turned off with `set_deferred`, because changing monitoring during a physics callback is unsafe. This stops further overlap signals.
  - `queue_free()` defers the actual removal to the end of the frame, so the handler can still run again before then. That is why the flag is needed.
- `collected.emit()` fires before `queue_free()`, so listeners get the signal while the coin still exists.
- The scene, collision shapes, layers and masks, the `"player"` group and the input actions are assumed to be provided. I haven't run these scripts in Godot, so they are untested.

### references
/knowledge/notes/characterbody2d-movement.md
/knowledge/notes/area2d-detection.md
/knowledge/notes/input-handling.md