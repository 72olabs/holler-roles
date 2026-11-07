"""Bundled MCP servers (profile field `mcp`, spec/AGENT-PROFILE.md and spec/LAUNCH.md).

A server is either remote (an https URL, with an optional bearer token taken from a named environment variable) or
local (`npx` or `uvx` running one package pinned to an exact version, environment variables passed through by name).
Values never appear in a bundle. Holler core enforces the same rules at launch. Nothing here grants approval for the
servers' tools: they prompt like any unapproved tool.

The canonical form, used for MANIFEST.json and for comparing the two harnesses, is
{name: {"command": str, "args": [str], "env": [sorted names]}} for a local server and
{name: {"url": str[, "bearer_token_env": name]}} for a remote one.
"""
import json
import re

SERVER_NAME = re.compile(r"[a-z][a-z0-9-]{0,31}")
ENV_NAME = re.compile(r"[A-Z_][A-Z0-9_]{0,63}")
LOCAL_KEYS = {"command", "args", "env"}
REMOTE_KEYS = {"url", "bearer_token_env"}
MAX_URL_BYTES = 2048
# A DNS host name: lowercase labels, at least two, the last alphabetic (so no IPv4 literal in any notation).
DNS_HOST = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?")
# URL path characters, percent-escapes well formed (Go's url.Parse in Holler core refuses a bad one); no "@".
URL_PATH = re.compile(r"(?:/(?:[A-Za-z0-9._~!$&'()*+,;=:-]|%[0-9A-Fa-f]{2})*)*")
COMMANDS = ("npx", "uvx")
MAX_SERVERS, MAX_ARGS, MAX_ARG_BYTES, MAX_ENV = 8, 32, 256, 16

# Every pattern is matched with fullmatch: Python's `$` also matches before a trailing newline, Go's (Holler core) does not.
# Exact versions: no ranges, tags, build metadata or leading zeros. The prerelease forms are the intersection of
# the shared rule (X.Y.Z-<pre>) and Holler core's validator, so a profile that builds is never refused at launch:
# npm takes X.Y.Z or X.Y.Z-<dot-separated identifiers>; PyPI takes X.Y.Z only (core reads PyPI prereleases as
# 1.0.0rc1, the shared rule as 1.0.0-rc1; until they agree, neither is accepted).
# Major, minor and patch stop at 15 digits: npm reads a part above Number.MAX_SAFE_INTEGER as a dist-tag, which the
# package owner can move. Prerelease identifiers are strict semver (no empty or leading-zero numeric identifiers),
# as in Holler core.
_NUM = r"(?:0|[1-9][0-9]{0,14})"
_PRE = r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
RELEASE = rf"{_NUM}\.{_NUM}\.{_NUM}"
NPM_VERSION = rf"{RELEASE}(?:-{_PRE}(?:\.{_PRE})*)?"
NPM_SPEC = re.compile(rf"(?:@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*@{NPM_VERSION}")
PY_SPEC = re.compile(rf"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?=={RELEASE}")
# npm-package-arg reads a spec ending like an archive as a local file, so `foo@1.0.0-x.tgz` would install a tarball
# from the launch folder although it matches the semver pattern.
NPM_ARCHIVE = re.compile(r"\.(?:tgz|tar|gz|tbz2?|txz|zip|whl)\Z", re.I)
UVX_COMMAND = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
NPX_YES = ("-y", "--yes")
# npm options that must not follow the package: another package, registry, config or prefix, or a shell command
# (-c/--call). Matched as prefixes, as Holler core does.
NPX_REFUSED_PREFIXES = ("--package", "-p", "--registry", "--userconfig", "--prefix", "--call", "-c")
# The agent's own identity and continuity handles: never passed to third-party code.
ENV_RESERVED_PREFIXES = ("HOLLER_", "CLAUDE_CODE_")
ENV_RESERVED = {"CLAUDECODE", "CODEX_HOME"}


def utf8(s):
    """The UTF-8 bytes of s; a string that has no UTF-8 form (a lone surrogate) is over every limit."""
    try:
        return s.encode()
    except UnicodeEncodeError:
        return b"\0" * (MAX_ARG_BYTES + 1)


