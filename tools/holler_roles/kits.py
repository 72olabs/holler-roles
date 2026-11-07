"""Kit sources: kits.lock pins each kit repository by commit; kits are read only through kit.json."""
import json
import os
import re

import common
from common import LOCK_PATH, RESERVED_SOURCES, ROOT, die, git, json_dump, read, skill_frontmatter, tree_hash, write

NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
IN_REPO = "holler-roles"      # the source name of this repository's own kits/
OVERLAY_SOURCE = "overlay"
# Licences a kit may ship under (SPDX ids). Anything else, or NOASSERTION, is refused: we redistribute every kit.
ALLOWED_LICENCES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD", "CC0-1.0", "CC-BY-4.0", "Unlicense"}

BLOCKED_LICENCE = re.compile(r"NOASSERTION|\bA?GPL|\bLGPL|-NC\b|\bNC-|SSPL|BUSL|proprietary|all rights reserved", re.I)


LICENSE_REF = re.compile(r"^LicenseRef-[A-Za-z0-9.-]+$")


def check_licence(expr, where):
    """SPDX expression of allowed ids. LicenseRef-<name> marks your own kit's terms (spec/KIT.md); NOASSERTION fails."""
    ids = [t for t in re.split(r"\s+(?:AND|OR)\s+|[()]", str(expr or "")) if t.strip()]
    bad = [t.strip() for t in ids if t.strip() not in ALLOWED_LICENCES and not LICENSE_REF.match(t.strip())]
    if not ids or bad:
        die(f"{where}: licence {expr!r} is not on the allowed list {sorted(ALLOWED_LICENCES)}")


def load_lock():
    if not os.path.isfile(LOCK_PATH):
        die("kits.lock is missing; run `bin/holler-roles lock`")
    with open(LOCK_PATH) as f:
        lock = json.load(f)
    if lock.get("lock_format") != 2:
        die("kits.lock: lock_format must be 2 (spec/KIT.md)")
    lock.setdefault("kits", {})
    lock.setdefault("sources", {})
    return lock


def checkout_path(name, src):
    path = os.path.normpath(os.path.join(ROOT, src["checkout"]))
    if not os.path.isdir(os.path.join(path, "kits")):
        die(f"kit source {name}: no checkout at {path} (clone {src['repo']} there)")
    return path


def check_checkout(name, src, path):
    head = git("rev-parse", "HEAD", cwd=path)
    if head != src["commit"]:
        die(f"kit source {name}: checkout {path} is at {head}, kits.lock pins {src['commit']}. "
            f"Check out the pinned commit, or re-pin with `bin/holler-roles lock`.")
    dirty = git("status", "--porcelain", "--", "kits", cwd=path)
    if dirty:
        die(f"kit source {name}: uncommitted changes under {path}/kits:\n{dirty[:500]}")


def load_kit(kit_dir):
    meta = json.loads(read(os.path.join(kit_dir, "kit.json")))
    for key in ("kit_format", "name", "version", "upstream", "sha", "licence", "skills", "notices", "licence_files", "bundle"):
        if key not in meta:
            die(f"{kit_dir}/kit.json: missing {key}")
    if meta["kit_format"] != 1 or not NAME_RE.match(meta["name"]) or meta["name"] in RESERVED_SOURCES:
        die(f"{kit_dir}/kit.json: bad kit_format or name")
    if meta["bundle"] not in ("skills", "whole"):
        die(f"{kit_dir}/kit.json: bundle must be skills or whole")
    for f in meta["licence_files"] + meta["notices"]:
        if not os.path.isfile(os.path.join(kit_dir, f)):
            die(f"kit {meta['name']}: {f} listed in kit.json is missing")
    if not meta["licence_files"]:
        die(f"kit {meta['name']}: no licence files")
    check_licence(meta["licence"], f"kit {meta['name']}")
    for u in (meta.get("upstreams", []) if not LICENSE_REF.search(str(meta["licence"]).split()[0]) else []):
        # upstream licences are free text ("Apache-2.0; parts adapted from X, MIT"): name an allowed id, no blocked one
        text = str(u.get("licence") or "")
        if not any(re.search(rf"(?<![\w.-]){re.escape(i)}(?![\w.-])", text) for i in ALLOWED_LICENCES) or BLOCKED_LICENCE.search(text):
            die(f"kit {meta['name']}: upstream {u.get('name')} licence {text!r} is not clearly permissive")
    for s in meta["skills"]:
        d = os.path.join(kit_dir, s["path"])
        fm = skill_frontmatter(d)
        if fm.get("name") != s["name"]:
            die(f"kit {meta['name']}: {s['path']}/SKILL.md name {fm.get('name')!r} != kit.json {s['name']!r}")
        if " ".join(str(fm.get("description", "")).split()) != " ".join(s["description"].split()):
            die(f"kit {meta['name']}: {s['name']} description differs between SKILL.md and kit.json")
        if len(s["description"]) > 1024:
            die(f"kit {meta['name']}: {s['name']} description over 1024 characters")
    for h in meta.get("hooks", []):
        if not os.path.isdir(os.path.join(kit_dir, h["path"])):
            die(f"kit {meta['name']}: hook folder {h['path']} missing")
    for a in meta.get("agents", []):
        if not os.path.isfile(os.path.join(kit_dir, a["path"])):
            die(f"kit {meta['name']}: agent file {a['path']} missing")
    return meta


