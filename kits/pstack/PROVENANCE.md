# Provenance: pstack

Kit `pstack` 1.0.0, licence MIT. Assembled on 2026-10-24 by 72o Labs from the upstream repository
below at the pinned commit. Contents keep their original licences.

| Upstream | URL | Commit | Licence | Path |
| --- | --- | --- | --- | --- |
| pstack-claude | https://github.com/michael-denyer/pstack-claude | `356c6e0f978df729eb16f227d795f34d221c5aad` | MIT | `plugins/pstack` |

## Changes

- `patches/upstream/<item>.patch`: diff from the pristine upstream file at the pinned commit to this kit's
  file. `a/` paths are relative to the upstream repository root, `b/` paths to this kit folder. Applied
  with `patch -p1` in a checkout of the pinned commit, each patch turns the upstream file into the kit file.
  - `why.patch`: `plugins/pstack/skills/why/SKILL.md` to `skills/why/SKILL.md`.
  - `figure-it-out.patch`: `plugins/pstack/skills/figure-it-out/SKILL.md` to `skills/figure-it-out/SKILL.md`.
  - `investigation.patch`, `bug-fix.patch`, `feature.patch`, `refactoring.patch`, `perf-issue.patch`,
    `prototype.patch`, `session-pickup.patch`, `pause-safely.patch`:
    `plugins/pstack/skills/poteto-mode/playbooks/<name>.md` to `skills/<name>/SKILL.md`.
- Every other file under `skills/` and `agents/` is unchanged: byte-identical to `plugins/pstack/<same path>`.
- `LICENSE`, `LICENSE-cursor-team-kit`, `LICENSE-thermos`, `NOTICE.md` and `NOTICE-skills.md` are unchanged
  copies of the files at the upstream repository root.
- MODIFICATIONS.md states every change in prose.

## pstack (vendored subset)

| Field | Value |
| --- | --- |
| Source | https://github.com/michael-denyer/pstack-claude (path `plugins/pstack`, plus root licence files) |
| Commit | `356c6e0f978df729eb16f227d795f34d221c5aad` (tag-less; `VERSION` 0.9.102, committed 2026-10-23 00:11 +0100) |
| Upstream of the port | https://github.com/cursor/plugins/tree/main/pstack, compared at `8b3326d99fd4b993cb33a24dad8af03175c642c5` (pstack 0.15.30) |
| Licence | MIT (port, © 2026 Michael Denyer; original pstack © 2026 Lauren Tan). Imported cursor-team-kit and thermos skills MIT © 2026 Cursor. See `LICENSE*`, `NOTICE.md`, `NOTICE-skills.md` |
| Licence notes | MIT: ship `LICENSE*` and `NOTICE*.md` with the kit |
| Fetched | 2026-10-23, `git clone` of the source, HEAD as above |
| Copied | `plugins/pstack` from a clone at the commit above, minus the exclusions below |

### Why this source and not cursor/plugins

The upstream `cursor/plugins/pstack` is a Cursor plugin (`.cursor-plugin/plugin.json`): its playbooks name Cursor primitives (`/loop`, `~/.cursor/projects` transcripts, `grok-4.7-xhigh-fast` model defaults, "control skill"). It ships no Claude Code or Codex manifest. The Denyer port tracks upstream (last sync at upstream 7b353f7, v0.15.27) and rewrites those parts for Claude Code (Agent tool, `loop`, Claude transcript paths, resume storage) with a Codex tool map (`skills/poteto-mode/references/codex-tools.md`). One skills tree serves both harnesses, so it is the single source for both.

Diff of the eight playbook files between the two at the pinned commits: wording only (model defaults, `/loop` vs `loop` skill, control vs driver skill), except session-pickup and pause-safely, which the port moved onto a git-dir checkpoint (`scripts/resume.mjs`). figure-it-out is a skill, not a playbook, in both.

### What was kept

- `skills/`: every skill except those excluded below. Byte-identical to the source, except the changes listed under Changes.
- `agents/poteto-agent.md`, `agents/comment-sicko.md` (used by the playbooks and `no-comments`).
- `LICENSE`, `LICENSE-cursor-team-kit`, `LICENSE-thermos`, `NOTICE.md`, `NOTICE-skills.md`.

### What was excluded, and why

