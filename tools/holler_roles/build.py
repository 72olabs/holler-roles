"""Build agents from profiles: dist/<agent>/<version>/{claude/plugins, codex/home-template, launch.json, MANIFEST.json}
and the team bundle dist/<team>-<version>.tar.gz. Deterministic: same sources, same bytes."""
import gzip
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib

import common
from common import (BRIEF_CAP, DIST, LISTING_HARD, LISTING_SOFT, PLATFORM_PLUGIN, ROOT, copy_file, copy_tree, die,
                    file_sha, json_dump, load_team, overlay_hash, parse_yaml, personal_path, read, reset_dir,
                    skill_frontmatter, source_commit, source_path, split_frontmatter, tree_hash, walk, write)
from kits import IN_REPO, NAME_RE, load_kits, load_lock

PROFILE_KEYS = {"profile_format", "name", "version", "display_name", "role", "harnesses", "layers", "skills", "manual",
                "agents", "hooks", "never", "models", "claude", "codex", "holler", "presentation"}
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
HOOK_MATCHER = "startup|resume|clear|compact"
MANUAL_FLAG = "disable-model-invocation: true"
HIDDEN_FLAGS = "disable-model-invocation: true\nuser-invocable: false"
OPENAI_POLICY = "# holler-roles: not in the model's skill listing for this agent\npolicy:\n  allow_implicit_invocation: false\n"

# SessionStart hook: print a text file as additionalContext. Reads stdin and the file only.
BRIEF_HOOK = r"""#!/bin/sh
# holler-roles SessionStart hook: print a brief file as additionalContext.
# usage: session-brief.sh <file>        stdin: the hook input JSON
# Reads stdin and the file only. No network, no writes.
brief=${1:?usage: session-brief.sh <file>}
input=$(cat)
# claude --agent <name>: the main thread runs that agent's own prompt, not the agent brief.
if printf '%s' "$input" | grep -q '"agent_type"[[:space:]]*:[[:space:]]*"'; then
  exit 0
fi
[ -r "$brief" ] || { echo "holler-roles: cannot read $brief" >&2; exit 1; }
printf '%s' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"'
LC_ALL=C awk 'BEGIN { ORS = "" }
{
  if (NR > 1) print "\\n"
  n = length($0)
  for (i = 1; i <= n; i++) {
    c = substr($0, i, 1)
    if (c == "\\") print "\\\\"
    else if (c == "\"") print "\\\""
    else if (c == "\t") print "\\t"
    else if (c == "\r") print "\\r"
    else print c
  }
}
END { print "\\n" }' "$brief"
printf '%s\n' '"}}'
"""


# --- profiles ----------------------------------------------------------------------------------------

def agent_names():
    dirs = [os.path.join(ROOT, "profiles")] + ([os.path.join(common.OVERLAY, "profiles")] if common.OVERLAY else [])
    return sorted({f[:-3] for d in dirs if os.path.isdir(d) for f in os.listdir(d) if f.endswith(".md")})


def read_profile(name):
    path = source_path("profiles", f"{name}.md")
    if not os.path.isfile(path):
        die(f"no profile {path}")
    fm, body = split_frontmatter(read(path))
    p = parse_yaml(fm) or {}
    unknown = set(p) - PROFILE_KEYS
    if unknown:
        die(f"profiles/{name}.md: unknown keys {sorted(unknown)}")
    for key in ("profile_format", "name", "version", "display_name", "role", "harnesses", "layers", "skills", "holler"):
        if key not in p:
            die(f"profiles/{name}.md: missing {key}")
    if p["profile_format"] != 1 or p["name"] != name or not NAME_RE.match(name) or not SEMVER.match(str(p["version"])):
        die(f"profiles/{name}.md: bad profile_format, name or version")
    if not set(p["harnesses"]) <= {"claude", "codex"}:
        die(f"profiles/{name}.md: harnesses must be claude and/or codex")
    h = p["holler"]
    if not (h.get("actor") and NAME_RE.match(h["actor"]) and h.get("role_text") and h.get("accepts")):
        die(f"profiles/{name}.md: holler needs actor, role_text and accepts")
    # Holler's profile limits (holler_profile): role_text <= 2048 bytes; accepts <= 32 entries of <= 64 bytes, no control chars
    if len(" ".join(h["role_text"].split()).encode()) > 2048:
        die(f"profiles/{name}.md: holler.role_text over 2048 bytes")
    if not all(isinstance(a, str) for a in h["accepts"]):
        die(f"profiles/{name}.md: holler.accepts entries must be strings (quote entries that contain ': ')")
    if len(h["accepts"]) > 32 or any(len(a.encode()) > 64 or any(ord(c) < 32 for c in a) for a in h["accepts"]):
        die(f"profiles/{name}.md: holler.accepts needs <= 32 entries of <= 64 bytes each (Holler rejects longer ones)")
    pres = p.get("presentation") or {}
    if pres.get("voice"):
        die(f"profiles/{name}.md: presentation.voice is reserved and must be empty (spec/AGENT-PROFILE.md)")
    if "claude" in p and p["claude"]:
        die(f"profiles/{name}.md: claude launch options are not allowed in launch format 1 (extra_args must be empty); use a hook")
    if p.get("models"):
        print(f"note: {name}: models is a recommendation only; it is recorded in launch.json and not applied")
    for k in ("manual", "agents", "hooks", "never"):
        p[k] = list(p.get(k) or [])
    return p, body


