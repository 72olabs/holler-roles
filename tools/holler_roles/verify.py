"""verify: the kits pin, the bundle manifest and launch contract, plugin validity, the Codex listing (offline, no model
call) and reproducibility (two clean rebuilds give the same tarball)."""
import glob
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import tomllib

import mcp_servers
from build import build_all, bundle_name, dist_root
from common import die, file_sha, load_team, read, split_frontmatter, tree_hash, walk
from kits import load_kits

LAUNCH_ENV = {"HOLLER_ACTOR", "HOLLER_ROLE", "HOLLER_NAME_MODE", "HOLLER_DISPLAY_NAME"}


def report(cond, msg, bad):
    print(f"{'ok  ' if cond else 'FAIL'}  {msg}")
    if not cond:
        bad.append(msg)


def inside(bundle, rel):
    if os.path.isabs(rel) or ".." in rel.split("/"):
        return False
    full = os.path.realpath(os.path.join(bundle, rel))
    return full.startswith(os.path.realpath(bundle) + os.sep) and os.path.isdir(full)


def check_bundle(bundle, bad):
    man = json.loads(read(os.path.join(bundle, "manifest.json")))
    files = {f["path"]: f["sha256"] for f in man["files"]}
    on_disk = set(walk(bundle)) - {"manifest.json"}
    links = [os.path.join(dp, n) for dp, ds, fs in os.walk(bundle) for n in ds + fs if os.path.islink(os.path.join(dp, n))]
    report(not links, f"bundle has no symlinks{': ' + str(links[:3]) if links else ''}", bad)
    report(set(files) == on_disk, f"manifest.json lists exactly the {len(on_disk)} files in the bundle", bad)
    mism = [p for p, h in files.items() if p in on_disk and file_sha(os.path.join(bundle, p)) != h]
    report(not mism, f"every file matches its manifest sha256{': ' + str(mism[:3]) if mism else ''}", bad)
    off = [a["agent"] for a in man["agents"] if a["version"] != man["version"]]
    report(man["bundle"] == "starter-team" and not off,
           f"bundle is starter-team and every agent carries its version {man['version']}{': ' + str(off) if off else ''}", bad)
    return man


