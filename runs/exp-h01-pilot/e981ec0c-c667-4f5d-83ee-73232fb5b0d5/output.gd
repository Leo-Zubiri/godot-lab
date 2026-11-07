extends Node

var _timer: Timer

func _ready() -> void:
	_timer = Timer.new()
	_timer.one_shot = true
	_timer.wait_time = 1.0
	_timer.timeout.connect(_on_timeout)
	add_child(_timer)
	_timer.start()

func _on_timeout() -> void:
	print("Timeout fired once")
