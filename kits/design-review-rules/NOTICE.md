# Notices

These rule sets were written for an independent design reviewer. They are modified extracts of several
open-licensed sources; every contributing licence is in this folder.

- `skills/design-review-passes/SKILL.md`: modified extract of gstack (https://github.com/garrytan/gstack,
  commit b04cc35832183a89ed71eed628de15a6f315a1a8), `plan-design-review/sections/review-sections.md`
  (Passes 1-7) and `design-review/SKILL.md` (first impression, trunk test, audit categories), MIT,
  Copyright (c) 2026 Garry Tan (`LICENSE-gstack`). The surface classifier, the reflexes and the
  three-looks calibration in that text are derived, through gstack, from impeccable
  (https://github.com/pbakaus/impeccable), Copyright Paul Bakaus, Apache License 2.0
  (`LICENSE-Apache-2.0.txt`). Cut: plan editing, per-issue questions, mockup regeneration, the fix loop,
  browser scripts, detector commands and per-pass ratings.
- `skills/slop-tells/SKILL.md`: modified, merged and deduplicated extract of gstack
  `review/design-checklist.md` section 1 (MIT; its rule ids and names come from impeccable, Apache-2.0),
  OpenDesign `craft/anti-ai-slop.md` (https://github.com/nexu-io/open-design, commit e03d5c2,
  Apache-2.0, `LICENSE-open-design`; adapted there from https://github.com/referodesign/refero_skill,
  MIT, Copyright (c) 2026 Refero, `LICENSE-refero_skill`), and the calibration passage and typographic
  defaults of Anthropic's `frontend-design` skill (https://github.com/anthropics/skills, commit dbd4588,
  Apache-2.0, `LICENSE-anthropics-skills.txt`). Rewritten as visual checks.
- `skills/a11y-floor/SKILL.md`: Vercel Labs web interface guidelines
  (https://github.com/vercel-labs/web-interface-guidelines, `command.md`, commit 434b7f9), MIT,
  Copyright (c) 2025 Vercel Labs (`LICENSE-web-interface-guidelines`), and OpenDesign
  `craft/accessibility-baseline.md` (Apache-2.0), each with the removals recorded in the file. The
  pristine upstream files are in `upstream/`.

All three skills were modified by 72o Labs (frontmatter added; extraction, merging and the removals
above). Each skill carries a "Modified by 72o Labs" comment naming its sources.
`patches/upstream/a11y-floor.patch` records the change from the pristine Vercel Labs `command.md` to
`skills/a11y-floor/SKILL.md`. The other changes are hand extractions with no meaningful line diff;
PROVENANCE.md describes each.
