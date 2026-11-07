# Provenance: gstack

Kit `gstack` 1.0.0, licence MIT. Assembled on 2026-10-24 by 72o Labs from the upstream repositories
below at the pinned commits, reviewed on 2026-10-23 and 2026-10-24. Contents keep their original licences.

| Upstream | URL | Commit | Licence | Path |
| --- | --- | --- | --- | --- |
| gstack | https://github.com/garrytan/gstack | `b04cc35832183a89ed71eed628de15a6f315a1a8` | MIT | `careful` |
| impeccable (via gstack) | https://github.com/pbakaus/impeccable | `see gstack NOTICE.md at b04cc35` | Apache-2.0 | `design-consultation parts` |

## Changes

- `patches/upstream/<item>.patch`: diff from the pristine upstream files at the pinned commit to the files in
  this kit. One patch per item: `office-hours.patch`, `careful.patch`.
- `skills/design-system-doc` and `skills/design-variants` are hand extractions with no meaningful line diff;
  they are described below.
- `LICENSE` is byte-identical to gstack's `LICENSE`, and `LICENSE-Apache-2.0.txt` to gstack's
  `licenses/Apache-2.0.txt`, at the pinned commit.
- NOTICE.md states every change in prose.

## office-hours

| Field | Value |
| --- | --- |
| Source | https://github.com/garrytan/gstack (path `openclaw/skills/gstack-openclaw-office-hours`, plus root `LICENSE`) |
| Commit | `b04cc35832183a89ed71eed628de15a6f315a1a8` (committed 2026-10-23T05:47:18Z; upstream HEAD on 2026-10-23 was `6f7488a70f23`) |
| Licence | MIT (`LICENSE`, © 2026 Garry Tan). gstack's `NOTICE.md` (Apache-2.0 impeccable and DESIGN.md material) covers `lib/`, `scripts/resolvers/design.ts` and `design-consultation/`; none of that is in this item |
| Fetched | 2026-10-23, fresh clone of the commit above into an empty directory; SHA re-verified |
| Copied | `SKILL.md` from a clone at the commit above, then `patches/upstream/office-hours.patch` |
| Licence note | MIT; no impeccable-derived or other third-party text inside |

### Reviewed (2026-10-23)

Files: `LICENSE`, `SKILL.md`.

Prose only: no scripts, no hooks, no network calls. Reads the workspace and `git log`; writes one design doc in the repository.

Flagged in vendored prose (kept): pushback examples keep the founder's quoted "20% year over year" (a BAD-example quote, not a claim).

### Changes

`patches/upstream/office-hours.patch`: 9 lines added, 15 removed. Modified by 72o Labs.

- Frontmatter `name`: `gstack-openclaw-office-hours` becomes `office-hours`.
- The "YC Office Hours" title becomes "Office Hours", and the "You are a **YC office hours partner**" persona sentence is dropped from the opening paragraph (upstream `SKILL.md:6-8`); a "Modified by 72o Labs" comment is added.
- "### Garry's Note" deleted (upstream `SKILL.md:358-364`): the three YC pitch variants with `ycombinator.com/apply`. Phase 4.5 now feeds the Signal Reflection instead of "the closing message".
- Design doc save path: "save it to memory" and "Save the design doc to `memory/`" (upstream `SKILL.md:282,340`) become `docs/office-hours/YYYY-MM-DD-<slug>.md` in the current repository, with "Write nothing outside the repository."
- "There are 10,000 AI developer tools right now" (upstream `SKILL.md:94`, no source) becomes "There are many AI developer tools right now" so the agent does not repeat an invented count.

### Excluded

| Excluded | Reason |
| --- | --- |
| Everything outside `openclaw/skills/gstack-openclaw-office-hours/` | gstack is a runtime with global state, hooks and update checks; only this file is used. The full `office-hours/` skill (with `open https://ycombinator.com/apply?ref=gstack` in `office-hours/sections/design-and-handoff.md:419`) is not included |

## design-system-doc

