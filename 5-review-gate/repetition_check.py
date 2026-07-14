#!/usr/bin/env python3
"""Cheap repetition pre-check for a labeled FINAL .md.

Runs in milliseconds (no LLM, no subagent). Catches the MECHANICAL repetition
that has been failing the cold read and forcing extra expensive review rounds:
  - verbatim duplicate sentences (e.g. the same CTA pasted top and bottom),
  - repeated long word-runs (e.g. the same destination list stated in three
    sections), collapsed to one report each.

Mandated, naturally-recurring brand/geo phrases (the port names, the company
name) are whitelisted so they do not create noise.

The WRITER runs this after step 8 and fixes the hits BEFORE spawning the
independent cold reader, so the human cold read usually passes in ONE round.
Advisory (WARN only); judgment still belongs to the cold read.

Usage:  py _scripts/repetition_check.py runs/<slug>/08-final-<slug>.md
Exit 0 always. Prints WARN lines, or "clean".
"""
import sys, re
from collections import Counter

STOP_LABELS = re.compile(r'^(URL|META TITLE|META DESCRIPTION):', re.I)

# Phrases that SHOULD recur across a page (geo anchoring + brand). Normalized.
WHITELIST = [
    # Add YOUR brand + geo phrases that legitimately recur on a page,
    # normalized to lowercase. Examples:
    # 'acme logistics',
    # 'port of houston',
]

def load_prose(path):
    lines = open(path, encoding='utf-8').read().splitlines()
    out, in_schema = [], False
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith('<script'):
            in_schema = True
        if in_schema:
            if s.endswith('</script>'):
                in_schema = False
            continue
        if STOP_LABELS.match(s):
            continue
        s = re.sub(r'^(H1|H2|H3|P):\s*', '', s)
        s = re.sub(r'^[-*]\s+', '', s)
        if s.startswith('[') and s.endswith(']'):
            continue
        if s.startswith('|'):
            continue
        s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s)
        out.append(s)
    return out

def norm(t):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', '', t.lower())).strip()

def main():
    if len(sys.argv) < 2:
        print('usage: repetition_check.py <final.md>'); sys.exit(0)
    prose = load_prose(sys.argv[1])
    text = ' '.join(prose)
    hits = []

    # 1) verbatim duplicate sentences (>= 6 words)
    sents = re.split(r'(?<=[.?!])\s+', text)
    sc, disp = Counter(), {}
    for s in sents:
        n = norm(s)
        if len(n.split()) >= 6:
            sc[n] += 1
            disp.setdefault(n, s.strip())
    dup_sent_norms = {n for n, c in sc.items() if c >= 2}
    for n in dup_sent_norms:
        hits.append(f'DUP SENTENCE x{sc[n]}: "{disp[n][:120]}"')

    # 2) repeated long runs, whitelist-aware, collapsed to maximal spans.
    nt = norm(text)
    for w in WHITELIST:                      # break whitelisted phrases
        nt = nt.replace(w, ' ~ ')
    words = nt.split()
    N = 7
    grams = Counter(tuple(words[i:i+N]) for i in range(len(words)-N+1)
                    if '~' not in words[i:i+N])
    repeated = {g for g, c in grams.items() if c >= 2}
    flagged = sorted(i for i in range(len(words)-N+1)
                     if tuple(words[i:i+N]) in repeated)
    # merge consecutive flagged start-positions into one span
    spans, span_txt = [], Counter()
    i = 0
    while i < len(flagged):
        j = i
        while j+1 < len(flagged) and flagged[j+1] <= flagged[j]+1:
            j += 1
        start, end = flagged[i], flagged[j]+N
        txt = ' '.join(words[start:end])
        if not any(norm(disp[n]).find(txt) >= 0 for n in dup_sent_norms):
            span_txt[txt] += 1
        i = j+1
    for txt, c in span_txt.items():
        hits.append(f'REPEATED RUN: "...{txt}..."')

    if not hits:
        print('repetition_check: clean'); sys.exit(0)
    print('repetition_check: %d issue(s) - review before the cold read:' % len(hits))
    for h in hits[:25]:
        print('  WARN ' + h)
    sys.exit(0)

if __name__ == '__main__':
    main()
