# AI Content Pipeline — the full setup

The pipeline I use to write SEO content with Claude: five pieces that make the careless path impossible. Everything client-specific has been stripped out; every mechanism is intact.

It runs on Claude Code (or any harness that supports PreToolUse hooks), but the ideas transfer to any AI writing setup: the gates are just scripts that block a file write until evidence exists on disk.

## The five pieces

| # | Folder | What it does |
|---|--------|--------------|
| 1 | `1-research-gate/` | Blocks the draft from being written until real research (SERP, People Also Ask, live page capture) is saved to disk. Not a prompt instruction — a hook the model cannot talk its way past. |
| 2 | `2-semantic-writing-skill/` | The writing skill. Headings and entities come from the research, not a template. |
| 3 | `3-client-facts-file/` | Template for the per-client knowledge base. If a claim isn't in this file, it doesn't go on the page. |
| 4 | `4-humanize/` | Banned-term linter plus a starter denylist of AI tells. Grows from client feedback so the same mistake never recurs. |
| 5 | `5-review-gate/` | Blocks a page from being marked "done" until a separate reviewer (not the writer) has read it and left proof on disk. Includes a repetition pre-check. |

## Folder layout the scripts expect

```
your-client-folder/
  _context/facts/banned_terms.txt     <- denylist (see 4-humanize)
  _scripts/                           <- put the .py files here
  runs/<page-slug>/
    _raw/                             <- research evidence lands here
      s1*.json                        <- SERP capture, {"ok": true, ...}
      s3*.json                        <- PAA capture,  {"ok": true, ...}
      audit_live.txt                  <- live page text (>= 600 chars)
      client_new.txt                  <- OR marker: page doesn't exist yet
    05-draft.md ... 08-final-<slug>.md
    run.json                          <- written_by / reviewed_by / review_status
    review.md                         <- the independent reviewer's notes
```

How you capture the research is up to you (browser automation, an API, by hand). The gate only checks that the evidence exists and is real.

## Wiring the hooks (Claude Code)

In your project's `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python _scripts/guard_writer.py" },
          { "type": "command", "command": "python _scripts/guard_review.py" }
        ]
      }
    ]
  }
}
```

Exit code 2 from a hook blocks the write and feeds the stderr message back to the model, so it knows exactly what's missing and goes to fix it.

## Manual checks

```
python _scripts/review_gate.py                # is every page really reviewed?
python _scripts/term_lint.py                  # banned terms in every final
python _scripts/repetition_check.py runs/<slug>/08-final-<slug>.md
```

## For the humanization pass

The banned-term linter here catches known phrases. For the broader sweep of AI patterns (sentence structures, rhythm, the usual tells) I also run the open-source humanizer skill: https://github.com/blader/humanizer — not mine, credit where due.

## One honest warning

None of this makes the AI good. It makes the careless path impossible. You still review outlines by hand, you still google the keyword yourself, and a human who knows the subject still reads every page. The system just guarantees those steps can't be skipped.

— Nikola Milicevic
