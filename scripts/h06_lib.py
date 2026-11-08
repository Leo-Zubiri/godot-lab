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
