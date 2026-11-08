### script
```gdscript
# player.gd
extends CharacterBody2D

@export var speed: float = 200.0
@export var jump_velocity: float = -400.0

var gravity: float = ProjectSettings.get_setting("physics/2d/default_gravity")


func _physics_process(delta: float) -> void:
	# Gravity while airborne
	if not is_on_floor():
		velocity.y += gravity * delta

	# Jump only when on the floor
	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = jump_velocity

	# Horizontal movement
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
	collected.emit()
	queue_free()
```

### explanation
**player.gd**
- `gravity` is read from the project setting `physics/2d/default_gravity`, so it matches the project's physics configuration.
- `_physics_process` adds `gravity * delta` to `velocity.y` only when `is_on_floor()` is false. `is_on_floor()` reflects the result of the previous `move_and_slide()` call.
- A jump sets `velocity.y` to a negative value (up in 2D) only when `jump` is just pressed and the body is on the floor.
- `Input.get_axis("move_left", "move_right")` gives a value from -1 to 1. It sets horizontal velocity, and `move_toward` decelerates to a stop when there is no input.
- `move_and_slide()` applies `velocity` and handles collisions. In Godot 4 it uses the `velocity` property, so it takes no arguments.

**coin.gd**
- The script connects `body_entered`, which fires when a `PhysicsBody2D` such as a `CharacterBody2D` enters the area. Whether the area detects the player is set by the layers and masks the harness provides.
- The `_collected` flag makes collection happen exactly once. If several bodies enter in the same physics step, or the signal fires again before the node is freed, later calls return early.
- `queue_free()` defers deletion to the end of the frame. The flag guards that window, so `collected` cannot be emitted twice.
- The group check uses `is_in_group("player")`, so other bodies are ignored.

### references
- Godot 4 docs: CharacterBody2D (`move_and_slide`, `is_on_floor`, `velocity`)
- Godot 4 docs: Area2D (`body_entered` signal)
- Godot 4 docs: Input (`get_axis`, `is_action_just_pressed`)
- Godot 4 docs: Node (`queue_free`, `is_in_group`)