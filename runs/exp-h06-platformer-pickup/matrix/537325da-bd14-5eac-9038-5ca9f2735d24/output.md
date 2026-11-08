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

	# Jump only when on the floor.
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
	if not body_entered.is_connected(_on_body_entered):
		body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	if _collected:
		return
	if not body.is_in_group("player"):
		return

	_collected = true
	# Stop further overlap callbacks (deferred: we are inside a physics callback).
	set_deferred("monitoring", false)
	collected.emit()
	queue_free()
```

### explanation
**player.gd**
- `_physics_process` runs at the fixed physics rate. It adds `get_gravity() * delta` to `velocity` only when `is_on_floor()` is false. `get_gravity()` returns the project's default 2D gravity vector, or an `Area2D` gravity override if one applies.
- The jump sets `velocity.y` to a negative value, which is up in Godot 2D. It fires only when `Input.is_action_just_pressed("jump")` and `is_on_floor()` are both true, so there is no air jump and holding the button doesn't re-trigger it.
- `Input.get_axis("move_left", "move_right")` returns -1, 0 or 1 (or an analog value). Horizontal velocity is `direction * speed`, and it decays to 0 with `move_toward` when there is no input.
- `move_and_slide()` is called once per frame, after velocity is set. It moves the body, resolves collisions, and updates the floor state used on the next frame.

**coin.gd**
- The `collected` signal is declared at the top of the script.
- `_ready` connects `body_entered` in code, guarded by `is_connected` so a connection already made in the editor isn't duplicated. The player is a `CharacterBody2D`, so `body_entered` is the right signal.
- Collecting exactly once is enforced three ways:
  - The `_collected` flag is set before the signal is emitted. It blocks re-entrancy, such as a second body or a second callback in the same frame, and any handler that triggers another overlap.
  - `set_deferred("monitoring", false)` stops further overlap detection. It is deferred because changing monitoring during a physics callback is disallowed.
  - `queue_free()` removes the node at the end of the frame.
- Non-player bodies are ignored via `is_in_group("player")`. The group, collision layers and masks, and input actions are assumed to come from the project.

### references
none