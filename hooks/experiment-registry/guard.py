#!/usr/bin/env python3
"""Claude Code PreToolUse guard for the append-only experiment registry (experiments.jsonl).

Denies:
  - Write, Edit, MultiEdit, NotebookEdit whose target resolves (after symlinks) to a file named
    experiments.jsonl;
  - Bash commands that name experiments.jsonl together with a shell write: redirection
    (>, >>, >|, &>), tee, sed -i, perl -i, truncate, rm, mv, cp, dd, ln, chmod, chown, touch,
    install, rsync, git checkout/restore/reset/rm/mv/apply/stash/clean, or an interpreter
    one-liner that opens or writes a file.
Allows everything else, including the sanctioned writer:
  python3 -I <experiment-card>/scripts/experiments.py add|readout ...
(which never names the file with a redirection).

Input: the hook JSON on stdin (tool_name, tool_input, cwd). Output on deny: a JSON
hookSpecificOutput with permissionDecision "deny", exit 0. If stdin is not JSON but mentions the
registry, exit 2 (blocking) with the reason on stderr; otherwise exit 0 (allow).

This is a guard against accidental or casual edits, not a security boundary: a command that
builds the file name at runtime (variables, globs, base64) can get past it. `experiments.py verify`
detects any edit after the fact through the record hash chain.

holler-roles product agent (first written 2026-10-23). Python 3 standard library only; run with python3 -I.
"""
import json
import os
import re
import sys

REGISTRY_NAME = "experiments.jsonl"
FILE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
REASON = ("The experiment registry is append-only. Register or read out a card with the "
          "experiment-card script: python3 -I <experiment-card dir>/scripts/experiments.py add|readout ... "
          "A changed target is a new card with supersedes, never an edit.")

NAME_RE = re.compile(r"experiments\.jsonl")
WRITE_PATTERNS = [
    re.compile(r"(?:^|[^<0-9&])(?:[0-9]|&)?>>?\|?\s*['\"]?[^\s;&|'\"]*experiments\.jsonl"),  # > >> >| 2> &>
    re.compile(r"\btee\b[^;&|]*experiments\.jsonl"),
    re.compile(r"\b(?:sed|perl|ruby)\b[^;&|]*\s-[a-zA-Z]*i"),
    re.compile(r"\b(?:truncate|rm|unlink|mv|cp|dd|ln|chmod|chown|chflags|touch|install|rsync|shred|ed|ex)\b"),
    re.compile(r"\bopen\s*\("),
    re.compile(r"\b(?:write_text|write_bytes|writeFile|appendFile)\b"),
    re.compile(r"\bgit\s+(?:checkout|restore|reset|rm|mv|apply|am|stash|clean)\b"),
]


def emit_deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


def resolve(path, cwd):
    if not path:
        return ""
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(cwd or os.getcwd(), path)
    return os.path.realpath(path)


def file_targets(tool_input):
    for key in ("file_path", "notebook_path", "path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            yield value


def check_file_tool(tool_input, cwd):
    for target in file_targets(tool_input):
        if os.path.basename(target) == REGISTRY_NAME or os.path.basename(resolve(target, cwd)) == REGISTRY_NAME:
            return f"{REASON} (blocked write to {target})"
    return None


def check_bash(command):
    if not NAME_RE.search(command):
        return None
    # A command that names the registry may read it (cat, head, wc, grep, jq) or call the script.
    # It may not combine the name with any write primitive, anywhere in the command.
    for pat in WRITE_PATTERNS:
        if pat.search(command):
            return f"{REASON} (blocked shell command naming {REGISTRY_NAME}: matched {pat.pattern!r})"
    return None


def main():
    raw = sys.stdin.read()
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        if REGISTRY_NAME in raw:
            print(f"experiment-registry guard: unreadable hook input that mentions {REGISTRY_NAME}; blocking", file=sys.stderr)
            return 2
        return 0
    tool = event.get("tool_name") or ""
    tool_input = event.get("tool_input") or {}
    cwd = event.get("cwd") or ""
    reason = None
    if tool in FILE_TOOLS:
        reason = check_file_tool(tool_input, cwd)
    elif tool == "Bash":
        reason = check_bash(str(tool_input.get("command") or ""))
    if reason:
        return emit_deny(reason)
    return 0


if __name__ == "__main__":
    sys.exit(main())
