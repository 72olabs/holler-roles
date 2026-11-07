"""Run ../guard.py against cases.jsonl. usage: python3 -I tests/run_cases.py   (exit 1 on any failure)"""
import json, os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
guard = os.path.join(os.path.dirname(here), "guard.py")
fails = 0


def run(payload):
    r = subprocess.run([sys.executable, "-I", guard], input=payload, capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        return f"exit{r.returncode}"
    out = r.stdout.strip()
    if not out:
        return "allow"
    return (json.loads(out).get("hookSpecificOutput") or {}).get("permissionDecision", "allow")


for line in open(os.path.join(here, "cases.jsonl")):
    case = json.loads(line)
    got = run(json.dumps(case["input"]))
    ok = got == case["expect"]
    fails += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {case['expect']:5} {got:5} {case['name']}")
got = run("not json")
ok = got == "deny"
fails += not ok
print(f"{'ok  ' if ok else 'FAIL'} deny  {got:5} unparseable payload denies (fails closed)")
print(f"{fails} failed")
sys.exit(1 if fails else 0)
