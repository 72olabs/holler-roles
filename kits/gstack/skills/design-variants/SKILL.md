---
name: design-variants
description: "Explore several genuinely different directions for one screen, flow, state or asset before anything is built. Use for 'give me N directions', 'show me options', 'explore', 'mock up a few takes', 'what could X look like', 'show me alternatives'. Writes text concepts first and waits for confirmation before rendering HTML or image variants."
---

<!-- Modified by 72o Labs: extracted from garrytan/gstack@b04cc35 design-shotgun/SKILL.md, Steps 1, 3a, 3b and 5 (MIT, see ../../LICENSE and ../../NOTICE.md). Rewritten: gstack paths, binaries, taste-profile scripts, the $D design binary, the comparison-board server and approved.json are removed. Rendering, seeds and the taste log were added by 72o Labs. -->

# Design variants

Produce distinct directions, let the human pick, record why. You do not rank or score your own variants.

## 1. Context (two rounds of questions at most)

Read `DESIGN.md` and `design/taste-log.md` first. Then make sure you know:

1. **Who**: the audience and their expertise.
2. **Job to be done**: what the user is trying to finish on this surface.
3. **What exists**: components, screens and patterns already in the repository.
4. **Flow**: how users arrive and where they go next.
5. **Edge cases**: long names, zero results, errors, small windows, first-time versus power user.

Ask one question that states what you inferred and asks only for the gaps, plus how many variants (default 3; up to 8 for an important surface). After two rounds, proceed and list your assumptions.

If DESIGN.md exists, say: "I'll follow DESIGN.md: its fonts and palette stay fixed and the variants differ in layout and composition. Say so if you want to go off-system."

## 2. Concepts before anything is rendered

Write N text concepts as a lettered list, each a separate direction, not a tweak:

```
I'll explore 3 directions:

A) "Name" - one-line visual description
B) "Name" - one-line visual description
C) "Name" - one-line visual description
```

**Anti-convergence.** When DESIGN.md exists it decides what varies: keep its fonts and palette, vary layout and composition. Without one, vary font family, palette and layout approach. If two concepts look like siblings, replace the weaker one with a deliberately different direction.

**Swap-headline test.** If someone could swap the headline text between two variants without noticing, they are too similar. Variants should feel made by separate design teams, not by one team on different days.

**Seeds.** Give each concept a different random seed string (for example from `openssl rand -hex 4`) and let it push the choice of composition, density and emphasis. Models predict rather than randomize; the seed forces variety. Never show the seed in the design.

**Brief ambitiously.** Name an aesthetic world for each concept ("a ship's logbook", "an air-traffic strip board"), not "a clean, modern layout".

Read the taste log and say which entries each concept follows or departs from. Taste is a preference, not a constraint; convergence across sessions is the failure mode.

## 3. Confirm before spending

Show the concepts and ask, before rendering anything:

- A) Render all N
- B) Change some concepts (which)
- C) Add more
- D) Fewer (which to drop)

Revise and re-confirm for B, C or D, at most two rounds. Image mockups cost money: more than 4 images in one go needs the human's explicit yes, with the count stated.

## 4. Render

All output goes into one folder in the project: `design/explorations/<YYYY-MM-DD>-<slug>/`.

- **HTML variants** (default): one self-contained file per variant, `variant-a.html`, `variant-b.html`, ... Use the brief's real content, never lorem ipsum; mark generated copy as placeholder. Render the populated state plus at least one of empty, loading or error when the surface holds data. Screenshot each at the agreed viewport (`variant-a.png`) and open every screenshot before you show it.
- **Image mockups**: use the imagegen skill. It records each prompt in the same folder's `prompts.md`.
- Write `index.md` in the folder: one line per variant with its letter, name, one-line description and files.

## 5. Present, pick, record

Show every variant at once, in letter order, with its name and description. Do not rank them, recommend one, or score them. You may say which constraint each one trades against the others.

Ask the human to pick (or reject all) and why. Then confirm what you understood:

```
PICKED:   B "Name"
REJECTED: A, C
REASONS:  [the human's words, verbatim]
NEXT:     [iterate on B / systematize into DESIGN.md / build]
Is this right?
```

After confirmation, append the entry with the taste-log skill. A rejected set is also an entry.

## Rules

- DESIGN.md is the default constraint unless the human says otherwise.
- Concepts first, rendering second, and nothing paid without confirmation.
- Never pick for the human and never grade your own variants. Review comes from an independent reviewer (the reviewer agent, asked with holler-review-request), approval from the human.
- Generated copy is placeholder until a human rewrites it.
