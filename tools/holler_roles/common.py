"""Shared helpers for the holler-roles build: paths, hashing, deterministic file writes, frontmatter, YAML."""
import hashlib
import json
import os
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIST = os.path.join(ROOT, "dist")
LOCK_PATH = os.path.join(ROOT, "kits.lock")
TEAM_PATH = os.path.join(ROOT, "team.json")
BUNDLE = "starter-team"  # Holler's runtime accepts only this bundle name (spec/LAUNCH.md)

BRIEF_CAP = 9800         # Claude Code caps one hook's additionalContext at 10,000 characters
LISTING_SOFT = 16
LISTING_HARD = 18
PLATFORM_PLUGIN = "holler-platform"
RESERVED_SOURCES = {"own", "holler"}
SOURCE_DIRS = ("profiles", "layers", "skills", "hooks", "agents")

# The user's overlay (spec/OVERLAY.md): their own profiles, layers, skills, hooks and personal layers, kept outside
# this repository. Set by the CLI from --overlay DIR or HOLLER_ROLES_OVERLAY. None for release builds.
OVERLAY = None
OVERLAY_GIVEN = None   # the overlay path as given (before symlinks resolve), for the absolute-path check


class BuildError(SystemExit):
    pass


def die(msg):
    raise BuildError(f"holler-roles: {msg}")


