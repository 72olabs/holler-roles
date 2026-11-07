# Notices

The craft rulebooks come from OpenDesign (https://github.com/nexu-io/open-design, path `craft/`, commit
`e03d5c23f308c39f4de7c057568df66c29a84385`), Apache License 2.0 (`LICENSE`). OpenDesign states that its craft content is adapted
from refero_skill (https://github.com/referodesign/refero_skill), MIT License, Copyright (c) 2026
Refero (`LICENSE-refero_skill`). `UPSTREAM-README.md` is OpenDesign's `craft/README.md`, unchanged.

Changes (Apache-2.0 section 4(b)): each `skills/<name>/SKILL.md` was modified by 72o Labs from the upstream
file named below by adding YAML frontmatter and a reading note above a horizontal rule; the text after
the rule is the upstream file, unchanged. Extra files next to a SKILL.md are unchanged copies. The
pristine upstream files are in `upstream/craft/`; `patches/upstream/<skill>.patch` is a diff from the
pristine upstream file at the commit above to the kit's SKILL.md and shows the additions.

| Skill | From |
| --- | --- |
| typography | `craft/typography.md` (+ `typography-hierarchy.md`, unchanged) |
| color | `craft/color.md` |
| motion | `craft/animation-discipline.md` |
| state-coverage | `craft/state-coverage.md` |
