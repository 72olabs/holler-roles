---
name: experiment-card
description: "Pre-register a product or growth change before it ships, then read it out. Use for 'before we ship this', 'set up an experiment', 'how will we know it worked', 'what's the target', 'did it work', 'read out the test', 'is the experiment done'. Appends cards and readouts to the append-only registry .agents/experiments.jsonl."
---

# Experiment card

A card is written before a growth change ships. It fixes what success means while nobody knows the result yet. The readout compares the actual result with that card and reports misses as misses.

The registry is `.agents/experiments.jsonl` in the project. It is append-only. Write to it only with `scripts/experiments.py` in this skill's directory. Never edit, rewrite, reorder or delete lines, with any tool. A hook blocks direct edits in Claude Code; `experiments.py verify` detects them anywhere.

## When a change needs a card

Any change meant to move a growth number: site copy, onboarding, emails, pricing page, launch, social or content experiment, channel test. No card, no claim: a metric change is not attributed to a change that had no card.

## Register a card

1. Print the template: `python3 -I <this skill>/scripts/experiments.py template`.
2. Fill every field in a draft file such as `drafts/cards/<slug>.json`:

| Field | What goes in it |
| --- | --- |
| `id` | `exp-YYYY-MM-DD-<slug>` (today's date) |
| `title`, `change`, `hypothesis` | What ships, where, to whom, and why it should move the metric |
| `prediction` | The outcome this card predicts, in one sentence |
| `metric.name`, `metric.source` | The metric and its authoritative source: the system and the query or report that will be read at the decision date |
| `metric.window_days` | How far back that source keeps data, if limited (X: 30). The decision date must fall inside it |
| `baseline` | `value`, `date`, `label` (measured / user-provided / calculated / estimated / proxy) and `source`. Read it before registering |
| `target` | `comparator` (`>=`, `>`, `<=`, `<`) and `value` |
| `start_date`, `decision_date` | When exposure starts (today or later) and when the result is read |
| `min_sample` | `value` and `unit` (visitors, signups, impressions). Below it the result is inconclusive |
| `kill` | `criterion` in words; add `comparator` and `threshold` when it is a number |
| `supersedes`, `supersede_reason` | Only for a changed card: the old id and why |

3. Anything you cannot fill is a `[NEED: …]`; the script refuses a card that still has one. Get the missing fact from the human or the source, or do not ship the change as an experiment.
4. Show the card to the human. Register it only after they approve it in their own message in this session, naming the card:
   `python3 -I <this skill>/scripts/experiments.py add --card drafts/cards/<slug>.json --approved-by <their name>`
5. Quote the script's output in your reply.

A changed target, date, metric or sample size is a new card with `supersedes` and `supersede_reason`. The old card stays. A readout against a superseded card says so.

## Read out

At or after the decision date, read the metric from the source named on the card, then:

```sh
python3 -I <this skill>/scripts/experiments.py readout --card <id> --actual <n> --source "<where you read it>" \
  --date <YYYY-MM-DD the value was read> --label measured --sample <n> [--kill-triggered yes|no] [--notes "..."]
```

The script records and prints the verdict: `target-met`, `target-missed`, `kill`, `inconclusive` (sample below the minimum) or `early-look` (before the decision date; never a result). Report it as printed: the target, the actual with its label and source, the gap, and every note. A miss is reported as a miss, with no reframing into a win. Correlation is not causation: say what else changed in the same window.

## Other commands

- `list [--open] [--due-by YYYY-MM-DD]`: cards and their state; use `--open --due-by <date>` to find readouts that are due.
- `show <id>`: the card and its readouts.
- `verify`: checks the hash chain and record types. Run it before a readout and report any problem to the human instead of repairing the file.

The script reads `--registry`, else `$HOLLER_EXPERIMENTS`, else `.agents/experiments.jsonl`. `add` and `readout` never create a registry. If the file is missing, say so and offer `experiments.py init`, which creates an empty registry (and `.agents/`) and nothing else; run it after the user agrees. `$HOLLER_EXPERIMENT_MAX_DAYS`, when set, caps the days between start and decision date.

Exit codes: 0 ok, 1 refused (the reason is printed), 2 usage error.
