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
- Gravity is read from `physics/2d/default_gravity` and added to `velocity.y` scaled by `delta` only while `is_on_floor()` is false. `is_on_floor()` reflects the previous `move_and_slide()` result, which is the usual pattern.
- Jump sets `velocity.y` to a negative value, because +y points down in 2D. It is gated by `is_on_floor()`, so there is no mid-air jump.
- Horizontal movement uses `Input.get_axis("move_left", "move_right")`. With no input, `velocity.x` is decelerated to 0 with `move_toward`.
- `move_and_slide()` takes no arguments in Godot 4. It uses the body's `velocity` property and updates it after collisions.

**coin.gd**
- The `collected` signal is declared on the coin.
- `body_entered` fires when a `PhysicsBody2D`, such as a `CharacterBody2D`, enters the area. The handler filters on `is_in_group("player")`.
- The `_collected` flag makes collection happen once. `queue_free()` only defers deletion to the end of the frame, so the signal could fire again in the same frame, for example if several bodies enter or the player has multiple overlapping shapes. The flag returns early in those cases, so `collected` is emitted once and `queue_free()` is called once.
- The flag is set before `collected.emit()`. A listener that re-enters the coin therefore cannot trigger a second collection.
- The code assumes the player is a physics body. If the player were an `Area2D`, you would also need to connect `area_entered`.
- The coin's `monitoring` is left at its default, which is true. The collision layers and masks are assumed to be set up by the project.

### references
- Godot docs: CharacterBody2D (`move_and_slide`, `is_on_floor`, `velocity`)
- Godot docs: Area2D (`body_entered` signal)
- Godot docs: Using CharacterBody2D/move_and_slide (platformer movement example)
- Godot docs: Node (`is_in_group`, `queue_free`)