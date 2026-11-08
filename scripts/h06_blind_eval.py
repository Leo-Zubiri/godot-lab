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

    leaks_total = 0; built = 0
    import random
    order = sorted(blind.values()); random.Random("h06-eval-order").shuffle(order)  # eval order independent of gen order
    for rid, bid in blind.items():
        raw = load_generation(os.path.join(args.gen_dir, rid))
        if raw is None:
            continue
        parsed = L.parse_structured_output(raw)
        eval_input = L.build_blind_quality_input(parsed)     # script+explanation ONLY, normalized
        hits = L.leakage_scan(eval_input)
        leaks_total += len(hits)
        bd = os.path.join(args.out, bid); os.makedirs(bd, exist_ok=True)
        open(os.path.join(bd, "eval_input.md"), "w").write(eval_input)
        json.dump({"blind_id": bid, "leakage_hits": hits, "rubric": os.path.relpath(RUBRIC, ROOT),
                   "evaluator_model_id": "claude-opus-5-5"}, open(os.path.join(bd, "meta.json"), "w"), indent=2)
        built += 1

    print(f"DRY-RUN blind-quality: built {built} evaluator inputs; eval_order (sample)={order[:5]}; leakage_hits_total={leaks_total}")
    if leaks_total:
        print("!! LEAKAGE DETECTED in evaluator inputs — fix before any run"); sys.exit(2)
    if args.execute:
        print("REFUSED: --execute gated; blind quality evaluation not authorized."); sys.exit(3)

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
