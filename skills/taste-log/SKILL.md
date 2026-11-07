---
name: taste-log
description: Read and append to design/taste-log.md, the dated record of the human's design picks and rejections with the reason in their own words. Read it before proposing any direction, palette, type or layout; append right after the human picks, rejects or overrides something ("go with B", "not this", "I like it because", "too busy").
---

# Taste log

`design/taste-log.md` in the project is the memory of the human's taste. It is append-only and it records reasons, because a pick without a reason teaches nothing.

## Read before proposing

Before any proposal (directions, palette, faces, layout, motion, copy tone), read the whole file. In the proposal, cite the entries you follow or depart from by date. When the request contradicts a strong entry, say so once: "On 2026-10-12 you rejected dense card grids because '...'. Proceed anyway, or keep that?" Newer entries outweigh older ones; the file never decides for the human. Taste is a preference, not a constraint, and repeating the same look every session is the failure mode to avoid.

## Append after a human decision

Write only decisions the human made, never your own preferences or a reviewer's findings. Create the file with a `# Taste log` heading if it is missing; otherwise append at the end, never edit or reorder earlier entries.

```markdown
## 2026-10-23 - inbox empty state
- shown: design/explorations/2026-10-23-inbox-empty/ (A, B, C)
- picked: B "Quiet ledger"
- rejected: A "Mission control", C "Postcard"
- reason (human's words): "B feels calm when nothing needs me; A shouts, C is cute"
- dimensions: layout, color, voice
```

- **Reason in the human's words**, quoted verbatim. If they gave none, ask once ("What made B win?"). If they still give none, write `reason: (none given)`. Never paraphrase into your own vocabulary and never invent one.
- `dimensions`: which of fonts, color, layout, aesthetic, motion, voice the reason is about, only when the reason says so.
- An override of DESIGN.md or of an earlier entry is an entry too.
- A whole set rejected: `picked: none` with the reason.
