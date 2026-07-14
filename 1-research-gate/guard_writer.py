#!/usr/bin/env python3
"""
PreToolUse guard for the SEO pipeline.

Hard, harness-enforced rule: the writer steps (05-draft, 06-human, 07-eeat,
08-final-<slug>) of a run CANNOT be written unless that run has REAL research
evidence on disk first. This is not a prompt instruction the model can talk
itself out of; the harness runs this before every Write/Edit and a non-zero
exit blocks the write.

Required evidence in runs/<slug>/_raw/ before any writing-stage artifact:
  1. SERP capture     s1*.json (or *step1*.json) with "ok": true   (real Google SERP)
  2. PAA capture      s3*.json (or *step3*.json) with "ok": true   (real People Also Ask)
  3. LIVE client page audit_live.txt  >= 600 chars  (live page captured via Chrome)
     OR new-page marker client_new.txt  (genuinely new page, no live URL)

If any is missing, the write is BLOCKED with a message naming what is missing.
Non-writing artifacts (00..04, run.json, review.md, _raw/*, dashboards) pass through.

Input: hook JSON on stdin -> {"tool_name": "...", "tool_input": {"file_path": "..."}}
Exit 0 = allow, exit 2 = block (stderr explains why).
"""
import sys, os, json, glob, re

WRITING_ARTIFACT = re.compile(r'^(05-draft|06-human|07-eeat|08-final-.+)\.md$', re.I)
MIN_AUDIT_CHARS = 600


def _json_ok(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f).get('ok') is True
    except Exception:
        return False


def _any_ok(raw_dir, *patterns):
    for pat in patterns:
        for p in glob.glob(os.path.join(raw_dir, pat)):
            if _json_ok(p):
                return True
    return False


def main():
    # Never brick unrelated tools: if we cannot read the event, allow.
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool = data.get('tool_name', '')
    if tool not in ('Write', 'Edit'):
        sys.exit(0)

    fp = (data.get('tool_input') or {}).get('file_path', '') or ''
    if not fp:
        sys.exit(0)

    fp = os.path.normpath(fp)
    name = os.path.basename(fp)
    if not WRITING_ARTIFACT.match(name):
        sys.exit(0)  # not a writing-stage artifact -> allow

    # This IS a writing-stage artifact. From here, default is BLOCK unless proven.
    try:
        run_dir = os.path.dirname(fp)
        slug = os.path.basename(run_dir)
        raw = os.path.join(run_dir, '_raw')

        missing = []
        if not _any_ok(raw, 's1*.json', '*step1*.json'):
            missing.append("SERP capture (runs/%s/_raw/s1*.json with ok:true) - run research.mjs step1" % slug)
        if not _any_ok(raw, 's3*.json', '*step3*.json'):
            missing.append("PAA capture (runs/%s/_raw/s3*.json with ok:true) - run research.mjs step3" % slug)

        audit = os.path.join(raw, 'audit_live.txt')
        newmark = os.path.join(raw, 'client_new.txt')
        has_audit = os.path.exists(audit) and os.path.getsize(audit) >= MIN_AUDIT_CHARS
        has_new = os.path.exists(newmark)
        if not (has_audit or has_new):
            missing.append("LIVE client page capture (runs/%s/_raw/audit_live.txt >=600 chars via Chrome) "
                           "OR new-page marker (runs/%s/_raw/client_new.txt)" % (slug, slug))

        if missing:
            sys.stderr.write(
                "BLOCKED writing %s.\n"
                "No page may be written before its research evidence exists on disk.\n"
                "Missing:\n  - %s\n"
                "Capture the live page and SERP/PAA first (Chrome + research.mjs), "
                "then retry the write.\n" % (name, "\n  - ".join(missing))
            )
            sys.exit(2)
    except Exception as e:
        # On any failure verifying a writing artifact, fail CLOSED (block).
        sys.stderr.write("BLOCKED writing %s: guard could not verify research evidence (%s).\n" % (name, e))
        sys.exit(2)

    sys.exit(0)


if __name__ == '__main__':
    main()
