#!/usr/bin/env python3
"""h06 experiment v2 — shared, testable construction logic (no model calls here).

Single source of truth for: the generation prompt (identical across conditions except the knowledge clause),
the output contract, structured-output parsing, blind-eval input construction (script+explanation only, normalized,
no references/labels/paths/ids/metadata), deterministic condition<->blind mapping, failure scoring, and a leakage scan.

Importable by the runners and the test suite. Keep execution (claude -p / godot) in the runner wrappers.
"""
from __future__ import annotations
import hashlib, importlib.util, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
CONDITIONS = ["A", "A_prime", "B"]

# --- frozen prompt pieces (protocol v2) ---
GENERAL = ("You are assisting with a Godot 4.7.2 GDScript project. Complete the task. "
           "Return EXACTLY three sections and nothing else, with no narration about your process, tools, or sources:\n"
           "### script\n(one or more ```gdscript code blocks: the deliverable files)\n"
           "### explanation\n(technical explanation only)\n"
           "### references\n(references actually used, one per line, or the single word: none)\n")

def retrieval_clause(knowledge_path: str) -> str:
    # Used ONLY for A' (empty dir) and B (read-only knowledge). Never names the condition.
    return ("A reference knowledge base is available (read-only) at the attached directory: %s . "
            "Before answering you may read its AGENTS.md and notes; cite any references you actually use in "
            "### references. If it is empty or unhelpful, write 'none' and proceed." % knowledge_path)

def build_generation_prompt(condition: str, task_prompt: str, knowledge_path: str | None) -> str:
    """Identical base for all conditions; only A'/B add the retrieval clause. Condition label never appears."""
    assert condition in CONDITIONS
    parts = [GENERAL]
    if condition in ("A_prime", "B"):
        assert knowledge_path, "A'/B require a knowledge_path (A' empty dir, B read-only checkout)"
        parts.append(retrieval_clause(knowledge_path))
    # condition A: no retrieval clause, no knowledge path
    parts.append("TASK:\n" + task_prompt)
    return "\n\n".join(parts)

def read_task_prompt(task_md_path: str) -> str:
    txt = open(task_md_path, encoding="utf-8").read()
    m = re.search(r"##\s*Prompt.*?\n(.*?)(?:\n##\s|\Z)", txt, re.S)
    return (m.group(1).strip() if m else txt.strip())

# --- structured output parsing ---
def parse_structured_output(text: str) -> dict:
    """Split a generation into {script, explanation, references, malformed:bool}."""
    def section(name: str) -> str:
        m = re.search(r"(?mi)^###\s*%s\s*\n(.*?)(?=^###\s|\Z)" % name, text, re.S)
        return (m.group(1).strip() if m else "")
    script, expl, refs = section("script"), section("explanation"), section("references")
    malformed = not (script and expl)  # references may be empty/none
    return {"script": script, "explanation": expl, "references": refs, "malformed": malformed}

