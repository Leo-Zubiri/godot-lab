#!/usr/bin/env python3
"""h06 VISUAL verification (AUXILIARY evidence, NOT a correctness oracle — GUT is). For each run, extracts the ORIGINAL
candidate player.gd/coin.gd (never modifying the submission), records SHA-256 before AND after, copies them into an
isolated auxiliary Godot project, runs the real engine in a window under Xvfb, and saves genuine viewport screenshots of
the gameplay states. Writes evidence/visual/<cond>/<run_id>/ + a manifest. Clearly separate from the experiment.
"""
import argparse, csv, glob, hashlib, json, os, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h06_lib as L

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
PROJ = os.path.join(SCRIPTS, "h06_visual_proj")
GODOT_BIN = os.environ.get("GODOT_BIN", "/home/zub/.local/bin/godot-mono")
CONDDIR = {"A": "A", "A_prime": "A-prime", "B": "B"}

def sha256(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()

def godot_version():
    try: return subprocess.check_output([GODOT_BIN, "--version"], text=True).strip().splitlines()[0]
    except Exception: return "unknown"

def run_visual(rid, cond, gen_dir, out_root):
    d = os.path.join(gen_dir, rid)
    parsed = L.parse_structured_output(open(os.path.join(d, "output.md"), encoding="utf-8").read())
    files = L.extract_gdscript_files(parsed["script"])
    rec = {"run_id": rid, "condition": cond, "godot_version": godot_version(),
           "kind": "actual-running-engine-screenshot", "harness": "scripts/h06_visual_proj (auxiliary)"}
    if "player.gd" not in files or "coin.gd" not in files:
        rec.update(status="skipped", reason="missing deliverable file(s)")
        return rec
    rec["player_sha256_before"] = sha256(files["player.gd"]); rec["coin_sha256_before"] = sha256(files["coin.gd"])
    ut = os.path.join(PROJ, "under_test"); os.makedirs(ut, exist_ok=True)
    open(os.path.join(ut, "player.gd"), "w").write(files["player.gd"])
    open(os.path.join(ut, "coin.gd"), "w").write(files["coin.gd"])
    shotdir = os.path.join(out_root, CONDDIR[cond], rid); os.makedirs(shotdir, exist_ok=True)
    env = dict(os.environ, H06_SHOT_DIR=shotdir, H06_RUN_ID=rid)
    cmd = ["xvfb-run", "-a", "-s", "-screen 0 640x360x24",
           GODOT_BIN, "--path", PROJ, "--resolution", "480x270", "res://main.tscn"]
    try:
        p = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
        rec["exit_code"] = p.returncode
        open(os.path.join(shotdir, "godot_stdout.txt"), "w").write(p.stdout[-6000:])
        open(os.path.join(shotdir, "godot_stderr.txt"), "w").write(p.stderr[-6000:])
    except subprocess.TimeoutExpired:
        rec.update(status="timeout", reason="visual run exceeded 120s")
    # SHA after (prove the candidate files were not modified by the run)
    rec["player_sha256_after"] = sha256(open(os.path.join(ut, "player.gd")).read())
    rec["coin_sha256_after"] = sha256(open(os.path.join(ut, "coin.gd")).read())
    rec["unmodified"] = (rec["player_sha256_before"] == rec["player_sha256_after"]
                         and rec["coin_sha256_before"] == rec["coin_sha256_after"])
    shots = sorted(os.path.basename(x) for x in glob.glob(os.path.join(shotdir, "*.png")))
    rec["screenshots"] = shots; rec["screenshot_count"] = len(shots)
    sm = os.path.join(shotdir, "_manifest_shots.json")
    if os.path.exists(sm):
        try: rec["engine_state"] = json.load(open(sm))
        except Exception: pass
    rec.setdefault("status", "ok" if shots else "no-screenshots")
    return rec

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen-dir", default=os.path.join(ROOT, "runs/exp-h06-platformer-pickup/matrix"))
    ap.add_argument("--out", default=os.path.join(ROOT, "experiments/exp-h06-platformer-pickup/evidence/visual"))
    ap.add_argument("--runs", default="", help="comma-separated run_ids; default = all")
    args = ap.parse_args()
    if not shutil.which("xvfb-run"):
        print("ERROR: xvfb-run not available; cannot do offscreen visual verification."); sys.exit(2)
    os.makedirs(args.out, exist_ok=True)
    cond = {r["run_id"]: r["condition"] for r in csv.DictReader(open(os.path.join(args.gen_dir, "condition_map.csv")))}
    ids = [x for x in args.runs.split(",") if x] or [os.path.basename(p) for p in sorted(glob.glob(os.path.join(args.gen_dir, "*"))) if os.path.isdir(p)]
    manifest = []
    for rid in ids:
        if rid not in cond:
            continue
        rec = run_visual(rid, cond[rid], args.gen_dir, args.out)
        manifest.append(rec)
        print(f"{rid[:8]} [{cond[rid]}]: status={rec.get('status')} shots={rec.get('screenshot_count')} "
              f"collected={(rec.get('engine_state') or {}).get('collected')} unmodified={rec.get('unmodified')}")
    json.dump(manifest, open(os.path.join(args.out, "manifest.json"), "w"), indent=2)
    # clean the transient candidate files out of the aux project (harness stays, candidates do not persist)
    for fn in ("player.gd", "coin.gd"):
        fp = os.path.join(PROJ, "under_test", fn)
        if os.path.exists(fp): os.remove(fp)
    print(f"VISUAL COMPLETE: {len(manifest)} runs -> {args.out}/manifest.json")

if __name__ == "__main__":
    main()
