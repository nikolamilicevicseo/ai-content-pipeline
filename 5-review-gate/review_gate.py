#!/usr/bin/env python3
"""
review_gate.py — FAIL-CLOSED review gate for the SEO content pipeline.

Purpose (read this first):
    A page is NOT "done" because an agent wrote review_status: pass.
    A page is done only when an INDEPENDENT reviewer (a different agent than
    the writer) cold-read the rendered page and left a verifiable artifact.

This script does not trust any agent's self-report. It checks the artifacts
on disk and exits NON-ZERO (RED) the moment any of these is true:

    1. run.json is missing written_by / reviewed_by, OR they are equal
       -> the writer reviewed its own work (the bug that keeps recurring).
    2. review.md is missing or empty.
    3. review.md confesses a self / in-context review (degraded reviewer).
    4. review.md has no quoted lines from the page (a real cold read quotes).
    5. the FINAL md contains an orchestration / process-leak phrase
       (instruction text that leaked into customer copy).

Exit code: 0 = GREEN (all checks pass), 1 = RED (one or more failed).

Usage:
    python _scripts/review_gate.py                 # scan every runs/<slug>/
    python _scripts/review_gate.py runs/<slug>     # check one run
"""

import sys
import os
import re
import json
import glob

# --- 3. review.md must not confess a self / in-context / degraded review ----
CONFESSION_MARKERS = [
    r"separate reviewer subagent (was )?not available",
    r"cold read done in-context",
    r"in-context",
    r"same pass that wrote",
    r"self[- ]review",
    r"reviewer (subagent )?(was )?(not |un)available",
    r"done by the (writer|author)",
    r"author of the page",
]

# --- 5. orchestration / process-leak phrases that must never reach copy ------
# These are meta-instruction words. A customer service page never says them.
LEAK_PHRASES = [
    r"going live",
    r"this batch",
    r"shipping batch",
    r"with this batch",
    r"coming on the site",
    r"\bpage coming\b",
    r"coming soon",
    r"its own page coming",
    r"per the instructions",
    r"per my instructions",
    r"as requested",
    r"as instructed",
    r"sibling page",
    r"gets its own page",
    r"part of this batch",
    r"the writer agent",
    r"reviewer agent",
    r"review gate",
    r"cold[- ]read",
    r"\bsubagent\b",
    r"\bSEO step\b",
    r"\b0\d-(serp|kontekst|final|struktura|draft|human|eeat)\b",
]


def _read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


def _find_first(patterns, text):
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0)
    return None


def check_run(run_dir, run=None):
    """Return (is_green, reasons, slug) for one run folder.

    If `run` (a dict) is passed, it is used as the run state instead of reading
    run.json from disk. The hook passes the PROPOSED run.json here so a fake
    "pass" is blocked BEFORE it ever lands on disk.
    """
    reasons = []
    slug = os.path.basename(os.path.normpath(run_dir))

    # ---- run.json ----------------------------------------------------------
    if run is None:
        rj_path = os.path.join(run_dir, "run.json")
        rj_text = _read(rj_path)
        run = {}
        if rj_text is None:
            reasons.append("run.json missing")
        else:
            try:
                run = json.loads(rj_text)
            except json.JSONDecodeError as e:
                reasons.append(f"run.json is not valid JSON: {e}")

    # ---- 1. writer != reviewer (the core structural check) -----------------
    written_by = (run.get("written_by") or "").strip()
    reviewed_by = (run.get("reviewed_by") or "").strip()
    if not written_by or not reviewed_by:
        reasons.append(
            "run.json has no written_by/reviewed_by -> cannot prove an "
            "independent reviewer existed (writer may have self-passed)"
        )
    elif written_by == reviewed_by:
        reasons.append(
            f"written_by == reviewed_by ({written_by}) -> the writer reviewed "
            "its own page"
        )

    # ---- the independent review must actually PASS -------------------------
    # GREEN means DONE = reviewed AND passed. A reviewer verdict of fail/blocked/
    # pending is RED, no matter that the review happened. (This is the bug the
    # first proof run exposed: a real review can correctly say FAIL.)
    declared = (run.get("review_status") or "").strip().lower()
    if declared != "pass":
        reasons.append(
            f'review_status is "{declared or "unset"}", not "pass" -> the '
            "independent reviewer did not pass the page; it is not done"
        )

    # ---- 2. review.md present and non-trivial ------------------------------
    rv_path = os.path.join(run_dir, "review.md")
    rv_text = _read(rv_path)
    if rv_text is None:
        reasons.append("review.md missing")
        rv_text = ""
    elif len(rv_text.strip()) < 200:
        reasons.append("review.md is empty/too short to be a real cold read")

    # ---- 3. no self-review confession --------------------------------------
    if rv_text:
        hit = _find_first(CONFESSION_MARKERS, rv_text)
        if hit:
            reasons.append(f'review.md confesses a degraded review: "{hit}"')

    # ---- 4. a real cold read quotes the page -------------------------------
    if rv_text and len(rv_text.strip()) >= 200:
        # a genuine reviewer quotes lines; require at least 2 quoted spans
        quotes = re.findall(r'[\"“][^\"”\n]{12,}[\"”]', rv_text)
        if len(quotes) < 2:
            reasons.append(
                "review.md quotes nothing from the page (a real cold read "
                "quotes the lines it judges)"
            )

    # ---- 5. process-leak scan on the FINAL md ------------------------------
    finals = glob.glob(os.path.join(run_dir, "08-final-*.md"))
    if not finals:
        reasons.append("no 08-final-*.md to scan")
    for fp in finals:
        txt = _read(fp) or ""
        hit = _find_first(LEAK_PHRASES, txt)
        if hit:
            reasons.append(
                f'FINAL ({os.path.basename(fp)}) contains orchestration leak: '
                f'"{hit}"'
            )

    # ---- consistency: agent says pass but gate found problems --------------
    declared = (run.get("review_status") or "").strip().lower()
    if declared == "pass" and reasons:
        reasons.append(
            'run.json says review_status: "pass" but the checks above failed '
            "-> this is a FAKE pass"
        )

    return (len(reasons) == 0, reasons, slug)


def main():
    args = sys.argv[1:]
    if args:
        targets = args
    else:
        base = os.path.join(os.getcwd(), "runs")
        targets = [
            d for d in glob.glob(os.path.join(base, "*"))
            if os.path.isdir(d) and os.path.exists(os.path.join(d, "run.json"))
        ]

    any_red = False
    for run_dir in sorted(targets):
        green, reasons, slug = check_run(run_dir)
        if green:
            print(f"GREEN  {slug}")
        else:
            any_red = True
            print(f"RED    {slug}")
            for r in reasons:
                print(f"         - {r}")

    print()
    if any_red:
        print("RESULT: RED — one or more pages are NOT independently reviewed. "
              "They are not done.")
        sys.exit(1)
    print("RESULT: GREEN — every page has a verifiable independent review.")
    sys.exit(0)


if __name__ == "__main__":
    main()
