# Launch contract (launch format 1)

Holler's runtime (`holler agent start --role <r> --harness claude|codex --project <dir> --bundle <dir>
[--model <m>] [--effort <e>] [--access ask|full]`) starts a default agent from a starter-team bundle by reading
that agent's `launch.json`. `--role none` starts a plain session with no bundle (see below). This file is the contract
between `bin/holler-roles build` and the runtime. Anything outside it is `bundle_invalid`.

## Bundle layout

```
<bundle>/                         e.g. starter-team-0.1.0/ (the tarball unpacks to exactly this)
  manifest.json                   every other file with its sha256
  LICENSE                         Apache-2.0 for the holler-roles parts; kits keep their own licences
  NOTICE.md                       every third-party kit in the bundle, with upstreams and licence locations
  <agent>/launch.json             one per agent: eng, product, reviewer, designer
  <agent>/MANIFEST.json           the agent's own build record (kits used, sizes)
  <agent>/claude/plugins/         one --plugin-dir: role plugin, holler-platform, one plugin per kit
  <agent>/codex/home-template/    AGENTS.md, config.toml, skills/, HOME-SETUP.md
```

The tarball `<bundle>.tar.gz` is deterministic (sorted entries, mtime 0, uid/gid 0, no user names, gzip
without name or time) and holds no symlinks or hard links. `<bundle>.tar.gz.sha256` sits next to it.

## manifest.json

```json
{
  "manifest_format": 1,
  "bundle": "starter-team",
  "version": "0.1.0",
  "source": {"holler-agents": "<commit>[-dirty]"},
  "kits": {"<external kit source>": {"repo": "<url>", "commit": "<sha>"}},
  "agents": [{"agent": "eng", "version": "0.1.0", "display_name": "Ada", "icon": "👩‍💻",
              "launch": "eng/launch.json", "content_hash": "sha256:...", "harnesses": ["claude", "codex"],
              "listed_skills": 16, "manual_skills": 8}],
  "files": [{"path": "eng/launch.json", "sha256": "<hex>", "size": 1234}]
}
```

- `source.holler-agents` is the holler-roles commit the bundle was built from (the key keeps its original name);
  kits in the repository's own `kits/` are covered by it. `kits` lists only external kit sources (spec/KIT.md).
- `files` lists every file in the bundle except `manifest.json` itself, with paths relative to the bundle root.
- The runtime verifies every hash before it reads any `launch.json`, and again at launch. A missing, extra or
  changed file is `bundle_invalid`.
- `content_hash` is the build's tree hash of `<agent>/` (path, exec bit and sha256 of each file, excluding
  `MANIFEST.json`); informational for the runtime, checked by `bin/holler-roles verify`.

## launch.json schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "holler-agents/launch-format-1",
  "type": "object",
  "required": ["launch_format", "agent", "version", "display_name", "icon", "env", "holler", "first_prompt", "harnesses"],
  "additionalProperties": false,
  "properties": {
    "launch_format": {"const": 1},
    "agent": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
    "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+([-+][0-9A-Za-z.-]+)?$"},
    "display_name": {"type": "string", "minLength": 1, "maxLength": 64},
    "icon": {"type": ["string", "null"], "description": "v0.1: an emoji (same as icon_emoji); later an icon ID or a bundle-relative image path"},
    "icon_emoji": {"type": ["string", "null"]},
    "icon_brief": {"type": ["string", "null"], "description": "text cue for the icon artist; not shown to the model"},
    "tagline": {"type": ["string", "null"]},
    "role": {"type": "string"},
    "env": {
      "type": "object",
      "additionalProperties": false,
      "required": ["HOLLER_ACTOR", "HOLLER_ROLE", "HOLLER_NAME_MODE", "HOLLER_DISPLAY_NAME"],
      "properties": {
        "HOLLER_ACTOR": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
        "HOLLER_ROLE": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
        "HOLLER_NAME_MODE": {"const": "allocate"},
        "HOLLER_DISPLAY_NAME": {"type": "string", "maxLength": 64}
      }
    },
    "holler": {
      "type": "object",
      "required": ["actor", "role_text", "accepts"],
      "properties": {
        "actor": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
        "role_text": {"type": "string", "maxLength": 2048},
        "accepts": {"type": "array", "maxItems": 32, "items": {"type": "string", "maxLength": 64}}
      }
    },
    "first_prompt": {"type": "string", "description": "the positional prompt for the interactive session's first turn"},
    "recommended_models": {"type": ["object", "null"], "description": "recommendation only; the runtime never applies it"},
    "harnesses": {
      "type": "object",
      "minProperties": 1,
      "additionalProperties": false,
      "properties": {
        "claude": {
          "type": "object",
          "required": ["plugin_dir", "extra_args"],
          "properties": {
            "plugin_dir": {"$ref": "#/$defs/relpath"},
            "extra_args": {"type": "array", "maxItems": 0},
            "context": {"type": "array", "items": {"type": "string"}},
            "wake": {"type": "object"},
            "plugins": {"type": "array", "items": {"type": "string"}},
            "skills": {"type": "array", "items": {"type": "string"}},
            "manual": {"type": "array", "items": {"type": "string"}},
            "agents": {"type": "array", "items": {"type": "string"}},
            "hooks": {"type": "array", "items": {"type": "string"}}
          }
        },
        "codex": {
          "type": "object",
          "required": ["codex_home_template", "extra_args"],
          "properties": {
            "codex_home_template": {"$ref": "#/$defs/relpath"},
            "extra_args": {"type": "array", "maxItems": 0},
            "context": {"type": "array", "items": {"type": "string"}},
            "wake": {"type": "object"},
            "sandbox": {"enum": [null, "read-only", "workspace-write"]},
            "skills": {"type": "array", "items": {"type": "string"}},
            "manual": {"type": "array", "items": {"type": "string"}}
          }
        }
      }
    }
  },
  "$defs": {
    "relpath": {"type": "string", "pattern": "^(?!/)(?!.*(^|/)\\.\\.(/|$))[A-Za-z0-9._/-]+$",
                "description": "relative to the bundle root; must resolve to a directory inside the bundle"}
  }
}
```

