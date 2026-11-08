#!/usr/bin/env python3
"""Shared execution helper: run `claude -p` as a fresh, isolated subprocess (ephemeral HOME, no tools, no web) and
return the parsed stream. Used by the evaluation runners (NOT the generator, which goes through the bwrap sandbox).
No knowledge is ever mounted here — evaluators only see the prompt they are given.
"""
import os, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h06_lib as L

SCRIPTS = os.path.dirname(os.path.abspath(__file__))

def run_claude_print(prompt: str, model: str, timeout_s: int = 300, budget_usd: float = 5.0) -> dict:
    """Fresh-session claude -p with NO tools and web disabled. Returns parse_stream_jsonl(...) plus raw_stream."""
    claude_bin = os.path.realpath(shutil.which("claude") or "")
    home = subprocess.check_output(["bash", os.path.join(SCRIPTS, "h06_mkhome.sh")], text=True).strip()
    env = dict(os.environ, HOME=home, DISABLE_AUTOUPDATER="1", CLAUDE_CODE_DISABLE_AUTO_MEMORY="1",
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1", DISABLE_TELEMETRY="1")
    cmd = [claude_bin, "-p", prompt, "--model", model,
           "--allowedTools", "",              # evaluator uses no tools
           "--disallowedTools", "WebSearch", "WebFetch",
           "--max-budget-usd", str(budget_usd),
           "--output-format", "stream-json", "--verbose"]
    try:
        p = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env, timeout=timeout_s)
        stream = p.stdout
        rc = p.returncode
    except subprocess.TimeoutExpired as e:
        stream = (e.stdout or "") if isinstance(e.stdout, str) else ""
        rc = 124
    finally:
        shutil.rmtree(home, ignore_errors=True)
    parsed = L.parse_stream_jsonl(stream)
    parsed["raw_stream"] = stream
    parsed["return_code"] = rc
    return parsed
