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

	# Horizontal movement, -1..1 from the two actions.
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
	# queue_free() is deferred to the end of the frame, so several overlaps
	# can still reach this handler first. The flag makes collection one-shot.
	if _collected:
		return
	if not body.is_in_group("player"):
		return
	_collected = true
	# Physics state can't be changed during a signal callback, so defer this.
	set_deferred("monitoring", false)
	collected.emit()
	queue_free()
```

### explanation
**player.gd**
- All movement runs in `_physics_process(delta)`, so it uses the fixed timestep.
- Gravity is added to `velocity` as `get_gravity() * delta`, and only when `not is_on_floor()`. `get_gravity()` returns the project's default 2D gravity.
- Jumping sets `velocity.y` to a negative value, because up is negative Y in 2D. It requires `is_action_just_pressed("jump")` and `is_on_floor()`. Holding the button therefore doesn't re-trigger it, and it can't happen in the air.
- `Input.get_axis("move_left", "move_right")` returns a value in -1..1, which is scaled by `SPEED` and assigned to `velocity.x`.
- `move_and_slide()` takes no arguments in Godot 4. It uses the `velocity` property, moves the body, and updates the floor state for the next frame.

**coin.gd**
- `signal collected` is declared, and `body_entered` is connected with the Godot 4 Callable syntax in `_ready()`.
- The handler returns early for any body not in the `"player"` group.
- `_collected` is what guarantees exactly-once behavior. `queue_free()` only removes the node at the end of the frame. Without the flag, two overlap events in the same frame, for example from two player bodies, could emit `collected` twice.
- `set_deferred("monitoring", false)` stops further overlap reports. It is deferred because Godot doesn't allow changing monitoring state while physics callbacks are being flushed.
- `collected.emit()` fires before `queue_free()`, so listeners get the signal while the coin still exists.
- Layers, masks, the collision shapes and the `"player"` group are assumed to be set up by the scene, as the task states.
- I haven't run these scripts in Godot. The knowledge-base notes I used mark their claims as proposed and not yet validated in a lab.

### references
/knowledge/notes/characterbody2d-movement.md
/knowledge/notes/area2d-detection.md
/knowledge/notes/input-handling.md
/knowledge/notes/gdscript-signals.md