### script
```gdscript
# player.gd
extends CharacterBody2D

@export var speed: float = 200.0
@export var jump_velocity: float = -400.0


func _physics_process(delta: float) -> void:
	# Gravity only while airborne.
	if not is_on_floor():
		velocity += get_gravity() * delta

	# Jump only from the floor.
	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = jump_velocity

	# Horizontal movement: -1, 0 or 1.
	var direction: float = Input.get_axis("move_left", "move_right")
	if direction != 0.0:
		velocity.x = direction * speed
	else:
		velocity.x = move_toward(velocity.x, 0.0, speed)

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
	# Stop further overlap detection (deferred: physics state is locked during signals).
	set_deferred("monitoring", false)
	collected.emit()
	queue_free()
```

### explanation
**player.gd**
- `_physics_process` runs on the fixed physics tick, so `delta` is the physics step.
- `get_gravity()` returns the gravity vector from the project's 2D physics settings, including any Area2D gravity override. It is added to `velocity` only when `is_on_floor()` is false, so gravity applies only while airborne.
- The jump sets `velocity.y` to a negative value, because up is negative Y in 2D. It requires `Input.is_action_just_pressed("jump")` and `is_on_floor()`, so there are no mid-air jumps.
- `Input.get_axis("move_left", "move_right")` returns -1, 0 or 1. Horizontal velocity is `direction * speed`, and it decelerates to 0 with `move_toward` when there is no input.
- `move_and_slide()` uses the body's `velocity` property, moves and slides along collisions, and updates the floor state for the next frame.

**coin.gd**
- The script connects `body_entered` in `_ready`. A `CharacterBody2D` is a physics body, so `body_entered` is the right signal.
- The handler ignores any body that is not in the `"player"` group.
- It sets the `_collected` flag before doing anything else, so re-entrant or duplicate callbacks return early. `collected` is emitted once and `queue_free()` is called once.
- `queue_free()` only frees the node at the end of the frame. Other bodies could overlap in the same frame and trigger the handler again, so the flag and `set_deferred("monitoring", false)` prevent that. The deferred setter is needed because changing monitoring during a physics callback is not allowed.
- `collected.emit()` comes before `queue_free()`, so listeners connected to the signal run while the coin is still valid.
- I have not run these scripts in the engine.

### references
none