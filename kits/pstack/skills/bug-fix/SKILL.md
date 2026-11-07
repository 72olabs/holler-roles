---
name: bug-fix
description: "Fix broken behavior. Use when the user reports a bug or regression: \"X is broken\", \"doesn't work\", \"stopped working\", \"still shows X after Y\", \"wrong output\", \"error when\", \"crashes\", \"used to work\", \"fix this\". Reproduce first, find the root cause, fix it, and show the failing-then-passing run."
---

<!-- holler-roles: converted from pstack skills/poteto-mode/playbooks/bug-fix.md at 356c6e0f978d (MIT, see ../../LICENSE). Frontmatter and this preamble are added; the text after the rule is unchanged. -->

**Before you start**

Paths in this preamble are relative to this skill's folder.

1. Read the Principles section of the pstack principles index, `../poteto-mode/SKILL.md`. Before applying a principle, read its leaf skill at `../principle-<name>/SKILL.md`.
2. Open a task list whose first items are this playbook's steps, copied verbatim. A step you skip stays on the list with `skip: <reason>`.
3. Do not report done without runtime evidence: output from running the changed thing on the surface the task names. Tests or "it compiles" alone are not done.

Reading the playbook: its relative links resolve from `../poteto-mode/playbooks/`. "The installed plugin", `<plugin>` and "this pstack" mean the folder two levels up from this skill (`../..`), which holds `skills/` and `agents/`. The sections it cites (Non-negotiables, Subagents, Models, Writing the reply) are in the principles index; Opening a PR is `../poteto-mode/playbooks/opening-a-pr.md`. A skill it names that is not in your skill list is a file at `../<name>/SKILL.md`: read it instead of invoking it. When you spawn `pstack:poteto-agent`, give it the absolute path of `../poteto-mode/SKILL.md`. On Codex, map Claude tool and model names with `../poteto-mode/references/codex-tools.md`.

---

### Bug fix

**You own this task. Plan, review, verify.** Delegate investigation and the fix to subagents, stay in the lead. Pick each subagent's reasoning level for the job, per the Subagents section.

Be scientific. Every shipped line traces to runtime evidence. Belt-and-suspenders that "might help" is a hypothesis, not a fix. It does not ship. When evidence refutes a hypothesis, revert what it motivated. The smallest change the evidence justifies ships, nothing more.

1. Reproduce it yourself on the matching surface via the driver skill (Non-negotiables), even when a debug or instrumentation protocol says to ask the user to reproduce. Ask the user only with a stated, specific reason the control surface cannot reach the target, and only after driving it as far as it goes. If it won't reproduce directly, synthesize the trigger, tighten conditions, or instrument until it fires.
2. Binary-search the cause. Form the candidate hypotheses, then rule them out until one survives. Seed them with `how` over the affected subsystem and the **why** skill for regression history. Each pass, take the split that cuts the most remaining problem space, get runtime evidence, eliminate. When program state is unclear, add instrumentation or logging and read it as the code runs. Don't guess. Drive a long or stubborn hunt with Claude Code's `loop` skill. Confirm the surviving *mechanism* with runtime evidence before the step-3 architect/interrogate fan-out.
3. Plan the fix. If it crosses a function boundary, `architect` first. Delegate implementation to a subagent using your configured bug-fix model (default in poteto-mode's Models section) with a specific scope.
4. Verify on the same surface. The original repro now passes. "Inconclusive" or wrong-surface is not a pass. Flag it. Unit tests show branch behavior, not bug absence.
5. Stage the commits so the failing repro lands before the fix in git history. See the **tdd** skill for the failing-test-first cadence when the bug has a cheap local test path. Skip it when the test would be expensive, integration-heavy, or unclear.
   This is the canonical **sequence-verifiable-units** principle skill, the failing test first and the fix on top.
6. Run **Opening a PR**.

**Reply:** what was broken, root cause, fix, how you verified. Quote the decisive failing and passing output, trimmed to the assertion and the counts.