def env_name_problem(v, what="env name"):
    if not isinstance(v, str) or not ENV_NAME.fullmatch(v):
        return f"{what} {v!r} must match {ENV_NAME.pattern} (names only, never values)"
    if v.startswith(ENV_RESERVED_PREFIXES) or v in ENV_RESERVED:
        return (f"{what} {v} is reserved: HOLLER_*, CLAUDE_CODE_*, CLAUDECODE and CODEX_HOME are the agent's own "
                f"handles and never reach a server")
    return None


def server_problem(name, spec):
    """Why this server breaks the rules, or None. spec is the profile's mapping (env as a list of names)."""
    if not isinstance(name, str) or not SERVER_NAME.fullmatch(name):
        return f"server name {name!r} must match {SERVER_NAME.pattern}"
    if name == "holler":
        return "server name holler is reserved for the Holler connector"
    if not isinstance(spec, dict):
        return "must be a mapping: url (remote) or command, args and env (local)"
    unknown = set(spec) - LOCAL_KEYS - REMOTE_KEYS
    if unknown:
        return f"unknown keys {sorted(unknown)} (remote: url, bearer_token_env; local: command, args, env)"
    if set(spec) & REMOTE_KEYS:
        if set(spec) & LOCAL_KEYS:
            return ("mixes a remote server (url, bearer_token_env) with a local one (command, args, env); "
                    "declare one kind per server")
        return remote_problem(spec)
    command, args, env = spec.get("command"), spec.get("args"), spec.get("env")
    env = [] if env is None else env
    if command not in COMMANDS:
        return f"command must be exactly npx or uvx, not {command!r}"
    if not isinstance(args, list) or not args:
        return "args must be a non-empty list"
    if len(args) > MAX_ARGS:
        return f"{len(args)} args (at most {MAX_ARGS})"
    for a in args:
        if not isinstance(a, str) or not 1 <= len(utf8(a)) <= MAX_ARG_BYTES or "\0" in a:
            return f"argument {a!r} must be a string of 1 to {MAX_ARG_BYTES} bytes of UTF-8 without NUL (quote numbers)"
        if "${" in a:
            return f"argument {a!r} contains ${{: Claude would expand it; pass variables through env"
    if not isinstance(env, list):
        return "env must be a list of variable names (values come from the user's environment)"
    if len(env) > MAX_ENV:
        return f"{len(env)} env names (at most {MAX_ENV})"
    for v in env:
        problem = env_name_problem(v)
        if problem:
            return problem
    if len(set(env)) != len(env):
        return "env names repeat"
    return (npx_problem if command == "npx" else uvx_problem)(args)


def remote_problem(spec):
    """A remote server: an https URL to a DNS host, nothing that carries a value or points at this machine."""
    url, bearer = spec.get("url"), spec.get("bearer_token_env")
    if not isinstance(url, str) or not url:
        return "a remote server needs url"
    if len(utf8(url)) > MAX_URL_BYTES:
        return f"url is over {MAX_URL_BYTES} bytes"
    if "${" in url:
        return "url contains ${: Claude would expand it; use bearer_token_env for a token"
    if not url.startswith("https://"):
        return f"url {url!r} must start with https://"
    if "?" in url or "#" in url:
        return f"url {url!r} has a query or fragment; neither is allowed (they tend to carry tokens)"
    if "@" in url or "\\" in url:
        return f"url {url!r} contains @ or a backslash; neither is allowed anywhere (userinfo, parser confusion)"
    rest = url[len("https://"):]
    cut = rest.find("/")
    host, path = (rest, "") if cut < 0 else (rest[:cut], rest[cut:])
    if host == "localhost" or host.endswith(".localhost"):
        return f"url host {host!r} is this machine; a bundled server must be a remote DNS host"
    if ":" in host or "[" in host:
        return f"url host {host!r} has a port or an IPv6 literal; give a DNS host name on the default port"
    if len(host) > 253 or not DNS_HOST.fullmatch(host):
        return f"url host {host!r} must be a lowercase DNS host name of two or more labels, no trailing dot (no IP literals)"
    if not URL_PATH.fullmatch(path):
        return f"url path {path!r} may hold only URL path characters (percent-encode the rest)"
    if bearer is not None:
        return env_name_problem(bearer, "bearer_token_env")
    return None