def split_ref(ref, where):
    if not isinstance(ref, str) or ref.count("/") != 1:
        die(f"{where}: bad reference {ref!r} (want <source>/<name>)")
    return ref.split("/")


# --- resolution --------------------------------------------------------------------------------------

def resolve(profile, kits):
    """Resolve every reference. Returns a plan: plugins -> skills/agents/hooks with source dirs."""
    name = profile["name"]
    plan = {}   # plugin name -> {"kind", "kit", "skills": {skill: {"dir", "mode"}}, "agents": {}, "hooks": {}}

    def plugin(pname, kind, kit=None):
        return plan.setdefault(pname, {"kind": kind, "kit": kit, "skills": {}, "agents": {}, "hooks": {}})

    seen = {}
    for mode, refs in (("listed", profile["skills"]), ("manual", profile["manual"])):
        for ref in refs:
            src, sk = split_ref(ref, f"{name}.{mode}")
            if src == "holler":
                d = os.path.join(ROOT, "skills", sk)
                if not sk.startswith("holler-") or not os.path.isfile(os.path.join(d, "SKILL.md")):
                    die(f"{name}: {ref} is not a holler coordination skill")
                pl = plugin(PLATFORM_PLUGIN, "platform")
            elif src == "own":
                d = source_path("skills", sk)
                if sk.startswith("holler-") or not os.path.isfile(os.path.join(d, "SKILL.md")):
                    die(f"{name}: {ref} is not an original skill in skills/")
                pl = plugin(name, "role")
            else:
                if src not in kits:
                    die(f"{name}: {ref}: no kit {src} in kits.lock")
                kdir, meta, _ = kits[src]
                entry = next((s for s in meta["skills"] if s["name"] == sk), None)
                if not entry:
                    die(f"{name}: {ref}: kit {src} has no skill {sk} in kit.json")
                d = os.path.join(kdir, entry["path"])
                pl = plugin(src, "kit", src)
            fm_name = skill_frontmatter(d).get("name")
            if fm_name != sk:
                die(f"{name}: {ref}: SKILL.md name is {fm_name!r}")
            if sk in seen:
                die(f"{name}: skill name {sk} referenced twice ({seen[sk]} and {ref})")
            seen[sk] = ref
            pl["skills"][sk] = {"dir": d, "mode": mode, "ref": ref}
    for ref in profile["agents"]:
        src, ag = split_ref(ref, f"{name}.agents")
        if src in ("own", "holler"):
            f = source_path("agents", ag + ".md")
            if not os.path.isfile(f):
                die(f"{name}: {ref}: no agents/{ag}.md")
            plugin(name, "role")["agents"][ag] = f
        else:
            if src not in kits:
                die(f"{name}: {ref}: no kit {src}")
            kdir, meta, _ = kits[src]
            entry = next((a for a in meta.get("agents", []) if a["name"] == ag), None)
            if not entry:
                die(f"{name}: {ref}: kit {src} has no agent {ag}")
            plugin(src, "kit", src)["agents"][ag] = os.path.join(kdir, entry["path"])
    for ref in profile["hooks"]:
        src, hk = split_ref(ref, f"{name}.hooks")
        if src == "own":
            d = source_path("hooks", hk)
            if not os.path.isfile(os.path.join(d, "hook.json")):
                die(f"{name}: {ref}: no hooks/{hk}/hook.json")
            spec = json.loads(read(os.path.join(d, "hook.json")))
            plugin(name, "role")["hooks"][hk] = (d, spec)
        else:
            if src not in kits:
                die(f"{name}: {ref}: no kit {src}")
            kdir, meta, _ = kits[src]
            spec = next((h for h in meta.get("hooks", []) if h["name"] == hk), None)
            if not spec:
                die(f"{name}: {ref}: kit {src} has no hook {hk}")
            plugin(src, "kit", src)["hooks"][hk] = (os.path.join(kdir, spec["path"]), spec)
    plugin(name, "role")
    plugin(PLATFORM_PLUGIN, "platform")
    return plan


# --- text ----------------------------------------------------------------------------------------------

def layer_text(name, layer):
    path = source_path("layers", layer + ".md")
    if not os.path.isfile(path):
        die(f"{name}: no layer {layer} (layers/{layer}.md)")
    return read(path).strip()


