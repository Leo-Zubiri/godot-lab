### script
```gdscript
# player.gd
extends CharacterBody2D

@export var speed: float = 300.0
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
	body_entered.connect(_on_overlap)
	area_entered.connect(_on_overlap)


func _on_overlap(other: Node) -> void:
	if _collected:
		return
	if not other.is_in_group("player"):
		return
	_collected = true
	set_deferred("monitoring", false)
	collected.emit()
	queue_free()
```

### explanation
**player.gd**
- `gravity` is read from `physics/2d/default_gravity`, so it follows the project setting. It is added to `velocity.y` scaled by `delta`, and only while `is_on_floor()` is false.
- The jump sets `velocity.y` to a negative value (up in 2D). It needs `is_action_just_pressed("jump")` and `is_on_floor()`, so there is no mid-air jump. The floor check uses the result of the previous frame's `move_and_slide()`.
- `Input.get_axis("move_left", "move_right")` gives the horizontal direction. With no input, `velocity.x` decelerates to zero via `move_toward`.
- `move_and_slide()` is called once per physics frame to apply `velocity` and collisions.

**coin.gd**
- `collected` is declared as a signal.
- `body_entered` is the normal path, because a `CharacterBody2D` is a physics body. `area_entered` is also connected, in case the player is represented by an Area2D. Both use the same handler.
- The `_collected` flag makes collection happen exactly once. It is set before `collected.emit()`, so a second overlap signal in the same frame, or one from a second player-group node, returns early.
- Only nodes in group `"player"` trigger collection.
- `set_deferred("monitoring", false)` stops further overlap signals. It is deferred because changing monitoring during a physics callback is not allowed.
- `queue_free()` removes the coin at the end of the frame.
- Any listener connected to `collected` runs synchronously before the coin is freed.

### references
none