def npx_problem(args):
    i = 0
    while i < len(args) and args[i] in NPX_YES:
        i += 1
    if i == len(args):
        return "npx needs a package pinned to an exact version: name@X.Y.Z or @scope/name@X.Y.Z"
    if not NPM_SPEC.fullmatch(args[i]):
        what = "an option" if args[i].startswith("-") else "a package spec"
        return (f"npx: {args[i]!r} is {what} that is not allowed here; only -y/--yes may come before the package, which "
                f"must be pinned to an exact version: name@X.Y.Z or @scope/name@X.Y.Z (no ranges, tags, URLs, git refs or paths)")
    if NPM_ARCHIVE.search(args[i]):
        return f"npx: {args[i]!r} ends like an archive (.tgz, .tar, .gz, .zip, ...), which npm installs as a local file"
    for a in args[i + 1:]:
        if a == "--" or a.startswith(NPX_REFUSED_PREFIXES):
            return f"npx: argument {a!r} is not allowed (--, or starting with {', '.join(NPX_REFUSED_PREFIXES)})"
    return None


def uvx_problem(args):
    if args[0] == "--from":
        if len(args) < 3:
            return "uvx --from needs name==X.Y.Z and a command"
        spec, cmd = args[1], args[2]
        if not PY_SPEC.fullmatch(spec):
            return f"uvx --from: {spec!r} must be name==X.Y.Z, an exact version (no prerelease or extras)"
        if not UVX_COMMAND.fullmatch(cmd):
            return f"uvx --from: command {cmd!r} must be a plain executable name of at most 64 characters"
        return None
    if args[0].startswith("-"):
        return f"uvx: option {args[0]!r} is not allowed; only name==X.Y.Z or --from name==X.Y.Z <command>"
    if not PY_SPEC.fullmatch(args[0]):
        return f"uvx: {args[0]!r} must be name==X.Y.Z, an exact version (no prereleases, extras, ranges, URLs, git refs or paths)"
    return None


def canonical(spec):
    if "url" in spec:
        bearer = spec.get("bearer_token_env")
        return {"url": spec["url"], **({"bearer_token_env": bearer} if bearer is not None else {})}
    return {"command": spec["command"], "args": list(spec["args"]), "env": sorted(spec.get("env") or [])}


def check(servers, where):
    """The profile's `mcp` value, checked; returns the canonical form ({} when absent). Raises with a clear message."""
    from common import die
    if servers is None or servers == {}:
        return {}
    if not isinstance(servers, dict):
        die(f"{where}: mcp must be a mapping of server name to {{url, bearer_token_env}} or {{command, args, env}}")
    if len(servers) > MAX_SERVERS:
        die(f"{where}: mcp declares {len(servers)} servers (at most {MAX_SERVERS})")
    out = {}
    for name in sorted(servers, key=str):
        problem = server_problem(name, servers[name])
        if problem:
            die(f"{where}: mcp server {name}: {problem}")
        out[name] = canonical(servers[name])
    return out


