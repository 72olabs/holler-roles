---
name: investigation
description: "Answer a question about the code without changing it. Use for \"how does X work\", \"why does X do Y\", \"where is X handled\", \"what calls this\", \"are we sure about X\", \"should we do X or Y\", \"explain this code\". Read-only; replies with cited evidence."
---

<!-- holler-roles: converted from pstack skills/poteto-mode/playbooks/investigation.md at 356c6e0f978d (MIT, see ../../LICENSE). Frontmatter and this preamble are added; the text after the rule is unchanged. -->

**Before you start**

Paths in this preamble are relative to this skill's folder.

1. Read the Principles section of the pstack principles index, `../poteto-mode/SKILL.md`. Before applying a principle, read its leaf skill at `../principle-<name>/SKILL.md`.
2. Open a task list whose first items are this playbook's steps, copied verbatim. A step you skip stays on the list with `skip: <reason>`.
3. Do not report done without runtime evidence: output from running the changed thing on the surface the task names. Tests or "it compiles" alone are not done.

Reading the playbook: its relative links resolve from `../poteto-mode/playbooks/`. "The installed plugin", `<plugin>` and "this pstack" mean the folder two levels up from this skill (`../..`), which holds `skills/` and `agents/`. The sections it cites (Non-negotiables, Subagents, Models, Writing the reply) are in the principles index; Opening a PR is `../poteto-mode/playbooks/opening-a-pr.md`. A skill it names that is not in your skill list is a file at `../<name>/SKILL.md`: read it instead of invoking it. When you spawn `pstack:poteto-agent`, give it the absolute path of `../poteto-mode/SKILL.md`. On Codex, map Claude tool and model names with `../poteto-mode/references/codex-tools.md`.

---

### Investigation

**You own the answer. Plan, route, write.**

Investigation requests are read-only. They produce a cited explanation or a recommendation, not a code change.

1. Route through the **how** skill. For motivation questions, also route through the **why** skill.
2. Throughput checkpoint stays one line: `throughput checkpoint: n/a, read-only investigation`.
3. Produce the `how`-shaped output (Overview / Key Concepts / How It Works / Where Things Live / Gotchas), or a recommendation with a tradeoffs table if the request is a decision between alternatives.
4. Apply the **unslop** skill to the reply.

No PR, no babysit, no `architect` unless the investigation precedes a code change. If it does, hand back to the user and re-route to Bug fix or Feature.

**Reply:** the investigation output. For "are we sure?" answers, include your real judgment with reasons. Push back if the premise is wrong (see Autonomy).
