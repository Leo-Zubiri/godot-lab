extends GutTest
## Fixed h06 CANDIDATE validation suite (identical across A/A'/B). Validates res://under_test/{player,coin}.gd.
## Deterministic: builds the scene in code, steps PHYSICS FRAMES (no wall-clock), asserts with tolerances.
##
## I2: candidate scripts are loaded at RUNTIME (not preload) with base-type guards, so a parse-broken candidate
##     produces a controlled, attributable test FAILURE instead of breaking this suite's own compilation.
##
## Collision config — LAYER INDEX vs BITMASK VALUE (value = 1 << (index-1)):
##   Ground: layer idx1 -> value 1 ; mask 0
##   Player: layer idx2 -> value 2 ; mask value 1 (collides with ground)
##   Coin  : layer idx3 -> value 4 ; mask value 2 (scans for the player layer)

const GROUND_TOP := 90.0
const REST_Y := 70.0

var _spawned: Array = []
var _collect_count := 0
var _player: Dictionary = {}   # {script, ok, msg}
var _coin: Dictionary = {}

func before_all() -> void:
	for a in ["move_left", "move_right", "jump"]:
		if not InputMap.has_action(a):
			InputMap.add_action(a)
	_player = _load_candidate("res://under_test/player.gd", "CharacterBody2D")
	_coin = _load_candidate("res://under_test/coin.gd", "Area2D")

func _load_candidate(path: String, expected_base: String) -> Dictionary:
	# Runtime load; a parse error yields null here (console error) WITHOUT breaking this test script.
	var res: Variant = load(path)
	if res == null or not (res is GDScript):
		return {"script": null, "ok": false, "msg": "candidate %s failed to load/parse" % path}
	var base := (res as GDScript).get_instance_base_type()
	if base != expected_base:
		return {"script": null, "ok": false, "msg": "candidate %s extends %s, expected %s" % [path, base, expected_base]}
	return {"script": res, "ok": true, "msg": "ok"}

func _on_collected() -> void:
	_collect_count += 1

func after_each() -> void:
	for a in ["move_left", "move_right", "jump"]:
		Input.action_release(a)
	for n in _spawned:
		if is_instance_valid(n):
			n.queue_free()
	_spawned.clear()
	await wait_physics_frames(1)

func _track(n: Node) -> void:
	add_child(n); _spawned.append(n)

func _rect(w: float, h: float) -> RectangleShape2D:
	var s := RectangleShape2D.new(); s.size = Vector2(w, h); return s

# Returns null player if the candidate player script is invalid (test should already have failed on the guard).
func _build(player_y: float, add_coin: bool) -> Dictionary:
	var ground := StaticBody2D.new()
	ground.collision_layer = 1; ground.collision_mask = 0; ground.position = Vector2(0, 100)
	var gcs := CollisionShape2D.new(); gcs.shape = _rect(8000, 20); ground.add_child(gcs)
	_track(ground)

	var player: CharacterBody2D = CharacterBody2D.new()
	player.set_script(_player["script"])
	player.collision_layer = 2; player.collision_mask = 1
	player.add_to_group("player")
	var pcs := CollisionShape2D.new(); pcs.shape = _rect(20, 40); player.add_child(pcs)
	player.position = Vector2(0, player_y)
	_track(player)

	var coin: Area2D = null
	if add_coin:
		coin = Area2D.new(); coin.set_script(_coin["script"])
		coin.collision_layer = 4; coin.collision_mask = 2
		var ccs := CollisionShape2D.new(); var circ := CircleShape2D.new(); circ.radius = 16.0
		ccs.shape = circ; coin.add_child(ccs); coin.position = Vector2(0, player_y)
		_track(coin)
	return {"player": player, "coin": coin}

func test_player_script_valid() -> void:
	assert_true(_player["ok"], _player["msg"])   # attributable to the candidate, not the harness

func test_gravity_pulls_down_in_air() -> void:
	if not _player["ok"]: return assert_true(false, _player["msg"])
	var p: CharacterBody2D = _build(-100.0, false)["player"]
	await wait_physics_frames(1)
	assert_false(p.is_on_floor(), "should start airborne")
	var y0 := p.global_position.y
	await wait_physics_frames(10)
	assert_gt(p.velocity.y, 0.0, "gravity should make velocity.y positive (downward)")
	assert_gt(p.global_position.y, y0, "player should fall (y increases downward)")

func test_lands_on_floor() -> void:
	if not _player["ok"]: return assert_true(false, _player["msg"])
	var p: CharacterBody2D = _build(40.0, false)["player"]
	await wait_physics_frames(30)
	assert_true(p.is_on_floor(), "player should land on the ground")
	assert_almost_eq(p.velocity.y, 0.0, 5.0, "vertical velocity ~0 once resting")

func test_horizontal_movement() -> void:
	if not _player["ok"]: return assert_true(false, _player["msg"])
	var p: CharacterBody2D = _build(REST_Y, false)["player"]
	await wait_physics_frames(2)
	var x0 := p.global_position.x
	Input.action_press("move_right")
	await wait_physics_frames(5)
	assert_almost_eq(p.velocity.x, 300.0, 1.0, "velocity.x should equal SPEED while moving right")
	assert_gt(p.global_position.x, x0, "player should move right (x increases)")

func test_jump_from_floor() -> void:
	if not _player["ok"]: return assert_true(false, _player["msg"])
	var p: CharacterBody2D = _build(REST_Y, false)["player"]
	await wait_physics_frames(3)
	assert_true(p.is_on_floor(), "precondition: on floor before jump")
	Input.action_press("jump")
	await wait_physics_frames(1)
	assert_lt(p.velocity.y, 0.0, "jump should give upward (negative y) velocity")
	assert_false(p.is_on_floor(), "player leaves the floor after jumping")

func test_coin_collected_exactly_once() -> void:
	if not _player["ok"]: return assert_true(false, _player["msg"])
	if not _coin["ok"]: return assert_true(false, _coin["msg"])
	_collect_count = 0
	var coin: Area2D = _build(REST_Y, true)["coin"]
	coin.collected.connect(_on_collected)
	await wait_physics_frames(3)
	assert_eq(_collect_count, 1, "coin collected exactly once")
	await wait_physics_frames(5)
	assert_eq(_collect_count, 1, "no repeated collection on subsequent physics frames")
	assert_false(is_instance_valid(coin), "coin removed after queue_free()")
