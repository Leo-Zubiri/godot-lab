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

print(f"\nTOT: {P} passed, {F} failed")
sys.exit(1 if F else 0)
