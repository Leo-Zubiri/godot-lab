extends Node

var _timer: Timer

func _ready() -> void:
	_timer = Timer.new()
	_timer.one_shot = true
	_timer.wait_time = 1.0
	add_child(_timer)
	_timer.timeout.connect(_on_timeout, CONNECT_ONE_SHOT)
	_timer.start()

func _on_timeout() -> void:
	print("1 second elapsed: _on_timeout() called once")
