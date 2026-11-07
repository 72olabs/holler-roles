---
name: imagegen
description: Generate raster images with Codex image generation for design exploration - mood boards, divergent mockup directions, icons, illustrations, marketing visuals. Use when a direction is easier to judge as a picture than as HTML, or the user asks for an image, mockup picture, mood board, icon or illustration. Images are explorations, never shipped UI.
---

# Image generation for design exploration

## When

- Mood boards and divergent mockup directions (with design-variants).
- Icon, illustration and marketing-visual explorations.

Not for: the shipped UI (build it in HTML/React), icons that must match an existing SVG set (edit the SVGs), or anything whose text must be final.

## Gate

- State the number of images before generating. More than 4 images in one go needs the human's explicit yes. Count every image in a round, including retries.
- No other spending, uploading or publishing.

## Prompt

- If `DESIGN.md` exists, cite its tokens by name and value in every prompt: colors (`colors.accent #...`), faces (`typography.display`), radius, density, the one authored motion moment if relevant. Say which tokens you cited in `prompts.md`. Without DESIGN.md, say so in `prompts.md`.
- Use a labelled spec: Use case, Asset type, Subject, Style or medium, Composition, Palette (tokens), Text, Avoid.
- **Text in images is placeholder.** Ask for short neutral placeholder words or grey text bars, never final copy, product claims or numbers.

## Where files go

Every image used in the project lives in `design/explorations/<YYYY-MM-DD>-<slug>/`, next to `prompts.md`, which is append-only. One entry per image:

```markdown
## 01-<short-name>.png
- date: 2026-10-23 14:05
- harness: codex (image_gen tool) | model: <session model>
- design_md: DESIGN.md tokens cited: colors.accent #..., typography.display ... | none
- status: exploration, not shipped UI
- prompt:
  > <the exact prompt, verbatim>
```

Copy, never move, and never overwrite: if a name is taken, add `-v2`.

## How: in a Codex session

The built-in image tool saves to `$CODEX_HOME/generated_images/<thread-id>/<call-id>.png`. It takes no size, quality or destination argument; the file always lands there first.

1. `dir=design/explorations/$(date +%F)-<slug>; mkdir -p "$dir"; touch "$dir/.gen-start"`
2. Generate, one tool call per image.
3. `find "$CODEX_HOME/generated_images" -type f -name '*.png' -newer "$dir/.gen-start"` lists this round's files. Copy each with `cp -n` to `$dir/<nn>-<short-name>.png`, then `rm "$dir/.gen-start"`.
4. Append one `prompts.md` entry per image.

## How: in a Claude session

Claude has no image tool here; call Codex non-interactively. The image tool needs no shell write, so Codex runs read-only and you copy the files yourself. Codex uses its current home: `$CODEX_HOME` when set, otherwise `~/.codex`, and it must be logged in.

```sh
home="${CODEX_HOME:-$HOME/.codex}"
dir=design/explorations/$(date +%F)-<slug>; mkdir -p "$dir"; touch "$dir/.gen-start"
codex exec --sandbox read-only --ephemeral --skip-git-repo-check -C "$PWD" \
  "Use the built-in image generation tool to generate exactly <N> image(s), one call each. Do not run shell commands or write files. Prompt 1: <spec> ..."
find "$home/generated_images" -type f -name '*.png' -newer "$dir/.gen-start"
```

Then copy, record `prompts.md` (harness: codex exec from claude) and remove the marker as above. Open each copied image before you show it. Codex writes only its own session state and the images into its home; you change no configuration there. If `codex` is missing or not logged in, say so and stop: do not install or log in for the user.

## Report

List each copied path, its prompt, and the image count. Call them explorations. They go to the reviewer agent like any other target (holler-review-request); Codex-made images are best reviewed by a Claude reviewer, and the reverse.
