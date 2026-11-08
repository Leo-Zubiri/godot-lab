extends Node2D
## AUXILIARY visual verification (NOT a correctness oracle; GUT is). Loads the ORIGINAL candidate scripts from
## res://under_test/{player,coin}.gd (copied in unmodified by the Python driver), renders a real window, drives input,
## and saves genuine engine screenshots at each gameplay state. Mirrors the GUT harness: input actions move_left/
## move_right/jump; layers ground=1/mask0, player=2/mask1(+group "player"), coin=4/mask2; SPEED/gravity are the
## candidate's own. Quits when done or on a safety cap so it never hangs.

const GROUND_Y := 180.0
var _shotdir := ""
var _runid := ""
var _collected := false
var _coin: Area2D = null
var _player: CharacterBody2D = null
var _manifest: Array = []

func _ready() -> void:
	_shotdir = OS.get_environment("H06_SHOT_DIR")
	_runid = OS.get_environment("H06_RUN_ID")
	for a in ["move_left", "move_right", "jump"]:
		if not InputMap.has_action(a):
			InputMap.add_action(a)
	# key events so the actions are real input actions (candidate may use is_action_just_pressed)
	_bind(KEY_LEFT, "move_left"); _bind(KEY_RIGHT, "move_right"); _bind(KEY_SPACE, "jump")
	_build_scene()
	_run.call_deferred()

func _bind(key: int, action: String) -> void:
	var ev := InputEventKey.new(); ev.keycode = key
	InputMap.action_add_event(action, ev)

func _label(txt: String, pos: Vector2) -> void:
	var l := Label.new(); l.text = txt; l.position = pos; l.add_theme_color_override("font_color", Color.WHITE)
	add_child(l)

func _build_scene() -> void:
	RenderingServer.set_default_clear_color(Color(0.12, 0.13, 0.18))
	# ground
	var ground := StaticBody2D.new()
	ground.collision_layer = 1; ground.collision_mask = 0; ground.position = Vector2(240, GROUND_Y + 40)
	var gcs := CollisionShape2D.new(); var gs := RectangleShape2D.new(); gs.size = Vector2(900, 40); gcs.shape = gs
	ground.add_child(gcs)
	var gvis := ColorRect.new(); gvis.size = Vector2(900, 40); gvis.position = Vector2(-450, -20)
	gvis.color = Color(0.25, 0.5, 0.3); ground.add_child(gvis)
	add_child(ground)
	# player (candidate script)
	var ps: Variant = load("res://under_test/player.gd")
	_player = CharacterBody2D.new(); _player.set_script(ps)
	_player.collision_layer = 2; _player.collision_mask = 1; _player.add_to_group("player")
	var pcs := CollisionShape2D.new(); var prect := RectangleShape2D.new(); prect.size = Vector2(24, 40); pcs.shape = prect
	_player.add_child(pcs)
	var pvis := ColorRect.new(); pvis.size = Vector2(24, 40); pvis.position = Vector2(-12, -20)
	pvis.color = Color(0.3, 0.6, 1.0); _player.add_child(pvis)
	_player.position = Vector2(120, 40)
	add_child(_player)
	# coin (candidate script)
	var cs: Variant = load("res://under_test/coin.gd")
	_coin = Area2D.new(); _coin.set_script(cs)
	_coin.collision_layer = 4; _coin.collision_mask = 2
	var ccs := CollisionShape2D.new(); var circ := CircleShape2D.new(); circ.radius = 14.0; ccs.shape = circ
	_coin.add_child(ccs)
	var cvis := Polygon2D.new(); var pts := PackedVector2Array()
	for i in range(16):
		var ang := TAU * i / 16.0; pts.append(Vector2(cos(ang), sin(ang)) * 14.0)
	cvis.polygon = pts; cvis.color = Color(1.0, 0.85, 0.2); _coin.add_child(cvis)
	_coin.position = Vector2(360, GROUND_Y - 20)
	if _coin.has_signal("collected"):
		_coin.collected.connect(func(): _collected = true)
	add_child(_coin)
	_label("h06 visual verification — run %s" % _runid, Vector2(8, 6))

func _shoot(name: String, caption: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := "%s/%s.png" % [_shotdir, name]
	img.save_png(path)
	_manifest.append({"file": name + ".png", "caption": caption,
		"player_pos": [_player.global_position.x, _player.global_position.y] if is_instance_valid(_player) else null,
		"player_on_floor": _player.is_on_floor() if is_instance_valid(_player) else null,
		"coin_present": is_instance_valid(_coin), "collected": _collected})

func _wait(frames: int) -> void:
	for i in range(frames):
		await get_tree().physics_frame

func _run() -> void:
	await get_tree().process_frame
	await _shoot("01_initial", "Initial scene: player (blue) spawned above ground, coin (gold) to the right")
	# fall to ground
	var guard := 0
	while is_instance_valid(_player) and not _player.is_on_floor() and guard < 180:
		await _wait(1); guard += 1
	await _shoot("02_grounded", "Player at rest on the ground (is_on_floor)")
	# jump
	Input.action_press("jump"); await _wait(1); Input.action_release("jump")
	await _wait(6)
	await _shoot("03_jump", "Player airborne during a jump")
	# land again
	guard = 0
	while is_instance_valid(_player) and not _player.is_on_floor() and guard < 180:
		await _wait(1); guard += 1
	# move right toward the coin
	Input.action_press("move_right")
	guard = 0
	var shot_approach := false
	while not _collected and is_instance_valid(_coin) and guard < 240:
		await _wait(1); guard += 1
		if not shot_approach and is_instance_valid(_player) and _player.global_position.x > 250:
			shot_approach = true
			await _shoot("04_approach", "Player moving right, approaching the coin")
	Input.action_release("move_right")
	await _wait(3)
	await _shoot("05_collected", "After overlap: 'collected' fired=%s, coin removed=%s" % [_collected, not is_instance_valid(_coin)])
	var f := FileAccess.open("%s/_manifest_shots.json" % _shotdir, FileAccess.WRITE)
	f.store_string(JSON.stringify({"run_id": _runid, "collected": _collected,
		"coin_removed": not is_instance_valid(_coin), "shots": _manifest}, "  "))
	f.close()
	get_tree().quit(0)