# --- blind-eval input construction (quality) ---
def _normalizer():
    spec = importlib.util.spec_from_file_location("nfe", os.path.join(HERE, "normalize_for_eval.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def build_blind_quality_input(parsed: dict) -> str:
    """ONLY script + explanation, normalized (code verbatim, note-ids/paths anonymized). NO references, NO condition,
    NO paths/run-ids/metadata. This is all the blind quality evaluator sees (plus a random blind id + the rubric)."""
    nfe = _normalizer()
    doc = "### script\n" + parsed["script"] + "\n\n### explanation\n" + parsed["explanation"] + "\n"
    normalized, _log = nfe.normalize(doc)
    return normalized

# --- deterministic condition<->blind mapping (stored OUTSIDE evaluator inputs) ---
def deterministic_blind_map(run_ids: list[str], seed: str) -> dict:
    """Stable, reproducible blind-id assignment independent of generation order. Kept in a mapping file the
    evaluator never receives. Order is derived from a hash(seed, run_id) sort -> deterministic shuffle."""
    ordered = sorted(run_ids, key=lambda r: hashlib.sha256((seed + "|" + r).encode()).hexdigest())
    return {rid: "q-%03d" % (i + 1) for i, rid in enumerate(ordered)}

# --- failure scoring rules (defined BEFORE execution) ---
def failure_scoring(gen_status: str, validation_verdict: str) -> dict:
    """Deterministic treatment of failed/invalid outputs. Every attempt is preserved and scored (never dropped)."""
    # gen_status: ok | timeout | malformed | empty ; validation_verdict: PASS | FAIL | INVALID | NA
    scored = {"counts_in_pass_rate": True, "practical_validity": None, "quality_eval": "run", "note": ""}
    if gen_status in ("timeout", "empty"):
        scored.update(practical_validity=0, quality_eval="skip", note="no usable output; recorded as a failed attempt")
    elif gen_status == "malformed":
        scored.update(practical_validity=0, quality_eval="skip", note="did not follow the output contract")
    else:  # ok -> validation decides practical_validity
        scored["practical_validity"] = {"PASS": 3, "FAIL": 0, "INVALID": None, "NA": None}.get(validation_verdict)
        scored["note"] = "validated=%s" % validation_verdict
    return scored

# --- leakage scan: forbidden tokens that must NOT appear in any evaluator (quality) input ---
FORBIDDEN = [
    r"\bA_prime\b", r"\bcondition\b", r"\bbaseline\b", r"\bplacebo\b",
    r"/home/", r"godot-knowledge", r"knowledge[ -]base", r"\bKB\b", r"AGENTS\.md", r"\bnotes/\b",
    r"status:\s*proposed", r"91250e6", r"godot-knowledge-ro",
    r"characterbody2d-movement", r"area2d-detection", r"input-handling", r"\[ref-\d",
    r"\brun[_-]?id\b", r"\btrial\b", r"### references",
]
def leakage_scan(evaluator_input_text: str) -> list[str]:
    hits = []
    for pat in FORBIDDEN:
        if re.search(pat, evaluator_input_text, re.I):
            hits.append(pat)
    return hits

# --- evaluator payload: the EXACT object serialized and sent to the blind quality evaluator ---
# The evaluator receives ONLY these fields. Anything else (evaluator model id, leakage results, GUT/validation
# results, condition labels, paths, references, original run ids, execution order) is metadata and is FORBIDDEN here;
# such metadata lives only in local record files (e.g. meta.json), which are NEVER sent to the evaluator.
EVALUATOR_PAYLOAD_FIELDS = ("blind_id", "rubric", "submission")

class LeakageError(Exception):
    """Raised when a candidate submission contains condition-identifying content. Blocks the evaluator call."""

def build_evaluator_payload(blind_id: str, parsed: dict, rubric_text: str) -> dict:
    """Construct the EXACT payload for the blind quality evaluator.

    Fields (and ONLY these): blind_id, rubric (identical for all), submission (normalized ### script + ### explanation;
    references excluded, note-ids/paths anonymized). Runs the leakage scan on the SUBMISSION (never on the rubric, which
    legitimately discusses conditions/dimensions) and RAISES LeakageError if the candidate leaks condition info — this
    is a pure function with no I/O, so a leak is caught before any evaluator API call is ever made.
    """
    submission = build_blind_quality_input(parsed)     # normalized script+explanation ONLY
    hits = leakage_scan(submission)
    if hits:
        raise LeakageError("submission leaks condition-identifying content: %r" % hits)
    payload = {"blind_id": blind_id, "rubric": rubric_text, "submission": submission}
    assert set(payload) == set(EVALUATOR_PAYLOAD_FIELDS), "payload must contain EXACTLY the whitelisted fields"
    return payload

def serialize_evaluator_payload(payload: dict) -> str:
    """Deterministic JSON serialization of exactly what is sent. Refuses any payload whose key set is not the
    whitelist, so an accidentally-added metadata field fails loudly instead of leaking to the evaluator."""
    import json
    if set(payload) != set(EVALUATOR_PAYLOAD_FIELDS):
        raise ValueError("evaluator payload fields must be EXACTLY %s; got %s"
                         % (sorted(EVALUATOR_PAYLOAD_FIELDS), sorted(payload)))
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2)

# --- extract the deliverable gdscript files from the ### script section (for executable validation) ---
def extract_gdscript_files(script_text: str) -> dict:
    """Map the candidate's code blocks to {'player.gd', 'coin.gd'} using, in order: a filename comment in the block,
    the base type (CharacterBody2D->player, Area2D->coin), else block order (prompt asks player first, coin second).
    Returns {filename: code}; a file may be missing if it can't be identified."""
    blocks = re.findall(r"```(?:gdscript|gd|gdscript3)?\s*\n(.*?)```", script_text, re.S | re.I)
    if not blocks:
        # fall back: a fenced block with no language tag
        blocks = re.findall(r"```\s*\n(.*?)```", script_text, re.S)
    out = {}
    unclassified = []
    for b in blocks:
        code = b.rstrip() + "\n"
        head = "\n".join(code.splitlines()[:6]).lower()
        if "player.gd" in head:
            out.setdefault("player.gd", code); continue
        if "coin.gd" in head:
            out.setdefault("coin.gd", code); continue
        if "characterbody2d" in code.lower():
            out.setdefault("player.gd", code); continue
        if re.search(r"extends\s+Area2D", code):
            out.setdefault("coin.gd", code); continue
        unclassified.append(code)
    # order fallback for anything still unassigned
    for code in unclassified:
        if "player.gd" not in out:
            out["player.gd"] = code
        elif "coin.gd" not in out:
            out["coin.gd"] = code
    return out

# --- parse the evaluator's JSON verdict out of its (possibly fenced) result text ---
def parse_eval_json(result_text: str) -> dict:
    import json
    t = (result_text or "").strip()
    m = re.search(r"```(?:json)?\s*\n(.*?)```", t, re.S)
    if m:
        t = m.group(1).strip()
    else:
        a, b = t.find("{"), t.rfind("}")
        if a != -1 and b != -1 and b > a:
            t = t[a:b + 1]
    try:
        o = json.loads(t)
        o["parse_ok"] = True
        return o
    except Exception as e:
        return {"parse_ok": False, "error": str(e), "raw": (result_text or "")[:500]}

# --- claude -p stream-json parsing (pure; used by the execution wrappers) ---
def parse_stream_jsonl(text: str) -> dict:
    """Extract the fields we preserve from a `claude -p --output-format stream-json` transcript:
    resolved model, final result text, error/subtype, usage/cost/turns, and every tool_use (with the file paths
    read — the knowledge-access MEDIATOR check for B/A')."""
    import json
    model = result_text = subtype = None
    is_error = None; cost = dur = turns = None
    tool_uses = []  # {name, path}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        t = o.get("type")
        if t == "system" and o.get("subtype") == "init":
            model = o.get("model")
        elif t == "assistant":
            for c in (o.get("message", {}).get("content") or []):
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    inp = c.get("input") or {}
                    path = inp.get("file_path") or inp.get("path") or inp.get("pattern") or inp.get("glob") or ""
                    tool_uses.append({"name": c.get("name"), "path": path})
        elif t == "result":
            result_text = o.get("result")
            is_error = o.get("is_error")
            subtype = o.get("subtype")
            cost = o.get("total_cost_usd")
            dur = o.get("duration_ms")
            turns = o.get("num_turns")
    reads = sorted({tu["path"] for tu in tool_uses if tu["name"] in ("Read", "Glob", "Grep") and tu["path"]})
    knowledge_reads = [p for p in reads if "/knowledge" in p]
    return {"resolved_model": model, "result_text": result_text, "is_error": is_error, "subtype": subtype,
            "cost_usd": cost, "duration_ms": dur, "num_turns": turns,
            "tool_uses": tool_uses, "file_reads": reads, "knowledge_reads": knowledge_reads}
