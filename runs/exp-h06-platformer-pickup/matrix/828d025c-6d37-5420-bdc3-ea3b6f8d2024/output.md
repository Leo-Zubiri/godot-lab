### script
```gdscript
# player.gd
extends CharacterBody2D

const SPEED: float = 300.0
const JUMP_VELOCITY: float = -400.0


func _physics_process(delta: float) -> void:
	# Gravity only while airborne.
	if not is_on_floor():
		velocity += get_gravity() * delta

	# Jump only when grounded.
	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = JUMP_VELOCITY

	# Horizontal movement from the two actions (-1..1).
	var direction: float = Input.get_axis("move_left", "move_right")
	velocity.x = direction * SPEED

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
	# Stop further overlap reports; deferred because physics state is locked during signal callbacks.
	set_deferred("monitoring", false)
	collected.emit()
	queue_free()
```

### explanation
**player.gd**
- All movement runs in `_physics_process(delta)`, so it uses the fixed physics timestep.
- Gravity is not automatic on `CharacterBody2D`. It is added as `get_gravity() * delta` only when `is_on_floor()` is false. `get_gravity()` returns the project's default 2D gravity.
- The jump sets `velocity.y` to a negative value, because up is negative Y in 2D. It requires `is_action_just_pressed("jump")` and `is_on_floor()`, so there is no mid-air jump and holding the key doesn't re-trigger it.
- `Input.get_axis("move_left", "move_right")` gives -1, 0 or 1. It is scaled by `SPEED` and written to `velocity.x`.
- `move_and_slide()` takes no arguments in Godot 4. It uses the `velocity` property and updates the floor state for the next frame.

**coin.gd**
- `collected` is declared as a signal and emitted with `collected.emit()`.
- `body_entered` is connected in `_ready()` with the Callable form.
- The handler checks `body.is_in_group("player")`, so only player bodies trigger collection.
- Collection happens exactly once because of a `_collected` flag:
  - The flag is set before `emit()`. If a listener re-enters, or a second body or a second `body_entered` arrives in the same physics step before the deferred free, the guard returns early.
  - `queue_free()` only removes the node at the end of the frame, so the flag is what covers the rest of that frame.
  - `set_deferred("monitoring", false)` also stops the area from reporting further overlaps. It is deferred because changing monitoring directly inside a physics callback is not allowed.
- The collision shape, layers and masks, the `"player"` group, and the input actions are assumed to be set up by the scene or project. If the signal never fires, a layer/mask mismatch is the usual cause.

### references
/knowledge/notes/characterbody2d-movement.md
/knowledge/notes/area2d-detection.md
/knowledge/notes/gdscript-signals.md