Rules for v0.1:

- `extra_args` is empty for every harness. Agent restrictions live in the bundle (hooks, the Codex template's
  `sandbox_mode`), never in arguments.
- `env` holds exactly `HOLLER_ACTOR`, `HOLLER_ROLE`, `HOLLER_NAME_MODE` (`allocate`) and `HOLLER_DISPLAY_NAME`.
  No `PATH`, `NODE_OPTIONS`, API keys, proxies or other variables.
- `plugin_dir` and `codex_home_template` are relative to the bundle root and resolve inside it. The bundle has
  no symlinks. No absolute paths and no secrets anywhere in the bundle.
- `skills`, `manual`, `plugins`, `agents` and `hooks` are informational (what the agent will see); the runtime
  does not need them to launch.

## Runtime responsibilities (invariants the runtime enforces; launch.json cannot override them)

1. **Verify** `manifest.json` hashes before reading any `launch.json`, and again at launch. If the caller passes
   `--bundle-hash`, refuse a bundle whose manifest hash differs.
2. **Interactive launches only.** Claude: `claude --allowedTools <Holler's pre-approved tools> --plugin-dir
   <bundle>/<plugin_dir> [--model <m>] [--effort <e>] --session-id <runtime uuid> "<first_prompt>"` in a terminal
   the runtime owns (Terminal, iTerm or a PTY). `--allowedTools` comes first, so it ends at the next option; its
   value is the connector manifest's tools that need no explicit approval, comma-separated, with the plugin's
   tool prefix (C5's `holler_channel_post` among them).
   Codex: `codex [-m <m>] [-c model_reasoning_effort="<e>"] "<first_prompt>"` with `CODEX_HOME=<per-agent home>`.
   Arguments are an argv array, never a shell string. Never `-p`/`--print`, `codex exec`, `--bg`, `--mcp-config`
   or `--add-dir`. Bypass modes (`bypassPermissions`, `--dangerously-bypass-approvals-and-sandbox`) only under
   **Full access** below; `--dangerously-skip-permissions` never.
3. **Environment.** Start from the user's login environment, add only `launch.json` `env`, and unset
   `CLAUDE_CODE_ENTRYPOINT` (and the other `CLAUDE_CODE_*`/`CLAUDECODE` markers a parent Claude process may
   leave). The Holler connector skips its wake monitor for SDK entrypoints (`sdk-cli`, `sdk-ts`, `sdk-py`);
   an interactive start gets `cli`. Observed 2026-10-24: a session started from inside another Claude
   process inherited `CLAUDE_CODE_ENTRYPOINT=sdk-ts` until the runtime-style clean environment removed it.
4. **Codex home.** Copy `codex_home_template` to a per-agent home owned by the runtime; create `auth.json` there
   as a symlink to the user's `~/.codex/auth.json` (never a copy); append the user's Holler connector settings
   and the user-skill exclusions described in the template's `HOME-SETUP.md`. The Holler plugin's tool policy
   is then merged with the connector manifest's approvals: each manifest tool is listed, explicit-approval tools
   (and any the user set to `prompt`) stay `prompt`, the rest `approve`, and an unset default is `prompt`. This
   applies with or without a template (the `none` role too). The bundle never ships
   `auth.json`. Nothing under `~/.codex` is modified.
   The template may contain only `AGENTS.md`, `HOME-SETUP.md`, `config.toml` and `skills/**`; anything else (for
   example `rules/*.rules`, which can pre-approve commands) is `bundle_invalid`. In `config.toml`, `[features]` may
   set only `remote_plugin = false`, and `sandbox_mode` may be only `read-only` or `workspace-write`.
5. **Trust.** Claude refuses or prompts in folders it does not trust (`claude --bg`: "Workspace not trusted";
   interactive: the "Quick safety check" prompt). The runtime either starts in a folder the user already trusts
   or lets the user answer the prompt in the agent's terminal. It never writes `~/.claude.json` itself.
6. **Ready and live_wake check.** The runtime reads only daemon state, never the terminal transcript. The
   "ready" line the first prompt asks for is a cue for the human, not part of this contract.
   - A launch is `running` when (1) a session is registered with the exact `HOLLER_RUN` the runtime generated
     for this launch (never a match on the `<actor>-<hex>` prefix), and (2) that run's profile is published with
     `role_text` equal to `launch.json` `holler.role_text`.
   - Until then it is `starting`, with `pending` naming the first unmet step: `registration` or `profile`.
     `profile` usually means the agent is waiting on a trust or permission prompt in its terminal.
   - `live_wake` is reported separately, from the session's Who row (Claude: the hook-long-poll monitor is
     ready). When it is false, `wake_problem` says why; for Codex it is `codex_home_wake` until Holler core passes
     the session's `CODEX_HOME` to the wake (C2; see `harnesses.codex.wake`). The desktop shows "Running · can't
     wake yet" in that case.

