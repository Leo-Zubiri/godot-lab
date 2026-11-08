#!/usr/bin/env python3
"""h06 OBJECTIVE validation runner. For each generated run, extracts player.gd/coin.gd from the ORIGINAL structured
output (never modifying the submission), records candidate SHA-256, and runs the FIXED GUT harness
(scripts/run_h06_tests.sh) to produce practical_validity OBJECTIVELY — independent of, and never fed to, the blind
quality evaluator. Writes a per-run validation record, a consolidated evidence/godot-execution/{runs.json,environment.json},
and copies GUT reports/logs into the evidence package. Preserves every attempt.

practical_validity: PASS -> 3, FAIL -> 0, INVALID/parse-fail/missing-file -> None (NA, recorded, not coerced to 0).
"""
import argparse, csv, glob, hashlib, json, os, re, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h06_lib as L

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
GODOT_BIN = os.environ.get("GODOT_BIN", "/home/zub/.local/bin/godot-mono")

def sha256(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()

def godot_version():
    try: return subprocess.check_output([GODOT_BIN, "--version"], text=True).strip().splitlines()[0]
    except Exception: return "unknown"

def gut_version():
    cfg = os.path.join(ROOT, "fixtures/h06/addons/gut/plugin.cfg")
    m = re.search(r'version="([^"]+)"', open(cfg).read()) if os.path.exists(cfg) else None
    return m.group(1) if m else "unknown"

def parse_h06_yaml(path):
    d = {}
    if os.path.exists(path):
        for line in open(path):
            m = re.match(r'(\w+):\s*"?([^"\n]*)"?', line.strip())
            if m: d[m.group(1)] = m.group(2)
    return d

def validate_run(d, evidence_dir):
    rid = os.path.basename(d)
    out = os.path.join(d, "output.md")
    if not os.path.exists(out): return None
    parsed = L.parse_structured_output(open(out, encoding="utf-8").read())
    files = L.extract_gdscript_files(parsed["script"])
    vdir = os.path.join(d, "validation"); os.makedirs(vdir, exist_ok=True)
    rec = {"run_id": rid, "godot_version": godot_version(), "gut_version": gut_version(), "godot_bin": GODOT_BIN,
           "has_player": "player.gd" in files, "has_coin": "coin.gd" in files,
           "player_sha256": sha256(files["player.gd"]) if "player.gd" in files else None,
           "coin_sha256": sha256(files["coin.gd"]) if "coin.gd" in files else None}
    if "player.gd" not in files or "coin.gd" not in files:
        rec.update(verdict="INVALID", reason="missing deliverable file(s)", practical_validity=None,
                   command=None, exit_code=None)
        json.dump(rec, open(os.path.join(vdir, "validation.json"), "w"), indent=2)
        return rec
    tmp = tempfile.mkdtemp(prefix="h06-cand-")
    pf = os.path.join(tmp, "player.gd"); cf = os.path.join(tmp, "coin.gd")
    open(pf, "w").write(files["player.gd"]); open(cf, "w").write(files["coin.gd"])
    # record candidate SHA again AFTER writing (prove unmodified end-to-end)
    rec["player_sha256_after"] = sha256(open(pf).read()); rec["coin_sha256_after"] = sha256(open(cf).read())
    cmd = f"GODOT_BIN={GODOT_BIN} CAND_PLAYER=<player.gd> CAND_COIN=<coin.gd> OUT={d} scripts/run_h06_tests.sh"
    rec["command"] = cmd
    env = dict(os.environ, GODOT_BIN=GODOT_BIN, CAND_PLAYER=pf, CAND_COIN=cf, OUT=d)
    try:
        p = subprocess.run(["bash", os.path.join(SCRIPTS, "run_h06_tests.sh")],
                           env=env, capture_output=True, text=True, timeout=300)
        rec["exit_code"] = p.returncode
        open(os.path.join(vdir, "harness_stdout.txt"), "w").write(p.stdout)
        open(os.path.join(vdir, "harness_stderr.txt"), "w").write(p.stderr)
        line = next((l for l in p.stdout.splitlines() if l.startswith("CANDIDATE:")), "")
        san = next((l for l in p.stdout.splitlines() if l.startswith("HARNESS_SANITY:")), "")
        rec["candidate_line"] = line; rec["harness_sanity_line"] = san
        y = parse_h06_yaml(os.path.join(vdir, "h06.yaml"))
        verdict = y.get("candidate_verdict") or (re.search(r"verdict=(\w+)", line) or [None, "INVALID"])[1]
        rec.update(verdict=verdict, reason=y.get("reason", ""),
                   tests=y.get("tests"), failures=y.get("failures"), skipped=y.get("skipped"),
                   risky=y.get("risky"), pending=y.get("pending"), crash=y.get("crash"),
                   harness_err=y.get("harness_err"), candidate_err=y.get("cand_err"),
                   harness_sanity=y.get("harness_sanity_verdict"),
                   practical_validity={"PASS": 3, "FAIL": 0}.get(verdict, None))
    except subprocess.TimeoutExpired:
        rec.update(verdict="INVALID", reason="validation timeout", practical_validity=None, exit_code=124)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    json.dump(rec, open(os.path.join(vdir, "validation.json"), "w"), indent=2)
    # copy reports/logs into the evidence package
    gdir = os.path.join(evidence_dir, "gut-reports"); ldir = os.path.join(evidence_dir, "logs")
    os.makedirs(gdir, exist_ok=True); os.makedirs(ldir, exist_ok=True)
    for src, dst in [(os.path.join(vdir, "gut_report.xml"), os.path.join(gdir, f"{rid}.xml")),
                     (os.path.join(vdir, "harness_stdout.txt"), os.path.join(ldir, f"{rid}.stdout.txt")),
                     (os.path.join(vdir, "gut_stdout.txt"), os.path.join(ldir, f"{rid}.gut.txt"))]:
        if os.path.exists(src): shutil.copy(src, dst)
    return rec

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen-dir", default=os.path.join(ROOT, "runs/exp-h06-platformer-pickup/matrix"))
    ap.add_argument("--evidence", default=os.path.join(ROOT, "experiments/exp-h06-platformer-pickup/evidence/godot-execution"))
    args = ap.parse_args()
    os.makedirs(args.evidence, exist_ok=True)
    cond = {r["run_id"]: r["condition"] for r in csv.DictReader(open(os.path.join(args.gen_dir, "condition_map.csv")))}
    json.dump({"godot_version": godot_version(), "godot_bin": GODOT_BIN, "gut_version": gut_version(),
               "fixture": "fixtures/h06", "harness": "scripts/run_h06_tests.sh",
               "verdict_rules": "PASS requires failures=0, skipped=0, risky=0, pending=0, no crash, no harness error, tests>0"},
              open(os.path.join(args.evidence, "environment.json"), "w"), indent=2)
    runs = []
    for d in sorted(glob.glob(os.path.join(args.gen_dir, "*"))):
        if not os.path.isdir(d): continue
        rec = validate_run(d, args.evidence)
        if rec is None: continue
        rec["condition"] = cond.get(rec["run_id"])   # local-only mapping (NOT in blind payload)
        runs.append(rec)
        print(f"{rec['run_id'][:8]} [{rec['condition']}]: verdict={rec['verdict']} pv={rec['practical_validity']} "
              f"tests={rec.get('tests')} fail={rec.get('failures')} ({rec.get('reason','')})")
    json.dump(runs, open(os.path.join(args.evidence, "runs.json"), "w"), indent=2)
    json.dump({r["run_id"]: {"verdict": r["verdict"], "practical_validity": r["practical_validity"]} for r in runs},
              open(os.path.join(args.gen_dir, "validation_summary.json"), "w"), indent=2)
    print(f"VALIDATION COMPLETE: {len(runs)} runs -> {args.evidence}/runs.json")

if __name__ == "__main__":
    main()
