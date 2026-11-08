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

var _is_collected: bool = false


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	if _is_collected:
		return
	if not body.is_in_group("player"):
		return
	_is_collected = true
	# Stop further detection; deferred because we are inside a physics callback.
	set_deferred("monitoring", false)
	collected.emit()
	queue_free()
```

### explanation
**player.gd**
- All movement runs in `_physics_process(delta)`, so it uses the fixed timestep.
- Gravity is not automatic for `CharacterBody2D`. `get_gravity()` returns the project's default 2D gravity vector, and it is added to `velocity` scaled by `delta`. It is applied only when `is_on_floor()` is false. The floor state comes from the previous `move_and_slide()` call.
- Jumping uses `Input.is_action_just_pressed("jump")` combined with `is_on_floor()`. It sets `velocity.y` to a negative value, which is up in Godot's 2D coordinates. Holding the key does not re-trigger it, and it cannot fire in mid-air.
- `Input.get_axis("move_left", "move_right")` gives a value from -1 to 1. It is multiplied by `SPEED` and assigned to `velocity.x`.
- `move_and_slide()` takes no arguments in Godot 4. It reads and updates the built-in `velocity` and refreshes the floor state.

**coin.gd**
- `signal collected` is declared, and `body_entered` is connected to a handler with the Callable form in `_ready()`.
- The handler accepts only bodies in group `"player"`.
- "Exactly once" is enforced by two things:
  - The `_is_collected` flag makes the handler return early on any repeat call. This covers several bodies, or the same body entering again, in one physics step before the free is processed.
  - `set_deferred("monitoring", false)` stops further overlap detection. It is deferred because changing monitoring while physics signals are being flushed is not allowed.
- `collected.emit()` runs before `queue_free()`, so listeners are notified while the coin still exists. `queue_free()` then removes the node at the end of the frame.
- Layers, masks, collision shapes, the `"player"` group and the input actions are assumed to be set up by the scene or project, as the task specified.
- I did not run these scripts in Godot. The patterns come from the reference notes.

### references
/knowledge/notes/characterbody2d-movement.md
/knowledge/notes/area2d-detection.md
/knowledge/notes/gdscript-signals.md