#!/usr/bin/env python3
"""h06 PROVENANCE evaluation runner (v2) — SEPARATE from blind quality, with SEPARATE records. DRY-RUN by default:
builds provenance inputs from the `references` field only and writes them. Does NOT call the evaluator; real scoring
is gated behind --execute (refused: not authorized).

Provenance evaluates references for: existence, relevance, claim-source correspondence, attribution correctness.
Provenance scores are NEVER combined with blind quality scores (separate dir, separate schema).
"""
import argparse, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h06_lib as L

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen-dir", default=os.path.join(ROOT, "runs/exp-h06-platformer-pickup/dryrun"))
    ap.add_argument("--out", default=os.path.join(ROOT, "runs/exp-h06-platformer-pickup/provenance"))
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    built = 0
    for d in glob.glob(os.path.join(args.gen_dir, "*")):
        if not os.path.isdir(d):
            continue
        rid = os.path.basename(d)
        out = os.path.join(d, "output.md")
        if not os.path.exists(out):
            continue
        parsed = L.parse_structured_output(open(out, encoding="utf-8").read())
        refs = parsed["references"].strip()
        # provenance keeps run_id (it is NOT blind — it is a separate, non-quality assessment of the references)
        rec = {"run_id": rid, "references_raw": refs,
               "references_empty": (refs == "" or refs.lower() == "none"),
               "dimensions": ["existence", "relevance", "claim_source_correspondence", "attribution_correctness"],
               "note": "separate from blind quality; scores NEVER combined with quality scores"}
        pd = os.path.join(args.out, rid); os.makedirs(pd, exist_ok=True)
        json.dump(rec, open(os.path.join(pd, "provenance_input.json"), "w"), indent=2)
        built += 1

    print(f"DRY-RUN provenance: built {built} provenance inputs (references only), separate records at {args.out}")
    if args.execute:
        print("REFUSED: --execute gated; provenance evaluation not authorized."); sys.exit(3)

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