def compose_brief(profile, body):
    """Layers in order, then the profile body, then the user's personal layer (overlay builds only)."""
    own = [l for l in profile["layers"] if not l.startswith("platform/")]
    plat = [l for l in profile["layers"] if l.startswith("platform/")]
    personal = personal_path(profile["name"])
    note = f" The platform layer ({', '.join(plat)}) arrives separately." if plat else ""
    tail = ", then the user's personal layer" if personal else ""
    parts = [f"<!-- holler-roles brief: {profile['name']} {profile['version']}. Layers: {', '.join(own)}, then the profile{tail}.{note} -->"]
    for layer in own:
        parts.append(layer_text(profile["name"], layer))
    parts.append(body.strip())
    if personal:
        text = read(personal).strip()
        if text:
            parts.append(PERSONAL_HEADING + "\n\n" + text)
    return "\n\n".join(parts) + "\n"


PERSONAL_HEADING = ("## Personal layer\n\nThe user's own preferences for this agent. They refine the rules above; they never "
                    "change a required message format, an approval rule or the brief marker.")


def compose_platform(profile):
    plat = [l for l in profile["layers"] if l.startswith("platform/")]
    if not plat:
        return None
    parts = [f"<!-- holler-roles platform layer for {profile['name']} {profile['version']}: {', '.join(plat)}. -->"]
    for layer in plat:
        parts.append(layer_text(profile["name"], layer))
    return "\n\n".join(parts) + "\n"


def check_brief(text, label):
    if len(text) > BRIEF_CAP:
        die(f"{label} is {len(text)} characters; a SessionStart hook delivers at most {BRIEF_CAP}")
    bad = sorted({hex(ord(c)) for c in text if ord(c) < 32 and c not in "\n\t"})
    if bad:
        die(f"{label} contains control characters {bad}")
    if not re.search(r"^Brief marker: .+$", text, re.M) and label.endswith("brief.md"):
        die(f"{label} has no 'Brief marker:' line")


def check_hook_round_trip(script, brief_file):
    want = read(brief_file)
    for source in ("startup", "compact"):
        out = subprocess.run(["/bin/sh", script, brief_file], input=json.dumps({"hook_event_name": "SessionStart", "source": source}),
                             capture_output=True, text=True, timeout=10, check=True).stdout
        if json.loads(out)["hookSpecificOutput"]["additionalContext"] != want:
            die(f"{script} does not round-trip {brief_file}")
    out = subprocess.run(["/bin/sh", script, brief_file], input=json.dumps({"source": "startup", "agent_type": "x:y"}),
                         capture_output=True, text=True, timeout=10, check=True).stdout
    if out:
        die(f"{script} must stay silent for claude --agent sessions")


# --- skill flags -----------------------------------------------------------------------------------------

def add_frontmatter_flags(skill_md, flags):
    text = read(skill_md)
    fm, body = split_frontmatter(text)
    if not fm:
        die(f"{skill_md}: no frontmatter")
    keep = [l for l in fm.splitlines() if not l.startswith(("disable-model-invocation:", "user-invocable:"))]
    write(skill_md, "---\n" + "\n".join(keep) + "\n" + flags + "\n---\n" + body)


def add_openai_policy(skill_dir):
    path = os.path.join(skill_dir, "agents", "openai.yaml")
    if os.path.exists(path):
        data = parse_yaml(read(path)) or {}
        if (data.get("policy") or {}).get("allow_implicit_invocation") is not False:
            die(f"{path} exists without policy.allow_implicit_invocation: false")
        return
    write(path, OPENAI_POLICY)


# --- Claude plugins --------------------------------------------------------------------------------------

def hook_command(spec, hook_dir, plugin_rel):
    out = []
    for arg in spec["command"]:
        if not os.path.isabs(arg) and os.path.isfile(os.path.join(hook_dir, arg)):
            out.append(f'"${{CLAUDE_PLUGIN_ROOT}}/{plugin_rel}/{arg}"')
        elif re.match(r"^[A-Za-z0-9_./=-]+$", arg):
            out.append(arg)
        else:
            die(f"hook {spec['name']}: argument {arg!r} needs quoting; keep hook argv simple")
    return " ".join(out)


def run_hook_tests(name, hook_dir, spec):
    tests = spec.get("tests")
    if not tests or not os.path.isfile(os.path.join(hook_dir, tests)):
        die(f"hook {name}: no tests; a hook without tests does not ship")
    p = subprocess.run([sys.executable, "-I", "-B", os.path.join(hook_dir, tests)], cwd=hook_dir,
                       capture_output=True, text=True, timeout=300)
    tail = (p.stdout.strip().splitlines() or ["(no output)"])[-1]
    if p.returncode:
        die(f"hook {name}: tests failed ({tail})\n{p.stdout[-2000:]}{p.stderr[-1000:]}")
    return tail


def plugin_json(path, data):
    write(os.path.join(path, ".claude-plugin", "plugin.json"), json.dumps(data, indent=2) + "\n")


