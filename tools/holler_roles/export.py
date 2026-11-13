"""export <dest> [--deny FILE] [--allow-dirty]: copy the public part of this repository into an empty folder, for a
fresh-history public repository, then scan what was copied.

The public part is the tracked files matched by PUBLIC.txt: one path or folder per line, `!path` to exclude, `#`
comments. Anything not listed stays private, so a new file is private until someone lists it.

The scan fails the export when an exported file, or its path, contains (non-UTF-8 bytes are replaced, not skipped):
  - a home-folder path (/Users/<name>/, /home/<name>/) other than a placeholder;
  - something shaped like a credential (private keys, GitHub, Anthropic, OpenAI, Slack, AWS tokens);
  - an internal Holler id (msg_, chn_, thr_, req_, run_ followed by hex) from a real workspace;
  - the name of a file that stays private (a link that would dangle in the public repository), except AGENTS.md and
    CLAUDE.md, which public files name as a convention;
  - a relative Markdown link ([text](target), [ref]: target) that resolves to a tracked path that is not exported;
  - a word from the deny file (default: .export-deny when present; keep it out of PUBLIC.txt).
The copy is left in <dest> either way, so the hits can be read in place.

publish <clone>: export into a temporary folder and, only when the scan is clean, make the tracked files of a clean
clone of the public repository equal to it (files added, changed and removed). It plans every removal and write and
checks the whole plan first: no submodules, no symlink or untracked/ignored entry on the way to or at an exported path,
nothing written outside the working tree or into .git. After a refusal the clone is unchanged. It prints
`git status --short` and a suggested commit message, and stops: it never commits or pushes.
"""
import os
import re
import subprocess
import tempfile

from common import ROOT, copy_file, die, git, read, source_commit

SECRET = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{30,}|\bsk-ant-[A-Za-z0-9_-]{20,}"
    r"|\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}|\bxox[abprs]-[A-Za-z0-9-]{10,}|\bAKIA[0-9A-Z]{16}\b")
HOLLER_ID = re.compile(r"\b(?:msg|chn|thr|req|run)_[0-9a-f]{8,}\b")   # message, channel, thread ids from a real workspace
LINK = re.compile(r"\]\(\s*<?([^)\s>]+)|^\s*\[[^\]]+\]:\s*<?([^\s>]+)")   # [text](target), [ref]: target
HOME = re.compile(r"/(?:Users|home)/([A-Za-z0-9._-]+)")
PLACEHOLDERS = {"you", "me", "user", "username", "name", "runner", "example", "USER", "alice", "bob"}
DEFAULT_DENY = ".export-deny"
# every agent harness reads files with these names, so public files name them as the convention; a real link to our
# private copy is still caught, by resolving it (private_link)
CONVENTIONAL_NAMES = {"AGENTS.md", "CLAUDE.md"}


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


def private_link(rel, target, private):
    """The private tracked path a relative link in rel resolves to, or None (URLs, anchors, absolute paths)."""
    target = target.split("#", 1)[0].split("?", 1)[0]
    if not target or re.match(r"[A-Za-z][\w+.-]*:", target) or target.startswith("/"):
        return None
    resolved = os.path.normpath(os.path.join(os.path.dirname(rel), target)).replace(os.sep, "/")
    return resolved if resolved in private else None


def scan_line(rel, n, line, name_re, word_re, hits, private=frozenset()):
    for m in HOME.finditer(line):
        if m.group(1) not in PLACEHOLDERS and not m.group(1).startswith(("<", "$")):
            hits.append((rel, n, "home path", m.group(0)))
    # every match on a line, not the first: a caller that excuses one known finding must still see a second
    for m in SECRET.finditer(line):
        hits.append((rel, n, "credential-shaped", m.group(0)[:12] + "…"))
    for m in HOLLER_ID.finditer(line):
        hits.append((rel, n, "internal Holler id", m.group(0)))
    for m in LINK.finditer(line) if private and n else ():
        resolved = private_link(rel, m.group(1) or m.group(2), private)
        if resolved:
            hits.append((rel, n, "links to a private file", resolved))
    for m in name_re.finditer(line) if name_re else ():
        hits.append((rel, n, "names a private file", m.group(1)))
    for m in word_re.finditer(line) if word_re else ():
        hits.append((rel, n, "denied word", m.group(0)))


