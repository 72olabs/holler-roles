# readonly-guard hook (spec and review)

Agent: reviewer. Harness: Claude Code (PreToolUse). Codex: the reviewer's Codex home sets `sandbox_mode = "read-only"` instead.

## Rule

| Tool | Decision |
| --- | --- |
| `Edit`, `Write`, `MultiEdit`, `NotebookEdit` | deny |
| `Bash` | allow only when every segment (split on `;`, `&&`, `\|\|`, `\|`, `&`, newlines) is a read command (`ls`, `cat`, `head`, `grep`, `rg`, `find` without `-delete`/`-exec`, `sed` without `-i`, ...) or a read-only git subcommand (`status`, `log`, `diff`, `show`, `blame`, `rev-parse`, `ls-files`, `grep`, `cat-file`, `merge-base`, list forms of `branch`, `tag`, `remote`, `stash`, `worktree`, `config --get/--list`). Deny redirection into files, `tee`, command substitution, `xargs`, environment prefixes, shells, `git -c`, `--output`, `--ext-diff`. |
| anything else (Read, Grep, Glob, MCP tools such as Holler) | allow (no output) |
| unparseable input | deny (fails closed) |

Deny output: `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "[readonly-guard] ..."}}`, exit 0.

## Review (2026-10-24)

`guard.py` is 72o Labs code, Python 3 standard library only, run as `python3 -I`. It reads the hook JSON on stdin, writes nothing, starts no processes and makes no network calls. Tests: `tests/run_cases.py` (46 cases plus malformed input). Observed live on 2026-10-24: in a `--permission-mode bypassPermissions` Claude session the hook still denied `touch guard-probe.txt` and allowed `git log`.

## Limits

String matching, not a security boundary: a determined model could find an allowed command with side effects (for example a git configuration in the reviewed repository that runs a program). It stops casual and accidental writes; independence still rests on the brief.
