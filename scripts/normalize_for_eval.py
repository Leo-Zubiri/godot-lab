#!/usr/bin/env python3
"""Deterministic normalizer for blind evaluation (condition-leakage mitigation).

Input:  a run's output.md (ORIGINAL, never modified).
Output (into the run dir, NONE of which the evaluator receives except eval_input.md):
  - eval_input.md     : normalized artifact the evaluator scores
  - anon_map.json     : note-id -> neutral ref mapping (hidden correspondence)
  - normalize_log.json: ordered rules + match counts (audit trail)

Guarantees / design (per the audit methodology):
  * Code blocks (```...```) are kept VERBATIM -> script integrity by construction.
  * Only PROSE is normalized. Technical API names / GDScript are untouched.
  * Removes condition tells: filesystem paths, repo/dir/file names, process narration.
  * Anonymizes repo note-ids to neutral [ref-NN] (traceability preserved, identity hidden).
  * Preserves justified uncertainty: 'status: proposed' -> 'unverified' (kept, not deleted).
  * Deterministic: same input -> byte-identical output (no model, fixed ordered rules).
  * Does NOT pad/trim to equalize length or structure.
"""
import json, re, sys, os

# Fixed, sorted -> opaque neutral labels (deterministic, semantically empty).
NOTE_IDS = sorted([
    "gdscript-signals", "gdscript-static-typing", "node-lifecycle-callbacks",
    "autoload-singletons", "node-vs-resource-vs-autoload", "god-autoload",
    "godot-version-policy", "godot-index", "one-shot-timer",
])
REFMAP = {nid: f"[ref-{i+1:02d}]" for i, nid in enumerate(NOTE_IDS)}

# Cleanup pass (runs LAST): collapse redaction artifacts so "was-redacted" is not itself a tell.
CLEANUP = [
    ("dbl_the_cap",  r"\bThe the\b", "The", 0),
    ("dbl_the",      r"\bthe the\b", "the", re.I),
    ("the_so",       r"\bThe so\b", "So", 0),
    ("sp_before_pun",r"\s+([.,;:])", r"\1", 0),
    ("multi_space",  r"[ \t]{2,}", " ", 0),
    ("lead_space",   r"(?m)^[ \t]+(?=\S)", "", 0),
    ("multi_blank",  r"\n{3,}", "\n\n", 0),
]

# Ordered prose rules: (name, pattern, replacement, flags). Order matters.
# Strategy: (1) neutralize all names (paths/repo/dir/file/abbrev) to generic "reference material/guide";
# (2) remove whole process-narration clauses (consulting / emptiness / verification / tooling);
# (3) neutralize trust-status while KEEPING justified uncertainty; (4) anonymize note-ids (done after).
RULES = [
    # --- 1. names / paths / abbreviations -> generic ---
    ("abs_path",        r"/home/\S+",                              "[path]", 0),
    ("res_path",        r"res://\S+",                              "[path]", 0),
    ("repo_ro",         r"godot-knowledge-ro",                     "the reference material", re.I),
    ("repo_name",       r"godot-knowledge",                        "the reference material", re.I),
    ("kb_phrase",       r"knowledge[\s-]?base",                    "the reference material", re.I),
    ("kb_abbrev",       r"\bKB\b",                                 "the reference material", 0),
    ("outbox",          r"knowledge-outbox",                       "[omitted]", re.I),
    ("agents_md",       r"AGENTS\.md",                             "the reference guide", 0),
    ("claude_md",       r"CLAUDE\.md",                             "the reference guide", 0),
    ("notes_dir",       r"\bnotes/",                               "references ", 0),
    # --- 2. process-narration clauses (condition tells) — remove the whole clause/sentence ---
    ("empty_ref",       r"[^.\n]*the reference (?:material|guide)[^.\n]*\bis empty\b[^.\n]*\.?", "", re.I),
    ("usable_ref",      r"[^.\n]*the reference material[^.\n]*\bis usable\b[^.\n]*\.?", "", re.I),
    ("has_guidance",    r"[^.\n]*the reference material has[^.\n]*\bguidance\b[^.\n]*\.?", "", re.I),
    ("dir_empty",       r"[^.\n]*\bthe (?:directory|folder) is empty\b[^.\n]*\.?", "", re.I),
    ("no_usable",       r"[^.\n]*\bno usable (?:knowledge|references?|material)\b[^.\n]*\.?", "", re.I),
    ("not_verified",    r"(?:The reference material|It)\s+ha(?:s|ve)\s+not been verified by a human,?\s*", "", re.I),
    ("no_note_ids",     r"[^.\n]*\bcite no note ids\b[^.\n]*\.?", "", re.I),
    ("not_the_ref",     r",?\s*not (?:the )?the reference material\b", "", re.I),
    ("proceeding",      r"\bproceeding without it\b",              "proceeding", re.I),
    ("tooling",         r"[^.\n]*\b(?:parse-check|parse check|Bash was denied|shell access was denied|could ?n.?t run Godot|checked by reading only|denied in this session)\b[^.\n]*\.?", "", re.I),
    ("i_read",          r"\bI (?:read|consulted|looked at|checked)\b", "Per", re.I),
    ("i_used_notes",    r"\bI used (?:these |the )?references?\b",  "Per the references", re.I),
    # --- 3. trust status: keep justified uncertainty, drop the repo-frontmatter tell ---
    ("status_colon",    r"`?status:\s*proposed`?",                 "unverified", re.I),
    ("status_word",     r"\bstatus\s+`?proposed`?",                "unverified", re.I),
    ("proposed_bare",   r"`?\bproposed\b`?",                       "unverified", re.I),
]

def split_code(md):
    """Yield (is_code, segment). Fenced ``` blocks are code (kept verbatim)."""
    parts, i, code = [], 0, False
    for m in re.finditer(r"```", md):
        parts.append((code, md[i:m.start()]))
        parts.append((None, "```"))
        i = m.end(); code = not code
    parts.append((code, md[i:]))
    # collapse: segments between fences are code when 'code' flag was True
    out, is_code = [], False
    for tag, seg in parts:
        if tag is None:
            out.append((True, "```")); is_code = not is_code  # fence belongs to code span
        else:
            out.append((is_code, seg))
    return out

def normalize(md):
    log = []
    segs = split_code(md)
    new = []
    for is_code, seg in segs:
        if is_code:
            new.append(seg); continue
        for name, pat, repl, flags in RULES:
            seg, n = re.subn(pat, repl, seg, flags=flags)
            if n: log.append({"rule": name, "count": n})
        for nid, ref in REFMAP.items():
            seg, n = re.subn(re.escape(nid), ref, seg)
            if n: log.append({"rule": f"anon:{nid}", "count": n})
        for name, pat, repl, flags in CLEANUP:
            seg, n = re.subn(pat, repl, seg, flags=flags)
            if n: log.append({"rule": f"cleanup:{name}", "count": n})
        new.append(seg)
    return "".join(new), log

def main(path):
    d = os.path.dirname(path)
    orig = open(path, encoding="utf-8").read()
    norm, log = normalize(orig)
    open(os.path.join(d, "eval_input.md"), "w", encoding="utf-8").write(norm)
    json.dump(REFMAP, open(os.path.join(d, "anon_map.json"), "w"), indent=2)
    json.dump(log, open(os.path.join(d, "normalize_log.json"), "w"), indent=2)
    print(f"{os.path.basename(d)}: rules_applied={len(log)}")

if __name__ == "__main__":
    main(sys.argv[1])
