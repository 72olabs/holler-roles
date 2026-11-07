---
name: perf-issue
description: "Make something measurably faster or lighter. Use for \"X is slow\", \"takes N seconds\", \"laggy\", \"speed up X\", \"high CPU\", \"memory keeps growing\", \"perf regression\". Captures a baseline, fixes from the trace, reports before and after numbers."
---

<!-- holler-roles: converted from pstack skills/poteto-mode/playbooks/perf-issue.md at 356c6e0f978d (MIT, see ../../LICENSE). Frontmatter and this preamble are added; the text after the rule is unchanged. -->

**Before you start**

Paths in this preamble are relative to this skill's folder.

1. Read the Principles section of the pstack principles index, `../poteto-mode/SKILL.md`. Before applying a principle, read its leaf skill at `../principle-<name>/SKILL.md`.
2. Open a task list whose first items are this playbook's steps, copied verbatim. A step you skip stays on the list with `skip: <reason>`.
3. Do not report done without runtime evidence: output from running the changed thing on the surface the task names. Tests or "it compiles" alone are not done.

Reading the playbook: its relative links resolve from `../poteto-mode/playbooks/`. "The installed plugin", `<plugin>` and "this pstack" mean the folder two levels up from this skill (`../..`), which holds `skills/` and `agents/`. The sections it cites (Non-negotiables, Subagents, Models, Writing the reply) are in the principles index; Opening a PR is `../poteto-mode/playbooks/opening-a-pr.md`. A skill it names that is not in your skill list is a file at `../<name>/SKILL.md`: read it instead of invoking it. When you spawn `pstack:poteto-agent`, give it the absolute path of `../poteto-mode/SKILL.md`. On Codex, map Claude tool and model names with `../poteto-mode/references/codex-tools.md`.

---

### Perf issue

**You own the measurement story. Plan, review, verify the numbers.** Tie every fix to a measurement, don't read source instead of measuring.

1. Capture a baseline trace via the matching driver skill. Vet the baseline, and each later number, with the **benchmark-checklist** skill.
2. `how` to ground hypotheses. Don't claim a perf ceiling without running it first.
   Try the performance mantras in order, cheapest first:
   1. Don't do it. Stop work whose result nothing uses rather than cheapening it.
   2. Do it, but don't do it again.
   3. Do it less.
   4. Do it later.
   5. Do it when they're not looking.
   6. Do it concurrently.
   7. Do it cheaper.

   When an earlier mantra meets the target, stop.
3. Plan the fix from the trace. If it crosses a function boundary, `architect` first. Delegate implementation to a subagent using your configured perf-issue model (default in poteto-mode's Models section). Pick each subagent's reasoning level for the job, per the Subagents section. Review the diff. Capture a post-fix trace.
   Apply the **sequence-verifiable-units** principle skill, verifying each attempt before trying the next.
4. Parse and compare the artifacts (JSON to sqlite, diff). "Inconclusive" or wrong-surface is not a pass. Flag it.
5. Cite the measurement in the PR.
6. Run **Opening a PR**.

For sustained improvement against a metric rather than a one-off fix, use the Hillclimb playbook (`playbooks/hillclimb.md`).

**Reply:** baseline number, post-fix number, delta, artifact path.