def check_agent(bundle, entry, bad):
    agent = entry["agent"]
    out = os.path.join(bundle, agent)
    launch = json.loads(read(os.path.join(bundle, entry["launch"])))
    report(tree_hash(out, exclude={"MANIFEST.json"}) == entry["content_hash"], f"{agent}: content hash {entry['content_hash']}", bad)
    report(launch["launch_format"] == 1 and set(launch["env"]) == LAUNCH_ENV and launch["env"]["HOLLER_NAME_MODE"] == "allocate",
           f"{agent}: launch.json env is exactly {sorted(LAUNCH_ENV)} ({launch['env']['HOLLER_ACTOR']}, {launch['env']['HOLLER_DISPLAY_NAME']})", bad)
    for h, spec in launch["harnesses"].items():
        key = "plugin_dir" if h == "claude" else "codex_home_template"
        report(spec["extra_args"] == [], f"{agent}/{h}: extra_args is empty", bad)
        report(inside(bundle, spec[key]), f"{agent}/{h}: {key} {spec[key]} is relative and inside the bundle", bad)
    text = json.dumps(launch)
    report(not re.search(r'"/(Users|home|private|tmp|var)/', text) and "--print" not in text.replace("claude -p/--print", ""),
           f"{agent}: launch.json has no absolute paths or print-mode flags", bad)
    plugins = os.path.join(bundle, launch["harnesses"]["claude"]["plugin_dir"])
    home = os.path.join(bundle, launch["harnesses"]["codex"]["codex_home_template"])
    problems = []
    cl = launch["harnesses"]["claude"]
    for label in cl["skills"] + cl["manual"]:
        plugin, skill = label.split(":", 1)
        manual = label in cl["manual"]
        for d in (os.path.join(plugins, plugin, "skills", skill), os.path.join(home, "skills", plugin, "skills", skill)):
            if not os.path.isfile(os.path.join(d, "SKILL.md")):
                problems.append(f"missing {os.path.relpath(d, bundle)}")
                continue
            fm, _ = split_frontmatter(read(os.path.join(d, "SKILL.md")))
            dmi = "disable-model-invocation: true" in fm
            pol = os.path.isfile(os.path.join(d, "agents", "openai.yaml"))
            if manual != dmi or manual != pol:
                problems.append(f"{label}: manual={manual}, claude flag={dmi}, codex policy={pol}")
    report(not problems, f"{agent}: {len(cl['skills'])} listed and {len(cl['manual'])} manual skills carry the right flags in both harnesses"
           + (f": {problems[:3]}" if problems else ""), bad)
    missing = []
    for p in cl["plugins"]:
        kj = os.path.join(plugins, p, "kit.json")
        if os.path.isfile(kj):
            meta = json.loads(read(kj))
            for f in meta["licence_files"] + meta["notices"]:
                for base in (os.path.join(plugins, p), os.path.join(home, "skills", p)):
                    if not os.path.isfile(os.path.join(base, f)):
                        missing.append(os.path.relpath(os.path.join(base, f), bundle))
    report(not missing, f"{agent}: every kit plugin carries its licence and notice files in both harnesses"
           + (f": {missing[:3]}" if missing else ""), bad)
    try:
        cfg = tomllib.loads(read(os.path.join(home, "config.toml")))
        report(not any(k in cfg for k in ("model", "model_reasoning_effort", "approval_policy")),
               f"{agent}: codex config.toml parses and sets no model, effort or approval policy", bad)
    except tomllib.TOMLDecodeError as e:
        report(False, f"{agent}: codex config.toml does not parse: {e}", bad)
        cfg = None
    check_mcp(bundle, agent, plugins, cfg, bad)
    markers = re.findall(r"^Brief marker: .+$", read(os.path.join(home, "AGENTS.md")), re.M)
    report(len(markers) == 2, f"{agent}: AGENTS.md carries {markers}", bad)
    if shutil.which("claude"):
        for p in cl["plugins"]:
            r = subprocess.run(["claude", "plugin", "validate", os.path.join(plugins, p)], capture_output=True, text=True, timeout=120)
            report(r.returncode == 0, f"{agent}: claude plugin validate {p}", bad)
    return launch


def check_mcp(bundle, agent, plugins, cfg, bad):
    """Bundled MCP servers: MANIFEST.json, the role plugin's .mcp.json and the Codex mcp_servers agree and pass the rules;
    no other .mcp.json anywhere in the agent."""
    out = os.path.join(bundle, agent)
    want = json.loads(read(os.path.join(out, "MANIFEST.json"))).get("mcp", {})
    problems = []
    for name, spec in want.items():
        p = mcp_servers.server_problem(name, spec)
        if p:
            problems.append(f"MANIFEST.json {name}: {p}")
    if len(want) > mcp_servers.MAX_SERVERS:
        problems.append(f"MANIFEST.json declares {len(want)} servers")
    own = os.path.join("claude", "plugins", agent, ".mcp.json")
    if os.path.isfile(os.path.join(out, own)):
        text = read(os.path.join(out, own))
        try:
            got = mcp_servers.from_claude(json.loads(text))
        except ValueError:
            got = "not valid JSON"
        if isinstance(got, str):
            problems.append(f".mcp.json: {got}")
        elif got != want or not want:
            problems.append(".mcp.json differs from MANIFEST.json mcp")
        elif text != mcp_servers.claude_json(want):
            problems.append(".mcp.json is not in the build's deterministic form")
    elif want:
        problems.append(f"no {own} for the servers in MANIFEST.json")
    if cfg is not None:
        got = mcp_servers.from_codex(cfg.get("mcp_servers", {}))
        if isinstance(got, str):
            problems.append(f"codex config.toml: {got}")
        elif got != want:
            problems.append("codex config.toml mcp_servers differs from MANIFEST.json mcp")
    problems += mcp_servers.stray_declarations(out, agent, walk)
    report(not problems, f"{agent}: bundled MCP servers ({', '.join(sorted(want)) or 'none'}): remote https or pinned npx/uvx, env by name, the same in "
           f"Claude, Codex and MANIFEST.json, only in the role plugin's .mcp.json (no other .mcp.json, no plugin.json "
           f"mcpServers)" + (f": {problems[:3]}" if problems else ""), bad)


