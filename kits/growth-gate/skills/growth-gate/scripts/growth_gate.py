#!/usr/bin/env python3
"""growth-gate: deterministic pre-publish check for growth and content drafts.

usage:
  growth_gate.py [--json] [--reviewer-session ID] <file-or-dir>...
  growth_gate.py --four-us-prompt <file>
  growth_gate.py --four-us-scores '{"unique":3,"useful":3,"ultra_specific":2,"urgent":2}' <file>

Scans .md .markdown .mdx .txt .html .htm .eml files (directories recursively, skipping .git).
Every check names the outcome it claims to predict. Those predictions are hypotheses taken from
the sources credited below; none has been measured on this product.

Evidence annotation the metric checks accept, on the same line or the next line:
  <!-- evidence: <source> | <YYYY-MM-DD> | <label> -->      (invisible when rendered)
  [src: <source>; <YYYY-MM-DD>; <label>]
  a footnote [^n] whose definition holds source, date and label
labels: measured, user-provided, calculated, estimated, proxy.

Waiver for a false positive, on the same line (shown in the report, decided by the reviewer):
  <!-- gate-waive: <check-id> | <reason> -->
Not waivable: need-marker, draft-status-missing, send-without-approval, approval-claim-without-record,
same-session.

Exit codes: 0 no failing findings, 1 failing findings, 2 usage error.
Python 3 standard library only; run with python3 -I. Reads files; writes nothing; no network.

Credits: AI-tell patterns adapted from coreyhaines31/marketingskills skills/copywriting/references/
ai-tells.md (MIT, (c) 2025 Corey Haines) at e85f3cbc. Word tiers, the number-near-a-source idea and
the Four U's rubric and thresholds adapted from cgallic/kai-cmo-harness scripts/quality_gates/
banned_word_check.py, audit_provenance_lint.py and four_us_score.py (MIT, (c) 2026 Connor Gallic)
at 5f2dab24. See ../../../LICENSE-marketingskills and ../../../LICENSE-kai-quality-gates.
"""
import argparse
import json
import os
import re
import sys

EXTS = {".md", ".markdown", ".mdx", ".txt", ".html", ".htm", ".eml"}
LABELS = ("measured", "user-provided", "calculated", "estimated", "proxy")

PREDICTS = {
    "need-marker": "A placeholder or an unsupported claim reaches the public.",
    "metric-no-source": "A number nobody can trace when a reader, reviewer or the human asks where it came from.",
    "metric-incomplete-evidence": "A sourced number that cannot be re-checked or weighed (no date, or no measured/user-provided/calculated/estimated/proxy label).",
    "ai-overclaim": "A claim about the product or its AI that a user or reviewer can falsify, which costs trust in every other claim on the page.",
    "draft-status-missing": "A file is mistaken for approved copy and shipped without the human's sign-off.",
    "send-without-approval": "An instruction to send, post or publish is carried out by a later session or another agent without the human approving it.",
    "approval-claim-without-record": "A self-approved artifact: text says it is approved or ready with no record of who approved it and when.",
    "ai-tell": "Readers judge the copy machine-written and start doubting its claims (marketingskills ai-tells.md).",
    "ai-tell-cap": "Same as ai-tell, for devices that are fine once and a tell when stacked (warning only).",
    "same-session": "The author grades its own work and misses the errors it made.",
}
NOT_WAIVABLE = {"need-marker", "draft-status-missing", "send-without-approval", "approval-claim-without-record", "same-session"}

I = re.IGNORECASE