def build_claude(profile, plan, kits, out, texts, log):
    plugins = os.path.join(out, "claude", "plugins")
    name = profile["name"]
    summary = {"skills": [], "manual": [], "agents": [], "hooks": [], "plugins": []}
    for pname in sorted(plan):
        pl = plan[pname]
        root = os.path.join(plugins, pname)
        events = {}
        if pl["kind"] == "role":
            plugin_json(root, {"name": pname, "version": profile["version"],
                               "description": f"Holler {profile['display_name']} agent: brief, original skills and guards (holler-roles).",
                               "author": {"name": "72o Labs"}, "license": "Apache-2.0"})
            write(os.path.join(root, "brief.md"), texts["brief"])
            write(os.path.join(root, "hooks", "session-brief.sh"), BRIEF_HOOK, executable=True)
            events.setdefault("SessionStart", []).append({"matcher": HOOK_MATCHER, "hooks": [{
                "type": "command",
                "command": '/bin/sh "${CLAUDE_PLUGIN_ROOT}/hooks/session-brief.sh" "${CLAUDE_PLUGIN_ROOT}/brief.md"',
                "timeout": 10}]})
            check_hook_round_trip(os.path.join(root, "hooks", "session-brief.sh"), os.path.join(root, "brief.md"))
        elif pl["kind"] == "platform":
            plugin_json(root, {"name": pname, "version": profile["version"],
                               "description": "Holler coordination layer: the platform brief and the holler-* coordination skills (holler-roles).",
                               "author": {"name": "72o Labs"}, "license": "Apache-2.0"})
            if texts["platform"]:
                write(os.path.join(root, "platform.md"), texts["platform"])
                write(os.path.join(root, "hooks", "session-brief.sh"), BRIEF_HOOK, executable=True)
                events.setdefault("SessionStart", []).append({"matcher": HOOK_MATCHER, "hooks": [{
                    "type": "command",
                    "command": '/bin/sh "${CLAUDE_PLUGIN_ROOT}/hooks/session-brief.sh" "${CLAUDE_PLUGIN_ROOT}/platform.md"',
                    "timeout": 10}]})
                check_hook_round_trip(os.path.join(root, "hooks", "session-brief.sh"), os.path.join(root, "platform.md"))
        else:
            kdir, meta, source = kits[pl["kit"]]
            plugin_json(root, {"name": pname, "version": meta["version"], "description": meta["description"],
                               "author": {"name": f"{meta['upstream']} (packaged by 72o Labs)"},
                               "repository": meta["upstream"], "license": meta["licence"]})
            for f in meta["licence_files"] + meta["notices"] + ["kit.json"]:
                copy_file(os.path.join(kdir, f), os.path.join(root, f))
            if os.path.isdir(os.path.join(kdir, "patches")):
                copy_tree(os.path.join(kdir, "patches"), os.path.join(root, "patches"))
            if meta["bundle"] == "whole":
                listable = {s["name"]: s for s in meta["skills"]}
                ksk = os.path.join(kdir, "skills")
                for entry in sorted(os.listdir(ksk)):
                    d = os.path.join(ksk, entry)
                    if not os.path.isdir(d):
                        continue
                    if listable.get(entry, {}).get("added") and entry not in pl["skills"]:
                        continue
                    copy_tree(d, os.path.join(root, "skills", entry))
                    if entry not in pl["skills"] and os.path.isfile(os.path.join(d, "SKILL.md")):
                        add_frontmatter_flags(os.path.join(root, "skills", entry, "SKILL.md"), HIDDEN_FLAGS)
                        add_openai_policy(os.path.join(root, "skills", entry))
                for f in sorted(os.listdir(ksk)):
                    if os.path.isfile(os.path.join(ksk, f)):
                        copy_file(os.path.join(ksk, f), os.path.join(root, "skills", f))
        # selected skills (kit "whole" bundles already copied them)
        for sk, info in sorted(pl["skills"].items()):
            dest = os.path.join(root, "skills", sk)
            if not (pl["kind"] == "kit" and kits[pl["kit"]][1]["bundle"] == "whole"):
                copy_tree(info["dir"], dest)
            label = f"{pname}:{sk}"
            if info["mode"] == "manual":
                add_frontmatter_flags(os.path.join(dest, "SKILL.md"), MANUAL_FLAG)
                add_openai_policy(dest)
                summary["manual"].append(label)
            else:
                summary["skills"].append(label)
        for ag, f in sorted(pl["agents"].items()):
            copy_file(f, os.path.join(root, "agents", ag + ".md"))
            summary["agents"].append(f"{pname}:{ag}")
        for hk, (hdir, spec) in sorted(pl["hooks"].items()):
            tail = run_hook_tests(hk, hdir, spec)
            log.append(f"hook tests {pname}:{hk}: {tail}")
            copy_tree(hdir, os.path.join(root, "hooks", hk), skip_dirs=("tests",), skip_files=("hook.json",))
            events.setdefault(spec["event"], []).append({"matcher": spec["matcher"], "hooks": [{
                "type": "command", "command": hook_command(spec, hdir, f"hooks/{hk}"), "timeout": spec.get("timeout", 10)}]})
            summary["hooks"].append(f"{pname}:{hk}")
        if events:
            write(os.path.join(root, "hooks", "hooks.json"), json.dumps({
                "description": f"holler-roles {name} {profile['version']}: {pname} hooks",
                "hooks": events}, indent=2) + "\n")
        summary["plugins"].append(pname)
    return summary


# --- Codex home template -----------------------------------------------------------------------------------

