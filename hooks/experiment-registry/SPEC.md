# experiment-registry hook (spec)

Agents: product. Harness: Claude Code (PreToolUse). Codex: see Wiring.

## What it protects

`experiments.jsonl`, the append-only experiment registry. In a project it is `.agents/experiments.jsonl`, possibly a symlink to a shared file. The only sanctioned writer is the experiment-card script:

```sh
python3 -I <release>/claude/plugins/<role>/skills/experiment-card/scripts/experiments.py add --card <file> --approved-by <name>
python3 -I <...>/experiments.py readout --card <id> --actual <n> --source <s> --date <d> --label <l> --sample <n>
```

The script appends one JSON line per record under an exclusive `flock`, refuses to append when the hash chain is broken, and never creates or rewrites the file.

## Rule

| Tool | Decision |
| --- | --- |
| `Write`, `Edit`, `MultiEdit`, `NotebookEdit` | deny when `file_path` / `notebook_path`, as given or after `realpath` against the event's `cwd`, has the basename `experiments.jsonl` |
| `Bash` | deny when the command contains `experiments.jsonl` and any write primitive: redirection into it (`>`, `>>`, `>|`, `N>`, `&>`), `tee`, `sed/perl/ruby -i`, `truncate rm unlink mv cp dd ln chmod chown chflags touch install rsync shred ed ex`, `open(`, `write_text/write_bytes/writeFile/appendFile`, `git checkout/restore/reset/rm/mv/apply/am/stash/clean` |
| anything else | allow (no output, exit 0) |

Reads stay allowed: `Read`, `cat`, `head`, `wc`, `grep`, `jq`, `git log`, and redirecting a read into another file.

Deny output (exit 0):

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "The experiment registry is append-only. ..."}}
```

Unparseable hook input that mentions `experiments.jsonl` exits 2 (blocking, reason on stderr). Other unparseable input exits 0.

## Files

| File | Purpose |
| --- | --- |
| `guard.py` | The hook. Python 3 stdlib, run as `python3 -I`. No network, no writes, reads only `realpath` of the target |
| `hooks.claude.json` | Fragment for the role plugin's `hooks/hooks.json`, matcher `Write|Edit|MultiEdit|NotebookEdit|Bash`, command `python3 -I "${CLAUDE_PLUGIN_ROOT}/hooks/experiment-registry/guard.py"`, timeout 10 s |
| `tests/cases.jsonl`, `tests/run_cases.py` | 23 tool events plus 2 malformed inputs, run in a temp project with the same symlink layout. `python3 -I tests/run_cases.py` printed `0 failed` on 2026-10-23 |

## Wiring

- Claude: declared in `hook.json` (PreToolUse, matcher `Write|Edit|MultiEdit|NotebookEdit|Bash`). The build copies this folder to `hooks/experiment-registry/` in the agent's role plugin, merges the entry into the plugin's `hooks/hooks.json`, and runs `tests/run_cases.py` first; failing tests stop the build.
- Codex: Codex PreToolUse hooks need per-hook trust in the Codex UI, so the build does not wire guards into Codex homes. Codex relies on the script's hash chain (`experiments.py verify`) and the brief's rule.

## Limits

This guard stops accidental and casual edits. It is not a security boundary: a command that builds the path at runtime (variables, globs, encoded strings) passes. Detection after the fact is `experiments.py verify`, which checks the `prev` hash chain and reports edited, reordered or deleted lines.
