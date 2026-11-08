extends GutTest
## Fixed h06 harness (identical across A/A'/B). Validates scripts at res://under_test/{player,coin}.gd.
## Deterministic: builds the scene in code, steps PHYSICS FRAMES (never wall-clock), asserts with tolerances.
##
## Collision config — LAYER INDEX vs BITMASK VALUE (bit = 1 << (index-1)):
##   Ground: layer index 1 -> value 1 ; mask 0
##   Player: layer index 2 -> value 2 ; mask value 1 (collides with ground)
##   Coin  : layer index 3 -> value 4 ; mask value 2 (scans for the player layer)

const PLAYER := preload("res://under_test/player.gd")
const COIN := preload("res://under_test/coin.gd")
const GROUND_TOP := 90.0   # ground center y=100, half-height 10
const REST_Y := 70.0       # player half-height 20 -> rests at ground_top - 20

var _spawned: Array = []
var _collect_count := 0

func _on_collected() -> void:
	_collect_count += 1

func before_all() -> void:
	for a in ["move_left", "move_right", "jump"]:
		if not InputMap.has_action(a):
			InputMap.add_action(a)

func _track(n: Node) -> void:
	# Own teardown (not add_child_autofree): a node may self-free (coin queue_free) -> avoid double-free segfault.
	add_child(n)
	_spawned.append(n)

func after_each() -> void:
	for a in ["move_left", "move_right", "jump"]:
		Input.action_release(a)
	for n in _spawned:
		if is_instance_valid(n):
			n.queue_free()
	_spawned.clear()
	await wait_physics_frames(1)

func _rect(w: float, h: float) -> RectangleShape2D:
	var s := RectangleShape2D.new(); s.size = Vector2(w, h); return s

func _build(player_y: float, add_coin: bool, coin_mask: int = 2) -> Dictionary:
	var ground := StaticBody2D.new()
	ground.collision_layer = 1; ground.collision_mask = 0; ground.position = Vector2(0, 100)
	var gcs := CollisionShape2D.new(); gcs.shape = _rect(8000, 20); ground.add_child(gcs)
	_track(ground)

	var player: CharacterBody2D = CharacterBody2D.new()
	player.set_script(PLAYER)
	player.collision_layer = 2; player.collision_mask = 1
	player.add_to_group("player")
	var pcs := CollisionShape2D.new(); pcs.shape = _rect(20, 40); player.add_child(pcs)
	player.position = Vector2(0, player_y)
	_track(player)

	var coin: Area2D = null
	if add_coin:
		coin = Area2D.new(); coin.set_script(COIN)
		coin.collision_layer = 4; coin.collision_mask = coin_mask
		var ccs := CollisionShape2D.new(); var circ := CircleShape2D.new(); circ.radius = 16.0
		ccs.shape = circ; coin.add_child(ccs)
		coin.position = Vector2(0, player_y)   # overlap the player
		_track(coin)
	return {"ground": ground, "player": player, "coin": coin}

# --- Component tests ---
func test_gravity_pulls_down_in_air() -> void:
	var s := _build(-100.0, false)        # high above the floor
	var p: CharacterBody2D = s["player"]
	await wait_physics_frames(1)
	assert_false(p.is_on_floor(), "should start airborne")
	var y0 := p.global_position.y
	await wait_physics_frames(10)
	assert_gt(p.velocity.y, 0.0, "gravity should make velocity.y positive (downward)")
	assert_gt(p.global_position.y, y0, "player should fall (y increases downward)")

func test_lands_on_floor() -> void:
	var s := _build(40.0, false)          # just above rest, falls and lands
	var p: CharacterBody2D = s["player"]
	await wait_physics_frames(30)
	assert_true(p.is_on_floor(), "player should land on the ground")
	assert_almost_eq(p.velocity.y, 0.0, 5.0, "vertical velocity ~0 once resting")

func test_horizontal_movement() -> void:
	var s := _build(REST_Y, false)
	var p: CharacterBody2D = s["player"]
	await wait_physics_frames(2)
	var x0 := p.global_position.x
	Input.action_press("move_right")
	await wait_physics_frames(5)
	assert_almost_eq(p.velocity.x, 300.0, 1.0, "velocity.x should equal SPEED while moving right")
	assert_gt(p.global_position.x, x0, "player should move right (x increases)")

func test_jump_from_floor() -> void:
	var s := _build(REST_Y, false)
	var p: CharacterBody2D = s["player"]
	await wait_physics_frames(3)                # settle on floor
	assert_true(p.is_on_floor(), "precondition: on floor before jump")
	Input.action_press("jump")
	await wait_physics_frames(1)
	assert_lt(p.velocity.y, 0.0, "jump should give upward (negative y) velocity")
	assert_false(p.is_on_floor(), "player leaves the floor after jumping")

func test_coin_requires_matching_mask() -> void:
	# NEGATIVE control: coin masks a layer the player is NOT on -> no detection.
	var s := _build(REST_Y, true, 8)   # mask value 8 (index 4), player is layer 2
	var coin: Area2D = s["coin"]
	watch_signals(coin)
	await wait_physics_frames(3)
	assert_signal_emit_count(coin, "collected", 0, "coin must NOT collect when layer/mask don't match")
	assert_true(is_instance_valid(coin), "coin remains when not collected")

# --- Integration test ---
func test_coin_collected_exactly_once() -> void:
	_collect_count = 0
	var s := _build(REST_Y, true, 2)   # mask value 2 -> scans player layer 2
	var coin: Area2D = s["coin"]
	coin.collected.connect(_on_collected)   # plain method, no watch_signals/lambda on a self-freeing node
	await wait_physics_frames(3)
	assert_eq(_collect_count, 1, "coin collected exactly once")
	await wait_physics_frames(5)        # more frames must NOT re-collect
	assert_eq(_collect_count, 1, "no repeated collection on subsequent physics frames")
	assert_false(is_instance_valid(coin), "coin removed after queue_free()")
