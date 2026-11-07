"""Run ../check-careful.sh against cases.jsonl inside a scratch git repo whose origin/main exists,
so the default-branch force-push check has something to resolve. Writes nothing outside a temp dir.
usage: python3 -I tests/run_cases.py   (exit 1 on any failure)"""
import json, os, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
hook = os.path.join(os.path.dirname(here), "check-careful.sh")
fails = 0
with tempfile.TemporaryDirectory() as repo:
    env = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": repo, "GIT_CONFIG_NOSYSTEM": "1"}
    git = lambda *a: subprocess.run(["git", "-C", repo, *a], env=env, check=True, capture_output=True)
    git("init", "-q", "-b", "main")
    git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "--allow-empty", "-m", "init")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    def run(payload):
        r = subprocess.run(["/bin/bash", hook], input=payload, capture_output=True, text=True, cwd=repo, env=env, timeout=20)
        out = r.stdout.strip()
        try:
            got = (json.loads(out).get("hookSpecificOutput") or {}).get("permissionDecision", "allow") if out else "allow"
        except ValueError:
            got = f"bad-output({out[:40]!r})"
        return got if r.returncode == 0 else f"exit{r.returncode}"
    for line in open(os.path.join(here, "cases.jsonl")):
        case = json.loads(line)
        got = run(json.dumps(case["input"]))
        ok = got == case["expect"]
        fails += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {case['expect']:5} {got:5} {case['name']}")
    got = run("not json at all")
    ok = got == "ask"; fails += not ok
    print(f"{'ok  ' if ok else 'FAIL'} ask   {got:5} unparseable payload asks (fails closed)")
print(f"{fails} failed")
sys.exit(1 if fails else 0)
