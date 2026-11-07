"""Live load check for one agent on one harness (one model run).

usage: python3 -I tests/live_check.py <agent> claude|codex <out-dir>

Starts the built agent (dist/<agent>/<version>) the way launch.json says, in a scratch git repository under
<out-dir>, and asks it to list its skills, quote its markers, route one request and check its never-list.
Claude runs with `claude -p --model haiku` (stream-json, so the session's init event records the loaded skills and
plugins); Codex runs `codex exec` in a per-agent home made by `bin/holler-roles home`. These are load checks
only, on the cheapest models; a Holler-started agent must run interactively (spec/LAUNCH.md).

Writes only under <out-dir>. Prints a JSON summary; the raw output stays in <out-dir>.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROUTES = {
    "eng": ("The CSV export button stopped working after yesterday's deploy: it now downloads an empty file.", "bug-fix"),
    "product": ("Before engineering starts on team sharing, write the PRD they will build from.", "create-prd"),
    "reviewer": ("Please review the commits on branch feature/login (base main) against its acceptance check.", "code-review"),
    "designer": ("Give me three genuinely different directions for the inbox's empty state before anything is built.", "design-variants"),
}

PROMPT = """This is a load check for the agent's configuration. Do not use any tools and do not invoke any skill. Answer with exactly these four sections and nothing else:

SKILLS: the name of every skill in your available-skills list, comma-separated, exactly as listed (with any plugin prefix).
MARKERS: every line in your instructions or context that starts with "Brief marker:", quoted verbatim, one per line.
ROUTE: the one skill from your list you would use for this request, then " - " and a reason in at most eight words. Request: "{route}"
NEVER: for each of these names, "<name>: yes" if it is a skill in your list, else "<name>: no": {never}"""


CHEAP = {"claude": ["--model", "haiku"], "codex": ["-c", 'model="gpt-5.6-luna"', "-c", 'model_reasoning_effort="low"']}


def bundle_dir():
    team = json.load(open(os.path.join(ROOT, "team.json")))
    return os.path.join(ROOT, "dist", f"{team['name']}-{team['version']}")


def scratch_repo(path):
    os.makedirs(path, exist_ok=True)
    if not os.path.isdir(os.path.join(path, ".git")):
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
        with open(os.path.join(path, "README.md"), "w") as f:
            f.write("# scratch\n\nA scratch repository for an agent load check.\n")
        subprocess.run(["git", "add", "-A"], cwd=path, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "commit", "-q", "-m", "init"],
                       cwd=path, check=True)


SECTIONS = ("SKILLS", "MARKERS", "ROUTE", "NEVER")


def section(text, name):
    m = re.search(rf"^\**{name}\**:\s*(.*?)(?=^\**(?:{'|'.join(SECTIONS)})\**:|\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else ""


def main(argv):
    agent, harness, out = argv[0], argv[1], os.path.abspath(argv[2])
    bundle = bundle_dir()
    launch = json.load(open(os.path.join(bundle, agent, "launch.json")))
    profile_never = None
    for line in open(os.path.join(ROOT, "profiles", f"{agent}.md")):
        if line.startswith("never:"):
            profile_never = [n.strip() for n in line.split("[", 1)[1].rsplit("]", 1)[0].split(",") if n.strip()]
    never = profile_never or []
    route_q, route_want = ROUTES[agent]
    prompt = PROMPT.format(route=route_q, never=", ".join(never))
    work = os.path.join(out, f"{agent}-{harness}")
    repo = os.path.join(work, "repo")
    scratch_repo(repo)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE_CODE_", "CLAUDECODE", "CLAUDE_AGENT_SDK"))}
    env.update(launch["env"])
    spec = launch["harnesses"][harness]
    if harness == "claude":
        argv_run = ["claude", "--plugin-dir", os.path.join(bundle, spec["plugin_dir"])] + spec["extra_args"] + CHEAP["claude"]
        argv_run += ["-p", "--output-format", "stream-json", "--verbose", "--no-session-persistence", prompt]
        p = subprocess.run(argv_run, cwd=repo, env=env, capture_output=True, text=True, timeout=600)
        open(os.path.join(work, "stream.jsonl"), "w").write(p.stdout)
        open(os.path.join(work, "stderr.txt"), "w").write(p.stderr)
        init, result = {}, ""
        for line in p.stdout.splitlines():
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if ev.get("type") == "system" and ev.get("subtype") == "init":
                init = ev
            if ev.get("type") == "result":
                result = ev.get("result") or ""
        loaded = {"plugins": [pl.get("name") for pl in init.get("plugins", [])],
                  "skills": sorted(init.get("skills", []) or []),
                  "slash_commands": sorted(init.get("slash_commands", []) or []),
                  "model": init.get("model"), "entrypoint_note": "claude -p (load check only)"}
    else:
        home = os.path.join(work, "codex-home")
        subprocess.run([os.path.join(ROOT, "bin", "holler-roles"), "home", agent, home, "--project", repo], check=True,
                       capture_output=True, text=True)
        env["CODEX_HOME"] = home
        argv_run = ["codex", "exec"] + spec["extra_args"] + CHEAP["codex"] + ["--sandbox", "read-only", "--skip-git-repo-check",
                                                                            "-C", repo, "-o", os.path.join(work, "last-message.txt"), prompt]
        p = subprocess.run(argv_run, cwd=repo, env=env, capture_output=True, text=True, timeout=900)
        open(os.path.join(work, "stdout.txt"), "w").write(p.stdout)
        open(os.path.join(work, "stderr.txt"), "w").write(p.stderr)
        result = open(os.path.join(work, "last-message.txt")).read() if os.path.exists(os.path.join(work, "last-message.txt")) else p.stdout
        loaded = {"codex_home": home}
    open(os.path.join(work, "answer.txt"), "w").write(result)
    skills_said = [s.strip().split(":")[-1] for s in section(result, "SKILLS").replace("\n", ",").split(",") if s.strip()]
    want_listed = [s.split(":")[-1] for s in launch["harnesses"]["claude"]["skills"]]
    manual = [s.split(":")[-1] for s in launch["harnesses"]["claude"]["manual"]]
    markers = section(result, "MARKERS")
    route = section(result, "ROUTE")
    never_ans = section(result, "NEVER")
    summary = {
        "agent": agent, "harness": harness, "rc": p.returncode, "model_flags": CHEAP[harness],
        "skills_reported": len(skills_said),
        "listed_missing_from_report": sorted(set(want_listed) - set(skills_said)),
        "unexpected_in_report": sorted(set(skills_said) - set(want_listed)),
        "manual_in_report": sorted(set(skills_said) & set(manual)),
        "brief_marker": bool(re.search(r"holler \w+ agent brief", markers)),
        "platform_marker": "holler platform layer" in markers,
        "markers": markers,
        "route": route, "route_expected": route_want, "route_ok": route_want in route.split(" - ")[0],
        "never_answer": never_ans,
        "never_any_yes": bool(re.search(r":\s*yes", never_ans, re.I)),
        "loaded": loaded,
    }
    open(os.path.join(work, "summary.json"), "w").write(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
