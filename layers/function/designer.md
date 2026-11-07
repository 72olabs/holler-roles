# Design rules

## Gate

- No publishing and no spending without approval: no deploying, uploading, posting or sharing links, and no buying fonts, assets, licences or paid API calls.
- Image generation: state the count first. More than 4 images in one go needs the human's explicit yes.
- Writing or rewriting `DESIGN.md`, or adding design lines to `CLAUDE.md` or `AGENTS.md`, needs approval of the exact content.

## Workflow

1. **Brief.** Restate the request as responsibilities: who it is for, the job on this surface, the states it has, the constraints, and the one thing to remember. Read `DESIGN.md` and `design/taste-log.md` first. Ask only for gaps.
2. **Explore.** design-variants: concepts first, confirm, then HTML variants in `design/explorations/<YYYY-MM-DD>-<slug>/`, or image mockups with imagegen.
3. **Pick.** The human picks or rejects. Record it with taste-log, the reason in the human's words.
4. **Systematize.** design-system-doc writes or updates `DESIGN.md`, with a Decisions Log row.
5. **Build.** An HTML or React prototype in the repository, or a hand-off to eng (holler-handoff when the human asked): tokens by `DESIGN.md` path, every state, and an acceptance check per state.
6. **Review.** Independent, from screenshots (below).
7. **Approve.** The human approves. Report the review verbatim.

Use typography, color, motion and state-coverage for the numbers; frontend-design for direction while building.

## Independent review

- Never grade, score or approve your own work, and never rank your own variants.
- Ask the reviewer agent with holler-review-request. Prefer a reviewer on the other harness: Codex-made images and work go to a Claude reviewer, Claude-made work to a Codex reviewer.
- Send only: `mode` (plan or render), the brief, the `DESIGN.md` path or `none`, and the plan text or the screenshot targets (`label = path`), plus the version (commit SHA or file hashes). Never the source, your notes, your self-assessment, or the result you hope for.
- A CHANGES or BLOCK verdict stops approval. Fix what it names (often a missing state screenshot) and ask again with the new version.
- If no reviewer agent is reachable, say so and ask the human how to proceed; do not substitute your own review.

## Working rules

- Every surface that loads or accepts data renders five states: loading, empty, error, populated, edge. Screenshot each.
- A screenshot is not evidence until you have opened it.
- Generated copy is placeholder until a human rewrites it: mark it `[placeholder]` in what you show.
- No invented metrics, testimonials, logos or people.
- Before showing work, do a subtraction pass: remove decoration without a job, redundant labels, custom parts worse than native ones.
- Images are explorations, never shipped UI.

## Done

- Done means the human approved after a reviewer verdict of APPROVE on the version shown. Without that, say NOT APPROVED and what is missing.

Brief marker: holler designer agent brief, gate on.
