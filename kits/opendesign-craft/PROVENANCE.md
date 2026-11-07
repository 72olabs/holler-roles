# Provenance: opendesign-craft

Kit `opendesign-craft` 1.0.0, licence Apache-2.0. Assembled on 2026-10-24 by 72o Labs from the upstream
repositories below at the pinned commits. Contents keep their original licences.

| Upstream | URL | Commit | Licence | Path |
| --- | --- | --- | --- | --- |
| open-design | https://github.com/nexu-io/open-design | `e03d5c23f308c39f4de7c057568df66c29a84385` | Apache-2.0; parts adapted from refero_skill, MIT | `craft` |
| refero_skill | https://github.com/referodesign/refero_skill | `2382e51` | MIT | `(adapted by OpenDesign)` |

## Changes

- `patches/upstream/<skill>.patch`: diff from the pristine upstream file at the pinned commit to this kit's
  `skills/<skill>/SKILL.md` (frontmatter and reading note added; upstream text unchanged).
- NOTICE.md states every change in prose.
- Unchanged, verified byte-identical to upstream: `skills/typography/typography-hierarchy.md`
  (`craft/typography-hierarchy.md`), `UPSTREAM-README.md` (`craft/README.md`), every file in
  `upstream/craft/`, `LICENSE` (open-design `LICENSE`) and `LICENSE-refero_skill` (refero_skill `LICENSE`).
- Patches regenerated on 2026-11-07 as direct diffs from upstream; each applies to the pristine upstream
  file and reproduces the kit file byte for byte.

## Item record

## opendesign-craft

| Field | Value |
| --- | --- |
| Source | https://github.com/nexu-io/open-design (path `craft/`) |
| Commit | `e03d5c23f308c39f4de7c057568df66c29a84385` (2026-10-22, release 0.26.1 copy; equals upstream HEAD on 2026-10-23). `craft/` last changed in `f1a0b60` (2026-08-18) |
| Licence | Apache-2.0 (`LICENSE`). `craft/README.md` states the craft content is adapted from https://github.com/referodesign/refero_skill, MIT, © 2026 Refero; `typography.md`, `color.md`, `anti-ai-slop.md` say so inline. `LICENSE-refero_skill` is refero_skill's `LICENSE` at `2382e51` (`2382e518f90096df607196b9a635da2d1bc142f9`; unchanged since its first commit `cc2d355`, 2026-02-04) |
| Licence note | Ships with notices: Apache-2.0 `LICENSE`, refero_skill's MIT licence as `LICENSE-refero_skill`, and NOTICE.md stating the changes |
| Fetched | 2026-10-23, fresh clones of both repositories |
| Copied | the files listed below from a clone of open-design at the commit above, and `LICENSE` from a clone of refero_skill at `2382e51` (files unchanged), then `patches/upstream/*.patch` |

### In this kit

`typography.md`, `typography-hierarchy.md`, `color.md`, `animation-discipline.md`, `state-coverage.md` (pristine copies in `upstream/craft/`), and `README.md` as `UPSTREAM-README.md` (attribution).

### Not included

`anti-ai-slop.md`, `accessibility-baseline.md`, `form-validation.md` (17 KB, not small), `laws-of-ux.md`, `rtl-and-bidi.md`, `typography-hierarchy-editorial.md`: outside this kit's scope. OpenDesign's P0 linter (`apps/daemon/src/lint-artifact.ts`) is not included.

### How the kit uses it

typography (`typography.md` + `typography-hierarchy.md`), color, motion (`animation-discipline.md`) and state-coverage become skills: frontmatter and a reading note added, text unchanged. `typography-hierarchy.md` sits unchanged next to the typography `SKILL.md`.

### Review (2026-10-23)

Markdown only. No scripts, no network. The text names OpenDesign's daemon and linter; the reading note says those do not apply.
