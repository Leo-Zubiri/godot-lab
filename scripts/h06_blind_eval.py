#!/usr/bin/env python3
"""h06 BLIND QUALITY evaluation runner (v2). DRY-RUN by default: builds the exact evaluator inputs (normalized
script+explanation + random blind id + identical rubric), runs a leakage scan on each, and writes them for review.
Does NOT call the evaluator. Real scoring (claude-opus-5-5) is gated behind --execute (refused: not authorized).

The evaluator receives ONLY: normalized script, normalized explanation, a random blind id, and the rubric. It never
receives references, condition labels, paths, note ids, generation metadata, original run ids, or execution order.
"""
import argparse, csv, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h06_lib as L

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUBRIC = os.path.join(ROOT, "rubrics/godot-eval-v0_1.md")

def load_generation(d):
    """A generation dir has config.json + output.md (structured). For the dry-run demo we also accept a raw output.md."""
    out = os.path.join(d, "output.md")
    return open(out, encoding="utf-8").read() if os.path.exists(out) else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen-dir", default=os.path.join(ROOT, "runs/exp-h06-platformer-pickup/dryrun"))
    ap.add_argument("--out", default=os.path.join(ROOT, "runs/exp-h06-platformer-pickup/blind_quality"))
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    run_ids = [os.path.basename(p) for p in glob.glob(os.path.join(args.gen_dir, "*")) if os.path.isdir(p)]
    blind = L.deterministic_blind_map(run_ids, seed="h06-blind")
    # mapping stored OUTSIDE evaluator inputs
    with open(os.path.join(args.out, "blind_map.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["blind_id", "run_id"])
        for rid, bid in sorted(blind.items(), key=lambda kv: kv[1]): w.writerow([bid, rid])

    rubric_text = open(RUBRIC, encoding="utf-8").read()   # identical rubric for every submission
    leaks_total = 0; built = 0; blocked = []
    import random
    order = sorted(blind.values()); random.Random("h06-eval-order").shuffle(order)  # eval order independent of gen order
    for rid, bid in blind.items():
        raw = load_generation(os.path.join(args.gen_dir, rid))
        if raw is None:
            continue
        parsed = L.parse_structured_output(raw)
        bd = os.path.join(args.out, bid); os.makedirs(bd, exist_ok=True)
        try:
            # build_evaluator_payload runs the leakage scan on the submission and RAISES before any API call
            payload = L.build_evaluator_payload(bid, parsed, rubric_text)
        except L.LeakageError as e:
            hits = L.leakage_scan(L.build_blind_quality_input(parsed))
            leaks_total += len(hits); blocked.append(bid)
            # record the block locally; do NOT write a payload file (nothing is eligible to be sent)
            json.dump({"blind_id": bid, "blocked": True, "leakage_hits": hits, "reason": str(e)},
                      open(os.path.join(bd, "meta.json"), "w"), indent=2)
            continue
        # payload.json == EXACTLY what would be sent to the evaluator (blind_id + rubric + normalized submission)
        open(os.path.join(bd, "payload.json"), "w").write(L.serialize_evaluator_payload(payload))
        # meta.json == LOCAL record only, NEVER sent: evaluator model id, leakage result, rubric path, mapping stays elsewhere
        json.dump({"blind_id": bid, "sent_to_evaluator": False, "leakage_hits": [],
                   "rubric": os.path.relpath(RUBRIC, ROOT), "evaluator_model_id": "claude-opus-5-5",
                   "note": "meta.json is a LOCAL record and is NEVER included in payload.json / sent to the evaluator"},
                  open(os.path.join(bd, "meta.json"), "w"), indent=2)
        built += 1

    print(f"blind-quality: built {built} evaluator payloads; eval_order (sample)={order[:5]}; "
          f"leakage_hits_total={leaks_total}; blocked={blocked}")
    if leaks_total:
        # fail CLOSED: a leak blocks submission before any evaluator API call is reachable
        print("!! LEAKAGE DETECTED — these submissions are blocked and will NOT be sent to the evaluator"); sys.exit(2)
    if not args.execute:
        print("DRY-RUN: payloads built + leakage-scanned; no evaluator call made.")
        return
    # --- EXECUTE blind quality scoring (opus-5-5), in the randomized eval order ---
    import h06_exec
    EVAL_MODEL = "claude-opus-5-5"
    DIMS = ["technical_correctness", "api_correctness", "version_compatibility", "architectural_quality",
            "requirement_fulfillment", "source_quality", "provenance", "hallucinations", "clarity"]
    # practical_validity is OMITTED: it is measured objectively by the GUT harness, never by the blind evaluator.
    INSTR = (
        "You are a strict, blind code reviewer for a Godot 4.7.2 GDScript task. You are given a JSON object with a "
        "`blind_id`, the scoring `rubric`, and a `submission` (### script + ### explanation only). Apply the rubric and "
        "score ONLY correctness and requirement fulfillment — NOT verbosity, length, or style. Do NOT score "
        "`practical_validity` (an external executable harness determines it); set it to null. `hallucinations` is "
        "reverse-scored (3 = none). Output ONLY one JSON object, no prose, exactly:\n"
        '{"blind_id":"<id>","scores":{%s},"justifications":{<same keys>:"<=15 words each"}}\n'
        "Each score is an integer 0-3 or null (NA). Base every score solely on the submission.\n\n"
        % ", ".join('"%s":<0-3|null>' % d for d in DIMS))
    done = 0
    for bid in order:                         # randomized evaluation order, independent of generation order
        bd = os.path.join(args.out, bid)
        pj = os.path.join(bd, "payload.json")
        if not os.path.exists(pj):            # blocked/leaked submissions have no payload -> not sent
            continue
        payload_text = open(pj, encoding="utf-8").read()
        prompt = INSTR + "\n" + payload_text
        res = h06_exec.run_claude_print(prompt, EVAL_MODEL, timeout_s=300)
        open(os.path.join(bd, "eval_stream.jsonl"), "w").write(res["raw_stream"])
        scores = L.parse_eval_json(res["result_text"] or "")
        rec = {"blind_id": bid, "evaluator_model_requested": EVAL_MODEL, "evaluator_model_resolved": res["resolved_model"],
               "scores": scores.get("scores"), "justifications": scores.get("justifications"),
               "parse_ok": scores.get("parse_ok"), "is_error": res["is_error"], "cost_usd": res["cost_usd"]}
        json.dump(rec, open(os.path.join(bd, "scores.json"), "w"), indent=2)
        done += 1
        print(f"  scored {bid}: model={res['resolved_model']} parse_ok={scores.get('parse_ok')} cost={res['cost_usd']}", flush=True)
    print(f"BLIND QUALITY COMPLETE: {done} submissions scored by {EVAL_MODEL} (practical_validity excluded by design).")

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