# --- metrics -------------------------------------------------------------------------------
METRIC_RE = re.compile(
    r"(?:[$€£]\s?\d[\d,.]*\s?(?:[kmb]|bn|million|billion)?\b"
    r"|\b\d[\d,.]*\s?%"
    r"|\b\d[\d,.]*\s?(?:x|×)(?=\W|$)"
    r"|\b\d[\d,.]*\+?\s?(?:k\s)?(?:users?|customers?|signups?|sign-ups?|subscribers?|followers?|teams?|companies|developers?|founders?|agents?|"
    r"downloads?|installs?|visitors?|views?|impressions?|clicks?|leads?|trials?|conversions?|reviews?|stars?|"
    r"hours?|hrs?|minutes?|mins?|seconds?|days?|weeks?|months?|decisions?|messages?|sessions?|requests?)\b"
    r"|\b(?:mrr|arr|revenue|churn|retention|conversion rate|ctr|cac|ltv|nps|activation)\b[^.\n]{0,30}?\d"
    r"|\b\d[\d,.]*\+?\s+(?:[a-z-]+\s+){0,2}[a-z-]+s\b)",
    I,
)
NOT_METRIC_RE = re.compile(
    r"^\s*(?:#+\s*)?\d+[.)]\s|\b(?:19|20)\d\d-\d\d-\d\d\b|\bv?\d+\.\d+\.\d+\b|\b(?:step|phase|section|q|day|week)\s?\d+\b|\b(?:19|20)\d\d\b(?!\s?%)", I)
SOURCE_RE = re.compile(r"<!--\s*evidence\s*:|\[src\s*:|\bsource\s*:|\[\^[\w-]+\]|https?://", I)
DATE_RE = re.compile(r"\b(?:19|20)\d\d-\d\d-\d\d\b")
LABEL_RE = re.compile(r"\b(?:measured|user-provided|calculated|estimated|proxy)\b", I)
FOOTNOTE_DEF_RE = re.compile(r"^\[\^([\w-]+)\]:\s*(.*)$")
FOOTNOTE_REF_RE = re.compile(r"\[\^([\w-]+)\](?!:)")

# --- overclaims ----------------------------------------------------------------------------
OVERCLAIM_RES = [re.compile(p, I) for p in (
    r"\bthe only\b", r"\bfirst[- ]ever\b", r"(?:^|\s)#1\b", r"\bnumber one\b", r"\bbest[- ]in[- ]class\b",
    r"\bworld[- ]class\b", r"\bindustry[- ]leading\b", r"\bunmatched\b", r"\bunparalleled\b", r"\bunbeatable\b",
    r"\bguarantee[sd]?\b", r"\b100\s?%\b", r"\bzero (?:risk|errors?|bugs?|downtime|effort)\b",
    r"\bnever (?:fails?|breaks?|misses|miss|loses?|forgets?)\b", r"\balways (?:works|right|accurate|correct)\b",
    r"\bfully autonomous\b", r"\bset (?:it )?and forget\b", r"\bno humans? (?:needed|required|in the loop)\b",
    r"\breplaces? (?:your|the|a) (?:team|engineers?|developers?|pm|designer|marketer)s?\b", r"\bhuman[- ]level\b",
    r"\bagi\b", r"\bthinks like (?:a|you)\b", r"\bunderstands (?:you|your|everything|exactly)\b",
    r"\b(?:never|no|zero) hallucinat\w*\b", r"\bperfect(?:ly)? (?:accurate|reliable|secure)\b",
    r"\bstudies show\b", r"\bresearch (?:shows|proves)\b", r"\bexperts agree\b", r"\bscientifically proven\b",
    r"\btrusted by (?:thousands|millions|hundreds|leading|top|industry)\b", r"\bjoin (?:thousands|millions|hundreds)\b",
    r"\bloved by (?:thousands|millions|developers|teams)\b",
)]

