extends Node

func _ready() -> void:
	# create_timer() returns a one-shot SceneTreeTimer. It emits "timeout" once after 1.0 s and then frees itself.
	get_tree().create_timer(1.0).timeout.connect(_on_timeout)

func _on_timeout() -> void:
	print("Timeout fired once")
