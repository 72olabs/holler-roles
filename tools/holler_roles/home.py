"""Reference launcher pieces: make a per-agent Codex home from a template, and print or run the launch command.

  home <agent> <dest> [--project DIR]   copy dist/<agent>/<version>/codex/home-template to <dest>, link auth.json,
                                        append the user's Holler connector settings, hide ~/.agents skills
  launch <agent> claude|codex [--home DIR] [--print] [-- args...]
                                        exec the harness with the launch.json environment (Codex: --home required)

Reads ~/.codex (config.toml, holler.config.toml, plugins/cache/holler) and ~/.agents/skills; writes only <dest>.
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tomllib

from common import DIST, die, json_dump, load_team, read, write

USER_CODEX = os.path.join(os.path.expanduser("~"), ".codex")
AGENTS_SKILLS = os.path.join(os.path.expanduser("~"), ".agents", "skills")
HOLLER_BEGIN = "# BEGIN holler managed Codex MCP policy"
HOLLER_END = "# END holler managed Codex MCP policy"
HOLLER_PLUGIN = "holler@holler"


def toml_str(s):
    return json.dumps(s, ensure_ascii=True)


def bundle_dir():
    from build import bundle_name, dist_root
    path = os.path.join(dist_root(), bundle_name(load_team()))
    if not os.path.isfile(os.path.join(path, "manifest.json")):
        die(f"no bundle at {path}; run bin/holler-roles build (with the same overlay)")
    return path


def agent_launch(agent):
    b = bundle_dir()
    path = os.path.join(b, agent, "launch.json")
    if not os.path.isfile(path):
        die(f"{path} missing")
    return b, json.loads(read(path))


def holler_config_section(project=None):
    path = os.path.join(USER_CODEX, "config.toml")
    if not os.path.isfile(path):
        return ["# ~/.codex/config.toml not found: the Holler connector is not configured for Codex", ""]
    raw = read(path)
    user = tomllib.loads(raw)
    lines = ["", "# --- appended by holler-roles home: Holler connector (copied from ~/.codex/config.toml) ---"]
    market = (user.get("marketplaces") or {}).get("holler")
    plugin = (user.get("plugins") or {}).get(HOLLER_PLUGIN)
    if market and plugin and plugin.get("enabled"):
        lines.append("[marketplaces.holler]")
        for k in sorted(market):
            lines.append(f"{k} = {toml_str(market[k])}")
        lines += ["", f"[plugins.{toml_str(HOLLER_PLUGIN)}]", "enabled = true", ""]
        for key, state in sorted(((user.get("hooks") or {}).get("state") or {}).items()):
            if key.startswith(HOLLER_PLUGIN + ":") and "trusted_hash" in state:
                lines += [f"[hooks.state.{toml_str(key)}]", f"trusted_hash = {toml_str(state['trusted_hash'])}", ""]
        if HOLLER_BEGIN in raw and HOLLER_END in raw:
            lines += [raw[raw.index(HOLLER_BEGIN):raw.index(HOLLER_END) + len(HOLLER_END)], ""]
    else:
        lines += ["# Holler connector not enabled in ~/.codex/config.toml", ""]
    lines.append("# --- user-level skills (~/.agents/skills) kept out of this agent's listing ---")
    for skill_md in sorted(glob.glob(os.path.join(AGENTS_SKILLS, "*", "SKILL.md"))):
        lines += ["[[skills.config]]", f"path = {toml_str(skill_md)}", "enabled = false", ""]
    if project:
        lines += [f"[projects.{toml_str(os.path.realpath(project))}]", 'trust_level = "trusted"', ""]
    return lines


def cmd_home(argv):
    if len(argv) < 2:
        die("usage: holler-roles home <agent> <dest> [--project DIR]")
    agent, dest = argv[0], os.path.abspath(argv[1])
    project = argv[argv.index("--project") + 1] if "--project" in argv else None
    b, launch = agent_launch(agent)
    src = os.path.join(b, launch["harnesses"]["codex"]["codex_home_template"])
    if os.path.exists(dest) and os.listdir(dest):
        if not any(os.path.isfile(os.path.join(dest, m)) for m in (".holler-roles-home", ".holler-agents-home")):
            die(f"{dest} exists and was not made by holler-roles home; choose an empty folder")
    os.makedirs(dest, mode=0o700, exist_ok=True)
    # replace template-owned content; keep Codex's own state (sessions, logs, sqlite) if the home was used before
    for entry in ("skills", "AGENTS.md", "config.toml", "HOME-SETUP.md"):
        p = os.path.join(dest, entry)
        if os.path.isdir(p) and not os.path.islink(p):
            shutil.rmtree(p)
        elif os.path.lexists(p):
            os.unlink(p)
    shutil.copytree(src, dest, dirs_exist_ok=True)
    cfg = read(os.path.join(dest, "config.toml")).rstrip("\n").split("\n") + holler_config_section(project)
    text = "\n".join(cfg).rstrip() + "\n"
    tomllib.loads(text)
    write(os.path.join(dest, "config.toml"), text)
    os.chmod(os.path.join(dest, "config.toml"), 0o600)
    auth = os.path.join(dest, "auth.json")
    if os.path.lexists(auth) and not os.path.islink(auth):
        die(f"{auth} is a real file; expected a link to ~/.codex/auth.json")
    if os.path.lexists(auth):
        os.unlink(auth)
    os.symlink(os.path.join(USER_CODEX, "auth.json"), auth)
    hp = os.path.join(USER_CODEX, "holler.config.toml")
    if os.path.isfile(hp):
        shutil.copyfile(hp, os.path.join(dest, "holler.config.toml"))
        os.chmod(os.path.join(dest, "holler.config.toml"), 0o600)
    cache = os.path.join(USER_CODEX, "plugins", "cache", "holler")
    if os.path.isdir(cache):
        target = os.path.join(dest, "plugins", "cache", "holler")
        if os.path.isdir(target):
            shutil.rmtree(target)
        shutil.copytree(cache, target, symlinks=True)
    write(os.path.join(dest, ".holler-roles-home"), json_dump({"agent": agent, "template": os.path.relpath(src, DIST)}))
    print(dest)
    return 0


def clean_env(launch, harness, home=None):
    """The runtime invariants (spec/LAUNCH.md): only the launch.json env is added; Claude SDK markers are removed."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE_CODE_", "CLAUDECODE", "CLAUDE_AGENT_SDK"))}
    env.update(launch["env"])
    if harness == "codex":
        env["CODEX_HOME"] = home
    return env


