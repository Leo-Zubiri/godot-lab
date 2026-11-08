### script
```gdscript
# player.gd
extends CharacterBody2D

@export var speed: float = 200.0
@export var jump_velocity: float = -400.0

var gravity: float = ProjectSettings.get_setting("physics/2d/default_gravity")


func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y += gravity * delta

	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = jump_velocity

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
	collected.emit()
	queue_free()
```

### explanation
**player.gd**
- Gravity is read from `physics/2d/default_gravity` (a float setting, 980 by default) and added to `velocity.y` only while `is_on_floor()` is false, scaled by `delta`. Positive y points down in 2D, so `jump_velocity` is negative.
- The jump sets `velocity.y = jump_velocity`. It requires `is_action_just_pressed("jump")` and `is_on_floor()`. This means holding the key doesn't re-trigger it.
- `Input.get_axis("move_left", "move_right")` gives a value from -1 to 1. Horizontal velocity is `direction * speed`. With no input, it decelerates to 0 using `move_toward`.
- `move_and_slide()` takes no arguments in Godot 4. It uses the body's `velocity` property and updates `is_on_floor()` for the next frame.

**coin.gd**
- `body_entered` fires when a `PhysicsBody2D` (such as a `CharacterBody2D`) enters the area. It is connected in `_ready()`.
- The handler filters on `body.is_in_group("player")`. It then sets a `_collected` latch before emitting `collected` and calling `queue_free()`.
- The latch guarantees a single collection. `queue_free()` defers deletion to the end of the frame, so the signal could fire again for another overlapping body or a second player body in that same frame. The flag blocks that.
- `body_entered` is only emitted for bodies. If the player were an `Area2D`, you would also need `area_entered`. The task specifies a `CharacterBody2D` player, so only `body_entered` is needed.

### references
- Godot docs: CharacterBody2D (`move_and_slide`, `is_on_floor`, `velocity`)
- Godot docs: Area2D (`body_entered` signal)
- Godot docs: Input (`get_axis`, `is_action_just_pressed`)
- Godot docs: Node (`queue_free`, `is_in_group`)
- Godot docs: ProjectSettings (`physics/2d/default_gravity`)