| Field | Value |
| --- | --- |
| Source | https://github.com/garrytan/gstack: `design-consultation/SKILL.md`, `design-consultation/sections/proposal-and-preview.md` (committed rendered files, not the `.tmpl`) |
| Commit | `b04cc35832183a89ed71eed628de15a6f315a1a8` (v1.91.182.0, 2026-10-23). Upstream HEAD on 2026-10-23 was `6f7488a`; `git diff --stat b04cc35 6f7488a` over every file used here is empty |
| Licence | MIT, © 2026 Garry Tan (`LICENSE`). The font-selection procedure and the three-looks calibration are impeccable-derived (Apache-2.0, © Paul Bakaus) per gstack `NOTICE.md`: `LICENSE-Apache-2.0.txt` and `NOTICE.md` carried |
| Licence note | Ships with `LICENSE`, `LICENSE-Apache-2.0.txt` and `NOTICE.md` |
| Fetched | 2026-10-23, fresh `git clone` into an empty directory, checkout of the commit above |
| Copied | Hand extraction into a new `SKILL.md`, modified by 72o Labs. No patch: the 820-line upstream `SKILL.md` and its section file became a 179-line rewrite, so a line diff would not be readable |

Upstream sha256 at extraction:

| File | sha256 |
| --- | --- |
| `design-consultation/SKILL.md` | `3f188e448b02dd0824c62a6ab04508d3b3e3a69cc6c4a6b4b878f347005365e5` |
| `design-consultation/sections/proposal-and-preview.md` | `b946f62fd33594c0b91c49fcdde8ce1a86b8d047d15451a370491493e7ca21b1` |
| `NOTICE.md` | `879fc62ddab70035c6f697e1bc8afaaf0a380e8b3e4ffe256ca403c28d909f7c` |

### Kept

Phase 0 pre-checks (update / start fresh / cancel), product-context question, the memorable-thing question, research rules (read-only, sanitized queries, untrusted results, three-layer synthesis, eureka), the design-knowledge dials, the font procedure and offline fallback, the three-looks calibration, the anti-convergence directive, the SAFE/RISK proposal format, Coherence Validation and the coherence rules, drill-downs, the HTML preview requirements, confirm-before-write, the DESIGN.md template with its Decisions Log.

### Removed

- The gstack preamble (session, telemetry, learnings, artifacts sync, plan-status footer, voice and writing-style sections, AskUserQuestion tooling): runtime of another tool.
- Every `~/.claude/skills/gstack/bin/*` call: `gstack-design-md.ts`, `gstack-slug`, `gstack-paths`, `gstack-config`, `gstack-learnings-*`, `gstack-review-log`, `gstack-taste-update`, egress lib, Aside browser scripts.
- `$D` and Path A AI mockups (the OpenAI design binary); image mockups go through an imagegen skill instead.
- Outside voices (`codex exec` and a native subagent as co-proposers): review is left to a separate reviewer, which critiques rather than co-proposes.
- The 40-line AI-slop list: it is left to the reviewer (tells are applied at critique, not generation).
- The overused, banned and freely-available font lists (tells, likewise).
- Every `{{...}}` placeholder (none survive in the committed rendered files; the `.tmpl` files were not used).

### Changed

- The preview is written into the project at `design/explorations/<date>-design-system/` instead of `/tmp`.
- Writing agent instruction lines (gstack appends to `CLAUDE.md`) requires approval of the exact text.
- The frontmatter `description` was cut to about 350 characters (2026-10-24): trigger phrases kept, cross-references to skills outside the kit and body-level style rules dropped from the description.
- A "Modified by 72o Labs" comment at the top states the source, what was cut and the impeccable derivation.

### Review (2026-10-23)

Prose only. No scripts, no hooks, no network calls. The skill tells the agent to write `DESIGN.md`, a preview HTML under `design/explorations/`, and, with approval, a line in `CLAUDE.md`/`AGENTS.md`; all inside the repository and gated on approval. Research uses whatever web search the harness provides, read-only.

## design-variants

| Field | Value |
| --- | --- |
| Source | https://github.com/garrytan/gstack: `design-shotgun/SKILL.md` Step 1 (context dimensions), Step 3a (concepts, anti-convergence directive, swap-headline test), Step 3b (confirm before spending), Step 5 (feedback confirmation), Important Rules |
| Commit | `b04cc35832183a89ed71eed628de15a6f315a1a8`; unchanged at upstream HEAD `6f7488a` |
| Licence | MIT, © 2026 Garry Tan (`LICENSE`, `NOTICE.md`) |
| Licence note | Ships with `LICENSE` and `NOTICE.md` |
| Fetched | 2026-10-23, fresh clone at the commit above |
| Copied | Hand extraction into a new `SKILL.md`, modified by 72o Labs. No patch: the 904-line upstream `SKILL.md` became an 88-line rewrite, so a line diff would not be readable |

