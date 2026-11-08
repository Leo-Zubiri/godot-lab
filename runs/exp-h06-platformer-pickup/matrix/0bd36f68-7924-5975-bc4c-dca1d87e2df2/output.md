### script
```gdscript
# player.gd
extends CharacterBody2D

@export var speed: float = 300.0
@export var jump_velocity: float = -400.0  # negative Y is up in 2D


func _physics_process(delta: float) -> void:
	# Gravity while airborne.
	if not is_on_floor():
		velocity += get_gravity() * delta

	# Jump only when on the floor.
	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = jump_velocity

	# Horizontal movement.
	var direction := Input.get_axis("move_left", "move_right")
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
	# Stop further overlap detection immediately (deferred: we are inside a physics callback).
	set_deferred("monitoring", false)
	collected.emit()
	queue_free()
```

### explanation
**player.gd**
- `_physics_process` runs at the fixed physics rate, so gravity and movement are frame-rate independent.
- `get_gravity()` returns the project's default gravity vector, or an `Area2D` gravity override if one applies. `velocity += get_gravity() * delta` is applied only when `not is_on_floor()`.
- The jump sets `velocity.y` to a negative value, because up is negative Y in 2D. It requires `is_action_just_pressed("jump")` and `is_on_floor()`, so there is no mid-air jump and holding the key does not re-jump.
- `Input.get_axis("move_left", "move_right")` gives -1 to 1. With input, `velocity.x = direction * speed`. With none, `move_toward` decelerates to zero.
- `move_and_slide()` consumes `velocity` and updates the floor state. Gravity and jump are applied before it, so `is_on_floor()` reflects the previous move.

**coin.gd**
- The `collected` signal is declared and emitted once.
- `body_entered` is connected in `_ready()`. It fires when a `PhysicsBody2D`, such as the player's `CharacterBody2D`, enters the area. The handler filters on `body.is_in_group("player")`.
- Exactly-once is enforced in three ways:
  - The `_collected` flag makes any second `body_entered` call return early. Two bodies could enter in the same physics step before `queue_free()` runs at end of frame.
  - `set_deferred("monitoring", false)` stops further detection. It is deferred because changing monitoring during a physics callback is disallowed.
  - `queue_free()` removes the node at the end of the frame.
- `collected` is emitted before `queue_free()`, so listeners receive it while the coin is still valid.
- If the player were an `Area2D` instead, you would also connect `area_entered`. The task describes a `CharacterBody2D` player, so only `body_entered` is used.

### references
none