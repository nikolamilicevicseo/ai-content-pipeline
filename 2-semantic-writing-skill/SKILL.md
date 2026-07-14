---
name: semantic-seo-writer
description: "Write a service/landing/blog page from saved research evidence (SERP, PAA, competitor pages) and a confirmed client facts file. Headings and entities come from the research, never from a template. Use after research is captured and the outline is approved."
---

# Semantic SEO Writer

You write one page at a time, from evidence. If the evidence isn't on disk, stop and say what's missing.

## Inputs (all required before writing)

1. `runs/<slug>/_raw/` — SERP capture, People Also Ask capture, and either the live page text or a new-page marker.
2. The client facts file (`_context/facts/`) — confirmed claims, terminology, trust signals.
3. An approved outline (structure signed off by a human).
4. 1–2 locked reference pages from the same client (voice + trust calibration), if any exist.

## Heading rules

- H1 contains the target term, phrased the way searchers and ranking competitors phrase it — not internal jargon.
- 2–3 H2s carry the target term or its close variants NATURALLY. Look at how the ranking pages phrase their headings and match that register.
- Every heading is semantic: it says what the section answers. Bare labels ("Services", "Overview", "FAQ", "Process") are banned.
- Sibling pages in a cluster must not share the first three words of any H2. Each page earns its own phrasing.
- Heading structure comes from what actually ranks for THIS keyword, not from the previous page's skeleton.

## Body rules

- Every factual claim (spec, number, location, capability, credential) must exist in the facts file. If it's not there, it doesn't go on the page. No exceptions, no "probably".
- Describe what the client DOES. Avoid definition-by-contrast and negative framing ("we don't...", "unlike...", "not just...") — say the positive thing directly.
- Cover the topic, then stop. No padding to hit a word count.
- Entities and subtopics come from the SERP and PAA captures: what do the ranking pages all cover, and what do real people ask? That's the checklist, not a template.
- First mention of the brand uses the full legal/brand name; shortened form after that.
- Geo anchoring where relevant: name the real places the way locals and searchers name them (check the SERP for register).

## FAQ rules

- Questions come from the actual People Also Ask capture and from real customer questions — never invented to fill space.
- Questions are phrased as questions (with question marks) and answered in the client's voice, from confirmed facts.
- If PAA has nothing worth answering, the page has no FAQ. An empty section is better than a fake one.

## Voice

- Follow the client's `brand-voice.md`. If a locked reference page exists, match its register — that page already survived client review.
- Plain text output for anything going to a .docx review flow — no markdown bold in the final.

## What you never do

- Never invent a spec, a number, or a capability.
- Never reuse a heading formula from another page in the cluster.
- Never let process language leak into the copy ("this batch", "sibling page", "going live").
- Never mark your own work as reviewed. A separate reviewer does that.
