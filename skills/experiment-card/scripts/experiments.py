#!/usr/bin/env python3
"""Append-only experiment registry (experiment-card skill, holler-roles).

usage:
  experiments.py add --card FILE|- --approved-by NAME [--registry PATH]
  experiments.py readout --card ID --actual N --source S --date YYYY-MM-DD --label LABEL
                         --sample N [--kill-triggered yes|no] [--notes TEXT] [--registry PATH]
  experiments.py list [--open] [--due-by YYYY-MM-DD] [--registry PATH]
  experiments.py show ID [--registry PATH]
  experiments.py verify [--registry PATH]
  experiments.py template
  experiments.py init [--registry PATH]

Registry: --registry, else $HOLLER_EXPERIMENTS, else .agents/experiments.jsonl. Only `init` creates
a registry (empty, refusing an existing file); every other command needs it to exist. Records are only ever appended, one JSON object per line,
each carrying `prev`: the sha256 of the previous raw line ("genesis" for the first), so `verify`
detects edits made outside this script.

$HOLLER_EXPERIMENT_MAX_DAYS (optional): the decision date may be at most this many days after the
start date (for example 30 when the metric source keeps only 30 days).

Exit codes: 0 ok, 1 refused (validation or integrity failure), 2 usage error.
Python 3 standard library only. Run with `python3 -I`.
"""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import sys

LABELS = ("measured", "user-provided", "calculated", "estimated", "proxy")
COMPARATORS = (">=", ">", "<=", "<")
DEFAULT_REGISTRY = os.path.join(".agents", "experiments.jsonl")
ID_RE = re.compile(r"^exp-\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]{1,60}$")


class Refuse(Exception):
    pass


def registry_path(arg):
    return arg or os.environ.get("HOLLER_EXPERIMENTS") or DEFAULT_REGISTRY


def parse_date(value, field):
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError:
        raise Refuse(f"{field}: not an ISO date (YYYY-MM-DD): {value!r}")


def today():
    override = os.environ.get("HOLLER_EXPERIMENTS_TODAY")  # tests only
    return dt.date.fromisoformat(override) if override else dt.date.today()


def read_lines(path):
    if not os.path.exists(path):
        raise Refuse(f"registry not found: {path}. Create it with `experiments.py init` once the user agrees; add and readout do not create registries.")
    with open(path, "rb") as f:
        data = f.read()
    if data and not data.endswith(b"\n"):
        raise Refuse(f"{path}: last line has no newline; the file was edited outside this script. Run verify.")
    return [l for l in data.split(b"\n") if l]


def load(path):
    out = []
    for i, raw in enumerate(read_lines(path), 1):
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError as e:
            raise Refuse(f"{path}:{i}: not JSON ({e})")
        out.append((raw, rec))
    return out


def chain_ok(records):
    prev = "genesis"
    problems = []
    for i, (raw, rec) in enumerate(records, 1):
        if rec.get("prev") != prev:
            problems.append(f"line {i}: prev is {rec.get('prev')!r}, expected {prev!r} (edited, reordered or deleted lines)")
        prev = hashlib.sha256(raw).hexdigest()
    return problems


