# Provenance: growth-gate

Kit `growth-gate` 1.0.0, licence MIT. Written on 2026-10-23 and assembled on 2026-10-24 by 72o Labs,
adapting material from the upstream repositories below at the pinned commits. Contents keep their
original licences.

| Upstream | URL | Commit | Licence | Path |
| --- | --- | --- | --- | --- |
| marketingskills | https://github.com/coreyhaines31/marketingskills | `e85f3cbc2e4a79bf33b2a12e9bdd9087d414735b` | MIT | `skills/copywriting/references/ai-tells.md` |
| kai-cmo-harness | https://github.com/cgallic/kai-cmo-harness | `5f2dab2453069277d133ae1b19df22f6e173152f` | MIT | `scripts/quality_gates/` |

## Changes

- No patches. `skills/growth-gate` (`SKILL.md`, `references/checklist.md`, `scripts/growth_gate.py`) is new
  work by 72o Labs: rules and thresholds were re-expressed from the sources below, and no upstream file was
  copied and edited, so there is no meaningful line diff.
- `LICENSE-marketingskills` is byte-identical to marketingskills `LICENSE`, and `LICENSE-kai-quality-gates`
  to kai-cmo-harness `scripts/quality_gates/LICENSE`, at the pinned commits.
- NOTICE.md states the sources in prose.

## growth-gate

| Field | Value |
| --- | --- |
| Source | 72o Labs, written 2026-10-23 |
| Licence | MIT, with adapted MIT material: carries `LICENSE-marketingskills` (MIT, © 2025 Corey Haines) and `LICENSE-kai-quality-gates` (MIT, © 2026 Connor Gallic), verbatim |
| Derived from | coreyhaines31/marketingskills `skills/copywriting/references/ai-tells.md` @ `e85f3cbc2e4a79bf33b2a12e9bdd9087d414735b`: AI-tell pattern names and the ban/cap split, re-expressed as regexes |
| Derived from | cgallic/kai-cmo-harness `scripts/quality_gates/banned_word_check.py`, `audit_provenance_lint.py`, `four_us_score.py` @ `5f2dab2453069277d133ae1b19df22f6e173152f` (the MIT directory of a dual-licensed repo): word tiers, "risky number without a nearby source marker", Four U's rubric and its 12/16, none-below-2 thresholds. No kai code copied; nothing from kai's Elastic-licensed directories used |
| Licence note | Ship both licence files and the SKILL.md Credits section |

### What it runs

| File | Executes | Network | Writes |
| --- | --- | --- | --- |
| `scripts/growth_gate.py` | Nothing (stdlib regexes) | None | None. Reads the files and directories it is given |

Not adapted from kai: the Gemini call (`score_content`, needs `GEMINI_API_KEY` and `google-genai`) and the gate logger (`gate_logger.py` appends JSONL to `$KAI_GATE_LOG_DIR` or a default path). The Four U's mode here is offline only: `--four-us-prompt` prints the rubric, `--four-us-scores` checks scores a reviewer gives.

### Tested (2026-10-23)

On staging fixtures: a clean draft passes (exit 0); a bad draft trips every planted pattern: 12 failing findings across 8 checks plus the cap warning (exit 1); version numbers, ISO dates and step numbers are not flagged; a waiver on `ai-overclaim` is reported as waived while a waiver on `send-without-approval` is refused; `--reviewer-session` equal to `author_session` fails; no paths and a missing path exit 2; malformed Four U's scores exit 2. A copy of the first 120 lines of Holler's README (with `Status: DRAFT` added) produced two findings: a "No launcher, no cloud, no new" negation list and the unsourced "60 seconds" heading.

The predictions in the checks table are hypotheses from the credited sources. None has been measured on Holler's copy; register an experiment card before relying on one.
