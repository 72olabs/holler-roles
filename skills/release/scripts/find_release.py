"""Find a project's release script(s) from package.json and preflight them. Read-only.

usage: python3 -I find_release.py [project-dir] [--json]

Looks at <dir>/package.json and workspace packages (globs from "workspaces", plus apps/*, packages/*),
skipping node_modules. A script is release-like if its name is release, publish, dist, beta, sign
or notarize (or ends in :release, :beta, :publish) or its command runs electron-builder, notarytool
or codesign. For `node <file>` commands the file is read: environment variables it reads (reported
as set/missing, never their values), and whether it signs, notarizes or publishes. Nothing is
written and nothing is executed except `git --no-optional-locks status --porcelain` in each package directory.
"""
import glob
import json
import os
import re
import subprocess
import sys

NAME_RE = re.compile(r"(^|:)(release|publish|dist|beta|sign|notari[sz]e)$")
CMD_RE = re.compile(r"electron-builder|notarytool|codesign|--publish|semantic-release|changeset publish")
ENV_RE = re.compile(r"process\.env\.([A-Z][A-Z0-9_]*)|process\.env\[['\"]([A-Z][A-Z0-9_]*)['\"]\]")


def package_files(root):
    found = []
    top = os.path.join(root, "package.json")
    if os.path.isfile(top):
        found.append(top)
        try:
            data = json.load(open(top, encoding="utf-8"))
        except ValueError:
            data = {}
        ws = data.get("workspaces") or []
        if isinstance(ws, dict):
            ws = ws.get("packages") or []
    else:
        ws = []
    for pattern in list(ws) + ["apps/*", "packages/*"]:
        for d in sorted(glob.glob(os.path.join(root, pattern))):
            p = os.path.join(d, "package.json")
            if "node_modules" not in p.split(os.sep) and os.path.isfile(p) and p not in found:
                found.append(p)
    return found


def script_file(command, pkg_dir):
    m = re.match(r"^\s*node\s+(\S+\.(?:c?m?js))\b", command)
    if m:
        path = os.path.normpath(os.path.join(pkg_dir, m.group(1)))
        return path if os.path.isfile(path) else None
    return None


def inspect(command, path):
    text = command
    if path:
        text += "\n" + open(path, encoding="utf-8", errors="replace").read()
    env = sorted({a or b for a, b in ENV_RE.findall(text)})
    publish = re.findall(r"--publish[\s=\"',]+(\w+)", text)
    return {
        "env": {name: ("set" if os.environ.get(name) else "missing") for name in env},
        "signs": bool(re.search(r"forceCodeSigning|CSC_NAME|CSC_LINK|codesign|SIGN_ID", text)),
        "notarizes": bool(re.search(r"notari[sz]|APPLE_ID|APPLE_API_KEY|notarytool", text)),
        "publish_flags": sorted(set(publish)),
        "publishes": any(p != "never" for p in publish) or bool(re.search(r"semantic-release|changeset publish|npm publish|gh release", text)),
    }


def git_clean(d):
    try:
        out = subprocess.run(["git", "--no-optional-locks", "-C", d, "status", "--porcelain"], capture_output=True, text=True, timeout=20)
    except OSError:
        return None
    return None if out.returncode else (out.stdout.strip() == "")


def main(argv):
    root = os.path.abspath(next((a for a in argv if not a.startswith("--")), "."))
    rows = []
    for pj in package_files(root):
        d = os.path.dirname(pj)
        try:
            data = json.load(open(pj, encoding="utf-8"))
        except ValueError as e:
            rows.append({"package_json": pj, "error": f"unreadable: {e}"})
            continue
        for name, command in sorted((data.get("scripts") or {}).items()):
            if not (NAME_RE.search(name) or CMD_RE.search(command)):
                continue
            path = script_file(command, d)
            rows.append({"package": data.get("name"), "version": data.get("version"), "dir": d,
                         "run": f"npm run {name}", "script": name, "command": command,
                         "runs_file": path, "git_clean": git_clean(d), **inspect(command, path)})
    if "--json" in argv:
        print(json.dumps(rows, indent=2))
        return 0
    if not rows:
        print(f"no release-like script under {root}")
        return 1
    for r in rows:
        if "error" in r:
            print(f"{r['package_json']}: {r['error']}")
            continue
        print(f"{r['package']}@{r['version']}  ({r['dir']})")
        print(f"  {r['run']}  ->  {r['command']}")
        if r["runs_file"]:
            print(f"  runs {r['runs_file']}")
        flags = [k for k in ("signs", "notarizes", "publishes") if r[k]]
        print(f"  {', '.join(flags) or 'no signing, notarization or publishing detected'}"
              f"{'; --publish ' + ','.join(r['publish_flags']) if r['publish_flags'] else ''}")
        if r["env"]:
            print("  env: " + ", ".join(f"{k} {v}" for k, v in r["env"].items()))
        print(f"  git tree: {'clean' if r['git_clean'] else 'DIRTY' if r['git_clean'] is False else 'unknown'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
