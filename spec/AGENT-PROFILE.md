# Agent profile format (v1)

An agent profile is one Markdown file, `profiles/<name>.md`: YAML frontmatter, then a body. The build
(`bin/holler-roles build`) turns it into a Claude Code plugin folder and a Codex home template. This
file is the contract between profiles, kits (`spec/KIT.md`) and the build.

## Example

```yaml
---
profile_format: 1
name: eng                        # [a-z][a-z0-9-]*, unique; also the dist folder name
version: 0.1.0                   # semver; bump on any change that alters the build output
display_name: Eng                # human-facing name in launchers
role: Fixes bugs, builds features and answers questions about the code, with runtime evidence.
harnesses: [claude, codex]

layers:                          # brief, in order; files under layers/ (platform/* ships separately)
  - base
  - platform/holler
  - function/eng

skills:                          # listed: visible to the model and invocable by it
  - pstack/bug-fix               # <source>/<skill>
  - web-ui/frontend-design
  - own/release
  - holler/holler-handoff
manual:                          # user-invoked only (/name); not in the model's listing
  - pstack/how
  - holler/holler-teach

agents: [pstack/poteto-agent]    # subagents (Claude); same <source>/<name> references
hooks: [gstack/careful]          # guards (Claude PreToolUse); same references
never: [orchestrate, autopilot-full]   # names the build refuses to ship in any form

models: {}                       # optional recommendation only; unset in the starter team
codex: {sandbox: null}           # optional: read-only | workspace-write (Codex home template config)

holler:                          # the Holler card
  actor: eng                     # actor base name; Holler allocates eng-<hex>
  role_text: >-
    Engineering agent. ...
  accepts:
    - bug report with a symptom or repro

presentation:                    # optional product and brand layer; never sent to the model
  display_name: Ada
  icon_emoji: "👩‍💻"
  icon_brief: A portrait silhouette with an Analytical Engine gear.
  tagline: Builds it
  voice: null                    # reserved; must stay empty
---

# Eng

## Responsibilities
...
## Rules
...
## Done criteria
...
```

## Fields

