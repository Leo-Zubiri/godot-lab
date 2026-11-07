extends Node

func _ready() -> void:
	# One-shot: fires once after 1.0 s; CONNECT_ONE_SHOT disconnects after that call.
	get_tree().create_timer(1.0).timeout.connect(_on_timeout, CONNECT_ONE_SHOT)

func _on_timeout() -> void:
	print("1 second elapsed")
