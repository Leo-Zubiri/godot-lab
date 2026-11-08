#!/usr/bin/env python3
"""h06 generation MATRIX runner (v2). DRY-RUN by default — builds prompts/config/mapping and writes them for review;
it does NOT call any model. Actual generation is gated behind --execute AND protocol execution_authorized (currently
false), so this script cannot start the 15-generation matrix.

Isolation per condition (knowledge path only; label/path never leak to A/A'). Delivered by scripts/h06_sandbox.sh
(bubblewrap unprivileged user+mount namespace), which makes the knowledge the ONLY per-condition difference and mounts
it read-only. --add-dir is NOT used for knowledge (it grants read+write; the hard boundary is the read-only bind):
  A       -> /knowledge NOT mounted (absent; unreachable via parent dirs, symlinks, env, inherited mounts)
  A_prime -> /knowledge = read-only bind of a verified-empty dir
  B       -> /knowledge = read-only bind of the pinned-SHA checkout (cannot be modified)
Fail-closed: if bwrap/unprivileged namespaces are unavailable, the sandbox exits 99 and runs nothing.
Preserves every planned attempt; condition<->run mapping is written OUTSIDE evaluator inputs.
"""
import argparse, csv, json, os, re, shutil, subprocess, sys, tempfile, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h06_lib as L

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
RO = "/home/zub/Documents/GODOT/godot-knowledge-ro-h06"
EMPTY = os.path.expanduser("~/.cache/h06-empty-knowledge")
PROTOCOL = os.path.join(ROOT, "conditions/protocol-v2.yaml")
N = 5
GEN_MODEL = "claude-sonnet-5-5"; EFFORT = "high"
IN_SANDBOX_KNOWLEDGE = "/knowledge"          # identical for A' and B; A has none
MAX_BUDGET_USD = 5.0; TIMEOUT_S = 600        # frozen per-run caps (see protocol-v2.yaml)

def knowledge_path(cond):
    return {"A": None, "A_prime": EMPTY, "B": RO}[cond]

def execution_authorized() -> bool:
    txt = open(PROTOCOL, encoding="utf-8").read()
    return bool(re.search(r"(?m)^execution_authorized:\s*true\b", txt))

