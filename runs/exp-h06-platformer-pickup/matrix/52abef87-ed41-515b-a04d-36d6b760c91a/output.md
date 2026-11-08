### script
```gdscript
# player.gd
extends CharacterBody2D

@export var speed: float = 300.0
@export var jump_velocity: float = -400.0


func _physics_process(delta: float) -> void:
	# Gravity only while airborne.
	if not is_on_floor():
		velocity += get_gravity() * delta

	# Jump only when grounded.
	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = jump_velocity

	# Horizontal movement: -1, 0 or 1.
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
	# Guard: several bodies may enter in the same frame, or the signal may
	# fire again before the deferred free happens.
	if _collected:
		return
	if not body.is_in_group("player"):
		return

	_collected = true
	# Stop further detection. This must be deferred because we are inside
	# a physics callback, where changing monitoring state directly is blocked.
	set_deferred("monitoring", false)
	collected.emit()
	queue_free()
```

### explanation
**player.gd**
- `get_gravity()` returns the project's default 2D gravity vector (including any Area2D gravity override). It is added to `velocity` scaled by `delta` only when `is_on_floor()` is false, so a grounded body doesn't accumulate downward speed.
- The jump runs only when `Input.is_action_just_pressed("jump")` and `is_on_floor()` are both true. It sets `velocity.y` to a negative value, which is upward in Godot 2D. Because it needs a fresh press, holding the button doesn't re-trigger it.
- `Input.get_axis("move_left", "move_right")` gives the horizontal direction. When there is no input, `move_toward` brings `velocity.x` to zero.
- `move_and_slide()` applies `velocity`, resolves collisions, and updates the floor state used on the next frame.

**coin.gd**
- `body_entered` is connected in `_ready()`. The handler ignores any body that isn't in the `"player"` group.
- The `_collected` flag makes collection happen exactly once. `queue_free()` is deferred to the end of the frame, so a second `body_entered` could otherwise arrive before the node is removed, for example when two player bodies overlap in the same physics step.
- `set_deferred("monitoring", false)` also stops further detection. A direct assignment inside a physics callback would raise a "can't change state while flushing queries" error.
- `collected` is emitted before `queue_free()`. Connected listeners run synchronously, and the node is freed after the frame.
- If the player already overlaps the coin when it spawns, `body_entered` still fires on the first physics update, so the coin is collected then.
- The knowledge base directory `/knowledge` was empty, so no references were used.

### references
none