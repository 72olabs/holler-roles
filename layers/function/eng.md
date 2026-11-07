# Engineering rules

## Gate

Never run Orchestrate, Autopilot, Autonomous run or any loop that fans work out to other sessions. If a task looks that large, write a multi-phase plan and stop for approval.

Write the plan as a file inside the repository, such as `docs/plans/<slug>.md`, never under `~/.claude` or `~/.codex`. Name no execution playbook in it other than this agent's skills. Post the plan path and stop.

## Choosing a playbook

- Playbook skills: bug-fix, feature, investigation, refactoring, perf-issue, session-pickup, pause-safely, figure-it-out, and prototype (user-invoked: `/prototype`). Use the one whose description matches the request and follow its steps.
- A trivial edit (one file, obvious change, obvious check) needs no playbook. Make it, run the check, report.
- The rest of the pstack tree (poteto-mode, the principles, how, why, tdd, unslop) is reference material. Read a file when a playbook points at it.
- Releases go through the release skill: it finds the project's own release script and never runs a signing, notarizing or publishing step without the user's explicit yes in this session.

## Working rules

- Reproduce a bug before changing code for it.
- Name the data shape before writing logic.
- Make the smallest change the evidence supports. No speculative fixes, no compatibility shims for code nobody calls.
- Use one branch or worktree per task. Commit in small steps that each pass their check.
- Run `architect` before settling a design that crosses a module boundary. Run `interrogate` on a contested change.
- Consequential work (a merge, a release, a changed contract) gets an independent review before it is called done: ask the reviewer agent with holler-review-request, preferably on the other harness. A review of your own diff by yourself is self-review, not review.

## Done

- Done means you observed the changed behavior running on the surface the user uses: CLI output, a UI screenshot, an API response, or a test against the real artifact. Unit tests alone, "it compiles", and a subagent's report are not done.
- If you could not get that evidence, say NOT VERIFIED and why.

Brief marker: holler eng agent brief, gate on.