def write(path, data, executable=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(data, str):
        data = data.encode("utf-8")
    with open(path, "wb") as f:
        f.write(data)
    os.chmod(path, 0o755 if executable else 0o644)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def is_exec(path):
    return bool(os.stat(path).st_mode & 0o111)


def copy_file(src, dst):
    if os.path.islink(src):
        die(f"refusing to copy a symlink: {src}")
    with open(src, "rb") as f:
        write(dst, f.read(), executable=is_exec(src))


def walk(path):
    """Relative paths of files under path, sorted. Symlinks are an error (dist has none)."""
    out = []
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames.sort()
        for d in dirnames:
            if os.path.islink(os.path.join(dirpath, d)):
                die(f"symlinked directory: {os.path.join(dirpath, d)}")
        for f in filenames:
            if f == ".DS_Store" or f.endswith((".pyc",)):
                continue
            full = os.path.join(dirpath, f)
            out.append(os.path.relpath(full, path))
    return sorted(out)


def copy_tree(src, dst, skip_dirs=(), skip_files=()):
    for rel in walk(src):
        parts = rel.split(os.sep)
        if any(p in skip_dirs for p in parts[:-1]) or parts[-1] in skip_files or "__pycache__" in parts:
            continue
        copy_file(os.path.join(src, rel), os.path.join(dst, rel))


def file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_hash(path, exclude=()):
    """sha256 over (relative path, exec bit, content hash) of every file under path."""
    h = hashlib.sha256()
    for rel in walk(path):
        if rel in exclude:
            continue
        full = os.path.join(path, rel)
        mode = "x" if is_exec(full) else "-"
        h.update(f"F\0{rel}\0{mode}\0{file_sha(full)}\0".encode())
    return "sha256:" + h.hexdigest()


def split_frontmatter(text):
    if not text.startswith("---\n"):
        return "", text
    end = text.index("\n---\n", 4)
    return text[4:end], text[end + 5:]


def parse_yaml(text):
    """YAML safe_load: PyYAML when it is installed, else Ruby's Psych (on PATH; macOS and most Linux images)."""
    try:
        import yaml
    except ImportError:
        yaml = None
    if yaml is not None:
        try:
            return json.loads(json.dumps(yaml.safe_load(text)))
        except yaml.YAMLError as e:
            die(f"YAML parse error: {str(e)[:300]}")
    ruby = shutil.which("ruby")
    if not ruby:
        die("parsing YAML needs PyYAML (pip install pyyaml) or ruby on PATH")
    p = subprocess.run([ruby, "-E", "UTF-8:UTF-8", "-ryaml", "-rjson", "-e", "puts JSON.generate(YAML.safe_load($stdin.read))"],
                       input=text, capture_output=True, text=True)
    if p.returncode:
        die(f"YAML parse error: {p.stderr.strip()[:300]}")
    return json.loads(p.stdout)


def skill_frontmatter(skill_dir):
    fm, _ = split_frontmatter(read(os.path.join(skill_dir, "SKILL.md")))
    if not fm:
        die(f"{skill_dir}/SKILL.md has no frontmatter")
    return parse_yaml(fm) or {}


def reset_dir(path):
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    elif os.path.lexists(path):
        os.unlink(path)
    os.makedirs(path)


def git(*args, cwd):
    p = subprocess.run(["git", "--no-optional-locks", *args], cwd=cwd, capture_output=True, text=True)
    if p.returncode:
        die(f"git {' '.join(args)} failed in {cwd}: {p.stderr.strip()[:300]}")
    return p.stdout.strip()


def source_commit():
    """This repository's HEAD, with -dirty when tracked inputs differ from it."""
    try:
        head = git("rev-parse", "HEAD", cwd=ROOT)
    except BuildError:
        return "unknown"
    dirty = subprocess.run(["git", "--no-optional-locks", "status", "--porcelain", "--", "profiles", "layers", "skills",
                            "hooks", "kits", "tools", "kits.lock", "team.json", "bin"],
                           cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return head + ("-dirty" if dirty else "")


def set_overlay(path):
    global OVERLAY, OVERLAY_GIVEN
    if not path:
        OVERLAY = OVERLAY_GIVEN = None
        return
    OVERLAY_GIVEN = os.path.abspath(os.path.expanduser(path))
    path = os.path.realpath(OVERLAY_GIVEN)
    if not os.path.isdir(path):
        die(f"overlay {path} is not a folder")
    if path == ROOT or path.startswith(ROOT + os.sep):
        die("the overlay must live outside this repository")
    OVERLAY = path


def source_path(kind, *parts):
    """A source file or folder: the overlay's copy when it has one, else this repository's."""
    if kind not in SOURCE_DIRS:
        raise ValueError(kind)
    if OVERLAY:
        p = os.path.join(OVERLAY, kind, *parts)
        if os.path.exists(p):
            return p
    return os.path.join(ROOT, kind, *parts)


def personal_path(agent):
    """The user's personal layer for an agent, or None."""
    if not OVERLAY:
        return None
    p = os.path.join(OVERLAY, "personal", f"{agent}.md")
    return p if os.path.isfile(p) else None


def overlay_hash():
    """sha256 over the overlay's files (dotfiles and dot-folders such as .git skipped), or None."""
    if not OVERLAY:
        return None
    h = hashlib.sha256()
    for rel in walk(OVERLAY):
        if any(part.startswith(".") for part in rel.split(os.sep)):
            continue
        full = os.path.join(OVERLAY, rel)
        h.update(f"F\0{rel}\0{file_sha(full)}\0".encode())
    return "sha256:" + h.hexdigest()


def load_team():
    """team.json, and for an overlay build the local team: the overlay's team.json agents (or this repository's
    agents plus the overlay's new profiles) at version <team version>+local.<overlay hash>."""
    team = json.loads(read(TEAM_PATH))
    if team["name"] != BUNDLE:
        die(f"team.json name must be {BUNDLE}")
    team["release_version"] = team["version"]
    if not OVERLAY:
        return team
    agents = list(team["agents"])
    ov_team = os.path.join(OVERLAY, "team.json")
    if os.path.isfile(ov_team):
        ov = json.loads(read(ov_team))
        unknown = set(ov) - {"agents"}
        if unknown:
            die(f"overlay team.json: only 'agents' is allowed (unknown: {sorted(unknown)})")
        agents = list(ov["agents"])
    else:
        prof = os.path.join(OVERLAY, "profiles")
        if os.path.isdir(prof):
            agents += sorted(f[:-3] for f in os.listdir(prof) if f.endswith(".md") and f[:-3] not in agents)
    if not agents or len(set(agents)) != len(agents):
        die("the team needs at least one agent and no duplicates")
    team["agents"] = agents
    team["version"] = f"{team['version']}+local.{overlay_hash()[7:19]}"
    return team


def json_dump(obj):
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
