# Kit format (v1)

A kit is a folder of third-party skills, with the licences, notices and provenance that let us ship them.
Kits live in this repository under `kits/<kit>/`, one folder per kit, each under its own upstream licence (the
rest of the repository is Apache-2.0). `kits.lock` pins every kit by content hash, so a change to vendored text
that skips its patch and NOTICE.md fails the build. Kits from another repository, and your own kits in an overlay
(spec/OVERLAY.md), use the same format.

## Folder

```
kits/<kit>/
  kit.json            required
  LICENSE*            required: every upstream licence, verbatim
  NOTICE.md           required: attribution and every change in prose
  PROVENANCE.md       required: upstream URLs and commits, review record, how the kit was made
  patches/            required when anything differs from upstream: patches/upstream/*.patch (upstream ->
                      reviewed copy), patches/holler/<kit>.patch (reviewed copy -> kit)
  skills/<name>/      Agent Skills folders: SKILL.md with YAML frontmatter `name` and `description`
                      (<= 1024 characters), plus any files the skill references by relative path
  agents/<name>.md    optional Claude subagents
  hooks/<name>/       optional hooks, each with tests
  upstream/           optional pristine upstream files a skill was built from
```

## kit.json

```json
{
  "kit_format": 1,
  "name": "gstack",
  "version": "1.0.0",
  "description": "One sentence.",
  "upstream": "https://github.com/garrytan/gstack",
  "sha": "b04cc35832183a89ed71eed628de15a6f315a1a8",
  "licence": "MIT",
  "upstreams": [{"name": "gstack", "url": "...", "sha": "...", "licence": "MIT", "path": "careful"}],
  "licence_files": ["LICENSE", "LICENSE-Apache-2.0.txt"],
  "notices": ["NOTICE.md", "PROVENANCE.md"],
  "patches": ["patches/holler/gstack.patch", "patches/upstream/careful.patch"],
  "bundle": "skills",
  "skills": [{"name": "office-hours", "path": "skills/office-hours", "description": "..."}],
  "agents": [{"name": "poteto-agent", "path": "agents/poteto-agent.md", "harnesses": ["claude"]}],
  "hooks": [{
    "name": "careful", "path": "hooks/careful", "harnesses": ["claude"],
    "event": "PreToolUse", "matcher": "Bash",
    "command": ["/bin/bash", "check-careful.sh"], "timeout": 10,
    "tests": "tests/run_cases.py", "description": "..."
  }]
}
```

| Key | Meaning |
| --- | --- |
| `name`, `version` | Kit id (`[a-z][a-z0-9-]*`) and kit version. The id becomes the Claude plugin name, so it must not collide with a commonly installed plugin, and Claude Code reserves names that start with `claude-`, `anthropic-`, `anthropics-` or `cc-plugin-` (`claude plugin validate` refuses them). Name a kit for what it does. |
| `upstream`, `sha`, `licence` | The primary upstream, its pinned commit and the SPDX-style licence of the kit as shipped (`MIT`, `Apache-2.0`, `MIT AND Apache-2.0`). |
| `upstreams` | Every source the kit draws on, primary first. |
| `licence_files`, `notices` | Paths relative to the kit; the build copies all of them into every plugin and Codex folder made from the kit. |
| `patches` | Every patch file. |
| `bundle` | `skills`: ship only the selected skill folders. `whole`: ship the kit's whole `skills/` tree because skills reference each other by relative path (`../poteto-mode/...`); unselected skills are hidden (Claude `disable-model-invocation: true` and `user-invocable: false`; Codex `agents/openai.yaml` `policy.allow_implicit_invocation: false`). |
| `skills[]` | `name` (equals the SKILL.md `name`), `path`, `description` (equals the SKILL.md `description`). Only listed skills can be referenced by profiles. `added: true` marks a folder the kit added that no upstream file references; with `bundle: whole` it ships only when a profile selects it. |
| `agents[]` | Subagents a profile may select; `harnesses` says where they work. |
| `hooks[]` | Hooks a profile may select. `command` is argv relative to the hook folder; the build writes `"${CLAUDE_PLUGIN_ROOT}/hooks/<name>/..."`. `tests` is run (with `python3 -I`) by every build; a hook without passing tests does not ship. |

## Rules

- Skills follow the Agent Skills format (`SKILL.md` with `name` and `description`), so the same folder
  works in Claude Code and Codex. Relative paths inside a skill resolve from its folder; with
  `bundle: skills`, a skill may only reference files inside its own folder or `../../` (kit root:
  licences and notices).
- A kit never carries personal, customer or company-specific facts, and never instructs an agent to edit
  global configuration (`~/.claude`, `~/.codex`, `~/.agents`).
- Material without a clear open licence is not a kit. Neither is Anthropic's docx, xlsx, pptx or pdf.
- The build checks every kit's `licence` (an SPDX expression) against an allowed list of permissive licences
  (`ALLOWED_LICENCES` in `tools/holler_roles/kits.py`: MIT, Apache-2.0, BSD-2/3-Clause, ISC, 0BSD, CC0-1.0,
  CC-BY-4.0, Unlicense), and every `upstreams[].licence` must name one of them and no copyleft, non-commercial
  or `NOASSERTION` terms. A kit failing either is refused.
- Your own kit under your own terms uses the same format from your own repository, with
  `licence: LicenseRef-<name>`: add it to `kits.lock` as another source. Profiles reference it exactly like an
  open-licensed kit. Don't redistribute a bundle that contains it unless its terms allow that.

## Lock

`kits.lock` in this repository:

```json
{
  "lock_format": 2,
  "kits": {"pstack": {"version": "1.0.0", "licence": "MIT", "content_hash": "sha256:..."}},
  "sources": {
    "my-kits": {
      "repo": "https://github.com/<you>/my-kits.git",
      "commit": "<40-hex SHA>",
      "checkout": "../my-kits",
      "kits": {"house-style": {"version": "1.0.0", "licence": "LicenseRef-mine", "content_hash": "sha256:..."}}
    }
  }
}
```

- `kits`: every folder under `kits/`, by tree hash. A kit folder missing from the lock, or a hash that differs,
  stops the build.
- `sources` (optional): other repositories of kits, each pinned by commit; `checkout` is relative to this
  repository. The build refuses a checkout whose `HEAD` differs from `commit`, uncommitted changes under its
  `kits/`, or a kit whose hash differs from `content_hash`.
- Overlay kits (`<overlay>/kits/<kit>/`) are not pinned; they pass the same format and licence checks.
- A kit name may come from only one place.

`bin/holler-roles lock` records the hashes of `kits/` and re-pins every source to its checkout's current commit.