# --- send / publish / approval -------------------------------------------------------------
DRAFT_RE = re.compile(r"^\s*(?:status\s*:\s*\**\s*draft\b|\**\s*status\s*:?\s*\**\s*draft\b|>?\s*\**draft\b)", I)
SEND_RE = re.compile(
    r"\b(?:send|post|publish|tweet|announce|share|schedule|queue|email|launch|boost|dm|reply)\s+"
    r"(?:it|this|that|them|these|the (?:post|thread|tweet|email|newsletter|announcement|launch|update|draft|copy|video|clip|reply|changelog)s?"
    r"|to (?:the list|subscribers|users|everyone|all|our list|customers)|on (?:x|twitter|linkedin|bluesky|threads|reddit|hn|hacker news|product hunt)"
    r"|via buffer|through buffer|now|today|tomorrow|immediately|at \d)"
    r"|\bauto-?(?:post|publish|send|reply)\w*\b|\bshare ?now\b|\bgo(?:es)? live (?:now|today|tomorrow|on|at)\b|\bhit (?:send|publish|post)\b",
    I,
)
APPROVAL_WORDING_RE = re.compile(
    r"\b(?:after|once|if|when|until|pending|needs?|requires?|awaiting|for|subject to)\s+(?:the human'?s?\s+|human\s+|founder'?s?\s+)?(?:approval|approved|approves|sign-?off)\b"
    r"|\bhuman approves\b|\bapproval (?:required|needed|pending)\b|\bin buffer approvals\b|\bneeds approval\b", I)
APPROVAL_CLAIM_RE = re.compile(
    r"\b(?:is|was|been|got|now|already|fully|final)\s+approved\b|\bapproved (?:for|to) (?:publish|post|send|ship|launch)\w*\b"
    r"|\bready to (?:publish|post|send|ship|go live|launch)\b|\bcleared (?:to|for) (?:publish|post|send|ship|launch)\w*\b"
    r"|\bgood to go\b|\bsigned off\b", I)
APPROVED_BY_RE = re.compile(r"^\s*approved[_ -]by\s*:\s*\S.*\b(?:19|20)\d\d-\d\d-\d\d\b", I | re.M)

# --- AI tells (marketingskills ai-tells.md; kai banned_word_check) -------------------------
TELL_BAN = [(name, re.compile(p, I)) for name, p in (
    ("contrast reveal", r"\b(?:it'?s|this is|that'?s|this isn'?t|it isn'?t|isn'?t)\s+(?:not\s+)?(?:just\s+)?[^.;!?\n]{1,40}?[,;:—–]\s*(?:it'?s|this is|that'?s)\b"),
    ("contrast reveal", r"\bnot because\b[^.\n]{1,80}\.\s*because\b"),
    ("contrast reveal", r"\bnot just\b[^.\n]{1,50}?,?\s+but\b"),
    ("contrast reveal", r"\bless\s+\w+,\s*more\s+\w+\b"),
    ("contrast reveal", r"\bthe question isn'?t\b"),
    ("contrast reveal", r"\?\s*think again\b"),
    ("negation list", r"\bno\s+[^,.;\n]{1,30}[,.]\s*no\s+[^,.;\n]{1,30}[,.]\s*(?:no|just|zero)\b"),
    ("negation list", r"\bzero\s+\w+,\s*zero\s+\w+"),
    ("rhetorical question reveal", r"\b(?:the result|the catch|the best part|the kicker|the twist|the secret|the answer|why does (?:this|it) matter|the upshot)\?\s"),
    ("colon reveal", r"\b(?:the best part|here'?s the (?:secret|thing|kicker|truth|catch)|one word|the truth is|the secret)\s*:"),
    ("era opener", r"\bin today'?s (?:fast-paced|rapidly|ever-changing|digital|modern)\b|\bin an era of\b|\bever-evolving landscape\b"),
    ("false-choice opener", r"\bwhether you'?re an? [^.\n]{1,40} or an? \b"),
    ("throat-clearing", r"\bhere'?s the thing\b|\blet me be clear\b|\bhere'?s what nobody tells you\b|\blet'?s dive in\b|\bin this (?:guide|post|article),? we'?ll\b"),
    ("filler", r"\bit'?s (?:worth noting|important to note)\b|\bin conclusion\b|\bat the end of the day\b"),
    ("marketing phrase", r"\bsay goodbye to\b|\bsay hello to\b|\bunlock the power\b|\bunleash\b|\breimagined\b|\bredefined\b|\bto the next level\b|\btransform the way you\b|\bthe future of [^.\n]{1,30} is here\b|\bgame[- ]changer\b|\bthis changes everything\b|\beverything you need to\b|\ball-in-one\b"),
    ("weasel source", r"\bexperts agree\b|\bstudies show\b"),
    ("banned word", r"\b(?:delve|delves|delving|tapestry|testament to|realm|embark|beacon|multifaceted|paradigm|synergy|synergies|myriad|plethora|meticulous|meticulously|intricate|utilize|utilise|utilizing|supercharge|turbocharge|plays a crucial role)\b"),
    ("banned word", r"\bleverag(?:e|es|ing)\s+(?:the|your|our|this|these|ai|data)\b"),
)]
TELL_CAP_WORDS = re.compile(
    r"\b(?:seamless(?:ly)?|robust|streamline[sd]?|empower(?:s|ing)?|elevate[sd]?|unlock(?:s|ing)?|harness(?:es|ing)?|foster(?:s|ing)?|"
    r"enhance[sd]?|optimi[sz]e[sd]?|cutting[- ]edge|innovative|revolutionary|revolutioni[sz]e|transformative|holistic|comprehensive|pivotal|"
    r"crucial|vital|powerful|next[- ]level|world[- ]class|best[- ]in[- ]class|landscape|navigate|ecosystem|journey|"
    r"truly|genuinely|incredibly|deeply|fundamentally|significantly|simply|actually|literally|quietly|"
    r"thought leader(?:ship)?|paradigm shift|move the needle|low[- ]hanging fruit|circle back|deep dive|touch base|state[- ]of[- ]the[- ]art)\b", I)
