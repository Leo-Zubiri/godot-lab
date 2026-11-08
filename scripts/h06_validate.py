#!/usr/bin/env python3
"""h06 OBJECTIVE validation runner. For each generated run, extracts player.gd/coin.gd from the structured output and
runs the FIXED GUT harness (scripts/run_h06_tests.sh) to produce practical_validity OBJECTIVELY — independent of, and
never fed to, the blind quality evaluator. Writes a validation record per run and a summary.

practical_validity mapping (rubric): PASS -> 3, FAIL -> 0, INVALID/parse-fail/empty -> None (NA, recorded, not 0-coerced
unless it is a clear failure to produce usable code). Preserves every attempt.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h06_lib as L

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
GODOT_BIN = os.environ.get("GODOT_BIN", "/home/zub/.local/bin/godot-mono")

def validate_run(d):
    out = os.path.join(d, "output.md")
    if not os.path.exists(out):
        return None
    parsed = L.parse_structured_output(open(out, encoding="utf-8").read())
    files = L.extract_gdscript_files(parsed["script"])
    vdir = os.path.join(d, "validation"); os.makedirs(vdir, exist_ok=True)
    rec = {"has_player": "player.gd" in files, "has_coin": "coin.gd" in files}
    if "player.gd" not in files or "coin.gd" not in files:
        rec.update(verdict="INVALID", reason="missing deliverable file(s)", practical_validity=None)
        json.dump(rec, open(os.path.join(vdir, "validation.json"), "w"), indent=2)
        return rec
    tmp = tempfile.mkdtemp(prefix="h06-cand-")
    pf = os.path.join(tmp, "player.gd"); cf = os.path.join(tmp, "coin.gd")
    open(pf, "w").write(files["player.gd"]); open(cf, "w").write(files["coin.gd"])
    env = dict(os.environ, GODOT_BIN=GODOT_BIN, CAND_PLAYER=pf, CAND_COIN=cf, OUT=d)
    try:
        p = subprocess.run(["bash", os.path.join(SCRIPTS, "run_h06_tests.sh")],
                           env=env, capture_output=True, text=True, timeout=300)
        line = next((l for l in p.stdout.splitlines() if l.startswith("CANDIDATE:")), "")
        verdict = (re.search(r"verdict=(\w+)", line) or [None, "INVALID"])[1]
        reason = (re.search(r'reason="([^"]*)"', line) or [None, ""])[1]
        rec.update(verdict=verdict, reason=reason, harness_line=line,
                   practical_validity={"PASS": 3, "FAIL": 0}.get(verdict, None))
    except subprocess.TimeoutExpired:
        rec.update(verdict="INVALID", reason="validation timeout", practical_validity=None)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    json.dump(rec, open(os.path.join(vdir, "validation.json"), "w"), indent=2)
    return rec

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen-dir", default=os.path.join(ROOT, "runs/exp-h06-platformer-pickup/matrix"))
    args = ap.parse_args()
    if not os.path.isfile(GODOT_BIN) and not shutil.which(GODOT_BIN):
        print(f"ERROR: GODOT_BIN not found: {GODOT_BIN}"); sys.exit(2)
    summary = {}
    for d in sorted(glob.glob(os.path.join(args.gen_dir, "*"))):
        if not os.path.isdir(d):
            continue
        rid = os.path.basename(d)
        rec = validate_run(d)
        if rec is None:
            continue
        summary[rid] = {"verdict": rec["verdict"], "practical_validity": rec["practical_validity"], "reason": rec.get("reason", "")}
        print(f"{rid[:8]}: verdict={rec['verdict']} practical_validity={rec['practical_validity']} ({rec.get('reason','')})")
    json.dump(summary, open(os.path.join(args.gen_dir, "validation_summary.json"), "w"), indent=2)
    print(f"VALIDATION COMPLETE: {len(summary)} runs validated. Restore reference under_test/ after this.")

if __name__ == "__main__":
    main()