CODEX_SKIP_TOP = {".claude-plugin", "hooks", "agents", "brief.md", "platform.md"}


def build_codex(profile, out, texts):
    home = os.path.join(out, "codex", "home-template")
    plugins = os.path.join(out, "claude", "plugins")
    agents_md = texts["brief"] + ("\n" + texts["platform"] if texts["platform"] else "")
    write(os.path.join(home, "AGENTS.md"), agents_md)
    for pname in sorted(os.listdir(plugins)):
        src = os.path.join(plugins, pname)
        for rel in walk(src):
            if rel.split(os.sep)[0] in CODEX_SKIP_TOP:
                continue
            copy_file(os.path.join(src, rel), os.path.join(home, "skills", pname, rel))
    lines = [f"# holler-roles: Codex home template for {profile['name']} {profile['version']}.",
             "# Model, reasoning effort and approval policy are deliberately not set: the user's own choices apply.",
             "# A launcher copies this folder to a per-agent CODEX_HOME and appends the Holler connector settings",
             "# (see HOME-SETUP.md)."]
    sandbox = (profile.get("codex") or {}).get("sandbox")
    if sandbox:
        if sandbox not in ("read-only", "workspace-write"):
            die(f"{profile['name']}: codex.sandbox must be read-only or workspace-write")
        lines += [f'sandbox_mode = "{sandbox}"']
    lines += ["", "[skills.bundled]", "enabled = false", "", "[features]", "remote_plugin = false", ""]
    cfg = "\n".join(lines)
    tomllib.loads(cfg)
    write(os.path.join(home, "config.toml"), cfg)
    write(os.path.join(home, "HOME-SETUP.md"), HOME_SETUP.format(name=profile["name"]))
    return home


HOME_SETUP = """# Setting up a Codex home for {name}

This folder is a template. Codex writes its sessions and logs into its home, so each running agent gets its
own copy:

1. Copy this folder to a per-agent home, for example `<launcher state>/homes/{name}/codex`. The template has
   no symlinks.
2. Link the user's login: `auth.json` in the new home -> `~/.codex/auth.json` (Codex refreshes tokens in place,
   so the link keeps one login).
3. Append the Holler connector to the new home's `config.toml`, copied from `~/.codex/config.toml`:
   `[marketplaces.holler]`, `[plugins."holler@holler"]`, its `[hooks.state."holler@holler:..."]` trust entries
   and the block between `# BEGIN holler managed Codex MCP policy` and `# END ...`. Copy
   `~/.codex/holler.config.toml` and `~/.codex/plugins/cache/holler/` into the new home.
4. Keep user-level skills out of the agent's listing: for every `~/.agents/skills/*/SKILL.md`, append
   `[[skills.config]]` with that `path` and `enabled = false`.
5. Optionally copy the project's `[projects."<dir>"] trust_level` entry, or pass
   `-c 'projects={{"<dir>"={{trust_level="trusted"}}}}'` for one run.
6. Start Codex with `CODEX_HOME=<new home>` and the Holler environment from `launch.json`.

`bin/holler-roles home {name} <dest>` in the holler-roles repository is the reference implementation.
Nothing under `~/.codex` is changed by these steps.
"""


# --- launch.json, checks, manifest ------------------------------------------------------------------------------

def launch_json(profile, summary):
    """launch.json, launch format 1 (spec/LAUNCH.md). Paths are relative to the bundle root."""
    name = profile["name"]
    actor = profile["holler"]["actor"]
    pres = profile.get("presentation") or {}
    display = pres.get("display_name") or profile["display_name"]
    env = {"HOLLER_ACTOR": actor, "HOLLER_ROLE": actor, "HOLLER_NAME_MODE": "allocate", "HOLLER_DISPLAY_NAME": display}
    card = {"actor": actor, "role_text": " ".join(profile["holler"]["role_text"].split()),
            "accepts": list(profile["holler"]["accepts"])}
    harnesses = {}
    if "claude" in profile["harnesses"]:
        harnesses["claude"] = {
            "plugin_dir": f"{name}/claude/plugins",
            "extra_args": [],
            "context": [f"SessionStart hook in plugin {name} prints brief.md",
                        f"SessionStart hook in plugin {PLATFORM_PLUGIN} prints platform.md"],
            "wake": {
                "mode": "hook-long-poll",
                "requires": ("Interactive claude in a terminal the runtime owns (Terminal, iTerm or a PTY) with "
                             "CLAUDE_CODE_ENTRYPOINT unset, and the project folder trusted by Claude Code."),
                "never": "claude -p/--print, the Agent SDK (sdk-cli, sdk-ts, sdk-py), --bg: the connector does not wake them.",
            },
            "plugins": summary["plugins"],
            "skills": summary["skills"],
            "manual": summary["manual"],
            "agents": summary["agents"],
            "hooks": summary["hooks"],
        }
    if "codex" in profile["harnesses"]:
        harnesses["codex"] = {
            "codex_home_template": f"{name}/codex/home-template",
            "extra_args": [],
            "context": ["AGENTS.md in CODEX_HOME: brief.md followed by platform.md"],
            "wake": {
                "mode": "daemon queue (hollerd runs codex queue --thread <id>)",
                "status": "blocked",
                "blocker": ("hollerd runs codex queue without the session's CODEX_HOME, so a Codex agent in its own home "
                            "is not woken live; messages wait for its next turn. Needs the Holler core wake fix."),
                "never": "codex exec: it cannot be woken.",
            },
            "sandbox": (profile.get("codex") or {}).get("sandbox"),
            "skills": [s.split(":", 1)[1] for s in summary["skills"]],
            "manual": [s.split(":", 1)[1] for s in summary["manual"]],
        }
    return {
        "launch_format": 1,
        "agent": name,
        "version": profile["version"],
        "display_name": display,
        "icon": pres.get("icon_emoji"),
        "icon_emoji": pres.get("icon_emoji"),
        "icon_brief": pres.get("icon_brief"),
        "tagline": pres.get("tagline"),
        "role": profile["role"],
        "env": env,
        "holler": card,
        "first_prompt": ("You are the {display} agent ({name} {version}), started by Holler. "
                         "1. Call holler_profile now with role_text {role_text} and accepts {accepts}; this advisory write about yourself is approved. "
                         "2. Reply here with one line: your Holler actor and \"ready\". "
                         "3. Then wait. Handle Holler messages addressed to you and reply in the same thread.").format(
                             display=display, name=name, version=profile["version"],
                             role_text=json.dumps(card["role_text"]), accepts=json.dumps(card["accepts"])),
        "recommended_models": profile.get("models") or None,
        "harnesses": harnesses,
    }


