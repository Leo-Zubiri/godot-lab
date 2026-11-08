#!/usr/bin/env python3
"""h06 PROVENANCE evaluation runner (v2) — SEPARATE from blind quality, with SEPARATE records. DRY-RUN by default:
builds provenance inputs from the `references` field only and writes them. Does NOT call the evaluator; real scoring
is gated behind --execute (refused: not authorized).

Provenance evaluates references for: existence, relevance, claim-source correspondence, attribution correctness.
Provenance scores are NEVER combined with blind quality scores (separate dir, separate schema).
"""
import argparse, glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h06_lib as L

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RO = "/home/zub/Documents/GODOT/godot-knowledge-ro-h06"
EVAL_MODEL = "claude-opus-5-5"

def find_cited_files(refs: str):
    """Objectively resolve each non-empty reference line to a file in the pinned knowledge checkout (existence check).
    Matches by basename stem against notes/ and sources/. Returns [{ref, exists, path, text}]."""
    out = []
    pool = glob.glob(os.path.join(RO, "notes", "*.md")) + glob.glob(os.path.join(RO, "sources", "*.md"))
    for line in refs.splitlines():
        ref = line.strip().lstrip("-* ").strip()
        if not ref or ref.lower() == "none":
            continue
        key = re.sub(r"\.md$", "", os.path.basename(ref)).lower()
        match = next((p for p in pool if key and key in os.path.basename(p).lower()), None)
        entry = {"ref": ref, "exists": bool(match), "path": (os.path.relpath(match, RO) if match else None)}
        entry["text"] = (open(match, encoding="utf-8").read()[:4000] if match else "")
        out.append(entry)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen-dir", default=os.path.join(ROOT, "runs/exp-h06-platformer-pickup/matrix"))
    ap.add_argument("--out", default=os.path.join(ROOT, "runs/exp-h06-platformer-pickup/provenance"))
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    built = 0; scored = 0
    exec_lib = None
    if args.execute:
        import h06_exec as exec_lib
    for d in sorted(glob.glob(os.path.join(args.gen_dir, "*"))):
        if not os.path.isdir(d):
            continue
        rid = os.path.basename(d)
        out = os.path.join(d, "output.md")
        if not os.path.exists(out):
            continue
        parsed = L.parse_structured_output(open(out, encoding="utf-8").read())
        refs = parsed["references"].strip()
        empty = (refs == "" or refs.lower() == "none")
        cited = [] if empty else find_cited_files(refs)
        rec = {"run_id": rid, "references_raw": refs, "references_empty": empty,
               "cited_count": len(cited),
               "cited": [{"ref": c["ref"], "exists": c["exists"], "path": c["path"]} for c in cited],
               "dimensions": ["existence", "relevance", "claim_source_correspondence", "attribution_correctness"],
               "note": "separate from blind quality; scores NEVER combined with quality scores"}
        pd = os.path.join(args.out, rid); os.makedirs(pd, exist_ok=True)
        json.dump(rec, open(os.path.join(pd, "provenance_input.json"), "w"), indent=2)
        built += 1

        if args.execute:
            if empty:
                rec["provenance_scores"] = None
                rec["provenance_note"] = "no references cited -> provenance NA (not scored, not 0)"
            else:
                srcblocks = "\n\n".join("REFERENCE: %s\nEXISTS_IN_KB: %s\nCONTENT:\n%s"
                                        % (c["ref"], c["exists"], c["text"] or "(not found in knowledge base)") for c in cited)
                prompt = (
                    "You assess the PROVENANCE of references a solution cited (separate from code quality). Given the "
                    "solution's EXPLANATION and the cited knowledge-base entries (with an objective existence flag), score "
                    "0-3 on: existence (do cited sources exist as given), relevance (do they pertain to the task), "
                    "claim_source_correspondence (do the explanation's claims actually match the sources), "
                    "attribution_correctness (are citations attributed to the right source). Output ONLY JSON: "
                    '{"scores":{"existence":<0-3>,"relevance":<0-3>,"claim_source_correspondence":<0-3>,'
                    '"attribution_correctness":<0-3>},"justifications":{<same keys>:"<=15 words"}}\n\n'
                    "EXPLANATION:\n" + parsed["explanation"][:4000] + "\n\nCITED ENTRIES:\n" + srcblocks)
                res = exec_lib.run_claude_print(prompt, EVAL_MODEL, timeout_s=300)
                open(os.path.join(pd, "prov_stream.jsonl"), "w").write(res["raw_stream"])
                pj = L.parse_eval_json(res["result_text"] or "")
                rec["provenance_scores"] = pj.get("scores")
                rec["provenance_justifications"] = pj.get("justifications")
                rec["parse_ok"] = pj.get("parse_ok")
                rec["evaluator_model_resolved"] = res["resolved_model"]
                rec["cost_usd"] = res["cost_usd"]
                scored += 1
            json.dump(rec, open(os.path.join(pd, "provenance_result.json"), "w"), indent=2)

    if not args.execute:
        print(f"DRY-RUN provenance: built {built} inputs (references only, existence pre-checked), at {args.out}")
        return
    print(f"PROVENANCE COMPLETE: {built} runs, {scored} with references scored by {EVAL_MODEL} (rest NA = no references).")

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