def append(path, rec):
    with open(path, "ab") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            records = load(path)
            problems = chain_ok(records)
            if problems:
                raise Refuse("registry integrity check failed; not appending:\n  " + "\n  ".join(problems))
            rec["prev"] = hashlib.sha256(records[-1][0]).hexdigest() if records else "genesis"
            line = json.dumps(rec, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode() + b"\n"
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    return rec


def require_intact(path, records):
    problems = chain_ok(records)
    if problems:
        raise Refuse(f"{path}: integrity check failed; nothing appended. Report this to the human, do not repair the file:\n  " + "\n  ".join(problems))
    return records


def cards(records):
    return {r["id"]: r for _, r in records if r.get("type") == "card"}


def readouts(records, card_id):
    return [r for _, r in records if r.get("type") == "readout" and r.get("card") == card_id]


def superseded_by(records, card_id):
    return [r["id"] for _, r in records if r.get("type") == "card" and r.get("supersedes") == card_id]


def need(card, *keys):
    cur = card
    path = []
    for k in keys:
        path.append(k)
        if not isinstance(cur, dict) or k not in cur or cur[k] in (None, ""):
            raise Refuse(f"missing field: {'.'.join(path)}")
        cur = cur[k]
    if isinstance(cur, str) and "[NEED" in cur:
        raise Refuse(f"{'.'.join(path)} is still a [NEED: ...] marker; a card cannot be registered without it")
    return cur


def number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Refuse(f"{field}: must be a number, got {value!r}")
    return value


def validate_card(card, existing):
    if card.get("type", "card") != "card":
        raise Refuse("type must be 'card'")
    cid = need(card, "id")
    if not ID_RE.match(cid):
        raise Refuse(f"id must look like exp-YYYY-MM-DD-<slug> (lowercase, dashes): {cid!r}")
    if cid in existing:
        raise Refuse(f"id already registered: {cid}. A changed card is a new id with supersedes: {cid}")
    for k in ("title", "change", "hypothesis", "prediction"):
        need(card, k)
    need(card, "metric", "name")
    need(card, "metric", "source")
    window = card["metric"].get("window_days")
    if window is not None and (not isinstance(window, int) or window <= 0):
        raise Refuse("metric.window_days must be a positive integer when set")

    baseline_value = number(need(card, "baseline", "value"), "baseline.value")
    baseline_date = parse_date(need(card, "baseline", "date"), "baseline.date")
    if need(card, "baseline", "label") not in LABELS:
        raise Refuse(f"baseline.label must be one of {', '.join(LABELS)}")
    need(card, "baseline", "source")

    target_value = number(need(card, "target", "value"), "target.value")
    comparator = need(card, "target", "comparator")
    if comparator not in COMPARATORS:
        raise Refuse(f"target.comparator must be one of {' '.join(COMPARATORS)}")
    if target_value == baseline_value:
        raise Refuse("target.value equals baseline.value; the card predicts no change")

    start = parse_date(need(card, "start_date"), "start_date")
    decision = parse_date(need(card, "decision_date"), "decision_date")
    created = today()
    if baseline_date > created:
        raise Refuse(f"baseline.date {baseline_date} is in the future")
    if start < created:
        raise Refuse(f"start_date {start} is before today ({created}): pre-register before the change ships, or set the real ship date")
    if decision <= start:
        raise Refuse("decision_date must be after start_date")
    limits = []
    if window is not None:
        limits.append((window, f"metric.window_days ({window})"))
    env_max = os.environ.get("HOLLER_EXPERIMENT_MAX_DAYS")
    if env_max:
        limits.append((int(env_max), f"HOLLER_EXPERIMENT_MAX_DAYS ({env_max})"))
    for days, why in limits:
        if (decision - start).days > days:
            raise Refuse(f"decision_date is {(decision - start).days} days after start_date; the limit is {why}. The metric source will not hold the data by then.")

    sample = need(card, "min_sample", "value")
    if isinstance(sample, bool) or not isinstance(sample, int) or sample <= 0:
        raise Refuse("min_sample.value must be a positive integer")
    need(card, "min_sample", "unit")

    need(card, "kill", "criterion")
    kill = card["kill"]
    if "threshold" in kill:
        number(kill["threshold"], "kill.threshold")
        if kill.get("comparator") not in COMPARATORS:
            raise Refuse(f"kill.comparator must be one of {' '.join(COMPARATORS)} when kill.threshold is set")

    sup = card.get("supersedes")
    if sup is not None:
        if sup not in existing:
            raise Refuse(f"supersedes {sup!r}: no such card")
        need(card, "supersede_reason")
    return created


def cmd_add(args):
    path = registry_path(args.registry)
    raw = sys.stdin.read() if args.card == "-" else open(args.card, encoding="utf-8").read()
    try:
        card = json.loads(raw)
    except json.JSONDecodeError as e:
        raise Refuse(f"card is not JSON: {e}")
    if not isinstance(card, dict):
        raise Refuse("card must be a JSON object")
    if not args.approved_by.strip():
        raise Refuse("--approved-by must name the human who approved this card in their own message")
    existing = cards(require_intact(path, load(path)))
    created = validate_card(card, existing)
    card = dict(card)
    card.update({"type": "card", "created": created.isoformat(), "approved_by": args.approved_by.strip()})
    card.pop("prev", None)
    rec = append(path, card)
    print(f"registered {rec['id']} in {path}")
    print(f"  metric: {rec['metric']['name']} ({rec['metric']['source']})")
    print(f"  baseline {rec['baseline']['value']} on {rec['baseline']['date']} [{rec['baseline']['label']}]; target {rec['target']['comparator']} {rec['target']['value']}")
    print(f"  decision date {rec['decision_date']}; minimum sample {rec['min_sample']['value']} {rec['min_sample']['unit']}")
    if rec.get("supersedes"):
        print(f"  supersedes {rec['supersedes']}: {rec['supersede_reason']}")


def meets(value, comparator, threshold):
    return {">=": value >= threshold, ">": value > threshold, "<=": value <= threshold, "<": value < threshold}[comparator]


def cmd_readout(args):
    path = registry_path(args.registry)
    records = require_intact(path, load(path))
    allcards = cards(records)
    card = allcards.get(args.card)
    if card is None:
        raise Refuse(f"no such card: {args.card}")
    if args.label not in LABELS:
        raise Refuse(f"--label must be one of {', '.join(LABELS)}")
    when = parse_date(args.date, "--date")
    if when > today():
        raise Refuse(f"--date {when} is in the future")
    if args.sample < 0:
        raise Refuse("--sample must be >= 0")
    decision = parse_date(card["decision_date"], "decision_date")
    target = card["target"]
    met = meets(args.actual, target["comparator"], target["value"])
    gap = args.actual - target["value"]
    notes = []
    kill_eval = None
    kill = card.get("kill", {})
    if "threshold" in kill:
        kill_eval = meets(args.actual, kill["comparator"], kill["threshold"])
    elif args.kill_triggered:
        kill_eval = args.kill_triggered == "yes"
    if kill_eval is None:
        notes.append("kill criterion is prose: state with evidence whether it was triggered (--kill-triggered yes|no)")

    later = superseded_by(records, card["id"])
    if when < decision:
        verdict = "early-look"
        notes.append(f"before the decision date ({decision}): early numbers are noise, not a result")
    elif args.sample < card["min_sample"]["value"]:
        verdict = "inconclusive"
        notes.append(f"sample {args.sample} is below the pre-registered minimum {card['min_sample']['value']} {card['min_sample']['unit']}")
    elif kill_eval:
        verdict = "kill"
    elif met:
        verdict = "target-met"
    else:
        verdict = "target-missed"
    if later:
        notes.append(f"this card was superseded by {', '.join(later)}; judge against the card that was registered before the result, and say so")
    if args.label != "measured":
        notes.append(f"actual is labelled {args.label}, not measured: report it as such")

    rec = {
        "type": "readout", "card": card["id"], "date": when.isoformat(),
        "actual": {"value": args.actual, "source": args.source, "label": args.label},
        "sample": args.sample, "target": target, "met_target": met, "gap_to_target": gap,
        "kill_triggered": kill_eval, "verdict": verdict, "notes": notes,
        "recorded": today().isoformat(),
    }
    if args.notes:
        rec["analyst_notes"] = args.notes
    append(path, rec)
    word = "MET" if met else "MISSED"
    print(f"readout {card['id']}: verdict {verdict}")
    print(f"  target {target['comparator']} {target['value']}; actual {args.actual} [{args.label}, {args.source}, {when}] -> {word} (gap {gap:+g})")
    print(f"  baseline {card['baseline']['value']} on {card['baseline']['date']}; sample {args.sample} / minimum {card['min_sample']['value']} {card['min_sample']['unit']}")
    for n in notes:
        print(f"  note: {n}")


def cmd_list(args):
    path = registry_path(args.registry)
    records = load(path)
    due = parse_date(args.due_by, "--due-by") if args.due_by else None
    for cid, card in sorted(cards(records).items(), key=lambda kv: kv[1]["decision_date"]):
        ro = readouts(records, cid)
        final = [r for r in ro if r["verdict"] != "early-look"]
        later = superseded_by(records, cid)
        state = "superseded by " + ",".join(later) if later else (final[-1]["verdict"] if final else "open")
        if args.open and (final or later):
            continue
        if due and parse_date(card["decision_date"], "decision_date") > due:
            continue
        print(f"{card['decision_date']}  {cid}  [{state}]  {card['metric']['name']} {card['target']['comparator']} {card['target']['value']}")


def cmd_show(args):
    records = load(registry_path(args.registry))
    card = cards(records).get(args.id)
    if card is None:
        raise Refuse(f"no such card: {args.id}")
    print(json.dumps(card, indent=2, sort_keys=True, ensure_ascii=False))
    for r in readouts(records, args.id):
        print(json.dumps(r, indent=2, sort_keys=True, ensure_ascii=False))


def cmd_verify(args):
    path = registry_path(args.registry)
    records = load(path)
    problems = chain_ok(records)
    ids = set()
    for i, (_, r) in enumerate(records, 1):
        t = r.get("type")
        if t == "card":
            if r.get("id") in ids:
                problems.append(f"line {i}: duplicate id {r.get('id')}")
            ids.add(r.get("id"))
        elif t == "readout":
            if r.get("card") not in ids:
                problems.append(f"line {i}: readout for unknown or later card {r.get('card')}")
        else:
            problems.append(f"line {i}: unknown type {t!r}")
    if problems:
        raise Refuse("registry problems:\n  " + "\n  ".join(problems))
    print(f"ok: {path}, {len(records)} records, chain intact")


TEMPLATE = {
    "id": "exp-YYYY-MM-DD-short-slug",
    "title": "One line: what is being tested",
    "change": "What ships, where, and to whom",
    "hypothesis": "Because <evidence>, <change> will move <metric>",
    "prediction": "The outcome this card predicts, e.g. metric reaches target by the decision date",
    "metric": {"name": "e.g. signups per week", "source": "authoritative system and query or report name", "window_days": None},
    "baseline": {"value": 0, "date": "YYYY-MM-DD", "label": "measured", "source": "where the baseline was read"},
    "target": {"comparator": ">=", "value": 0},
    "start_date": "YYYY-MM-DD",
    "decision_date": "YYYY-MM-DD",
    "min_sample": {"value": 0, "unit": "e.g. visitors"},
    "kill": {"criterion": "Condition that stops the change early", "comparator": "<=", "threshold": 0},
    "supersedes": None,
    "supersede_reason": None,
}


def cmd_init(args):
    path = registry_path(args.registry)
    if os.path.lexists(path):
        raise Refuse(f"{path} already exists; init never touches an existing registry")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    os.close(fd)
    print(f"created empty registry {path}")


def main(argv):
    p = argparse.ArgumentParser(prog="experiments.py", description="Append-only experiment registry.")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("--card", required=True); a.add_argument("--approved-by", required=True); a.add_argument("--registry")
    r = sub.add_parser("readout")
    r.add_argument("--card", required=True); r.add_argument("--actual", type=float, required=True)
    r.add_argument("--source", required=True); r.add_argument("--date", required=True)
    r.add_argument("--label", required=True); r.add_argument("--sample", type=int, required=True)
    r.add_argument("--kill-triggered", choices=("yes", "no")); r.add_argument("--notes"); r.add_argument("--registry")
    l = sub.add_parser("list"); l.add_argument("--open", action="store_true"); l.add_argument("--due-by"); l.add_argument("--registry")
    s = sub.add_parser("show"); s.add_argument("id"); s.add_argument("--registry")
    v = sub.add_parser("verify"); v.add_argument("--registry")
    sub.add_parser("template")
    i = sub.add_parser("init"); i.add_argument("--registry")
    try:
        args = p.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        if args.cmd == "template":
            print(json.dumps({k: v for k, v in TEMPLATE.items()}, indent=2))
        else:
            {"add": cmd_add, "readout": cmd_readout, "list": cmd_list, "show": cmd_show, "verify": cmd_verify, "init": cmd_init}[args.cmd](args)
    except Refuse as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