def check_never(profile, out):
    never = set(profile["never"])
    found = set()
    for rel in walk(out):
        parts = rel.split(os.sep)
        base, stem = parts[-1], os.path.splitext(parts[-1])[0]
        if base == "SKILL.md" and len(parts) >= 2:
            found.add(parts[-2])
            fm, _ = split_frontmatter(read(os.path.join(out, rel)))
            m = re.search(r"^name:\s*\"?([^\"\n]+)\"?\s*$", fm, re.M)
            if m:
                found.add(m.group(1).strip())
        if "agents" in parts[:-1] and base.endswith(".md"):
            found.add(stem)
        if "playbooks" in parts[:-1] and base.endswith(".md"):
            found.add(stem)
        if "hooks" in parts[:-1]:
            idx = parts.index("hooks")
            if idx + 1 < len(parts) - 1:
                found.add(parts[idx + 1])
        if len(parts) >= 3 and parts[0] == "claude" and parts[1] == "plugins":
            found.add(parts[2])
    hit = sorted(never & found)
    if hit:
        die(f"{profile['name']}: build contains names listed under never: {hit}")


def check_paths(out):
    """No absolute path from the build machine in the output: this repository, the overlay or the home folder."""
    home = os.path.expanduser("~")
    needles = {p.encode() for p in (ROOT, os.path.abspath(ROOT))} | {p.encode() + b"/" for p in (home, os.path.realpath(home))}
    if common.OVERLAY:
        needles |= {common.OVERLAY.encode(), common.OVERLAY_GIVEN.encode()}
    for rel in walk(out):
        p = os.path.join(out, rel)
        with open(p, "rb") as f:
            data = f.read()
        for needle in needles:
            if needle in data:
                die(f"absolute build path in {rel}")


def manifest(out):
    files = []
    for rel in walk(out):
        full = os.path.join(out, rel)
        files.append({"path": rel, "sha256": file_sha(full), "size": os.path.getsize(full),
                      "mode": "0755" if os.stat(full).st_mode & 0o111 else "0644"})
    return files


# --- build ---------------------------------------------------------------------------------------------------

def build_agent(name, kits, dest_root, log, team):
    profile, body = read_profile(name)
    if common.OVERLAY:
        # Holler's runtime requires every agent in a bundle to carry the bundle's version.
        profile["version"] = team["version"]
    elif profile["version"] != team["version"]:
        die(f"profiles/{name}.md: version {profile['version']} differs from team.json {team['version']}; "
            f"Holler's runtime requires one version per bundle")
    plan = resolve(profile, kits)
    texts = {"brief": compose_brief(profile, body), "platform": compose_platform(profile)}
    check_brief(texts["brief"], f"{name}/brief.md")
    if texts["platform"]:
        check_brief(texts["platform"], f"{name}/platform.md")
    out = os.path.join(dest_root, name)
    reset_dir(out)
    summary = build_claude(profile, plan, kits, out, texts, log)
    build_codex(profile, out, texts)
    listed, manual = len(summary["skills"]), len(summary["manual"])
    if listed > LISTING_HARD:
        die(f"{name}: {listed} listed skills (limit {LISTING_HARD}); move some to manual")
    if listed > LISTING_SOFT:
        log.append(f"warning: {name} lists {listed} skills (target {LISTING_SOFT})")
    write(os.path.join(out, "launch.json"), json_dump(launch_json(profile, summary)))
    check_never(profile, out)
    check_paths(out)
    files = manifest(out)
    content_hash = tree_hash(out)
    kits_used = sorted(p for p in summary["plugins"] if p in kits)
    lock = load_lock()
    srcs = {}
    for k in kits_used:
        kdir, meta, src_name = kits[k]
        if src_name in lock["sources"]:
            commit, h = lock["sources"][src_name]["commit"], lock["sources"][src_name]["kits"][k]["content_hash"]
        elif src_name == IN_REPO:
            commit, h = None, lock["kits"][k]["content_hash"]   # this repository's kits/: its commit is source.holler-agents
        else:
            commit, h = None, tree_hash(kdir)
        srcs[k] = {"source": src_name, "commit": commit, "version": meta["version"], "licence": meta["licence"],
                   "content_hash": h}
    write(os.path.join(out, "MANIFEST.json"), json_dump({
        "agent": name, "version": profile["version"], "content_hash": content_hash, "kits": srcs,
        "brief_chars": len(texts["brief"]), "platform_chars": len(texts["platform"] or ""),
        "listed": listed, "manual": manual, "files": files}))
    return {"agent": name, "version": profile["version"], "dir": out, "content_hash": content_hash,
            "listed": listed, "manual": manual, "summary": summary,
            "brief_chars": len(texts["brief"]), "platform_chars": len(texts["platform"] or "")}


