"""readonly-guard: Claude Code PreToolUse hook that keeps a session read-only.

Denies file-writing tools (Edit, Write, MultiEdit, NotebookEdit) and any Bash command that is not on a
read-only allowlist: plain reads (ls, cat, head, grep, ...) and read-only git subcommands. Commands are
split on ; && || | and newlines; every segment must pass. Redirection into files, command substitution,
xargs, env, sudo and shells are denied. Everything else (Read, Grep, Glob, MCP tools such as Holler) is
allowed. Unparseable input is denied (fails closed).

Best-effort string checks, not a security boundary: pair it with the harness's own restrictions
(Claude --disallowedTools, Codex --sandbox read-only).

Python 3 standard library only; run as `python3 -I guard.py`. Reads stdin; writes nothing; no network.
"""
import json
import re
import shlex
import sys

WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

READ_COMMANDS = {
    "ls", "cat", "head", "tail", "wc", "grep", "egrep", "fgrep", "rg", "sort", "uniq", "cut", "tr", "diff", "cmp",
    "file", "stat", "pwd", "echo", "printf", "date", "basename", "dirname", "realpath", "readlink", "shasum",
    "sha256sum", "md5", "md5sum", "jq", "tree", "du", "which", "test", "[", "true", "column", "nl", "less", "more",
    "comm", "fold", "fmt", "od", "hexdump", "strings", "type", "whoami", "uname", "id",
}

GIT_READ = {
    "status", "log", "diff", "show", "blame", "annotate", "rev-parse", "ls-files", "ls-tree", "grep", "cat-file",
    "merge-base", "describe", "shortlog", "rev-list", "name-rev", "for-each-ref", "show-ref", "count-objects",
    "whatchanged", "range-diff", "cherry", "version", "help", "var", "check-ignore", "check-attr", "verify-commit",
    "verify-tag",
}
# Subcommands that only read with these forms.
GIT_LIST_ONLY = {
    "branch": {"-a", "-r", "-v", "-vv", "--list", "-l", "--show-current", "--contains", "--merged", "--no-merged",
               "--all", "--remotes", "--verbose", "--points-at", "--sort", "--format", "--column", "--no-column"},
    "tag": {"-l", "--list", "-n", "--contains", "--points-at", "--merged", "--no-merged", "--sort", "--format"},
    "remote": {"-v", "--verbose", "show", "get-url"},
    "worktree": {"list"},
    "stash": {"list", "show"},
    "config": {"--get", "--get-all", "--get-regexp", "--list", "-l", "--show-origin", "--show-scope", "--null", "-z",
               "--global", "--local", "--system", "--name-only"},
    "notes": {"list", "show"},
    "reflog": {"show"},
    "symbolic-ref": {"-q", "--quiet", "--short"},
}
GIT_GLOBAL_WITH_VALUE = {"-C", "--git-dir", "--work-tree"}
GIT_GLOBAL_FLAGS = {"--no-pager", "-P", "--no-optional-locks", "--literal-pathspecs", "--no-replace-objects"}
GIT_DENY_ARGS = ("--output", "--ext-diff", "--exec", "--upload-pack", "--receive-pack")

SAFE_REDIRECT = re.compile(r"(?:^|\s)(?:[12]?>\s*/dev/null|2>&1|>&2|1>&2)(?=\s|$)")
FIND_DENY = {"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprint0", "-fprintf", "-fls"}
SED_DENY = re.compile(r"(^|\s)(-i\S*|--in-place\S*)(\s|$)|\bw\s+\S|\bW\s+\S|/w\s|/W\s|\be\b")