def claude_mcp_env(bundle, agent):
    """{"CLAUDE_CODE_MCP_ALLOWLIST_ENV": "1"} when the agent's role plugin declares a local (stdio) MCP server, else {}.
    Claude otherwise hands its whole environment, HOLLER_* included, to stdio servers (spec/LAUNCH.md). Reads the
    .mcp.json Claude itself loads; one that can't be read counts as local (fail closed)."""
    path = os.path.join(bundle, agent, "claude", "plugins", agent, ".mcp.json")
    if not os.path.isfile(path):
        return {}
    try:
        servers = json.loads(read(path)).get("mcpServers") or {}
        local = any(not isinstance(s, dict) or s.get("type") != "http" for s in servers.values())
    except (ValueError, AttributeError):
        local = True
    return {"CLAUDE_CODE_MCP_ALLOWLIST_ENV": "1"} if local else {}


def cmd_launch(argv):
    if len(argv) < 2 or argv[1] not in ("claude", "codex"):
        die("usage: holler-roles launch <agent> claude|codex [--home DIR] [--print] [-- prompt]")
    agent, harness = argv[0], argv[1]
    rest = argv[2:]
    extra = rest[rest.index("--") + 1:] if "--" in rest else []
    opts = rest[:rest.index("--")] if "--" in rest else rest
    b, launch = agent_launch(agent)
    spec = launch["harnesses"][harness]
    home = None
    if harness == "claude":
        argv_out = ["claude", "--plugin-dir", os.path.join(b, spec["plugin_dir"])] + spec["extra_args"] + extra
    else:
        if "--home" not in opts:
            die("codex needs --home <per-agent CODEX_HOME> (make one with: holler-roles home <agent> <dest>)")
        home = os.path.abspath(opts[opts.index("--home") + 1])
        argv_out = ["codex"] + spec["extra_args"] + extra
    env = clean_env(launch, harness, home)
    # set after clean_env, which drops every inherited CLAUDE_CODE_* value
    mcp_env = claude_mcp_env(b, agent) if harness == "claude" else {}
    env.update(mcp_env)
    if "--print" in opts:
        shown = dict(launch["env"], **({"CODEX_HOME": home} if home else {}), **mcp_env)
        print("env -u CLAUDE_CODE_ENTRYPOINT " + " ".join(f"{k}={subprocess.list2cmdline([v])}" for k, v in shown.items()) + " "
              + " ".join(subprocess.list2cmdline([a]) for a in argv_out))
        return 0
    os.execvpe(argv_out[0], argv_out, env)
