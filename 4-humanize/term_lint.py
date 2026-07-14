#!/usr/bin/env python3
"""
Terminology linter for the SEO pipeline (client-specific data, generic mechanism).

Greps a produced page against the client's banned-term denylist and reports hits.
The denylist lives in `_context/facts/banned_terms.txt` (TAB: SEVERITY <TAB> regex <TAB> message).
This catches the exact mistakes the client already commented on so they cannot recur.

Usage:
  py _scripts/term_lint.py runs/<slug>/08-final-<slug>.md
  py _scripts/term_lint.py            # lints every runs/*/08-final-*.md

Exit code: 2 if any ERROR-severity hit, else 0 (WARN hits are reported but do not fail).
"""
import sys, os, re, glob

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
CLIENT = os.path.dirname(HERE)
DENY = os.path.join(CLIENT, "_context", "facts", "banned_terms.txt")


def load_rules():
    rules = []
    if not os.path.exists(DENY):
        return rules
    with open(DENY, encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip("\n")
            if not ln.strip() or ln.lstrip().startswith("#"):
                continue
            parts = ln.split("\t")
            parts = [p for p in parts if p != ""]
            if len(parts) < 3:
                continue
            sev, pat, msg = parts[0].strip().upper(), parts[1], "\t".join(parts[2:]).strip()
            try:
                rx = re.compile(pat, re.I)
            except re.error as e:
                sys.stderr.write("bad regex skipped: %s (%s)\n" % (pat, e))
                continue
            rules.append((sev, rx, msg, pat))
    return rules


def lint_file(path, rules):
    errors, warns = [], []
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    for i, line in enumerate(lines, 1):
        for sev, rx, msg, pat in rules:
            for m in rx.finditer(line):
                hit = (i, m.group(0).strip(), msg, line.strip()[:120])
                (errors if sev == "ERROR" else warns).append(hit)
    return errors, warns


def report(path, errors, warns):
    rel = os.path.relpath(path, CLIENT)
    if not errors and not warns:
        print("OK   %s — 0 banned terms" % rel)
        return
    print("---- %s ----" % rel)
    for i, hit, msg, ctx in errors:
        print("  ERROR L%d  >>%s<<  -> %s" % (i, hit, msg))
        print("            %s" % ctx)
    for i, hit, msg, ctx in warns:
        print("  WARN  L%d  >>%s<<  -> %s" % (i, hit, msg))


def main():
    rules = load_rules()
    if not rules:
        print("no denylist at %s — nothing to lint" % os.path.relpath(DENY, CLIENT))
        sys.exit(0)
    args = sys.argv[1:]
    if args:
        targets = args
    else:
        targets = sorted(glob.glob(os.path.join(CLIENT, "runs", "*", "08-final-*.md")))
    if not targets:
        print("no FINAL files to lint")
        sys.exit(0)
    total_err = 0
    for t in targets:
        if not os.path.exists(t):
            print("missing: %s" % t)
            continue
        errors, warns = lint_file(t, rules)
        total_err += len(errors)
        report(t, errors, warns)
    print("\n%d ERROR hit(s) across %d file(s)." % (total_err, len(targets)))
    sys.exit(2 if total_err else 0)


if __name__ == "__main__":
    main()
