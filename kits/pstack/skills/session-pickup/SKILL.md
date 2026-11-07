---
name: session-pickup
description: "Resume earlier work. Use for \"where were we\", \"catch me up\", \"what's left\", \"pick up where we left off\", \"continue from yesterday\", \"resume\", \"take over this branch\". Reads the saved checkpoint or prior transcript before doing anything."
---

<!-- holler-roles: converted from pstack skills/poteto-mode/playbooks/session-pickup.md at 356c6e0f978d (MIT, see ../../LICENSE). Frontmatter and this preamble are added; the text after the rule is unchanged. -->

**Before you start**

Paths in this preamble are relative to this skill's folder.

1. Read the Principles section of the pstack principles index, `../poteto-mode/SKILL.md`. Before applying a principle, read its leaf skill at `../principle-<name>/SKILL.md`.
2. Open a task list whose first items are this playbook's steps, copied verbatim. A step you skip stays on the list with `skip: <reason>`.
3. Do not report done without runtime evidence: output from running the changed thing on the surface the task names. Tests or "it compiles" alone are not done.

Reading the playbook: its relative links resolve from `../poteto-mode/playbooks/`. "The installed plugin", `<plugin>` and "this pstack" mean the folder two levels up from this skill (`../..`), which holds `skills/` and `agents/`. The sections it cites (Non-negotiables, Subagents, Models, Writing the reply) are in the principles index; Opening a PR is `../poteto-mode/playbooks/opening-a-pr.md`. A skill it names that is not in your skill list is a file at `../<name>/SKILL.md`: read it instead of invoking it. When you spawn `pstack:poteto-agent`, give it the absolute path of `../poteto-mode/SKILL.md`. On Codex, map Claude tool and model names with `../poteto-mode/references/codex-tools.md`.

---

### Session pickup

**You own the resume point. Read the prior trail, don't redo it.**

1. Read the project checkpoint first using [Resume storage](../references/resume-storage.md). A successful read gives the note and artifacts without requiring a path from the previous session. If the pointer is missing, locate the prior trail through a local transcript under Claude Code's per-project transcripts directory at `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects/<encoded-cwd>/*.jsonl` (`node <plugin>/skills/reflect/scripts/claude-project-dir.mjs` prints this session's directory, which holds the earlier sessions that started in the same directory. For one that started elsewhere, pass its start directory: `node <plugin>/skills/reflect/scripts/claude-project-dir.mjs "<start directory>"`. Do not glob across other directories under `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects/`, that crosses workspace boundaries and reads private chats from unrelated projects), a cloud-agent URL, or a pushed branch. An unavailable or incomplete checkpoint needs diagnosis rather than a silent fallback. For transcript fallback, read the metadata overview and last messages first, then scan back for the decision points. Parse a long transcript in a subagent and keep the reduced timeline in the main thread (the **principle-guard-the-context-window** skill). Pick each subagent's reasoning level for the job, per the Subagents section.
2. Reconstruct operational state. The branch and worktree, what already landed (`git log`, `git diff` against the base), the open todos, the decisions made. Use the prior trail to recover progress. For claims about human rulings, follow [Claims about human decisions](../../why/references/epistemics.md#claims-about-human-decisions). An agent summary is not the original ruling.
3. Diff done vs pending. Compare what shipped against what was planned, name the resume point, do not re-run the prior repro or redo completed work. Recheck claims that affect the remaining work without repeating completed investigations. Read artifacts linked by the resume note, including requested questions or checklists.
4. Route the remaining work to the matching playbook and pick the verdict: continue the execution, ship a finished recommendation, ratify or override a prior conclusion, or postmortem a failed run. The pickup playbook ends here. The routed playbook owns the rest.
5. Verify the inherited claims against the original goal on the real artifact (the **principle-prove-it-works** skill). A passing prior self-report is not the proof.

**Reply:** where the prior agent stopped, what you inherited vs redid (ideally nothing redone), the resume point, and the outcome.