def run_one_generation(r, out_dir):
    """Execute ONE sandboxed generation. Preserves every attempt (no retries). Returns a status dict."""
    cond = r["condition"]
    d = os.path.join(out_dir, r["run_id"]); os.makedirs(d, exist_ok=True)
    # prompt uses the IN-SANDBOX path (/knowledge) for A'/B; A has none. config.json already written by caller.
    prompt_kp = IN_SANDBOX_KNOWLEDGE if cond in ("A_prime", "B") else None
    prompt = L.build_generation_prompt(cond, open(os.path.join(d, "task_prompt.txt"), encoding="utf-8").read(), prompt_kp)
    open(os.path.join(d, "prompt.txt"), "w").write(prompt)

    claude_bin = os.path.realpath(shutil.which("claude") or "")
    home = subprocess.check_output(["bash", os.path.join(SCRIPTS, "h06_mkhome.sh")], text=True).strip()
    work = tempfile.mkdtemp(prefix="h06-work-")
    cargs = [claude_bin, "-p", prompt, "--model", GEN_MODEL, "--effort", EFFORT,
             "--allowedTools", "Read", "Glob", "Grep",
             "--disallowedTools", "WebSearch", "WebFetch",
             "--max-budget-usd", str(MAX_BUDGET_USD),
             "--output-format", "stream-json", "--verbose"]
    if cond in ("A_prime", "B"):
        cargs += ["--add-dir", IN_SANDBOX_KNOWLEDGE]
    env = dict(os.environ, H06_TOOLCHAIN="1", H06_HOME=home, H06_WORK=work,
               GODOT_KNOWLEDGE_RO=RO, APRIME_EMPTY=EMPTY)
    cmd = ["bash", os.path.join(SCRIPTS, "h06_sandbox.sh"), cond, "--"] + cargs

    status = "ok"
    try:
        with open(os.path.join(d, "stream.jsonl"), "w") as so, open(os.path.join(d, "gen.err"), "w") as se:
            p = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=so, stderr=se,
                               env=env, timeout=TIMEOUT_S)
        rc = p.returncode
        if rc in (98, 99):
            status = "isolation_fail"
    except subprocess.TimeoutExpired:
        rc = 124; status = "timeout"
    finally:
        shutil.rmtree(work, ignore_errors=True)
        shutil.rmtree(home, ignore_errors=True)

    stream = open(os.path.join(d, "stream.jsonl"), encoding="utf-8").read()
    parsed_stream = L.parse_stream_jsonl(stream)
    result_text = parsed_stream["result_text"] or ""
    open(os.path.join(d, "output.md"), "w").write(result_text)
    sections = L.parse_structured_output(result_text)
    if status == "ok":
        if not result_text.strip():
            status = "empty"
        elif parsed_stream["is_error"]:
            status = "error"
        elif sections["malformed"]:
            status = "malformed"
    rec = {"run_id": r["run_id"], "condition": cond, "trial": r["trial"], "order_index": r["order_index"],
           "status": status, "return_code": rc, "resolved_model": parsed_stream["resolved_model"],
           "requested_model": GEN_MODEL, "effort": EFFORT,
           "is_error": parsed_stream["is_error"], "subtype": parsed_stream["subtype"],
           "cost_usd": parsed_stream["cost_usd"], "duration_ms": parsed_stream["duration_ms"],
           "num_turns": parsed_stream["num_turns"], "malformed_contract": sections["malformed"],
           "knowledge_reads": parsed_stream["knowledge_reads"],
           "knowledge_read_count": len(parsed_stream["knowledge_reads"]),
           "all_file_reads": parsed_stream["file_reads"]}
    json.dump(rec, open(os.path.join(d, "result.json"), "w"), indent=2)
    return rec

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
        # prompt.txt written here reflects the IN-SANDBOX path for A'/B (what the model actually sees at run time)
        prompt_kp = IN_SANDBOX_KNOWLEDGE if r["condition"] in ("A_prime", "B") else None
        prompt = L.build_generation_prompt(r["condition"], task_prompt, prompt_kp)
        d = os.path.join(args.out, r["run_id"]); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "prompt.txt"), "w").write(prompt)
        open(os.path.join(d, "task_prompt.txt"), "w").write(task_prompt)   # frozen task text for the executor
        cfg = {"run_id": r["run_id"], "condition": r["condition"], "trial": r["trial"], "order_index": r["order_index"],
               "gen_model_id": GEN_MODEL, "effort": EFFORT, "web_access": "off",
               "isolation": "bwrap-ro-bind", "sandbox": "scripts/h06_sandbox.sh",
               "knowledge_mount": {"A": None, "A_prime": "/knowledge (ro, empty)", "B": "/knowledge (ro, pinned)"}[r["condition"]],
               "in_sandbox_knowledge_path": prompt_kp,
               "knowledge_host_path": kp, "knowledge_pin": "91250e6b2bd9e3966e7b22be94dea9bc2c263fae" if r["condition"] == "B" else None,
               "max_budget_usd": MAX_BUDGET_USD, "timeout_s": TIMEOUT_S, "preserve_attempt": True}
        json.dump(cfg, open(os.path.join(d, "config.json"), "w"), indent=2)

    print(f"Built {len(runs)} planned generations (A/A'/B x N={N}) + condition_map.csv at {args.out}")
    if not args.execute:
        print("DRY-RUN: no model calls. A prompts have NO retrieval clause/path; A'/B point at /knowledge.")
        return
    # --- EXECUTE (gated) ---
    if not execution_authorized():
        print("REFUSED: --execute given but protocol execution_authorized is not true."); sys.exit(3)
    os.makedirs(EMPTY, exist_ok=True)            # verified-empty A' dir
    summary = []
    for r in runs:   # runs is already in randomized order
        print(f"[{r['order_index']:>2}/{len(runs)}] generating run {r['run_id'][:8]} (order-randomized)...", flush=True)
        rec = run_one_generation(r, args.out)
        summary.append(rec)
        print(f"     -> status={rec['status']} model={rec['resolved_model']} turns={rec['num_turns']} "
              f"cost={rec['cost_usd']} kreads={rec['knowledge_read_count']}", flush=True)
    json.dump(summary, open(os.path.join(args.out, "generation_summary.json"), "w"), indent=2)
    oks = sum(1 for s in summary if s["status"] == "ok")
    print(f"MATRIX COMPLETE: {len(summary)} attempts preserved, {oks} well-formed. Summary at generation_summary.json")

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
