# Overlay format (v1)

An overlay is a folder of your own agent sources, kept outside this repository. It lets you personalise the starter
roles, add roles of your own and keep both across releases without forking. Every command takes
`--overlay DIR`; `HOLLER_ROLES_OVERLAY=DIR` sets it for a shell. Without one, the build is a release build of this
repository alone.

## Layout

```
<overlay>/
  personal/<agent>.md     your personal layer for an agent: appended to that agent's brief, after the profile body
  profiles/<name>.md      a new role, or a replacement for this repository's profile of the same name
  layers/<path>.md        layers your profiles name (layers/function/<name>.md for a new role)
  skills/<name>/          original skills, referenced as own/<name>
  hooks/<name>/           original guards (hook.json and tests), referenced as own/<name>
  agents/<name>.md        Claude subagents, referenced as own/<name>
  kits/<kit>/             third-party skills with their licences (spec/KIT.md), referenced as <kit>/<skill>
  team.json               optional: {"agents": [...]}, the agents to build
```

Every part is optional. Dotfiles and dot-folders (`.git`) are ignored, so the overlay can be its own git repository.

## Resolution

- **Sources.** A profile, layer, original skill, guard or subagent is read from the overlay when the overlay has it,
  else from this repository. The holler-* coordination skills are always this repository's. Kits come from this
  repository's `kits/`, the sources in `kits.lock` and the overlay's `kits/`; a kit name may come from only one of
  them. Overlay kits are not pinned, but pass the same format and licence checks.
- **Personal layer.** `personal/<agent>.md` is appended to that agent's brief under a "Personal layer" heading that
  tells the model it refines the rules above and never changes a required message format, an approval rule or the
  brief marker. It counts toward the 9,800-character brief limit. Write preferences and house rules, not secrets:
  the brief is shipped to the model on every session start.
- **MCP servers.** An overlay profile may declare `mcp` under the same rules (spec/AGENT-PROFILE.md): remote
  HTTPS servers or pinned `npx`/`uvx` packages, environment variable names only.
- **Agents.** With `team.json`, exactly its `agents`, in order. Without it, this repository's team plus every overlay
  profile not already in it. `holler.actor` must equal the agent's name.

## Output

- Overlay builds go to `dist/local/starter-team-<version>/` and `dist/local/starter-team-<version>.tar.gz`; a
  release in `dist/` is never touched.
- `<version>` is `<team version>+local.<12 hex>`, the hex from a hash of the overlay's files. Every agent in the
  bundle carries it (Holler's runtime requires one version per bundle), whatever its profile says. Change the overlay
  and the version changes: rebuild before `home`, `launch` or `verify`, with the same overlay.
- `manifest.json` records `source.overlay`, the overlay hash. The bundle is otherwise an ordinary launch format 1
  bundle (spec/LAUNCH.md), so it passes the same `verify` and the same runtime checks. The build refuses absolute
  paths from your machine in the output, including the overlay's own path.

## Creating a role

`holler-roles new <name> [--display NAME]` writes `profiles/<name>.md` and `layers/function/<name>.md` into the
overlay (or into this repository when no overlay is set) and refuses to overwrite. The scaffold builds as-is, with
the Holler coordination skills and no others. Then:

1. Write the role line, the Holler card (`role_text`, `accepts`) and the body: Responsibilities, Rules, Done criteria.
2. Put the rules that make the role different into its function layer, ending with its `Brief marker:` line.
3. List its skills: kit skills (`<kit>/<skill>`), your own (`own/<skill>`) and the coordination skills.
4. `holler-roles build`, `verify --no-codex`, then `launch <name> claude` or `home` and `launch` for Codex.