| Excluded | Reason |
| --- | --- |
| `hooks/` (all) | `session-start.sh` is the routing hook (injects the poteto-mode mandate at SessionStart). Not shipping it keeps the mandate off without a global file (the documented switch, `session hook: off`, lives in `~/.claude/pstack-models.md`). `pre-tool-use.sh` is Copilot-only and auto-approves reads and registered scripts. |
| `skills/setup-pstack/` | Writes the override sheet into `~/.claude` / `~/.codex` (global dirs). |
| `skills/automate-me/`, `skills/poteto-help/` | Writes a personal mode skill; setup guide that sends users to setup-pstack. |
| `skills/babysit/`, playbooks `babysit`, `shipping`, `worktree-cleanup` | Depend on `watch-pr`, `ship-pr` and `worktree-audit.mjs`, which are not vendored (PR automation, merges, disk pruning). |
| playbooks `orchestrate`, `autopilot-full`, `autopilot-stack`, `autonomous-run` | Not converted and not shipped. |
| `skills/poteto-mode/scripts/orch/`, `watch-pr/`, `bootstrap.ts`, `bun.lock`, `package.json`, `tsconfig.json`, `check-plan.test.ts`, `worktree-audit.mjs`, prettier config | Orchestrate store, PR watcher and merge driver, bun bootstrap, tests. |
| `skills/reflect/SKILL.md`, `reflect/scripts/find-transcript.mjs` | Reflect edits skills from transcripts. Only `reflect/scripts/claude-project-dir.mjs` is kept, because session-pickup calls it by path. |
| `pi/`, `.muse-plugin/`, `.github/`, `.codex-plugin/`, `.claude-plugin/`, `assets/`, `models.json` | Other harnesses, the upstream plugin manifests (this kit is described by `kit.json`), images, model-default source data. |
| `README.md`, `agents/thermo-nuclear-review-subagent.md`, `agents/thermo-nuclear-code-quality-review-subagent.md` | Not part of this kit. |

### Security review (2026-10-23)

No hooks are vendored. Every script that is vendored:

| File | Executes | Network | Writes outside the repo |
| --- | --- | --- | --- |
| `skills/poteto-mode/scripts/resume.mjs` | `git -C <project> rev-parse …` and `git branch --show-current` through `execFileSync` (no shell) | None | No. Writes only under `<git common dir>/pstack/resume/` (mode 0700/0600, atomic rename) and refuses paths that escape it |
| `skills/poteto-mode/scripts/check-playbooks.mjs` | Nothing | None | No. Read-only lint of `<repo>/.agents/playbooks/*.md` |
| `skills/poteto-mode/scripts/check-plan.mjs` | Nothing | None | No. Read-only lint of one plan file |
| `skills/reflect/scripts/claude-project-dir.mjs` | Nothing | None | No writes. **Reads outside the repo**: lists directory names under `$CLAUDE_CONFIG_DIR` or `~/.claude/projects` to find this session's transcript directory; session-pickup then reads transcripts there |
| `skills/show-me-your-work/scripts/log.sh` | `date`, `tr`, `perl` (append only) | None | Appends to whatever log path the agent passes; the skill says to keep it in the repo (`.audit/`) |

Instructions in vendored prose that reach outside the repo or act without asking (flagged for whoever deploys the kit):

- `poteto-mode/SKILL.md` Autonomy: "Reversible work and external actions (team chat, ticket updates, kicking off evals) proceed without asking."
- `poteto-mode/references/codex-tools.md` tells the agent to add `[features] multi_agent = true` to `~/.codex/config.toml` (global config). Not needed: stable and on by default in codex-cli 0.160.1.
- `poteto-mode/playbooks/multi-phase-plan.md` writes plans under `~/.claude/orchestrate/<slug>/docs/` by default and names Orchestrate or an Autopilot playbook as the execution playbook. Neither playbook ships in this kit.
- `poteto-mode/playbooks/opening-a-pr.md` uses `git reset --hard origin/<branch>` between delegates and rebases before opening PRs.
- `why` queries whatever MCP servers the session has (Datadog, Databricks, issue trackers) for evidence: network through those servers.
- `arena`, `swarm`, `interrogate`, `architect` and `how --critique` fan out to several subagents on different models (token cost).
- `poteto-agent.md` searches `~/.claude/plugins` for poteto-mode when its parent gives no path. The converted skills tell the agent to pass it the path of `../poteto-mode/SKILL.md`, so the search is not reached from them.

### Description trim (2026-10-24)

The frontmatter `description` of `skills/why/SKILL.md` was cut to about 350 characters to fit the skill listing: trigger phrases kept, cross-references to skills outside the kit and body-level style rules dropped from the description. The body is unchanged. Recorded in `patches/upstream/why.patch`.

### Playbooks published as skills

Eight playbooks and `figure-it-out` gained new frontmatter and a 72o Labs preamble. See MODIFICATIONS.md; recorded in the matching `patches/upstream/<name>.patch`.