def deterministic_tar(src_root, members, tar_path, prefix):
    """members: relative paths under src_root, sorted. Fixed metadata, gzip without name or time."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tar:
        dirs = set()
        for rel in members:
            parts = rel.split(os.sep)
            for i in range(1, len(parts)):
                dirs.add(os.sep.join(parts[:i]))
        entries = sorted([(d, True) for d in dirs] + [(m, False) for m in members])
        top = tarfile.TarInfo(prefix)
        top.type, top.mode, top.mtime, top.uid, top.gid, top.uname, top.gname = tarfile.DIRTYPE, 0o755, 0, 0, 0, "", ""
        tar.addfile(top)
        for rel, is_dir in entries:
            ti = tarfile.TarInfo(f"{prefix}/{rel}")
            ti.mtime, ti.uid, ti.gid, ti.uname, ti.gname = 0, 0, 0, "", ""
            if is_dir:
                ti.type, ti.mode = tarfile.DIRTYPE, 0o755
                tar.addfile(ti)
            else:
                full = os.path.join(src_root, rel)
                ti.size = os.path.getsize(full)
                ti.mode = 0o755 if os.stat(full).st_mode & 0o111 else 0o644
                with open(full, "rb") as f:
                    tar.addfile(ti, f)
    raw = buf.getvalue()
    gz = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=gz, mtime=0, compresslevel=9) as g:
        g.write(raw)
    write(tar_path, gz.getvalue())


def bundle_name(team):
    return f"{team['name']}-{team['version']}"


BUNDLE_LICENSE = """Copyright 2026 72o Labs

The agent profiles, briefs (brief.md, platform.md, AGENTS.md), the holler-* coordination skills, the original
skills and hooks in each agent's role and holler-platform plugins, and the launch files in this bundle are
licensed under the Apache License, Version 2.0: https://www.apache.org/licenses/LICENSE-2.0

Third-party components keep their own open-source licences. They are the plugins named after a kit (for
example pstack, gstack, web-ui) and the matching folders under codex/home-template/skills/; each carries its
licence, NOTICE.md, PROVENANCE.md and patches. NOTICE.md at the bundle root lists them all.