| Field | Required | Meaning |
| --- | --- | --- |
| `profile_format` | yes | `1` for this spec. |
| `name` | yes | Agent id. Used for the role plugin name, `dist/<name>/`, and the default actor. |
| `version` | yes | Agent version. It must equal the team version in `team.json`: Holler's runtime accepts a bundle only when every agent carries the bundle's version. The build refuses to overwrite a built bundle with different content. In an overlay build (spec/OVERLAY.md) every agent gets the local version instead. |
| `display_name` | yes | Neutral human-facing name (`Eng`, `Product`). `presentation.display_name` may replace it in the UI. |
| `role` | yes | One line: what the agent does. Shown by launchers; not part of the brief. |
| `harnesses` | yes | Subset of `[claude, codex]`. |
| `layers` | yes | Brief layers in order. `layers/<path>.md` in the overlay or this repository. An overlay's `personal/<name>.md` is appended after the body (spec/OVERLAY.md). Layers under `platform/` are delivered separately (their own SessionStart hook on Claude; appended on Codex). Each delivered text must stay at or under 9,800 characters. |
| `skills` | yes | Skill references the model sees and may invoke. |
| `manual` | no | Skill references shipped user-invoked only. Claude: `disable-model-invocation: true`. Codex: `agents/openai.yaml` with `policy.allow_implicit_invocation: false`. |
| `agents` | no | Subagent references. Claude only. |
| `hooks` | no | Guard references. Claude only (Codex hooks need per-hook trust in its UI). Each hook ships with tests that the build runs. |
| `never` | no | Names that must not appear in the build as a skill, playbook, agent, hook or plugin. The build fails if one does. |
| `models` | no | **Recommendation only, unset by default.** `{claude: {model, effort}, codex: {model, effort}}`. The build records it in `launch.json` under `recommended_models` and never writes it into a launch command or Codex config. The user's harness default applies; the user can change the default and switch models mid-conversation. |
| `claude` | no | Not allowed in launch format 1: `extra_args` must be empty (spec/LAUNCH.md). Restrict an agent with a hook. |
| `codex.sandbox` | no | Written into the Codex home template's `config.toml` (`sandbox_mode`); never an argument. |
| `holler.actor` | yes | Actor base name; must equal `name` (Holler's runtime starts the agent under that actor base). Launchers set `HOLLER_ACTOR=<actor>`, `HOLLER_ROLE=<actor>`, `HOLLER_NAME_MODE=allocate`, `HOLLER_DISPLAY_NAME=<display name>`. Configurable; the starter team uses the role names. |
| `holler.role_text`, `holler.accepts` | yes | The Holler card the session publishes with `holler_profile`. Holler's limits: `role_text` at most 2,048 bytes; `accepts` at most 32 entries of at most 64 bytes each (longer entries are rejected by Holler, so the build refuses them). Quote entries that contain `: `. |
| `presentation` | no | Product and brand layer, below. Not sent to the model. |

### Skill references

A reference is `<source>/<name>`:

| Source | Resolves to | Ships as |
| --- | --- | --- |
| `<kit>` (a kit name in `kits.lock`) | `kits/<kit>/kit.json` entry `skills[].name` / `agents[].name` / `hooks[].name` in the pinned kits checkout | Claude plugin `<kit>` (namespace `<kit>:<name>`); Codex `skills/<kit>/skills/<name>` |
| `own` | `skills/<name>/`, `agents/<name>.md` or `hooks/<name>/` in the overlay (spec/OVERLAY.md) or this repository | the role plugin `<agent>` (`<agent>:<name>`) |
| `holler` | `skills/holler-*` in this repository | the shared `holler-platform` plugin (`holler-platform:<name>`) |

**Replacing an open-licensed skill.** A profile names a skill only by reference. To swap
`web-ui/frontend-design` for an original or your own skill, write `own/frontend-design` (or add
another kit source with the same `kit.json` contract, for example your own kit repository, to
`kits.lock`) and change the one reference. The profile format, the build and the dist layout do not change.
Two references resolving to the same skill name in one agent are refused.

### Listing budget

An agent should list at most about 16 skills (`skills`), the holler skills included. Put rarely
needed skills under `manual`. The build prints the listed and manual counts and fails above 18.

## Body

The body is part of the brief, after the layers. Sections: `Responsibilities`, `Rules`, `Done criteria`.
Briefs are rules and done-criteria, never persona or backstory. No user-, company- or product-specific
facts: the starter agents work in any repository.

Every brief ends with a marker line `Brief marker: <text>` (the function layer carries it) so a load test
can ask the model to quote it.

## Presentation

`presentation` is the product and brand layer: how the agent appears to humans in launchers and in
Holler's app. It is optional. It is **not** sent to the model: the agents talk in the model's default
voice, and the functional brief stays rules-only.

| Field | Meaning |
| --- | --- |
| `display_name` | Name shown to humans (for example on Holler's Agents page). Instantly recognizable, generic figures only: no franchise characters. |
| `icon_emoji` | The v0.1 icon: an emoji. `launch.json` carries it as `icon` and `icon_emoji`. |
| `icon_brief` | Text cue for the icon artist (for example "owl or Greek helmet"), for later art. |
| `tagline` | One short line. |
| `voice` | Reserved, optional, empty (`null`). If a future profile sets it, the build must deliver it as a short section after the brief that changes tone only, never the work or any required message format. The build currently refuses a non-null `voice`. |

The build copies `presentation` into `launch.json` for launchers and the app. Actor base names stay
separate (`holler.actor`) so a display name can change without changing Holler identities.

## Build output

`bin/holler-roles build` writes the team bundle `dist/<team>-<version>/` and `dist/<team>-<version>.tar.gz`
(layout, `manifest.json` and `launch.json` in spec/LAUNCH.md). Per agent, `<bundle>/<agent>/`:

- `claude/plugins/`: one `--plugin-dir`. The role plugin `<agent>` (the brief and its SessionStart hook, own
  skills, own hooks), `holler-platform` (the platform layer and its hook, the holler skills), and one plugin per
  kit used (selected skills, agents and hooks, with the kit's licence, notice and provenance files).
- `codex/home-template/`: `AGENTS.md` (brief, then the platform layer), `config.toml` (no model or approval
  settings), `skills/<plugin>/...` (the same skill folders), `HOME-SETUP.md`.
- `launch.json` (spec/LAUNCH.md) and `MANIFEST.json` (the agent's build record).

All paths in the output are relative; the build output is byte-for-byte reproducible from the same sources.