def kit_hash(kit_dir):
    return tree_hash(kit_dir)


def kit_dirs(path):
    return sorted(k for k in os.listdir(path) if os.path.isfile(os.path.join(path, k, "kit.json"))) if os.path.isdir(path) else []


def add_kit(kits, kit, kdir, source):
    meta = load_kit(kdir)
    if meta["name"] != kit:
        die(f"{kdir}/kit.json names {meta['name']}")
    if kit in kits:
        die(f"kit {kit} appears in two sources ({kits[kit][2]} and {source})")
    kits[kit] = (kdir, meta, source)


def load_kits(verify=True):
    """{kit name: (kit dir, kit.json, source)}: this repository's kits/ (pinned by content hash in kits.lock), every
    external source in kits.lock (pinned by commit and hash), then the overlay's kits/ (unpinned; spec/OVERLAY.md)."""
    lock = load_lock()
    kits = {}
    here = os.path.join(ROOT, "kits")
    unlocked = sorted(set(kit_dirs(here)) - set(lock["kits"]))
    if unlocked:
        die(f"kits/{unlocked[0]} is not in kits.lock; run `bin/holler-roles lock`")
    for kit, rec in sorted(lock["kits"].items()):
        kdir = os.path.join(here, kit)
        if not os.path.isdir(kdir):
            die(f"kit {kit} pinned in kits.lock is not in kits/")
        if verify and kit_hash(kdir) != rec["content_hash"]:
            die(f"kit {kit}: tree hash {kit_hash(kdir)} != kits.lock {rec['content_hash']}. Changes to a kit go through "
                f"its patches and NOTICE.md (spec/KIT.md); then run `bin/holler-roles lock`.")
        add_kit(kits, kit, kdir, IN_REPO)
    for name, src in sorted(lock["sources"].items()):
        path = checkout_path(name, src)
        if verify:
            check_checkout(name, src, path)
        for kit, rec in sorted(src["kits"].items()):
            kdir = os.path.join(path, "kits", kit)
            if not os.path.isdir(kdir):
                die(f"kit {kit} pinned in kits.lock is not in {path}/kits")
            if verify and kit_hash(kdir) != rec["content_hash"]:
                die(f"kit {kit}: tree hash {kit_hash(kdir)} != kits.lock {rec['content_hash']}")
            add_kit(kits, kit, kdir, name)
    if common.OVERLAY:
        for kit in kit_dirs(os.path.join(common.OVERLAY, "kits")):
            add_kit(kits, kit, os.path.join(common.OVERLAY, "kits", kit), OVERLAY_SOURCE)
    return kits


def lock_record(kdir):
    meta = load_kit(kdir)
    return {"version": meta["version"], "licence": meta["licence"], "content_hash": kit_hash(kdir)}


def cmd_lock(argv):
    """Record the hash of every kit in kits/, and re-pin every external source to its checkout's current HEAD."""
    lock = load_lock() if os.path.isfile(LOCK_PATH) else {"lock_format": 2, "kits": {}, "sources": {}}
    here = os.path.join(ROOT, "kits")
    lock["kits"] = {kit: lock_record(os.path.join(here, kit)) for kit in kit_dirs(here)}
    print(f"kits/: {len(lock['kits'])} kits")
    for name, src in lock["sources"].items():
        path = checkout_path(name, src)
        dirty = git("status", "--porcelain", "--", "kits", cwd=path)
        if dirty:
            die(f"{path}: commit the kits first:\n{dirty[:500]}")
        src["commit"] = git("rev-parse", "HEAD", cwd=path)
        src["kits"] = {kit: lock_record(os.path.join(path, "kits", kit)) for kit in kit_dirs(os.path.join(path, "kits"))}
        print(f"{name}: {src['commit']} ({len(src['kits'])} kits)")
    write(LOCK_PATH, json_dump(lock))
    return 0
