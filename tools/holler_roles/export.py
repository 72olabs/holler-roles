"""export <dest> [--deny FILE] [--allow-dirty]: copy the public part of this repository into an empty folder, for a
fresh-history public repository, then scan what was copied.

The public part is the tracked files matched by PUBLIC.txt: one path or folder per line, `!path` to exclude, `#`
comments. Anything not listed stays private, so a new file is private until someone lists it.

The scan fails the export when an exported file contains:
  - a home-folder path (/Users/<name>/, /home/<name>/) other than a placeholder;
  - something shaped like a credential (private keys, GitHub, Anthropic, OpenAI, Slack, AWS tokens);
  - the name of a file that stays private (a link that would dangle in the public repository);
  - a word from the deny file (default: .export-deny when present; keep it out of PUBLIC.txt).
The copy is left in <dest> either way, so the hits can be read in place.
"""
import os
import re
import subprocess

from common import ROOT, copy_file, die, git, read

SECRET = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{30,}|\bsk-ant-[A-Za-z0-9_-]{20,}"
    r"|\bsk-(?:proj-)?[A-Za-z0-9]{32,}|\bxox[abprs]-[A-Za-z0-9-]{10,}|\bAKIA[0-9A-Z]{16}\b")
HOME = re.compile(r"/(?:Users|home)/([A-Za-z0-9._-]+)")
PLACEHOLDERS = {"you", "me", "user", "username", "name", "runner", "example", "USER", "alice", "bob"}
DEFAULT_DENY = ".export-deny"


def public_rules():
    path = os.path.join(ROOT, "PUBLIC.txt")
    if not os.path.isfile(path):
        die("PUBLIC.txt is missing")
    keep, drop = [], []
    for line in read(path).splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        (drop if line.startswith("!") else keep).append(line.lstrip("!").rstrip("/"))
    return keep, drop


def matches(rel, rules):
    return any(rel == r or rel.startswith(r + "/") for r in rules)


def deny_words(argv):
    path = argv[argv.index("--deny") + 1] if "--deny" in argv else os.path.join(ROOT, DEFAULT_DENY)
    if "--deny" in argv and not os.path.isfile(path):
        die(f"deny file {path} not found")
    if not os.path.isfile(path):
        return []
    return [w.strip() for w in read(path).splitlines() if w.strip() and not w.lstrip().startswith("#")]


def scan(dest, files, private_names, words):
    hits = []
    word_re = re.compile("|".join(re.escape(w) for w in words), re.I) if words else None
    name_re = re.compile(r"(?<![\w.-])(" + "|".join(re.escape(n) for n in sorted(private_names)) + r")(?![\w-])") if private_names else None
    for rel in files:
        with open(os.path.join(dest, rel), "rb") as f:
            raw = f.read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for m in HOME.finditer(line):
                if m.group(1) not in PLACEHOLDERS and not m.group(1).startswith(("<", "$")):
                    hits.append((rel, n, "home path", m.group(0)))
            if SECRET.search(line):
                hits.append((rel, n, "credential-shaped", SECRET.search(line).group(0)[:12] + "…"))
            if name_re and name_re.search(line):
                hits.append((rel, n, "names a private file", name_re.search(line).group(1)))
            if word_re and word_re.search(line):
                hits.append((rel, n, "denied word", word_re.search(line).group(0)))
    return hits


def cmd_export(argv):
    args = [a for a in argv if not a.startswith("--")]
    if "--deny" in argv:
        args = [a for a in args if a != argv[argv.index("--deny") + 1]]
    if len(args) != 1:
        die("usage: holler-roles export <dest> [--deny FILE] [--allow-dirty]")
    dest = os.path.abspath(args[0])
    if os.path.realpath(dest).startswith(ROOT + os.sep):
        die("export to a folder outside this repository")
    if os.path.exists(dest) and os.listdir(dest):
        die(f"{dest} is not empty")
    keep, drop = public_rules()
    tracked = git("ls-files", "-z", cwd=ROOT).split("\0")
    tracked = [t for t in tracked if t]
    public = sorted(t for t in tracked if matches(t, keep) and not matches(t, drop))
    private = [t for t in tracked if t not in public]
    dirty = subprocess.run(["git", "--no-optional-locks", "status", "--porcelain", "--", *public], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    if dirty and "--allow-dirty" not in argv:
        die(f"uncommitted changes in public files; commit them or pass --allow-dirty:\n{dirty[:800]}")
    os.makedirs(dest, exist_ok=True)
    for rel in public:
        copy_file(os.path.join(ROOT, rel), os.path.join(dest, rel))
    # a private document or folder named in a public file would be a dead link in the public repository
    def ancestors(path):
        parts = path.split("/")[:-1]
        return {"/".join(parts[:i]) for i in range(1, len(parts) + 1)}
    public_dirs = set().union(*(ancestors(p) for p in public)) if public else set()
    private_names = {os.path.basename(p) for p in private if p.endswith(".md")} - {os.path.basename(p) for p in public}
    # private folders by their path (a/b); a bare top-level folder name is often a common word
    private_names |= {d for d in (set().union(*(ancestors(p) for p in private)) if private else set()) - public_dirs if "/" in d}
    hits = scan(dest, public, private_names, deny_words(argv))
    print(f"exported {len(public)} files to {dest}; kept private: {len(private)} tracked files")
    for rel, n, kind, what in hits:
        print(f"FAIL  {rel}:{n}: {kind}: {what}")
    if hits:
        print(f"\n{len(hits)} problem(s); fix them in this repository and export again")
        return 1
    print("clean. Next: cd into it, git init, review, and only then push it anywhere.")
    return 0
