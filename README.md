# holler-roles

Role-based agents for Claude Code and Codex. A **role profile** is one Markdown file: the rules the agent works by
(layers), the skills it may use, its guards and its Holler card. `holler-roles` builds a profile into a Claude Code
plugin folder and a Codex home, so you run the role in your own harness, on your own account.

This repository holds Holler's starter team, the Holler coordination layer every agent carries, curated third-party
skill kits, and the build. It works with [Holler](https://github.com/72olabs/holler-connectors), which lets the agents
hand work to each other, ask for reviews and bring decisions to you.

## Starter team 0.2.0

| Agent | Display name | Does | Listed / manual skills | Guard |
| --- | --- | --- | --- | --- |
| eng | Ada | Fixes bugs, builds and refactors features, with runtime evidence | 16 / 8 | careful (gstack kit) |
| product | Athena | Discovery, PRDs, experiments; drafts only | 15 / 2 | experiment-registry |
| reviewer | Sherlock | Independent code and design review, one verdict per version; read-only | 10 / 2 | readonly-guard; Codex home read-only |
| designer | Leo | Directions, DESIGN.md, prototypes, design review requests | 12 / 2 | - |

Every agent carries `layers/platform/holler.md` and the five `skills/holler-*`. Models are not pinned: your
harness's default applies.

## Quick start

Needs Python 3.11+, git, and PyYAML or Ruby (to read YAML frontmatter).

```sh
bin/holler-roles build            # dist/starter-team-0.2.0/ and its .tar.gz
bin/holler-roles verify           # kit pins and licences, hashes, launch contract, plugins, Codex listing, reproducibility
bin/holler-roles launch eng claude                                     # Claude Code with the eng role
bin/holler-roles home eng ~/agents/eng/codex --project <dir>           # a Codex home for eng, then:
bin/holler-roles launch eng codex --home ~/agents/eng/codex
```

`launch --print` prints the command instead of running it. Install the Holler connector for your harness first if
you want the agents to talk to each other; without it the Holler skills have nothing to call.

## Make a role your own

Your changes live in an **overlay**: a folder outside this repository, so you can pull new releases without merge
conflicts (spec/OVERLAY.md).

```sh
export HOLLER_ROLES_OVERLAY=~/my-agents
mkdir -p ~/my-agents/personal
$EDITOR ~/my-agents/personal/eng.md            # your preferences, added to the end of eng's brief
bin/holler-roles new support --display Support   # a new role: ~/my-agents/profiles/support.md and its function layer
bin/holler-roles build && bin/holler-roles verify --no-codex
bin/holler-roles launch support claude
```

An overlay can add roles, replace a role's profile, add layers, original skills, guards and third-party kits, and
pick which agents to build (`team.json` with `agents`). Overlay builds go to `dist/local/` with version
`0.2.0+local.<hash>` and never replace a release.

To build a role from skills, list them in the profile: `<kit>/<skill>` from a kit (below, or your own), `own/<skill>` from
`skills/` (yours or this repository's) and `holler/<skill>` for coordination. `bin/holler-roles list` shows each
agent's listing size; keep it to about 16 listed skills and move the rest to `manual`.

A profile can also bring MCP servers (`mcp`): remote HTTPS servers, or `npx`/`uvx` packages pinned to an exact
version, with environment variables passed through by name. Their tools prompt like any other; see
spec/AGENT-PROFILE.md.

## Skill kits

`kits/` holds third-party skills, curated and adapted for these roles, each under its own upstream licence:

| Kit | Licence | Skills | Upstream |
| --- | --- | --- | --- |
| `pstack` | MIT | engineering playbooks: bug fix, feature, investigation, refactoring, perf, architect, interrogate and more | michael-denyer/pstack-claude (port of Lauren Tan's pstack) |
| `web-ui` | Apache-2.0 | frontend-design, webapp-testing | anthropics/skills |
| `gstack` | MIT | office-hours, design-system-doc, design-variants; the `careful` guard | garrytan/gstack |
| `pm-skills` | MIT | interview-script, opportunity-solution-tree, strategy-red-team, create-prd, beachhead-segment | phuryn/pm-skills |
| `marketingskills` | MIT | product-marketing, customer-research, launch, pricing | coreyhaines31/marketingskills |
| `growth-gate` | MIT | a pre-publish check for drafts | adapts marketingskills and kai-cmo-harness |
| `opendesign-craft` | Apache-2.0 | typography, color, motion, state-coverage | nexu-io/open-design |
| `design-review-rules` | MIT and Apache-2.0 | design-review-passes, slop-tells, a11y-floor | gstack, open-design, anthropics/skills, vercel-labs/web-interface-guidelines |

Each kit records its upstream commit, every change we made (NOTICE.md and patches) and its review (PROVENANCE.md).
`kits.lock` pins each kit by content hash. The build accepts only permissive licences.

## Contracts

| Spec | Covers |
| --- | --- |
| `spec/AGENT-PROFILE.md` | The profile format: fields, skill references, layers, the Holler card |
| `spec/OVERLAY.md` | Your own roles, layers, skills and personal layers |
| `spec/KIT.md` | Third-party skill kits, their licences and `kits.lock` |
| `spec/LAUNCH.md` | The bundle, `launch.json` and what Holler's runtime enforces when it starts an agent |

Sources: `profiles/`, `layers/`, `skills/` (holler-* and original skills), `hooks/` (original guards),
`tools/holler_roles/` (the build), `tests/` (offline tests and a one-run load check per agent and harness).

## The Holler coordination layer

`layers/platform/holler.md` is an always-on brief of about 60 lines: when to involve another agent, what a handoff,
review or decision must contain, what to propose instead of doing, and how to teach the user one feature at a time.
The five skills carry the procedures:

| Skill | Purpose |
| --- | --- |
| `holler-handoff` | Hand work to another session, or accept one, with the version and acceptance check |
| `holler-review-request` | Request or give an independent, version-bound review |
| `holler-decision-request` | One decision for the human, through to the outcome |
| `holler-team-setup` | Names and conversations, proposed as an exact change set |
| `holler-teach` | One feature, one sentence, in the app's words |

The connector's own `holler` skill teaches the mechanics (routing, claim and ACK, aliases); this layer adds only the
coordination judgment. Agents never orchestrate each other: writes stay with one agent, others review and advise,
and anything visible to other people is proposed to the human first.

## Licence

Apache-2.0 (LICENSE, NOTICE). Kits keep their own licences. Contributions: CONTRIBUTING.md (this repository is generated
from a private source; pull requests are welcome and imported by hand). Security: SECURITY.md.