EM_DASH = "—"

WAIVE_RE = re.compile(r"<!--\s*gate-waive\s*:\s*([\w-]+)\s*\|\s*([^>]+?)\s*-->", I)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def files_from(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            for d, dirs, fs in os.walk(p):
                dirs[:] = [x for x in dirs if x != ".git"]
                out += [os.path.join(d, f) for f in fs if os.path.splitext(f)[1].lower() in EXTS]
        elif os.path.isfile(p):
            out.append(p)
        else:
            raise FileNotFoundError(p)
    return sorted(set(out))


def front_matter(lines):
    meta = {}
    if lines and lines[0].strip() == "---":
        for j in range(1, min(len(lines), 60)):
            if lines[j].strip() == "---":
                break
            m = re.match(r"^\s*([\w-]+)\s*:\s*(.*)$", lines[j])
            if m:
                meta[m.group(1).lower()] = m.group(2).strip().strip("'\"")
    return meta


def scan(path, reviewer_session=None):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    lines = text.split("\n")
    findings = []
    meta = front_matter(lines)

    def add(line_no, check, severity, excerpt, detail=""):
        findings.append({"file": path, "line": line_no, "check": check, "severity": severity,
                         "excerpt": excerpt.strip()[:160], "detail": detail})

    footnotes = {}
    for ln in lines:
        m = FOOTNOTE_DEF_RE.match(ln.strip())
        if m:
            footnotes[m.group(1)] = m.group(2)

    # file-level: draft status and same-session review
    head = "\n".join(lines[:15])
    if not (meta.get("status", "").lower() == "draft" or any(DRAFT_RE.match(l) for l in lines[:15])):
        add(1, "draft-status-missing", "fail", head.split("\n")[0], "Add `Status: DRAFT` (or front matter `status: draft`) near the top until the human approves.")
    author = meta.get("author_session") or meta.get("author-session")
    if reviewer_session and author and author == reviewer_session:
        add(1, "same-session", "fail", f"author_session: {author}", "Run the gate from a different session than the one that wrote the draft.")
    approved_record = bool(APPROVED_BY_RE.search(text))

    in_fence = False
    para_caps = []
    para_start = 1
    em_dashes = 0
    for i, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if "[NEED" in raw:
            add(i, "need-marker", "fail", raw, "Resolve the [NEED: …] or keep the draft unpublished.")
        if in_fence:
            continue
        waivers = {m.group(1).lower(): m.group(2) for m in WAIVE_RE.finditer(raw)}
        visible = COMMENT_RE.sub("", raw)

        def hit(check, severity, detail=""):
            if check in waivers and check not in NOT_WAIVABLE:
                add(i, check, "waived", raw, f"waived: {waivers[check]}")
            else:
                add(i, check, severity, raw, detail)

        # metrics: number on the line must have source + date + label on this line or the next
        if FOOTNOTE_DEF_RE.match(stripped) or re.match(r"^\s*(?:status|approved[_ -]by|author[_-]session)\s*:", raw, I):
            pass
        else:
            masked = NOT_METRIC_RE.sub(" ", visible)
            if METRIC_RE.search(masked):
                nxt = lines[i].strip() if i < len(lines) else ""
                window = raw + ("\n" + nxt if re.match(r"(?:<!--\s*evidence|\[src\s*:|source\s*:|\[\^)", nxt, I) else "")
                for ref in FOOTNOTE_REF_RE.findall(window):
                    window += "\n" + footnotes.get(ref, "")
                if not SOURCE_RE.search(window):
                    hit("metric-no-source", "fail", "Add `<!-- evidence: <source> | <YYYY-MM-DD> | <label> -->` or remove the number.")
                elif not (DATE_RE.search(window) and LABEL_RE.search(window)):
                    hit("metric-incomplete-evidence", "fail", "The evidence needs a date and one label: measured, user-provided, calculated, estimated, proxy.")

        for rx in OVERCLAIM_RES:
            m = rx.search(visible)
            if m:
                hit("ai-overclaim", "fail", f"'{m.group(0).strip()}': state the checkable fact behind it, or cut it.")
                break

        if SEND_RE.search(visible) and not APPROVAL_WORDING_RE.search(raw):
            hit("send-without-approval", "fail", "Say the human approves first (e.g. 'after approval', 'queue as a Buffer draft for approval').")
        if APPROVAL_CLAIM_RE.search(visible) and not approved_record:
            hit("approval-claim-without-record", "fail", "Only the human approves. Add `approved_by: <name> <YYYY-MM-DD>` after they do, or remove the claim.")

        for name, rx in TELL_BAN:
            m = rx.search(visible)
            if m:
                hit("ai-tell", "fail", f"{name}: '{m.group(0).strip()[:60]}'")
                break

        em_dashes += visible.count(EM_DASH)
        if stripped == "":
            if len(para_caps) >= 2:
                add(para_start, "ai-tell-cap", "warn", ", ".join(para_caps), "Two or more capped words in one paragraph: rewrite with the fact they stand in for.")
            para_caps, para_start = [], i + 1
        else:
            para_caps += [m.group(0) for m in TELL_CAP_WORDS.finditer(visible)]
    if len(para_caps) >= 2:
        add(para_start, "ai-tell-cap", "warn", ", ".join(para_caps), "Two or more capped words in one paragraph: rewrite with the fact they stand in for.")
    if em_dashes > 2:
        add(0, "ai-tell-cap", "warn", f"{em_dashes} em dashes", "None in short copy (headlines, posts, subject lines); at most 1-2 per page in long copy.")
    return findings


FOUR_US = """Score the draft below on the Four U's, 1-4 each (adapted from kai-cmo-harness four_us_score.py, MIT).
Be harsh; 4 is rare.

UNIQUE: 4 a specific angle no competitor states; 3 fresh framing; 2 standard take; 1 generic.
USEFUL: 4 the reader can act on it now; 3 mostly actionable; 2 more inspiration than practice; 1 no next step.
ULTRA-SPECIFIC: 4 named examples, timeframes and numbers throughout; 3 some; 2 vague; 1 none.
  Evidence rule: a number counts only if it carries a source, date and label. An unsourced number lowers this score.
URGENT: 4 a real reason to act now; 3 timely; 2 any time; 1 no hook.

Return only JSON: {{"unique": n, "useful": n, "ultra_specific": n, "urgent": n, "notes": {{"unique": "...", "useful": "...", "ultra_specific": "...", "urgent": "..."}}}}

Draft:
---
{content}
---"""


def four_us_scores(raw):
    try:
        s = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(f"--four-us-scores is not JSON: {e}")
    dims = ("unique", "useful", "ultra_specific", "urgent")
    for d in dims:
        if not isinstance(s.get(d), int) or not 1 <= s[d] <= 4:
            raise SystemExit(f"--four-us-scores: {d} must be an integer 1-4")
    total = sum(s[d] for d in dims)
    passed = total >= 12 and all(s[d] >= 2 for d in dims)
    return {"scores": {d: s[d] for d in dims}, "total": total, "passed_kai_threshold": passed,
            "note": "Kai's thresholds (12/16, none below 2). Report-only: it does not change the exit code. "
                    "Predicts: generic copy readers skip (kai's claim; unvalidated here). Score from a different session than the author."}


def main(argv):
    ap = argparse.ArgumentParser(prog="growth_gate.py", description="Deterministic pre-publish gate for growth and content drafts.")
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--reviewer-session", help="this (reviewing) session's id; fails drafts whose front matter author_session matches")
    ap.add_argument("--four-us-prompt", action="store_true", help="print the Four U's rubric for one file and exit 0")
    ap.add_argument("--four-us-scores", help="JSON scores from a reviewer for one file; report-only")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    if not args.paths:
        print("growth_gate.py: give at least one file or directory", file=sys.stderr)
        return 2
    try:
        files = files_from(args.paths)
    except FileNotFoundError as e:
        print(f"growth_gate.py: no such file or directory: {e}", file=sys.stderr)
        return 2
    if not files:
        print("growth_gate.py: no .md/.txt/.html/.eml files found", file=sys.stderr)
        return 2
    if args.four_us_prompt or args.four_us_scores:
        if len(files) != 1:
            print("growth_gate.py: the Four U's options take exactly one file", file=sys.stderr)
            return 2
        content = open(files[0], encoding="utf-8", errors="replace").read()
        if args.four_us_prompt:
            print(FOUR_US.format(content=content[:8000]))
            return 0
        try:
            report = four_us_scores(args.four_us_scores)
        except SystemExit as e:
            print(f"growth_gate.py: {e}", file=sys.stderr)
            return 2
        print(json.dumps(report, indent=2))
        return 0

    findings = []
    for f in files:
        findings += scan(f, args.reviewer_session)
    failing = [x for x in findings if x["severity"] == "fail"]
    result = "fail" if failing else "pass"
    used = sorted({x["check"] for x in findings})
    if args.json:
        print(json.dumps({"result": result, "files": files, "findings": findings,
                          "predicts": {c: PREDICTS[c] for c in used}}, indent=2, ensure_ascii=False))
    else:
        for x in findings:
            print(f"{x['file']}:{x['line']}: {x['severity']} {x['check']}: {x['excerpt']}")
            if x["detail"]:
                print(f"    {x['detail']}")
        counts = {s: sum(1 for x in findings if x["severity"] == s) for s in ("fail", "warn", "waived")}
        print(f"\ngrowth-gate {result.upper()}: {len(files)} file(s), {counts['fail']} failing, {counts['warn']} warnings, {counts['waived']} waived")
        for c in used:
            print(f"  {c} predicts: {PREDICTS[c]}")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
