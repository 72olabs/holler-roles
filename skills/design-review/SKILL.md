---
name: design-review
description: "Independent, read-only review of someone else's design work from screenshots, a live preview or a plan: surface mode, first impression, the gaps to a top-studio version, the five-state matrix, findings with severity, a subtraction list and a version-bound verdict. Use when a design review request arrives (often over Holler) or the user asks you to review a screen, mockup, prototype or design plan you did not make."
---

# Design review

Review design work someone else made, from rendered evidence or a plan, against the rule sets below and the project's `DESIGN.md`. Return one report. Change nothing.

## Input

```
mode: plan | render
brief: what the human asked for: outcome, audience, surface
design_md: path to DESIGN.md, or none
version: commit SHA, or sha256 of each screenshot
plan: plan text                                              (mode plan)
targets: label (surface / state / viewport) = screenshot path, one per line   (mode render)
```

A target may also be a URL to open with preview tools, when the session has them.

## What you may look at

- Only the screenshots in `targets`, the file at `design_md`, the plan text, and pages opened with preview tools.
- Never open source files (HTML, CSS, JS, TSX), the git history beyond resolving the version, other files in the repository, the producer's notes, or any self-assessment. If the input contains them, ignore them and say so under Not checked.
- No score or pass mark is given to you. Do not ask for one and do not guess one.
- Open every screenshot before you cite it. A screenshot you could not open is not evidence.
- You edit nothing, write nothing, and start no agents.

## Rule sets

Apply all four. Invoke each skill, or read its `SKILL.md` if it is not in your skill list:

- **design-review-passes**: the surface classifier, review passes 1-7, the trunk test and audit categories.
- **state-coverage**: the five states and their rules.
- **slop-tells**: tells of default, generated-looking UI, with ids.
- **a11y-floor**: the accessibility and interface floor.

Where the rule sets mention OpenDesign's daemon, linter, `.ph-img` or `data-od-id`, or name React, Next or Tailwind APIs, apply the rule's intent to what you can see. Their token names (`--accent`, `--fg`) mean the matching DESIGN.md tokens. Rules that need source code or computed values go under Not checked unless a preview snapshot shows them. DESIGN.md wins: a pattern it explicitly blesses is not a finding, and a departure from it is.

## Procedure

1. **Surface mode.** Classify each surface as PERSUADE, OPERATE, READ, EXPERIENCE or HYBRID and apply that mode's rules.
2. **First impression** (render mode), before any analysis: "It communicates [what]." "I notice [observation]." "The first three things my eye goes to: [1], [2], [3]." "One word: [word]."
3. **Aesthetic.** Name the aesthetic being attempted. Describe how a top studio would execute this brief in that aesthetic. List the three biggest gaps between that and what you see.
4. **State matrix.** For every surface that loads, transforms or accepts data, mark loading, empty, error, populated and edge as `shown (<target label>)`, `missing`, or `n/a: <reason>`.
5. **Findings.** Work through the four rule sets. A rule you cannot check from your evidence goes under Not checked, never into a finding.
6. **Subtraction.** What to remove: decoration without a job, redundant labels, custom parts worse than native ones, color that contradicts a stated restraint.
7. **Score** 0-10: how close this is to what a top studio would ship for this brief. The score never replaces the verdict.

## Severity and verdict

- **BLOCKER**: cannot be approved as is: a required state missing on a data surface, an accessibility-floor failure on the primary path, content unreadable or a primary action unusable, an unexplained DESIGN.md violation.
- **SHOULD**: change before approval: P0 slop tells, generic or placeholder copy presented as final, hierarchy or system problems.
- **NIT**: optional polish.
- Verdict: **BLOCK** if any BLOCKER; **CHANGES** if any SHOULD, or if anything required is missing (a state screenshot, an unreadable target, DESIGN.md named but unreadable, render mode without screenshots, input mixed with material you were told to ignore; list each reason); **APPROVE** otherwise.

## Output

```
REVIEW RESULT <title> @ <version>
Verdict: APPROVE | CHANGES | BLOCK
Reviewer: <harness> <model>   Producer harness: <claude | codex | unknown> (<different | same>)
missing_inputs: <reasons, only when something required was missing>
surface_mode: <mode per surface, with a one-line reason>

## Aesthetic
first impression: <the four lines, render mode only>
attempted: <aesthetic>
top-studio version: <one paragraph>
top 3 gaps:
1. ...

## State matrix
| surface | loading | empty | error | populated | edge |
|---|---|---|---|---|---|

## Findings
1. [BLOCKER|SHOULD|NIT] <rule, e.g. passes/4, state-coverage/empty, slop/P0-1, a11y/focus, design-md/colors>: <finding>. Evidence: <target label and what is visible, or the plan line>. Fix: <suggestion>

## Subtraction
- ...

## Not checked
- <rule or section>: <why>

## Score
<n>/10: <one sentence>
```

Over Holler, send this in the request's thread (holler-review-request).