## Model, effort and access (RC4)

- **Model and effort** come only from the runtime's per-harness allowlists (Claude: `fable`, `opus`, `sonnet`,
  `haiku` and their `claude-*` full names, effort `low`–`max`; Codex: the gpt-6 and gpt-5.6 slugs the
  supported codex-cli knows, effort `low`–`xhigh`). Anything else is `option_invalid`. Empty means the tool's
  own default. `recommended_models` in `launch.json` stays a recommendation; the runtime never applies it.
- **Access** is `ask` or `full`. A missing or unknown value is `ask`, at start, in the launch record and in
  `holler agent list`. `full` comes only from the caller's `--access full`, which the desktop passes only after
  the human chose Full access in that chat and confirmed it. Nothing in a bundle, `launch.json`, profile,
  agent message or environment can set it. `holler agent start|restart --access full` from inside an agent
  (`HOLLER_RUN` or `HOLLER_LAUNCH_TAG` set) is refused with `access_denied`.
  - Claude: `--permission-mode bypassPermissions`. Holler's hooks still run, so registration and wake work.
  - Codex: `--dangerously-bypass-approvals-and-sandbox`, which overrides the template's `sandbox_mode` for this
    agent only. Folder trust for the launch folder is unchanged.
- `holler agent list` reports `model`, `effort` and `access` for every launch.

