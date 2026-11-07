# Provenance: design-review-rules

Kit `design-review-rules` 1.0.0, licence MIT AND Apache-2.0. Assembled on 2026-10-24 by 72o Labs from the
upstream repositories below at the pinned commits. Contents keep their original licences.

| Upstream | URL | Commit | Licence | Path |
| --- | --- | --- | --- | --- |
| gstack | https://github.com/garrytan/gstack | `b04cc35832183a89ed71eed628de15a6f315a1a8` | MIT (gstack, refero_skill); Apache-2.0 (impeccable, OpenDesign, Anthropic) notices | `plan-design-review, design-review, review` |
| open-design | https://github.com/nexu-io/open-design | `e03d5c23f308c39f4de7c057568df66c29a84385` | Apache-2.0 | `craft/anti-ai-slop.md, craft/accessibility-baseline.md` |
| anthropics/skills | https://github.com/anthropics/skills | `dbd4588f9e1033efb41dad4bef2f7947c8993d44` | Apache-2.0 | `skills/frontend-design` |
| web-interface-guidelines | https://github.com/vercel-labs/web-interface-guidelines | `434b7f91364665f2f733b310ec54809bf8f37937` | MIT | `command.md` |
| impeccable (via gstack) | https://github.com/pbakaus/impeccable | `see gstack NOTICE.md at b04cc35` | Apache-2.0 | `surface classifier, rule ids` |
| refero_skill (via open-design) | https://github.com/referodesign/refero_skill | `2382e51` | MIT | `(adapted by OpenDesign)` |

All upstreams were cloned fresh on 2026-10-23 at the commits above.

## Changes

- `patches/upstream/a11y-floor.patch`: diff from the pristine web-interface-guidelines `command.md` at
  `434b7f9` to `skills/a11y-floor/SKILL.md`. The `a/` path is relative to the upstream repository root, the
  `b/` path to this kit folder. Applied with `patch -p1` in a checkout of that commit, it turns `command.md`
  into the kit file. The section from `## Accessibility baseline (OpenDesign craft)` on shows as added lines;
  it is OpenDesign `craft/accessibility-baseline.md` with the changes described below.
- `skills/design-review-passes/SKILL.md` and `skills/slop-tells/SKILL.md`: no patch. They are hand extractions,
  rewritten and merged from several files, so no meaningful line diff exists. Described below.
- `upstream/`: pristine copies of the two files `a11y-floor` is built from, unchanged:
  `upstream/web-interface-guidelines/command.md` and `upstream/open-design/craft/accessibility-baseline.md`.
- Licence files, unchanged copies: `LICENSE-gstack` (gstack `LICENSE`), `LICENSE-Apache-2.0.txt`
  (gstack `licenses/Apache-2.0.txt`), `LICENSE-open-design` (open-design `LICENSE`),
  `LICENSE-web-interface-guidelines` (web-interface-guidelines `LICENSE`), `LICENSE-anthropics-skills.txt`
  (anthropics/skills `skills/frontend-design/LICENSE.txt`), `LICENSE-refero_skill` (refero_skill `LICENSE`).
- NOTICE.md states every change in prose. Each skill also carries a "Modified by 72o Labs" comment.

## Upstream files used

| Upstream file | sha256 |
| --- | --- |
| gstack `plan-design-review/sections/review-sections.md` | `ea53eeed2e3e28d10f524a761f12da49dbb9c10a6261ca79ca56873495d0ea74` |
| gstack `design-review/SKILL.md` | `810b3a513449c7f17ed40947ab441fbd68d503b1a114ddcedc47fe6d0c112688` |
| gstack `review/design-checklist.md` | `b9205f88313cc64902c0b13e9685722ab8138d3dcc58916154f47274abda7d83` |
| open-design `craft/anti-ai-slop.md` | `d0f57d3064451663f9dca81af170fc754acc4b1e77280fd5cfb3a04afeef9a5c` |
| open-design `craft/accessibility-baseline.md` | `ef6c5f670d114ceb4c347681bcf3be8637e5d1186165a9c79ca265f316c72d11` |
| anthropics/skills `skills/frontend-design/SKILL.md` | `d91970639e9f5c37682ac7ab60094d35f1c7c1f38d731bd56396563aee10c1d3` |
| web-interface-guidelines `command.md` | `d246b026f4f29b5823a9cc857f9edf3d2507002e055e32040cadeaf3b38e0234` |

