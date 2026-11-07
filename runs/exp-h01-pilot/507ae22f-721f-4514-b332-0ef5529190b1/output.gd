extends Node

func _ready() -> void:
	# Creates a one-shot SceneTreeTimer and connects it so _on_timeout() runs once.
	get_tree().create_timer(1.0).timeout.connect(_on_timeout, CONNECT_ONE_SHOT)

func _on_timeout() -> void:
	print("Timeout fired after 1 second")
