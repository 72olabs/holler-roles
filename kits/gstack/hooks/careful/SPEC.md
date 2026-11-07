# careful — Destructive Command Guardrails (always-on guard)

<!-- Modified by 72o Labs: adapted from gstack careful/SKILL.md.tmpl at b04cc358 (MIT, see LICENSE and
NOTICE.md). Here this is not a skill: it is an always-on PreToolUse hook in the agent's
plugin (hooks/careful/), so there is nothing to activate. The skill frontmatter (hooks with
gstack install paths), the usage-analytics block and the project-pattern files are removed. -->

Every Bash command in an eng session is checked for destructive patterns before it runs. If one
is detected, the user is asked (MEDIUM) or the call is refused (HIGH).

## What's protected

| Pattern | Example | Risk |
|---------|---------|------|
| `rm -rf` / `rm -r` / `rm --recursive` | `rm -rf /var/data` | Recursive delete |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;` | Data loss |
| `TRUNCATE` | `TRUNCATE orders;` | Data loss |
| `git push --force` / `-f` | `git push -f origin main` | History rewrite |
| `git reset --hard` | `git reset --hard HEAD~3` | Uncommitted work loss |
| `git checkout .` / `git restore .` | `git checkout .` | Uncommitted work loss |
| `kubectl delete` | `kubectl delete pod` | Production impact |
| `docker rm -f` / `docker system prune` | `docker system prune -a` | Container/image loss |

## PowerShell and cmd (Windows)

The hook also checks the PowerShell tool (Claude Code's main Windows shell)
and any `pwsh`/`powershell`/`cmd` launched from Bash. Matching ignores case,
covers aliases in command position, accepts parameter prefixes (`-r`, `-fo`)
and strips cmd `^` escapes. All rows above apply there too.

| Pattern | Example |
|---------|---------|
| `Remove-Item`/`rm`/`ri`/`del`/`erase`/`rd`/`rmdir` + `-Recurse` or `-Force` | `gci \| ri -r -fo` |
| cmd `rd /s`, `rmdir /s`, `del /s`, `erase /s` | `cmd /c rd /s /q C:\proj` |
| `Format-Volume`, `Clear-Disk`, `Clear-Content`, `[IO.Directory]::Delete`, `[IO.File]::Delete` | `Clear-Disk -Number 1` |
| `-EncodedCommand`, `iex`, `Start-Process` of a shell, `& $cmd` (can't be inspected) | `irm $url \| iex` |

**Best-effort on PowerShell.** String matching can't see a command built at
runtime. For a hard stop, add Claude Code permission deny rules, which parse
PowerShell and its aliases: `"deny": ["PowerShell(Remove-Item *)"]` in
`.claude/settings.json`. The hook runs through `bash`, so Windows needs Git Bash.

## Safe exceptions

These patterns are allowed without warning:
- `rm -rf node_modules` / `.next` / `dist` / `__pycache__` / `.cache` / `build` / `.turbo` / `coverage`

## How it works

The hook reads `tool_name` and the command from the tool input JSON, checks it against the
patterns above, and returns a `hookSpecificOutput` payload with
`permissionDecision: "ask"` and a warning reason if a match is found (the
decision must be nested under `hookSpecificOutput` — Claude Code ignores a
top-level `permissionDecision`). You can always override a MEDIUM warning and
proceed.

## HIGH tier (hard deny)

Two catastrophic shapes are **denied**, not asked: `rm -r`/`-R` of exactly
`/`, `~`, or `$HOME`, and force-push to the repo's **default branch**. SIMPLE
commands only (no `;`, `&&`, `||`, `|`, newline) — compound shapes fall
through to the MEDIUM ask; `--force-with-lease` is never HIGH. A best-effort
advisory hard-stop, not a policy boundary: the user can still run the command
themselves outside the agent.

There is no off switch inside a session: the hook ships in the role plugin.
