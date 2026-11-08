#!/usr/bin/env python3
"""h06 generation MATRIX runner (v2). DRY-RUN by default — builds prompts/config/mapping and writes them for review;
it does NOT call any model. Actual generation is gated behind --execute AND protocol execution_authorized (currently
false), so this script cannot start the 15-generation matrix.

Isolation per condition (knowledge path only; label/path never leak to A/A'):
  A       -> knowledge_path=None (no --add-dir, neutral cwd)
  A_prime -> empty dir
  B       -> read-only checkout at the pinned SHA
Preserves every planned attempt; condition<->run mapping is written OUTSIDE evaluator inputs.
"""
import argparse, csv, json, os, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h06_lib as L

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RO = "/home/zub/Documents/GODOT/godot-knowledge-ro-h06"
EMPTY = os.path.expanduser("~/.cache/h06-empty-knowledge")
N = 5
GEN_MODEL = "claude-sonnet-5-5"; EFFORT = "high"

def knowledge_path(cond):
    return {"A": None, "A_prime": EMPTY, "B": RO}[cond]

def build_matrix(seed="h06-v2"):
    import random
    rng = random.Random(seed)
    runs = []
    for cond in L.CONDITIONS:
        for trial in range(1, N + 1):
            runs.append({"run_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{seed}:{cond}:{trial}")),
                         "condition": cond, "trial": trial})
    rng.shuffle(runs)                       # randomized generation order
    for i, r in enumerate(runs, 1):
        r["order_index"] = i
    return runs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="attempt real generation (gated; refused unless authorized)")
    ap.add_argument("--out", default=os.path.join(ROOT, "runs/exp-h06-platformer-pickup/dryrun"))
    args = ap.parse_args()

    task_prompt = L.read_task_prompt(os.path.join(ROOT, "tasks/holdout/h06-platformer-pickup.md"))
    runs = build_matrix()
    os.makedirs(args.out, exist_ok=True)

    # condition<->run mapping: stored here, NEVER given to the evaluator
    with open(os.path.join(args.out, "condition_map.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["run_id", "condition", "trial", "order_index"])
        for r in runs: w.writerow([r["run_id"], r["condition"], r["trial"], r["order_index"]])

    for r in runs:
        kp = knowledge_path(r["condition"])
        prompt = L.build_generation_prompt(r["condition"], task_prompt, kp)
        d = os.path.join(args.out, r["run_id"]); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "prompt.txt"), "w").write(prompt)
        cfg = {"run_id": r["run_id"], "condition": r["condition"], "trial": r["trial"], "order_index": r["order_index"],
               "gen_model_id": GEN_MODEL, "effort": EFFORT, "web_access": "off",
               "knowledge_path": kp, "knowledge_pin": "91250e6b2bd9e3966e7b22be94dea9bc2c263fae" if r["condition"] == "B" else None,
               "add_dir": kp, "cwd": "neutral", "preserve_attempt": True}
        json.dump(cfg, open(os.path.join(d, "config.json"), "w"), indent=2)

    print(f"DRY-RUN: built {len(runs)} planned generations (A/A'/B x N={N}) + condition_map.csv at {args.out}")
    print("Condition A prompts contain NO retrieval clause and NO knowledge path; A'/B do (A'->empty, B->RO pin).")
    if args.execute:
        print("REFUSED: --execute is gated. The 15-generation matrix is NOT authorized (protocol execution_authorized=false).")
        sys.exit(3)

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