def codex_listing(bundle, agent, launch, bad):
    """Render Codex's model-visible prompt for a fresh home made from the template (no model call)."""
    if not shutil.which("codex"):
        print(f"skip  {agent}: codex not on PATH")
        return
    from home import AGENTS_SKILLS
    tmp = tempfile.mkdtemp(prefix=f"holler-roles-codex-{agent}-")
    try:
        home = os.path.join(tmp, "home")
        shutil.copytree(os.path.join(bundle, launch["harnesses"]["codex"]["codex_home_template"]), home)
        extra = []
        for skill_md in sorted(glob.glob(os.path.join(AGENTS_SKILLS, "*", "SKILL.md"))):
            extra += ["[[skills.config]]", f"path = {json.dumps(skill_md)}", "enabled = false", ""]
        with open(os.path.join(home, "config.toml"), "a") as f:
            f.write("\n" + "\n".join(extra))
        cwd = os.path.join(tmp, "proj")
        os.makedirs(cwd)
        subprocess.run(["git", "init", "-q"], cwd=cwd)
        r = subprocess.run(["codex", "debug", "prompt-input", "hello"], cwd=cwd, capture_output=True, text=True, timeout=120,
                           env=dict(os.environ, CODEX_HOME=home))
        names = {n.split(":")[-1] for n in re.findall(r"\\n- ([a-z0-9:-]+): ", r.stdout)}
        want, manual = set(launch["harnesses"]["codex"]["skills"]), set(launch["harnesses"]["codex"]["manual"])
        report(names == want, f"{agent}: codex listing (offline render) is exactly the {len(want)} listed skills"
               + (f"; missing {sorted(want - names)}" if want - names else "") + (f"; extra {sorted(names - want)}" if names - want else "")
               + (f"; manual leaked {sorted(names & manual)}" if names & manual else ""), bad)
        found = re.findall(r"Brief marker: ([^\\\n]+)", r.stdout)
        report(len(found) >= 2, f"{agent}: codex prompt carries {found}", bad)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_verify(argv):
    bad = []
    load_kits(verify=True)
    report(True, "every kit matches its kits.lock pin and passes the licence check", bad)
    team = load_team()
    base = bundle_name(team)
    bundle = os.path.join(dist_root(), base)
    if not os.path.isfile(os.path.join(bundle, "manifest.json")):
        die(f"no bundle at {bundle}; run bin/holler-roles build")
    man = check_bundle(bundle, bad)
    for entry in man["agents"]:
        launch = check_agent(bundle, entry, bad)
        if "--no-codex" not in argv:
            codex_listing(bundle, entry["agent"], launch, bad)
    tar_path = os.path.join(dist_root(), f"{base}.tar.gz")
    sha = file_sha(tar_path)
    report(sha == read(tar_path + ".sha256").split()[0], f"{base}.tar.gz sha256 {sha} matches its .sha256 file", bad)
    with tarfile.open(tar_path) as t:
        members = t.getmembers()
    names = sorted(m.name for m in members if m.isfile())
    want = sorted([f"{base}/{f['path']}" for f in man["files"]] + [f"{base}/manifest.json"])
    report(names == want and not any(m.issym() or m.islnk() for m in members),
           f"{base}.tar.gz unpacks to {base}/<agent>/launch.json and {base}/manifest.json: {len(want)} files, no links", bad)
    hashes = []
    for i in range(2):
        tmp = tempfile.mkdtemp(prefix="holler-roles-verify-")
        try:
            results, tar, _ = build_all(team["agents"], tmp, verbose=False)
            for r in results:
                want_hash = next(a["content_hash"] for a in man["agents"] if a["agent"] == r["agent"])
                if r["content_hash"] != want_hash:
                    report(False, f"rebuild {i + 1}: {r['agent']} {r['content_hash']} != bundle {want_hash}", bad)
            hashes.append(tar[1])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    report(hashes[0] == hashes[1] == sha, f"reproducible: two clean rebuilds give {hashes[0][:16]}… and {hashes[1][:16]}…; dist has {sha[:16]}…", bad)
    print(f"\n{'VERIFIED' if not bad else 'FAILED'}: {len(bad)} problem(s)")
    return 1 if bad else 0
