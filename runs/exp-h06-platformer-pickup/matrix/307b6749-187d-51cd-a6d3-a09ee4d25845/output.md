### script
```gdscript
# player.gd
extends CharacterBody2D

@export var speed: float = 200.0
@export var acceleration: float = 1600.0
@export var friction: float = 1600.0
@export var jump_velocity: float = -400.0


func _physics_process(delta: float) -> void:
	# Gravity while airborne
	if not is_on_floor():
		velocity += get_gravity() * delta

	# Jump only when on the floor
	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = jump_velocity

	# Horizontal movement
	var direction := Input.get_axis("move_left", "move_right")
	if direction != 0.0:
		velocity.x = move_toward(velocity.x, direction * speed, acceleration * delta)
	else:
		velocity.x = move_toward(velocity.x, 0.0, friction * delta)

	move_and_slide()
```

```gdscript
# coin.gd
extends Area2D

signal collected

var _is_collected: bool = false


func _ready() -> void:
	if not body_entered.is_connected(_on_body_entered):
		body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	if _is_collected:
		return
	if not body.is_in_group("player"):
		return

	_is_collected = true
	# Stop further detection immediately (deferred: physics is mid-flush).
	set_deferred("monitoring", false)
	set_deferred("monitorable", false)

	collected.emit()
	queue_free()
```

### explanation
**player.gd**
- `_physics_process` adds `get_gravity() * delta` to `velocity` only when `is_on_floor()` is false. `get_gravity()` reads the project's 2D default gravity, including any `Area2D` gravity override.
- A jump sets `velocity.y = jump_velocity`. The value is negative because +Y points down in 2D. It happens only if `is_action_just_pressed("jump")` and `is_on_floor()` are both true, so there are no air jumps and holding the key doesn't re-trigger it.
- `Input.get_axis("move_left", "move_right")` gives a value from -1 to 1. `move_toward` accelerates toward the target speed and applies friction when there is no input.
- `move_and_slide()` runs last. It uses the body's `velocity` and updates the floor state for the next frame.

**coin.gd**
- `collected` is declared as a signal. `body_entered` is connected in `_ready()`, with an `is_connected` guard.
- The handler returns early if the body is not in the `"player"` group. The `_is_collected` flag makes the collect logic run exactly once, even if several `body_entered` events arrive in the same physics step. This can happen when the player has multiple bodies or overlaps again before `queue_free()` takes effect at the end of the frame.
- On the first valid overlap the handler sets the flag, disables `monitoring` and `monitorable` with `set_deferred` (changing them directly during a physics callback is not allowed), emits `collected` once, and calls `queue_free()`.
- If the harness tests with a player that is an `Area2D` rather than a body, the same handler can also be connected to `area_entered`. The flag still guarantees a single collection.

### references
none