def decide(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": "[readonly-guard] " + reason}}))
    return 0


def check_git(words):
    i = 1
    while i < len(words):
        w = words[i]
        if w in GIT_GLOBAL_WITH_VALUE:
            i += 2
            continue
        if w.startswith(("--git-dir=", "--work-tree=")) or w in GIT_GLOBAL_FLAGS:
            i += 1
            continue
        if w == "-c" or w.startswith("-c") or w.startswith("--config-env"):
            return "git -c can run programs through configuration; not allowed in a read-only session"
        break
    if i >= len(words):
        return None
    sub, args = words[i], words[i + 1:]
    for a in args:
        if a.startswith(GIT_DENY_ARGS):
            return f"git {sub} {a} can write or run programs"
    if sub in GIT_READ:
        return None
    if sub in GIT_LIST_ONLY:
        allowed = GIT_LIST_ONLY[sub]
        if sub == "symbolic-ref":
            positional = [a for a in args if not a.startswith("-")]
            return None if len(positional) <= 1 and all(a in allowed for a in args if a.startswith("-")) else "git symbolic-ref with a target writes a ref"
        if sub == "config":
            flags = [a for a in args if a.startswith("-")]
            if not any(f in ("--get", "--get-all", "--get-regexp", "--list", "-l") for f in flags):
                return "git config without --get/--list can write configuration"
            return None if all(f in allowed for f in flags) else "git config flag not allowed"
        if sub in ("remote", "worktree", "stash", "notes", "reflog"):
            if not args:
                return None if sub == "remote" else f"git {sub} needs a read-only form (git {sub} alone writes)"
            return None if args[0] in allowed else f"git {sub} {args[0]} is not read-only"
        positional = [a for a in args if not a.startswith("-")]
        flags = [a.split("=")[0] for a in args if a.startswith("-")]
        if sub == "branch" and positional and not any(f in ("--list", "-l", "--contains", "--merged", "--no-merged", "--points-at") for f in flags):
            return "git branch with a name creates, renames or deletes a branch"
        if sub == "tag" and positional and not any(f in ("-l", "--list", "--contains", "--points-at", "--merged", "--no-merged") for f in flags):
            return "git tag with a name creates a tag"
        bad = [f for f in flags if f not in allowed]
        return f"git {sub} {' '.join(bad)} is not read-only" if bad else None
    return f"git {sub} is not on the read-only list"


def check_segment(seg):
    seg = SAFE_REDIRECT.sub(" ", seg).strip()
    if not seg:
        return None
    if re.search(r"[<>]", seg.replace("<<<", "")) and re.search(r"(^|[^<])>|>>", seg):
        return "redirection into a file"
    try:
        words = shlex.split(seg, posix=True)
    except ValueError:
        return "command could not be parsed"
    while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
        return "setting environment variables for a command is not allowed in a read-only session"
    if not words:
        return None
    cmd = words[0].rsplit("/", 1)[-1]
    if cmd == "git":
        return check_git(words)
    if cmd == "find":
        bad = [w for w in words[1:] if w in FIND_DENY]
        return f"find {' '.join(bad)} can modify files or run commands" if bad else None
    if cmd == "sed":
        script = " ".join(words[1:])
        return "sed -i or a sed write command modifies files" if SED_DENY.search(script) else None
    if cmd in READ_COMMANDS:
        return None
    return f"`{cmd}` is not on the read-only list (reads and read-only git only)"


def check_command(command):
    if "$(" in command or "`" in command or "<(" in command or ">(" in command:
        return "command substitution is not allowed in a read-only session"
    segments = re.split(r"\|\||&&|;|\||\n|&(?!>)", command)
    for seg in segments:
        why = check_segment(seg)
        if why:
            return why
    return None


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
        tool = data.get("tool_name") or ""
        tool_input = data.get("tool_input") or {}
    except (ValueError, AttributeError):
        return decide("hook input could not be parsed; denying (this session is read-only)")
    if tool in WRITE_TOOLS:
        return decide(f"{tool} is disabled: this agent is a read-only reviewer. Put the change in a finding instead.")
    if tool == "Bash":
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        if not isinstance(command, str):
            return decide("Bash input without a command")
        why = check_command(command)
        if why:
            return decide(f"{why}. This agent is a read-only reviewer: ask the producer to run it and send the output.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