def scan(dest, files, private_names, words, private=frozenset()):
    """Scan every exported path and file; private is the tracked paths (files and folders) that are not exported, for
    relative links that resolve to one. Bytes that aren't UTF-8 are replaced, never skipped, so a credential in a
    latin-1 or binary file is still found. Line 0 means the path itself."""
    hits = []
    word_re = re.compile("|".join(re.escape(w) for w in words), re.I) if words else None
    name_re = re.compile(r"(?<![\w.-])(" + "|".join(re.escape(n) for n in sorted(private_names)) + r")(?![\w-])") if private_names else None
    for rel in files:
        scan_line(rel, 0, rel, name_re, word_re, hits)
        with open(os.path.join(dest, rel), "rb") as f:
            text = f.read().decode("utf-8", errors="replace")
        for n, line in enumerate(text.splitlines(), 1):
            scan_line(rel, n, line, name_re, word_re, hits, private)
    return hits


def export_tree(dest, argv):
    """Copy the public files into the empty folder dest and scan them; returns (public files, private files, hits)."""
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
    private_names -= CONVENTIONAL_NAMES
    # private folders by their path (a/b); a bare top-level folder name is often a common word
    private_names |= {d for d in (set().union(*(ancestors(p) for p in private)) if private else set()) - public_dirs if "/" in d}
    private_dirs = (set().union(*(ancestors(p) for p in private)) if private else set()) - public_dirs
    hits = scan(dest, public, private_names, deny_words(argv), set(private) | private_dirs)
    print(f"exported {len(public)} files to {dest}; kept private: {len(private)} tracked files")
    for rel, n, kind, what in hits:
        print(f"FAIL  {rel}:{n}: {kind}: {what}")
    if hits:
        print(f"\n{len(hits)} problem(s); fix them in this repository and export again")
    return public, private, hits


def cmd_export(argv):
    args = [a for a in argv if not a.startswith("--")]
    if "--deny" in argv:
        args = [a for a in args if a != argv[argv.index("--deny") + 1]]
    if len(args) != 1:
        die("usage: holler-roles export <dest> [--deny FILE] [--allow-dirty]")
    _, _, hits = export_tree(os.path.abspath(args[0]), argv)
    if hits:
        return 1
    print("clean. Next: cd into it, git init, review, and only then push it anywhere.")
    return 0


def plan_publish(clone, public):
    """Decide what publish will do to the clone and check all of it before anything changes; die on the first
    problem, naming the path. Returns (tracked files to remove, folders those removals must leave empty)."""
    entries = [e for e in subprocess.run(["git", "--no-optional-locks", "ls-files", "-s", "-z"], cwd=clone,
                                         capture_output=True, text=True, check=True).stdout.split("\0") if e]
    modes = {e.split("\t", 1)[1]: e.split(" ", 1)[0] for e in entries}
    gitlinks = sorted(rel for rel, mode in modes.items() if mode == "160000")
    if gitlinks:
        die(f"the clone has a submodule ({', '.join(gitlinks)}); publish refuses clones with submodules")
    remove = sorted(set(modes) - set(public))
    removed = set(remove)
    gitdir = os.path.join(clone, ".git")
    for rel in remove:   # never delete through a symlinked folder, and only files git tracks
        parts = rel.split("/")
        for i in range(1, len(parts)):
            if os.path.islink(os.path.join(clone, *parts[:i])):
                die(f"{'/'.join(parts[:i])} in the clone is a symlink; remove it by hand")
        path = os.path.join(clone, rel)
        if os.path.isdir(path) and not os.path.islink(path):
            die(f"{rel} in the clone is a folder where git tracks a file; remove it by hand")
    emptied = set()
    for rel in public:
        parts = rel.split("/")
        if parts[0] == ".git":
            die(f"the export contains {rel}")
        for i in range(1, len(parts)):
            anc = "/".join(parts[:i])
            path = os.path.join(clone, anc)
            if os.path.islink(path):
                die(f"{anc} in the clone is a symlink; publish writes {rel} only into real folders")
            if not os.path.lexists(path):
                break   # nothing below an absent folder exists either
            if not os.path.isdir(path) and anc not in removed:
                die(f"{anc} in the clone is an untracked or ignored file where the export needs a folder")
        path = os.path.join(clone, rel)
        if os.path.isdir(path) and not os.path.islink(path):
            # a tracked folder becoming a file: everything in it must be tracked content that publish removes
            for top, dirs, files in os.walk(path):
                for name in files + [d for d in dirs if os.path.islink(os.path.join(top, d))]:
                    inner = os.path.relpath(os.path.join(top, name), clone)
                    if inner not in removed:
                        die(f"{inner} in the clone is untracked or ignored, inside {rel}, which the export writes as a file")
            emptied.add(rel)
        elif os.path.lexists(path) and rel not in modes:
            die(f"{rel} in the clone is untracked or ignored, and the export would overwrite it")
        elif os.path.lexists(path) and not (os.path.isfile(path) or os.path.islink(path)):
            die(f"{rel} in the clone is not a regular file")
        target = os.path.join(os.path.realpath(os.path.dirname(path)), parts[-1])
        if not target.startswith(clone + os.sep) or target == gitdir or target.startswith(gitdir + os.sep):
            die(f"{rel} would be written outside the clone's working tree")
    return remove, emptied


