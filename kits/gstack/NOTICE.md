# Notices

Everything in this kit is adapted from gstack (https://github.com/garrytan/gstack, commit
`b04cc35832183a89ed71eed628de15a6f315a1a8`), MIT License, Copyright (c) 2026 Garry Tan (`LICENSE`).

Parts of `skills/design-system-doc` (the font-selection procedure and the three-looks calibration) are
derived, through gstack, from impeccable (https://github.com/pbakaus/impeccable), Copyright Paul
Bakaus, Apache License 2.0 (`LICENSE-Apache-2.0.txt`), as gstack's own `NOTICE.md` states.

All four items were modified by 72o Labs. Each modified file carries a "Modified by 72o Labs" notice.

| Item | Upstream path | Changes |
| --- | --- | --- |
| `skills/office-hours` | `openclaw/skills/gstack-openclaw-office-hours/SKILL.md` | Name `office-hours`; the "YC Office Hours" title and the "You are a YC office hours partner" persona sentence made neutral; "Garry's Note" (the YC application pitch and link) deleted; design docs saved in the repository; an unsourced count softened (`patches/upstream/office-hours.patch`). |
| `skills/design-system-doc` | `design-consultation/SKILL.md`, `design-consultation/sections/proposal-and-preview.md` | Hand extraction: gstack runtime, binaries, telemetry, outside voices and slop lists removed; preview written into the project; approval before writing agent instruction files. No patch: the file was rewritten, see PROVENANCE.md. |
| `skills/design-variants` | `design-shotgun/SKILL.md` | Hand extraction: concept and variant steps kept; gstack binaries, comparison server and taste scripts removed; renders into `design/explorations/`; reasons recorded with a taste log; review goes to an independent reviewer agent. No patch: the file was rewritten, see PROVENANCE.md. |
| `hooks/careful` | `careful/` (`SKILL.md.tmpl` as `SPEC.md`, `bin/check-careful.sh`, `bin/hook-extract.sh`) | Analytics and gstack project-pattern files removed, freeze-only helpers removed, HIGH-tier messages reworded for an always-on hook (`patches/upstream/careful.patch`). Tests (`tests/`) added by 72o Labs. |

`patches/upstream/<item>.patch` is the diff from the pristine upstream files at the commit above to the
files in this kit. Files without a patch are described in PROVENANCE.md.
