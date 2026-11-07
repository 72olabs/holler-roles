---
name: growth-gate
description: "Lint drafts before anything goes out: unsourced numbers, overclaims, send or publish wording without approval, AI tells, open [NEED] markers. Use for 'is this ready to post', 'check this copy', 'gate the drafts', 'before I publish', 'sanity-check this email'. Run from a session that did not write them; for a peer's verdict use holler-review-request."
---

# Growth gate

A deterministic check plus a short human-judgment checklist, run on drafts before the human decides whether to publish. Passing the gate does not approve anything: only the human approves, sends, posts or publishes.

## Run it in a different session from the author

The session that wrote a draft does not gate it. Open a new session (another terminal, or the other harness) and ask it to gate the path. If that session is reached over Holler, ask with holler-review-request; this script is the check it runs. If the draft's front matter has `author_session: <id>` and you know this session's id, pass `--reviewer-session <id>`; the script fails a match. If you wrote any of the files in this session, say so and stop.

## Steps

1. Run the script from this skill's directory on the files or folder:

   ```sh
   python3 -I <this skill>/scripts/growth_gate.py drafts/<folder-or-file> [--json] [--reviewer-session <id>]
   ```

   Exit 0: no failing findings. Exit 1: failing findings. Exit 2: usage error.
2. Quote the report. For each finding give the file, line, check and what would fix it. Do not fix and re-run silently: the author session fixes; this session reports.
3. Work through `references/checklist.md` for what a script cannot judge. Answer each item yes, no or n/a, with the line it rests on.
4. Optional: Four U's score from this session, never the author's: `--four-us-prompt <file>` prints the rubric; score it, then `--four-us-scores '<json>' <file>` reports kai's thresholds. Report-only; it does not change the result.
5. Reply with: the script result, the checklist answers, the open items, and the reminder that publishing is the human's call.

## Checks and what each claims to predict

| Check | Fails on | Predicts (hypothesis, not measured here) |
| --- | --- | --- |
| `need-marker` | any `[NEED: …]` | A placeholder or unsupported claim reaches the public |
| `metric-no-source` | a number (%, x, currency, counts, durations, metric names) with no source on the line or an evidence line right after | A number nobody can trace when someone asks where it came from |
| `metric-incomplete-evidence` | a sourced number without a date and one label (measured, user-provided, calculated, estimated, proxy) | A number that cannot be re-checked or weighed |
| `ai-overclaim` | absolutes and unverifiable superlatives (the only, #1, guaranteed, 100%, never fails), AI capability claims (fully autonomous, human-level, no hallucinations, replaces your team), weasel sources (studies show, trusted by thousands) | A claim a user or reviewer can falsify, which costs trust in the rest of the page |
| `draft-status-missing` | no `Status: DRAFT` or front matter `status: draft` in the first 15 lines | A file mistaken for approved copy |
| `send-without-approval` | send, post, publish, schedule, queue, share-now or go-live wording with no approval wording on the line | Another session or agent ships it without the human's sign-off |
| `approval-claim-without-record` | "approved", "ready to publish", "good to go", "signed off" with no `approved_by: <name> <YYYY-MM-DD>` line | A self-approved artifact |
| `ai-tell` | banned patterns from marketingskills ai-tells.md: contrast reveal, negation list, rhetorical-question and colon reveals, era openers, throat-clearing, stock marketing phrases, banned vocabulary | Readers judge the copy machine-written and doubt its claims |
| `ai-tell-cap` (warning) | two or more capped words in one paragraph; more than two em dashes in a file | Same, for devices that are fine once |
| `same-session` | `author_session` equals `--reviewer-session` | The author misses its own errors |

Evidence annotation the metric checks accept, on the same line or the line right after:
`<!-- evidence: <source> | <YYYY-MM-DD> | <label> -->`, `[src: <source>; <YYYY-MM-DD>; <label>]`, or a footnote `[^n]` whose definition carries all three.

A false positive can be waived on its line with `<!-- gate-waive: <check> | <reason> -->`. The report lists every waiver for the human to see. `need-marker`, `draft-status-missing`, `send-without-approval`, `approval-claim-without-record` and `same-session` cannot be waived.

## Credits

AI-tell patterns adapted from marketingskills `skills/copywriting/references/ai-tells.md` (MIT, © 2025 Corey Haines, `../../LICENSE-marketingskills`). Word tiers, the number-near-a-source rule and the Four U's rubric adapted from kai-cmo-harness `scripts/quality_gates/` (MIT, © 2026 Connor Gallic, `../../LICENSE-kai-quality-gates`). Offline only: no model or API calls.
