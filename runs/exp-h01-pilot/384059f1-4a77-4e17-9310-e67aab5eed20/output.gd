extends Node

func _ready() -> void:
	var timer: SceneTreeTimer = get_tree().create_timer(1.0)
	timer.timeout.connect(_on_timeout, CONNECT_ONE_SHOT)

func _on_timeout() -> void:
	print("Timeout fired")