## Restart (RC4)

`holler agent restart <tag> [--model <m>] [--effort <e>] [--access ask|full]` changes model, effort or access
and keeps the conversation:

1. The runtime ends the launch's processes (and, for Codex, every process running from its home) before
   anything resumes. Two processes never share a session.
2. It resumes the same session in a new terminal: `claude --resume <the runtime's session id>`, or
   `codex resume --last` in the agent's own home (which holds only that agent's sessions).
3. `HOLLER_RUN` and `HOLLER_LAUNCH_TAG` stay the same, so the connector's continuity handles bind the same actor
   and its chats. Another launch never shares them.
4. Access changes only when `--access` is given; otherwise it keeps its value. A launch can't restart itself:
   a restart whose target run is the caller's `HOLLER_RUN` is `access_denied`, whatever its options.
5. If the tool refuses the resume (for example, an expired session), the launch is `exited` with
   `wake_problem: resume_failed`, keeping its run and session. The runtime never starts a fresh session in its
   place.

## The `none` role (RC4)

`--role none` (no `--bundle`) starts a plain Claude Code or Codex session with Holler connected and no starter
persona, plugins or skills:

- `HOLLER_ACTOR` is the tool's name with `allocate` naming, so it is named alias-else-actor like any session.
- The Codex home holds only Holler's connection settings and the launch folder's trust.
- The first prompt only asks it to wait for Holler messages.
- It is `running` once a session of its exact `HOLLER_RUN` is live. There is no `role_text` profile to wait
  for.

## Hooks shipped in the bundle

All hooks are Claude Code hooks inside the bundle's reviewed plugin folders. None makes network calls. None
writes files. Codex homes carry no hooks (Codex hooks need per-hook trust in its UI).

| Hook | Plugin | Event | What it does | Reads | Writes / network |
| --- | --- | --- | --- | --- | --- |
| `session-brief.sh` (brief) | `<agent>` | SessionStart `startup\|resume\|clear\|compact` | Prints `brief.md` as `additionalContext`; silent for `claude --agent` sessions | stdin, `brief.md` | none / none |
| `session-brief.sh` (platform) | `holler-platform` | same | Prints `platform.md` (the Holler platform layer) | stdin, `platform.md` | none / none |
| `careful` | `gstack` (eng) | PreToolUse `Bash` | Asks before destructive shell commands; denies `rm -rf` of `/` or `~` and force-push to the default branch. Reviewed in `kits/gstack/PROVENANCE.md` | stdin; runs read-only `git symbolic-ref`, `show-ref`, `branch --show-current` | none / none |
| `experiment-registry` | `product` | PreToolUse `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash` | Denies direct edits to `.agents/experiments.jsonl` (only the experiment-card script appends). See `hooks/experiment-registry/SPEC.md` | stdin, `realpath` of the target | none / none |
| `readonly-guard` | `reviewer` | PreToolUse `Edit\|Write\|MultiEdit\|NotebookEdit\|Bash` | Denies file-writing tools and any shell command outside a read-only allowlist. See `hooks/readonly-guard/SPEC.md` | stdin | none / none |

Every hook ships with tests (`tests/run_cases.py`) that the build runs; a failing test stops the build.
