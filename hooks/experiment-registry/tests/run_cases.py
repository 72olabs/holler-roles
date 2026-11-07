"""Run guard.py against cases.jsonl in a temp project whose .agents/experiments.jsonl links to a
context dir (a symlinked registry must be protected too). usage: python3 -I run_cases.py"""
import json, os, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
guard = os.path.join(os.path.dirname(here), "guard.py")
fails = 0
with tempfile.TemporaryDirectory() as tmp:
    ctx = os.path.join(tmp, "context"); proj = os.path.join(tmp, "proj")
    os.makedirs(ctx); os.makedirs(os.path.join(proj, ".agents")); os.makedirs(os.path.join(proj, "notes"))
    open(os.path.join(ctx, "experiments.jsonl"), "w").close()
    os.symlink(os.path.join(ctx, "experiments.jsonl"), os.path.join(proj, ".agents", "experiments.jsonl"))
    os.symlink(os.path.join(ctx, "experiments.jsonl"), os.path.join(proj, "notes", "exp-alias.jsonl"))
    for line in open(os.path.join(here, "cases.jsonl")):
        case = json.loads(line)
        payload = json.dumps(case["input"]).replace("{proj}", proj).replace("{ctx}", ctx)
        r = subprocess.run([sys.executable, "-I", guard], input=payload, capture_output=True, text=True)
        got = "deny" if (r.returncode == 2 or '"deny"' in r.stdout) else ("allow" if r.returncode == 0 else f"error({r.returncode})")
        ok = got == case["expect"]
        fails += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {case['expect']:5} {got:5} {case['name']}")
    r = subprocess.run([sys.executable, "-I", guard], input="not json experiments.jsonl", capture_output=True, text=True)
    ok = r.returncode == 2; fails += not ok
    print(f"{'ok  ' if ok else 'FAIL'} deny  {'deny' if ok else r.returncode} unparseable input naming the registry blocks")
    r = subprocess.run([sys.executable, "-I", guard], input="not json", capture_output=True, text=True)
    ok = r.returncode == 0; fails += not ok
    print(f"{'ok  ' if ok else 'FAIL'} allow {'allow' if ok else r.returncode} unparseable unrelated input passes")
print(f"{fails} failed")
sys.exit(1 if fails else 0)
