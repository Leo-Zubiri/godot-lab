extends Area2D
## Reference h06 coin. Collected exactly once when a node in group "player" overlaps.
signal collected
var _collected := false

func _ready() -> void:
	body_entered.connect(_on_body_entered)

func _on_body_entered(body: Node2D) -> void:
	if _collected:
		return
	if body.is_in_group("player"):
		_collected = true
		collected.emit()
		queue_free()
