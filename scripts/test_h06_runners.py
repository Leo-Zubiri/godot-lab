#!/usr/bin/env python3
"""Tests for the h06 experimental runners (no model calls). Covers: prompt identity + isolation, structured parsing,
blind-input construction + anonymization, deterministic mapping, failed-run scoring, and ADVERSARIAL leakage attempts
(try to recover condition/path/note-ids from evaluator inputs). Run: python3 -I scripts/test_h06_runners.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h06_lib as L

P = F = 0
def check(name, cond):
    global P, F
    if cond: P += 1; print(f"  PASS  {name}")
    else: F += 1; print(f"  FAIL  {name}")

TASK = "Implement player.gd and coin.gd."

print("== prompt identity + isolation ==")
pa = L.build_generation_prompt("A", TASK, None)
pap = L.build_generation_prompt("A_prime", TASK, "/tmp/empty")
pb = L.build_generation_prompt("B", TASK, "/ro/knowledge")
check("A has NO retrieval clause", "reference knowledge base" not in pa)
check("A' HAS retrieval clause -> empty dir", "/tmp/empty" in pap and "reference knowledge base" in pap)
check("B HAS retrieval clause -> RO path", "/ro/knowledge" in pb)
check("condition label never in any prompt", not any(x in (pa+pap+pb) for x in ["condition A", "A_prime", "baseline", "placebo"]))
check("A/A'/B share the same TASK + contract", all("### references" in p and TASK in p for p in (pa, pap, pb)))
check("A prompt contains no knowledge path", "/tmp/empty" not in pa and "/ro/knowledge" not in pa)

print("== structured output parsing ==")
good = "### script\n```gdscript\nextends Node\n```\n### explanation\nIt works.\n### references\nnone\n"
g = L.parse_structured_output(good)
check("parses script/explanation/references", g["script"] and g["explanation"] and not g["malformed"])
bad = L.parse_structured_output("just some prose, no sections")
check("malformed output flagged", bad["malformed"])

print("== blind quality input: excludes references + anonymizes ==")
clean = ("### script\n```gdscript\nextends CharacterBody2D\nfunc _ready(): pass\n```\n"
         "### explanation\nUses move_and_slide and is_on_floor; gravity each physics frame.\n"
         "### references\ncharacterbody2d-movement\n")
ci = L.build_blind_quality_input(L.parse_structured_output(clean))
check("references field excluded from blind input", "characterbody2d-movement" not in ci and "### references" not in ci)
check("clean blind input has no leakage", L.leakage_scan(ci) == [])

print("== ADVERSARIAL: try to leak condition/path/note-ids via the explanation ==")
dirty = ("### script\n```gdscript\nextends CharacterBody2D\n```\n"
         "### explanation\nThis is condition B; I read the godot-knowledge note characterbody2d-movement "
         "(status: proposed) from /home/zub/Documents/GODOT/godot-knowledge-ro-h06.\n### references\nnone\n")
di = L.build_blind_quality_input(L.parse_structured_output(dirty))
hits = L.leakage_scan(di)
check("adversarial explanation leak DETECTED by scan", len(hits) > 0)

print("== ADVERSARIAL: tell hidden in a CODE COMMENT (normalizer keeps code verbatim) ==")
codetell = ("### script\n```gdscript\n# condition B: from /home/zub/.../godot-knowledge-ro-h06\nextends Node\n```\n"
            "### explanation\nok\n### references\nnone\n")
cti = L.build_blind_quality_input(L.parse_structured_output(codetell))
check("code-comment leak DETECTED by scan (guard, since code isn't normalized)", len(L.leakage_scan(cti)) > 0)

print("== deterministic blind mapping ==")
ids = ["r3", "r1", "r2", "r5", "r4"]
m1 = L.deterministic_blind_map(ids, "s")
m2 = L.deterministic_blind_map(list(reversed(ids)), "s")   # order-independent
check("mapping deterministic + order-independent", m1 == m2)
check("mapping is a bijection", sorted(m1.values()) == [f"q-{i:03d}" for i in range(1, 6)])
check("different seed -> different mapping", L.deterministic_blind_map(ids, "other") != m1)

print("== failed-run scoring rules ==")
check("timeout -> practical_validity 0, quality skipped", L.failure_scoring("timeout", "NA")["practical_validity"] == 0)
check("malformed -> practical_validity 0", L.failure_scoring("malformed", "NA")["practical_validity"] == 0)
check("ok+PASS -> practical_validity 3", L.failure_scoring("ok", "PASS")["practical_validity"] == 3)
check("ok+FAIL -> practical_validity 0, still counted", L.failure_scoring("ok", "FAIL")["practical_validity"] == 0 and L.failure_scoring("ok", "FAIL")["counts_in_pass_rate"])

print("== evaluator PAYLOAD audit: exact serialized contents (Requirement 2) ==")
RUBRIC = "# Godot rubric\nScore A / A' / B blind to condition. practical_validity anchored to GUT. Pinned model id recorded."
parsed_ok = L.parse_structured_output(clean)
payload = L.build_evaluator_payload("q-007", parsed_ok, RUBRIC)
# 1) EXACTLY the whitelisted fields — nothing else
check("payload keys are EXACTLY {blind_id, rubric, submission}", set(payload) == {"blind_id", "rubric", "submission"})
check("payload.blind_id is the random blind id", payload["blind_id"] == "q-007")
check("payload.rubric is the identical rubric text", payload["rubric"] == RUBRIC)
check("payload.submission has script + explanation sections", "### script" in payload["submission"] and "### explanation" in payload["submission"])
# 2) submission excludes references + is leak-free
check("payload.submission excludes ### references + note-ids", "### references" not in payload["submission"] and "characterbody2d-movement" not in payload["submission"])
check("payload.submission passes leakage scan", L.leakage_scan(payload["submission"]) == [])
# 3) the EXACT serialized bytes contain no forbidden metadata sentinels
ser = L.serialize_evaluator_payload(payload)
import json as _json
reparsed = _json.loads(ser)
check("serialized payload deserializes to EXACTLY the 3 fields", set(reparsed) == {"blind_id", "rubric", "submission"})
SENTINELS = ["claude-opus-5-5", "claude-sonnet-5-5", "/home/", "91250e6", "godot-knowledge-ro",
             "A_prime", "condition_map", "order_index", "run_id", "trial", "gut_", "leakage_hits",
             "evaluator_model_id", "validation_verdict"]
present = [s for s in SENTINELS if s in ser]
check(f"serialized payload contains NO metadata sentinels (found: {present})", present == [])
# 4) a metadata field cannot be smuggled in — serializer refuses an off-whitelist key
try:
    L.serialize_evaluator_payload({**payload, "evaluator_model_id": "claude-opus-5-5"})
    check("serializer REJECTS an extra metadata field", False)
except ValueError:
    check("serializer REJECTS an extra metadata field", True)
try:
    L.serialize_evaluator_payload({"blind_id": "q-1", "rubric": "r"})  # missing submission
    check("serializer REJECTS a missing field", False)
except ValueError:
    check("serializer REJECTS a missing field", True)
# 5) leakage in the candidate BLOCKS payload construction (pure function -> happens before any API call)
try:
    L.build_evaluator_payload("q-008", L.parse_structured_output(dirty), RUBRIC)
    check("build_evaluator_payload RAISES on a leaking submission (blocks before API)", False)
except L.LeakageError:
    check("build_evaluator_payload RAISES on a leaking submission (blocks before API)", True)
# 6) leak hidden in a code comment is also blocked
try:
    L.build_evaluator_payload("q-009", L.parse_structured_output(codetell), RUBRIC)
    check("code-comment leak also blocks payload construction", False)
except L.LeakageError:
    check("code-comment leak also blocks payload construction", True)

print("== GUT / practical_validity separation (authorized rubric correction) ==")
# practical_validity is produced OBJECTIVELY by failure_scoring (GUT/parse), independent of the blind evaluator
pv = L.failure_scoring("ok", "PASS")["practical_validity"]
check("practical_validity comes from the objective GUT verdict (ok+PASS -> 3)", pv == 3)
# build_evaluator_payload takes NO validation/GUT argument -> it is structurally impossible to pass GUT in
import inspect as _inspect
sig = set(_inspect.signature(L.build_evaluator_payload).parameters)
check("payload builder accepts no GUT/validation parameter", sig == {"blind_id", "parsed", "rubric_text"})
# even with a real PASS verdict on the run, nothing run-specific is injected: rubric stays byte-identical and the
# submission carries no verdict value (dimension NAMES in the fixed rubric are fine; a RESULT value is not)
payload2 = L.build_evaluator_payload("q-010", parsed_ok, RUBRIC)
ser2 = L.serialize_evaluator_payload(payload2)
import json as _json2
rp2 = _json2.loads(ser2)
check("payload.rubric is byte-identical to the fixed rubric (no run verdict injected)", rp2["rubric"] == RUBRIC)
check("payload.submission carries no GUT verdict value", not any(t in rp2["submission"] for t in ["PASS", "FAIL", "INVALID", "validation_verdict"]))

print("== candidate file extraction (for objective GUT validation) ==")
scr = ("### script\n"
       "```gdscript\nextends CharacterBody2D\nfunc _physics_process(d): move_and_slide()\n```\n"
       "```gdscript\nextends Area2D\nsignal collected\n```\n"
       "### explanation\nx\n### references\nnone\n")
files = L.extract_gdscript_files(L.parse_structured_output(scr)["script"])
check("extracts player.gd from CharacterBody2D block", "player.gd" in files and "CharacterBody2D" in files["player.gd"])
check("extracts coin.gd from Area2D block", "coin.gd" in files and "Area2D" in files["coin.gd"])
scr2 = "### script\n```gdscript\n# coin.gd\nextends Node\n```\n```gdscript\n# player.gd\nextends Node\n```\n### explanation\nx\n"
files2 = L.extract_gdscript_files(L.parse_structured_output(scr2)["script"])
check("filename comment classifies blocks", files2.get("coin.gd","").find("# coin.gd")>=0 and files2.get("player.gd","").find("# player.gd")>=0)

print("== stream-json parsing + mediator ==")
stream = ('{"type":"system","subtype":"init","model":"claude-sonnet-5-5"}\n'
          '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"/knowledge/notes/a.md"}}]}}\n'
          '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"/tmp/x"}}]}}\n'
          '{"type":"result","result":"### script\\n...","is_error":false,"subtype":"success","total_cost_usd":0.1,"duration_ms":1234,"num_turns":3}\n')
ps = L.parse_stream_jsonl(stream)
check("parses resolved model", ps["resolved_model"] == "claude-sonnet-5-5")
check("parses result/cost/turns", ps["cost_usd"] == 0.1 and ps["num_turns"] == 3 and ps["is_error"] is False)
check("mediator captures ONLY knowledge reads", ps["knowledge_reads"] == ["/knowledge/notes/a.md"])

print("== evaluator JSON parsing ==")
ej = L.parse_eval_json('here:\n```json\n{"blind_id":"q-1","scores":{"clarity":3}}\n```\n')
check("parses fenced evaluator JSON", ej["parse_ok"] and ej["scores"]["clarity"] == 3)
ej2 = L.parse_eval_json('{"scores":{"clarity":2}} trailing')
check("parses bare-object evaluator JSON", ej2["parse_ok"] and ej2["scores"]["clarity"] == 2)
check("flags unparseable evaluator output", L.parse_eval_json("no json here")["parse_ok"] is False)

print(f"\nTOT: {P} passed, {F} failed")
sys.exit(1 if F else 0)
