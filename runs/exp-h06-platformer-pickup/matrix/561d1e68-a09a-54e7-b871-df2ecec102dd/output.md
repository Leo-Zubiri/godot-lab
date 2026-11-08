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
- Gravity is read from `physics/2d/default_gravity` (a float, default 980) and added to `velocity.y` scaled by `delta` only while `is_on_floor()` is false. Since Godot 2D uses +Y as down, the jump velocity is negative.
- Jumping uses `is_action_just_pressed("jump")` combined with `is_on_floor()`, so it happens only on the floor and only once per press.
- Horizontal input uses `Input.get_axis("move_left", "move_right")`, giving -1, 0 or 1 (or analog values). With no input, velocity decelerates to zero via `move_toward`.
- `move_and_slide()` is called once at the end of each physics frame. It applies `velocity`, handles sliding, and updates the floor state.

**coin.gd**
- `collected` is declared as a signal. `body_entered` is connected in `_ready()`. It fires for `PhysicsBody2D` nodes (such as a `CharacterBody2D`) that enter the area, which matches the player.
- The `_collected` flag guards against double collection. `queue_free()` only defers deletion to the end of the frame, so a second `body_entered` could fire before the node is gone. The flag makes the handler return early in that case, so `collected` is emitted and `queue_free()` is called exactly once.
- The signal is emitted before `queue_free()`, so listeners get it while the coin is still valid.
- If the player were an `Area2D` rather than a body, you would also need to connect `area_entered`. The task specifies a `CharacterBody2D` player, so only `body_entered` is needed.

### references
none