def publish_into(clone, source_root, export, message):
    """Make the working tree of a clean clone equal to an export; refuses before changing anything, so after any
    refusal the clone is exactly as it was. export(out) fills the empty folder out and returns (public files, ok);
    message() gives the suggested commit message. Shared by holler-roles publish and any other generated copy."""
    clone = os.path.realpath(clone)
    if not os.path.isdir(os.path.join(clone, ".git")) or git("rev-parse", "--show-toplevel", cwd=clone) != clone:
        die(f"{clone} is not the top of a git clone")
    if git("rev-parse", "--show-toplevel", cwd=source_root) == clone or source_root.startswith(clone + os.sep):
        die("publish into a clone of the public repository, not into this one")
    if git("status", "--porcelain", cwd=clone):
        die(f"{clone} has uncommitted changes; commit, stash or discard them first")
    with tempfile.TemporaryDirectory(prefix="holler-publish-") as tmp:
        out = os.path.join(tmp, "out")
        public, ok = export(out)
        if not ok:
            return 1
        remove, emptied = plan_publish(clone, public)
        # the plan is checked: from here on only tracked files are removed and only checked paths written
        for rel in remove:
            if os.path.lexists(os.path.join(clone, rel)):
                os.unlink(os.path.join(clone, rel))
            parent = os.path.dirname(os.path.join(clone, rel))
            while parent != clone and not os.listdir(parent):
                os.rmdir(parent)
                parent = os.path.dirname(parent)
        for rel in emptied:   # left with only empty folders, which git does not see
            for top, dirs, _ in os.walk(os.path.join(clone, rel), topdown=False):
                for d in dirs:
                    os.rmdir(os.path.join(top, d))
            if os.path.isdir(os.path.join(clone, rel)):
                os.rmdir(os.path.join(clone, rel))
        for rel in public:
            dst = os.path.join(clone, rel)
            if os.path.islink(dst):   # a tracked symlink becoming a file: replace the link, never follow it
                os.unlink(dst)
            copy_file(os.path.join(out, rel), dst)
    status = subprocess.run(["git", "--no-optional-locks", "status", "--short"], cwd=clone, capture_output=True,
                            text=True, check=True).stdout.rstrip()   # not git(): it strips the first line's leading space
    print(f"\n{clone}:\n{status or '(no changes: the clone already matches the export)'}")
    if status:
        print(f"\nSuggested commit message:\n  {message()}\n"
              "Review the changes, then commit and push them yourself; publish never does.")
    return 0


def cmd_publish(argv):
    """publish <clone>: refuses before changing anything; after any refusal the clone is exactly as it was."""
    if len(argv) != 1 or argv[0].startswith("-"):
        die("usage: holler-roles publish <clone of the public repository>")

    def export(out):
        public, _, hits = export_tree(out, [])
        return public, not hits
    return publish_into(argv[0], ROOT, export, lambda: f"Sync from holler roles/ at {source_commit()}")