def stray_declarations(agent_dir, agent, walk):
    """Anything else in an agent's output that would make a harness start an MCP server, as Holler core reads it: a
    .mcp.json (any case) outside the role plugin, a plugin.json with mcpServers (any case), or a Claude plugin
    manifest that is not a readable JSON object."""
    own = "/".join(("claude", "plugins", agent, ".mcp.json"))
    out = []
    for rel in walk(agent_dir):
        rel_posix = rel.replace("\\", "/")
        parts = rel_posix.split("/")
        base = parts[-1].lower()
        if base == ".mcp.json" and rel_posix != own:
            out.append(f"{rel_posix}: .mcp.json outside the role plugin")
        elif base == "plugin.json":
            try:
                with open(f"{agent_dir}/{rel}", "rb") as f:
                    data = json.loads(f.read().decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                data = None
            if not isinstance(data, dict):
                if len(parts) >= 2 and parts[-2].lower() == ".claude-plugin":
                    out.append(f"{rel_posix}: not a readable JSON object")
                continue
            if any(k.lower() == "mcpservers" for k in data):
                out.append(f"{rel_posix}: declares mcpServers (declare servers in the profile's mcp)")
    return out


# --- output ----------------------------------------------------------------------------------------------------------

def claude_json(servers):
    """The role plugin's .mcp.json: deterministic JSON, env and the bearer token passed through as ${VAR}."""
    body = {}
    for name, s in sorted(servers.items()):
        if "url" in s:
            entry = {"type": "http", "url": s["url"]}
            if "bearer_token_env" in s:
                entry["headers"] = {"Authorization": "Bearer ${" + s["bearer_token_env"] + "}"}
            body[name] = entry
            continue
        entry = {"command": s["command"], "args": s["args"]}
        if s["env"]:
            entry["env"] = {v: "${" + v + "}" for v in s["env"]}
        body[name] = entry
    return json.dumps({"mcpServers": body}, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def from_claude(data):
    """Canonical form of a parsed .mcp.json, or a problem string."""
    if not isinstance(data, dict) or set(data) != {"mcpServers"} or not isinstance(data["mcpServers"], dict):
        return "top level must be exactly {\"mcpServers\": {...}}"
    if len(data["mcpServers"]) > MAX_SERVERS:
        return f"{len(data['mcpServers'])} servers (at most {MAX_SERVERS})"
    out = {}
    for name, s in data["mcpServers"].items():
        if isinstance(s, dict) and ({"type", "url", "headers"} & set(s)):
            spec = remote_from_claude(s)
            if isinstance(spec, str):
                return f"server {name}: {spec}"
            problem = server_problem(name, spec)
            if problem:
                return f"server {name}: {problem}"
            out[name] = canonical(spec)
            continue
        if not isinstance(s, dict) or set(s) - LOCAL_KEYS:
            return f"server {name}: only command, args, env (local) or type, url, headers (remote)"
        env = s.get("env", {})
        if not isinstance(env, dict) or any(v != "${" + k + "}" for k, v in env.items()):
            return f"server {name}: env must map each name to ${{NAME}} (no values)"
        spec = {"command": s.get("command"), "args": s.get("args"), "env": list(env)}
        problem = server_problem(name, spec)
        if problem:
            return f"server {name}: {problem}"
        out[name] = canonical(spec)
    return out


BEARER_HEADER = re.compile(r"Bearer \$\{([A-Z_][A-Z0-9_]{0,63})\}")


def remote_from_claude(s):
    """A remote .mcp.json entry as a profile spec, or a problem string."""
    if set(s) - {"type", "url", "headers"} or s.get("type") != "http" or "url" not in s:
        return "a remote server is exactly type \"http\", url and optional headers"
    spec = {"url": s["url"]}
    if "headers" in s:
        h = s["headers"]
        m = BEARER_HEADER.fullmatch(h.get("Authorization", "")) if isinstance(h, dict) and set(h) == {"Authorization"} else None
        if not m:
            return "headers may only be {\"Authorization\": \"Bearer ${NAME}\"}"
        spec["bearer_token_env"] = m.group(1)
    return spec


def toml_str(s):
    out = ['"']
    for c in s:
        if c in '"\\':
            out.append("\\" + c)
        elif ord(c) < 0x20 or ord(c) == 0x7F:
            out.append(f"\\u{ord(c):04X}")
        else:
            out.append(c)
    return "".join(out + ['"'])


def codex_toml(servers):
    """[mcp_servers.<name>] tables for the Codex home template's config.toml (lines, each table preceded by a blank)."""
    lines = []
    for name, s in sorted(servers.items()):
        if "url" in s:
            lines += ["", f"[mcp_servers.{name}]", f"url = {toml_str(s['url'])}"]
            if "bearer_token_env" in s:
                lines.append(f"bearer_token_env_var = {toml_str(s['bearer_token_env'])}")
            continue
        lines += ["", f"[mcp_servers.{name}]", f"command = {toml_str(s['command'])}",
                  "args = [" + ", ".join(toml_str(a) for a in s["args"]) + "]"]
        if s["env"]:
            lines.append("env_vars = [" + ", ".join(toml_str(v) for v in s["env"]) + "]")
    return lines


def from_codex(table):
    """Canonical form of a parsed config.toml mcp_servers table, or a problem string."""
    if not isinstance(table, dict):
        return "mcp_servers must be a table"
    if len(table) > MAX_SERVERS:
        return f"{len(table)} servers (at most {MAX_SERVERS})"
    out = {}
    for name, s in table.items():
        if not isinstance(s, dict) or set(s) - {"command", "args", "env_vars", "url", "bearer_token_env_var"}:
            return f"server {name}: only command, args, env_vars (local) or url, bearer_token_env_var (remote)"
        renames = {"command": "command", "args": "args", "env_vars": "env", "url": "url",
                   "bearer_token_env_var": "bearer_token_env"}
        spec = {renames[k]: v for k, v in s.items()}
        problem = server_problem(name, spec)
        if problem:
            return f"server {name}: {problem}"
        out[name] = canonical(spec)
    return out
