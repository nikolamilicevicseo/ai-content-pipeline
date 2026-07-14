#!/usr/bin/env python3
"""
PreToolUse guard: a page CANNOT be declared done/pass without an independent
review on disk. Harness-enforced — the model cannot talk its way past it.

It fires on Write/Edit to a run.json. If the write would set the RUN-LEVEL
review_status: "pass" (or the RUN-LEVEL status: "done"), it runs the
review_gate checks against the PROPOSED state. If the gate is RED, the write
is BLOCKED (exit 2):

  - written_by / reviewed_by missing or equal  -> writer self-passed
  - review.md missing / too short / confesses an in-context (self) review
  - review.md quotes nothing from the page
  - the FINAL md carries an orchestration/process-leak phrase

Everything else passes through. Crucially, a PHASE-level "status": "done"
inside the phases[] array is NOT a done-declaration and is allowed — only the
top-level run status / review_status are gated. The guard reconstructs the full
proposed JSON (Write content, or the on-disk file with the Edit applied) and
inspects only the top-level keys, so per-phase progress writes are never
falsely blocked.

Fail-closed: if it looks like a done-declaration but cannot be verified, BLOCK.

Input: hook JSON on stdin. Exit 0 = allow, exit 2 = block (stderr explains).
"""
import sys, os, json, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from review_gate import check_run
except Exception:
    check_run = None

# Fallback-only patterns (used when the proposed JSON cannot be parsed).
RUN_DONE = re.compile(r'"review_status"\s*:\s*"pass"|"status"\s*:\s*"done"', re.I)
FIELD = lambda key, txt: (
    (re.search(r'"%s"\s*:\s*"([^"]*)"' % key, txt or "") or [None, ""])[1])


def proposed_full_text(ti):
    """The complete run.json text this Write/Edit would produce, if derivable."""
    if "content" in ti and ti.get("content") is not None:
        return ti["content"]  # Write = whole file
    # Edit: apply the replacement to the on-disk file so we can judge the
    # resulting TOP-LEVEL fields, ignoring nested per-phase statuses.
    old = ti.get("old_string", "")
    new = ti.get("new_string", "")
    fp = ti.get("file_path", "")
    try:
        with open(fp, encoding="utf-8") as f:
            disk = f.read()
    except Exception:
        return None
    if ti.get("replace_all"):
        return disk.replace(old, new)
    return disk.replace(old, new, 1)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if data.get("tool_name", "") not in ("Write", "Edit"):
        sys.exit(0)

    ti = data.get("tool_input") or {}
    fp = ti.get("file_path", "") or ""
    if os.path.basename(os.path.normpath(fp)) != "run.json":
        sys.exit(0)

    run_dir = os.path.dirname(os.path.normpath(fp))

    full_text = proposed_full_text(ti)
    proposed = None
    if full_text is not None:
        try:
            proposed = json.loads(full_text)
        except Exception:
            proposed = None

    if proposed is not None:
        # PRECISE: only the TOP-LEVEL run status / review_status count.
        declares_done = (
            str(proposed.get("status", "")).lower() == "done"
            or str(proposed.get("review_status", "")).lower() == "pass"
        )
    else:
        # FALLBACK (unparseable): be conservative on the changed snippet only.
        snippet = ti.get("content") or ti.get("new_string") or ""
        declares_done = bool(RUN_DONE.search(snippet))
        base = {}
        try:
            with open(os.path.join(run_dir, "run.json"), encoding="utf-8") as f:
                base = json.load(f)
        except Exception:
            base = {}
        proposed = dict(base)
        for k in ("review_status", "status", "written_by", "reviewed_by"):
            v = FIELD(k, snippet)
            if v:
                proposed[k] = v

    if not declares_done:
        sys.exit(0)  # intermediate / per-phase write, let it through

    if check_run is None:
        sys.stderr.write(
            "BLOCKED: cannot mark run done — review_gate module failed to load, "
            "so an independent review cannot be verified.\n")
        sys.exit(2)

    green, reasons, slug = check_run(run_dir, run=proposed)
    if not green:
        sys.stderr.write(
            "BLOCKED: '%s' cannot be marked done/pass.\n"
            "A page is done only when a SEPARATE reviewer (not the writer) "
            "cold-read it and left proof on disk. Failing checks:\n  - %s\n"
            "Fix: produce the page through the write/review workflow so a "
            "different agent writes review.md and stamps reviewed_by, then "
            "retry.\n" % (slug, "\n  - ".join(reasons)))
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