| File | sha256 |
| --- | --- |
| `design-shotgun/SKILL.md` | `9e4d57b0ea537d52f27818aabe87b5e919efa95a4ddbf41b4e0c4068c4501ae2` |
| `design-shotgun/sections/doctrine.md` | `db00be4d927e48ebeff614f761a8d118b294c527fab4596bf48b54a7296503fd` (read, not used) |

### Removed

Preamble, session detection (`approved.json`), taste-profile scripts (`gstack-taste-update`, decay maths), `$D variants|generate|iterate|compare|serve`, the comparison-board HTTP server, `gstack-design-claim`, round accounting of paid images, Aside screenshots, `$GSTACK_STATE_ROOT` paths.

### Added by 72o Labs (not in gstack)

- Rendering into `design/explorations/<date>-<slug>/` (HTML variants with screenshots, or image mockups through imagegen), an `index.md` per folder.
- Seed strings per concept and "brief ambitiously" (after Chimala's process).
- No ranking or scoring of one's own variants; reasons recorded with taste-log (gstack records picks without reasons).
- Review comes from an independent reviewer (the reviewer agent, asked with holler-review-request), approval from the human.
- The frontmatter `description` was cut to about 350 characters (2026-10-24): trigger phrases kept, cross-references to skills outside the kit and body-level style rules dropped from the description.
- A "Modified by 72o Labs" comment at the top states the source and what was removed and added.

### Review (2026-10-23)

Prose only; no scripts, hooks or network. Writes HTML, PNG screenshots and `index.md` under `design/explorations/`. Image spending is gated (more than 4 images needs a yes).

## careful

| Field | Value |
| --- | --- |
| Source | https://github.com/garrytan/gstack (path `careful/`: `SKILL.md.tmpl`, `bin/check-careful.sh`, `bin/hook-extract.sh`; root `LICENSE`) |
| Commit | `b04cc35832183a89ed71eed628de15a6f315a1a8` (the gstack pin the design items use) |
| Licence | MIT (`LICENSE`); `NOTICE.md` records the adaptation |
| Fetched | 2026-10-24, clone at the commit above, HEAD verified |
| Copied | The three files from a clone at the commit above (`SKILL.md.tmpl` lands as `SPEC.md`), then `patches/upstream/careful.patch` |
| Licence note | MIT; `LICENSE` and `NOTICE.md` ship with it |

### Reviewed (2026-10-24)

- `check-careful.sh` (bash 3.2 compatible): reads the hook JSON on stdin, extracts `tool_name` and `tool_input.command` with `python3 -c` (stdlib `json`), and prints a `hookSpecificOutput` decision: `ask` for the destructive families (recursive rm, SQL DROP/TRUNCATE, force-push, `git reset --hard`, `git checkout .`/`restore .`, `kubectl delete`, `docker rm -f`/`system prune`, Windows shell forms), `deny` for two simple shapes (recursive rm of `/`, `~`, `$HOME`; force-push to the default branch, resolved with read-only `git symbolic-ref`/`show-ref`/`branch --show-current`). Unparseable input asks (fails closed). No network.
- `hook-extract.sh`: sourced helpers (JSON field extraction through `python3` or `node`, JSON string encoding, the decision envelope).
- Upstream writes: `gstack_hook_log_fire` appended analytics to the gstack state root; the project-pattern block read `~/.gstack/careful-patterns.txt` and ran `../../bin/gstack-slug`. Both removed, so the adapted hook writes nothing and runs no gstack binary.

### Changes (`patches/upstream/careful.patch`)

Modified by 72o Labs. 18 lines added, 191 removed.

- `check-careful.sh`: analytics calls and the "Additive project patterns" block removed; HIGH-tier messages reworded (no `/careful` session to end); header notice added.
- `hook-extract.sh`: freeze-only path normalisation, the state-root twin and the analytics writer removed; header notice added.
- `SPEC.md` (from `SKILL.md.tmpl`): skill frontmatter (hooks with `$HOME/.claude/skills/gstack/...` paths), the analytics bash block and "Project patterns" removed; title, intro and HIGH-tier text describe an always-on guard; header notice added.
- Added by 72o Labs, no upstream counterpart: `tests/` (`cases.jsonl`, 22 cases, and `run_cases.py`, which runs them in a scratch git repo with an `origin/main`). The hook registration (PreToolUse, matcher `Bash`, `/bin/bash check-careful.sh`, timeout 10) is declared in `kit.json`.
