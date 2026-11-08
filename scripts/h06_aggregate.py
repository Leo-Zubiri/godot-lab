#!/usr/bin/env python3
"""h06 v2 AGGREGATION (matrix). Joins, AFTER blind scoring, the condition<->run<->blind maps with: blind quality scores,
objective practical_validity (GUT), and provenance scores. Keeps the three STRICTLY SEPARATE (never averages GUT into the
blind quality vector; never feeds anything back to the evaluator). Writes results JSON + a Markdown summary.

N=5 per condition — EXPLORATORY. No statistical-significance claim is made or supported here.
"""
import argparse, csv, glob, json, os, statistics, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QDIMS = ["technical_correctness", "api_correctness", "version_compatibility", "architectural_quality",
         "requirement_fulfillment", "source_quality", "provenance", "hallucinations", "clarity"]
CONDS = ["A", "A_prime", "B"]

def load_map(path, k, v):
    m = {}
    if os.path.exists(path):
        for row in csv.DictReader(open(path)):
            m[row[k]] = row[v]
    return m

def mean(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return round(statistics.mean(xs), 3) if xs else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", default=os.path.join(ROOT, "runs/exp-h06-platformer-pickup/matrix"))
    ap.add_argument("--blind", default=os.path.join(ROOT, "runs/exp-h06-platformer-pickup/blind_quality"))
    ap.add_argument("--prov", default=os.path.join(ROOT, "runs/exp-h06-platformer-pickup/provenance"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results/exp-h06-platformer-pickup-matrix.json"))
    args = ap.parse_args()

    cond_of = load_map(os.path.join(args.matrix, "condition_map.csv"), "run_id", "condition")
    run_of_blind = load_map(os.path.join(args.blind, "blind_map.csv"), "blind_id", "run_id")

    runs = {}   # run_id -> record
    for d in sorted(glob.glob(os.path.join(args.matrix, "*"))):
        if not os.path.isdir(d):
            continue
        rid = os.path.basename(d)
        gen = json.load(open(os.path.join(d, "result.json"))) if os.path.exists(os.path.join(d, "result.json")) else {}
        val = json.load(open(os.path.join(d, "validation", "validation.json"))) if os.path.exists(os.path.join(d, "validation", "validation.json")) else {}
        runs[rid] = {"condition": cond_of.get(rid), "gen_status": gen.get("status"),
                     "resolved_model": gen.get("resolved_model"), "knowledge_read_count": gen.get("knowledge_read_count"),
                     "cost_usd": gen.get("cost_usd"),
                     "practical_validity": val.get("practical_validity"), "gut_verdict": val.get("verdict"),
                     "quality": None}

    # attach blind quality scores via blind_map (join happens only now, after scoring)
    for bd in sorted(glob.glob(os.path.join(args.blind, "*"))):
        sj = os.path.join(bd, "scores.json")
        if not os.path.isdir(bd) or not os.path.exists(sj):
            continue
        bid = os.path.basename(bd)
        rid = run_of_blind.get(bid)
        if rid in runs:
            sc = json.load(open(sj))
            runs[rid]["quality"] = sc.get("scores")
            runs[rid]["blind_id"] = bid

    # attach provenance (separate)
    for pd in sorted(glob.glob(os.path.join(args.prov, "*"))):
        pr = os.path.join(pd, "provenance_result.json")
        if not os.path.isdir(pd) or not os.path.exists(pr):
            continue
        rid = os.path.basename(pd)
        if rid in runs:
            p = json.load(open(pr))
            runs[rid]["provenance"] = p.get("provenance_scores")
            runs[rid]["references_empty"] = p.get("references_empty")

    # per-condition aggregates (kept separate)
    agg = {}
    for c in CONDS:
        rs = [r for r in runs.values() if r["condition"] == c]
        q = {dim: mean([(r["quality"] or {}).get(dim) for r in rs if r.get("quality")]) for dim in QDIMS}
        agg[c] = {
            "n": len(rs),
            "gen_status": {s: sum(1 for r in rs if r["gen_status"] == s) for s in sorted({r["gen_status"] for r in rs})},
            "practical_validity_mean": mean([r["practical_validity"] for r in rs]),
            "gut_pass": sum(1 for r in rs if r["gut_verdict"] == "PASS"),
            "quality_means": q,
            "quality_overall_mean": mean([v for v in q.values() if v is not None]),
            "mean_knowledge_reads": mean([r.get("knowledge_read_count") for r in rs]),
            "provenance_runs_with_refs": sum(1 for r in rs if r.get("references_empty") is False),
        }

    result = {"runs": runs, "by_condition": agg,
              "caveats": ["N=5 per condition is EXPLORATORY; no statistical significance.",
                          "Generator and evaluator are both Anthropic models (not provider-independent).",
                          "practical_validity is objective (GUT); quality is blind-evaluator; provenance is separate — never combined.",
                          "A' is an instruction+empty-dir placebo; see mean_knowledge_reads for A' retrieval attempts."]}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(result, open(args.out, "w"), indent=2)

    def row(label, fn):
        return "| %s | %s | %s | %s |" % (label, fn("A"), fn("A_prime"), fn("B"))
    md = ["# h06 matrix results (A / A' / B, N=5 each) — EXPLORATORY\n",
          "**No statistical-significance claim (N=5).** Quality (blind evaluator), practical_validity (objective GUT), "
          "and provenance are reported SEPARATELY.\n",
          "| metric | A | A' | B |", "|---|---|---|---|",
          row("n", lambda c: agg[c]["n"]),
          row("GUT PASS (practical validity)", lambda c: agg[c]["gut_pass"]),
          row("practical_validity mean", lambda c: agg[c]["practical_validity_mean"]),
          row("quality overall mean (blind)", lambda c: agg[c]["quality_overall_mean"]),
          row("mean knowledge reads", lambda c: agg[c]["mean_knowledge_reads"]),
          row("runs citing references", lambda c: agg[c]["provenance_runs_with_refs"]),
          "", "## Blind quality means per dimension", "| dimension | A | A' | B |", "|---|---|---|---|"]
    for dim in QDIMS:
        md.append(row(dim, lambda c, d=dim: agg[c]["quality_means"][d]))
    md += ["", "## Caveats"] + ["- " + c for c in result["caveats"]]
    open(os.path.splitext(args.out)[0] + ".md", "w").write("\n".join(md) + "\n")
    print("AGGREGATION COMPLETE ->", args.out, "and", os.path.splitext(args.out)[0] + ".md")
    print("\n".join(md[:12]))

if __name__ == "__main__":
    main()