## design-review-passes

| Field | Value |
| --- | --- |
| Sources | gstack `plan-design-review/sections/review-sections.md` Passes 1-7, `design-review/SKILL.md` Phase 1 (first impression) and Phase 3 (trunk test, audit categories 1-10), at `b04cc35` |
| Licence | MIT, © 2026 Garry Tan (`LICENSE-gstack`). The surface classifier, the reflexes and the three-looks calibration are derived, through gstack, from impeccable, Apache-2.0 (`LICENSE-Apache-2.0.txt`) |
| Derivation | Hand extraction, rewritten. Frontmatter added. The AI-slop blacklist moved to `slop-tells` |

### Removed from the gstack sources

Plan editing and the per-issue AskUserQuestion loop ("STOP ... Do NOT batch"), FIX TO 10 rewrite instructions, mockup regeneration (`$D iterate`), TODOS and implementation-task outputs, review logs, the fix loop (Phase 7-11: locate source, fix, commit, re-test), Aside and `$B` browser scripts, the impeccable detector probe and scans, per-pass 0-10 ratings, outside voices.

## slop-tells

| Field | Value |
| --- | --- |
| Sources | gstack `review/design-checklist.md` §1 at `b04cc35` (its rule ids and names come from impeccable); OpenDesign `craft/anti-ai-slop.md` P0 ("seven cardinal sins") at `e03d5c2`; anthropics/skills `frontend-design` calibration clusters and typographic defaults at `dbd4588` |
| Licence | MIT (gstack); Apache-2.0 (impeccable via gstack, OpenDesign, Anthropic). OpenDesign's text is adapted from refero_skill, MIT, © 2026 Refero (`LICENSE-refero_skill`) |
| Derivation | Deduplicated union of the three sources, rewritten as visual checks: grep instructions and confidence tags removed, overlapping items merged. Frontmatter added |

## a11y-floor

| Field | Value |
| --- | --- |
| Sources | web-interface-guidelines `command.md` at `434b7f9` (2026-10-05; equals upstream HEAD on 2026-10-23); OpenDesign `craft/accessibility-baseline.md` at `e03d5c2` (2026-10-22, release 0.26.1 copy; equals upstream HEAD on 2026-10-23; `craft/` last changed in `f1a0b60`, 2026-08-18) |
| Licence | MIT, © 2025 Vercel Labs (`LICENSE-web-interface-guidelines`); Apache-2.0 (`LICENSE-open-design`). `craft/README.md` in open-design states the craft content is adapted from refero_skill, MIT, © 2026 Refero; `LICENSE-refero_skill` is refero_skill's `LICENSE` at `2382e51` (unchanged since its first commit `cc2d355`, 2026-02-04) |
| Derivation | The two upstream files in sequence, each with removals. The first part is recorded in `patches/upstream/a11y-floor.patch` |

Changes to `command.md`: the command frontmatter replaced by the skill's frontmatter; the title block (`$ARGUMENTS`) and the `## Rules` heading replaced by a new title, a reading note, a `## Web interface guidelines (Vercel Labs)` heading and the 72o Labs comment; `### Hydration Safety` (React/Next SSR) and `## Output Format` removed; "Prefer uncontrolled inputs" and "Deep-link ... via nuqs" removed (React-only). Other headings and rules unchanged.

Changes to `accessibility-baseline.md`: a `## Accessibility baseline (OpenDesign craft)` heading and the 72o Labs comment added above it; the title demoted to `##`; the sections "Prior art and scope" and "The legal floor changes by jurisdiction" removed; the remaining `##` section headings demoted to `###`. Rule text unchanged.

The reading note says rules that need source code or computed values go under Not checked unless a preview snapshot shows them.

## Review (2026-10-23)

Markdown only. No scripts, hooks or agents: nothing executes, no network, no writes. The web-interface-guidelines
`install.sh` was not vendored and not run. The OpenDesign P0 linter (`apps/daemon/src/lint-artifact.ts`) is not
vendored.