A bundle built with a user's overlay (version <x.y.z>+local.<hash>) also contains that user's own profiles,
layers and skills, under whatever terms the user chose.
"""


def bundle_notice(bundle_dir, results):
    """Aggregate third-party notices: every kit used by any agent, with its upstreams and where its licences sit."""
    kits = {}
    for r in results:
        plugins = os.path.join(bundle_dir, r["agent"], "claude", "plugins")
        for p in sorted(os.listdir(plugins)):
            kj = os.path.join(plugins, p, "kit.json")
            if os.path.isfile(kj):
                meta = json.loads(read(kj))
                kits.setdefault(p, (meta, []))[1].append(r["agent"])
    lines = ["# Third-party notices", "",
             "This bundle includes the open-licensed kits below, as pinned by content hash in the kits.lock of the",
             "source commit recorded in manifest.json. Each kit's folder holds its licence files, NOTICE.md (attribution",
             "and every change), PROVENANCE.md and patches: `<agent>/claude/plugins/<kit>/` and",
             "`<agent>/codex/home-template/skills/<kit>/`.", ""]
    for name, (meta, agents) in sorted(kits.items()):
        lines += [f"## {name} {meta['version']} ({meta['licence']})", "", f"Used by: {', '.join(agents)}. {meta['description']}", ""]
        for u in meta["upstreams"]:
            lines.append(f"- {u['name']}: {u['url']} at `{u['sha']}`, {u['licence']} (`{u['path']}`)")
        lines += ["", f"Licence files: {', '.join('`' + f + '`' for f in meta['licence_files'])}. Notices: "
                  f"{', '.join('`' + f + '`' for f in meta['notices'])}.", ""]
    return "\n".join(lines)


def build_team(bundle_dir, results, team, kits_lock, commit):
    """manifest.json at the bundle root (every file with its sha256), then the deterministic tarball next to it."""
    base = os.path.basename(bundle_dir)
    write(os.path.join(bundle_dir, "LICENSE"), BUNDLE_LICENSE)
    write(os.path.join(bundle_dir, "NOTICE.md"), bundle_notice(bundle_dir, results))
    members = [m for m in walk(bundle_dir) if m != "manifest.json"]
    agents = []
    for r in results:
        launch = json.loads(read(os.path.join(bundle_dir, r["agent"], "launch.json")))
        agents.append({"agent": r["agent"], "version": r["version"], "display_name": launch["display_name"],
                       "icon": launch["icon"], "launch": f"{r['agent']}/launch.json", "content_hash": r["content_hash"],
                       "harnesses": sorted(launch["harnesses"]), "listed_skills": r["listed"], "manual_skills": r["manual"]})
    team_manifest = {
        "manifest_format": 1,
        "bundle": team["name"], "version": team["version"],
        "source": dict({"holler-agents": commit}, **({"overlay": overlay_hash()} if common.OVERLAY else {})),
        "kits": {k: {"repo": v["repo"], "commit": v["commit"]} for k, v in kits_lock["sources"].items()},
        "agents": agents,
        "files": [{"path": m, "sha256": file_sha(os.path.join(bundle_dir, m)), "size": os.path.getsize(os.path.join(bundle_dir, m))}
                  for m in members],
    }
    write(os.path.join(bundle_dir, "manifest.json"), json_dump(team_manifest))
    tar_path = os.path.join(os.path.dirname(bundle_dir), f"{base}.tar.gz")
    deterministic_tar(bundle_dir, sorted(members + ["manifest.json"]), tar_path, base)
    sha = file_sha(tar_path)
    write(os.path.join(os.path.dirname(bundle_dir), f"{base}.tar.gz.sha256"), f"{sha}  {base}.tar.gz\n")
    return tar_path, sha


def build_all(names, dest_root, verbose=True):
    """Build agents into dest_root/<bundle>/<agent>; with the whole team, also manifest.json and the tarball."""
    kits = load_kits()
    lock = load_lock()
    team = load_team()
    bundle_dir = os.path.join(dest_root, bundle_name(team))
    os.makedirs(bundle_dir, exist_ok=True)
    log, results = [], []
    for n in names:
        r = build_agent(n, kits, bundle_dir, log, team)
        results.append(r)
        if verbose:
            print(f"{n} {r['version']}: listed {r['listed']}, manual {r['manual']}, brief {r['brief_chars']} chars, "
                  f"platform {r['platform_chars']} chars, {r['content_hash']}")
    tar = None
    if sorted(names) == sorted(team["agents"]):
        tar = build_team(bundle_dir, [r for n in team["agents"] for r in results if r["agent"] == n], team, lock, source_commit())
    if verbose:
        for line in log:
            print(line)
    return results, tar, bundle_dir


def dist_root():
    """dist/ for release builds; dist/local/ for overlay builds, so a local build never replaces a release."""
    return os.path.join(DIST, "local") if common.OVERLAY else DIST


def cmd_build(argv):
    """build [agent...|all] [--force]: the whole team installs dist/<bundle>/ and dist/<bundle>.tar.gz;
    a subset is built into dist/partial/<bundle>/ for inspection only. With an overlay: dist/local/."""
    force = "--force" in argv
    args = [a for a in argv if not a.startswith("--")]
    team = load_team()
    names = team["agents"] if not args or args == ["all"] else args
    for n in names:
        if n not in agent_names():
            die(f"no profile {n}")
    whole = sorted(names) == sorted(team["agents"])
    staging = tempfile.mkdtemp(prefix="holler-roles-build-")
    try:
        results, tar, bundle_dir = build_all(names, staging)
        base = os.path.basename(bundle_dir)
        dest_parent = dist_root() if whole else os.path.join(dist_root(), "partial")
        final = os.path.join(dest_parent, base)
        if whole and os.path.isdir(final):
            if tree_hash(final, exclude={"manifest.json"}) != tree_hash(bundle_dir, exclude={"manifest.json"}) and not force:
                die(f"{final} exists with different content. Bump the team version in team.json (and agent versions), or pass --force.")
        if os.path.isdir(final):
            shutil.rmtree(final)
        os.makedirs(dest_parent, exist_ok=True)
        shutil.copytree(bundle_dir, final)
        for r in results:
            print(f"{os.path.relpath(final, ROOT)}/{r['agent']}  {r['content_hash']}")
        if tar:
            for f in (f"{base}.tar.gz", f"{base}.tar.gz.sha256"):
                shutil.copyfile(os.path.join(staging, f), os.path.join(dist_root(), f))
            print(f"{os.path.relpath(dist_root(), ROOT)}/{base}.tar.gz  sha256:{tar[1]}")
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return 0
