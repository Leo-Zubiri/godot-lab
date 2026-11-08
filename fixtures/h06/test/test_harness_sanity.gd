extends GutTest
## HARNESS SANITY — NOT candidate validation. Verifies the FIXTURE's collision layer/mask wiring using a BARE Area2D
## (no under_test/ candidate). Reported separately; EXCLUDED from candidate quality scores and candidate pass-rate.
## (I3: the collision-mask negative control tests the engine/fixture, not generated code, so it must not score candidates.)

var _spawned: Array = []
var _hits := 0

func after_each() -> void:
	for n in _spawned:
		if is_instance_valid(n):
			n.queue_free()
	_spawned.clear()
	await wait_physics_frames(1)

func _track(n: Node) -> void:
	add_child(n); _spawned.append(n)

func _on_body_entered(_b: Node2D) -> void:
	_hits += 1

func _make(area_mask: int) -> void:
	_hits = 0
	var body := StaticBody2D.new()
	body.collision_layer = 2; body.collision_mask = 0   # body on layer index 2 (value 2)
	var bcs := CollisionShape2D.new(); var br := RectangleShape2D.new(); br.size = Vector2(20, 40)
	bcs.shape = br; body.add_child(bcs); _track(body)
	var area := Area2D.new()
	area.collision_layer = 4; area.collision_mask = area_mask
	var acs := CollisionShape2D.new(); var ac := CircleShape2D.new(); ac.radius = 16.0
	acs.shape = ac; area.add_child(acs); _track(area)
	area.body_entered.connect(_on_body_entered)

func test_sanity_matching_mask_detects() -> void:
	_make(2)                 # mask value 2 includes the body's layer (idx2) -> detect
	await wait_physics_frames(3)
	assert_eq(_hits, 1, "fixture wiring: matching layer/mask DOES detect the body")

func test_sanity_nonmatching_mask_ignores() -> void:
	_make(8)                 # mask value 8 (idx4) excludes the body's layer -> no detect
	await wait_physics_frames(3)
	assert_eq(_hits, 0, "fixture wiring: non-matching layer/mask does NOT detect")
