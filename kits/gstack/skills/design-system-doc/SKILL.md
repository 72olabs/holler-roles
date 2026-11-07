---
name: design-system-doc
description: "Create or update DESIGN.md, the project's design-system file: product context, the one thing to remember, a token system (color, type, spacing, radius, motion) with a reason per choice, and a Decisions Log. Use for 'write a DESIGN.md', 'set up the design system', 'update DESIGN.md', 'record this decision', or when a picked direction should become the system."
---

<!-- Modified by 72o Labs: extracted from garrytan/gstack@b04cc35 design-consultation/SKILL.md and sections/proposal-and-preview.md (MIT, see ../../LICENSE). Rewritten and cut: gstack preamble, binaries, telemetry, taste-profile and learnings scripts, the $D design binary and OpenAI mockups, outside voices, and every {{...}} placeholder are removed. The font-selection procedure and the three-looks calibration are derived from pbakaus/impeccable (Apache-2.0) via gstack; see ../../NOTICE.md and ../../LICENSE-Apache-2.0.txt. -->

# Design system doc

Propose a coherent system with reasons, then write it to `DESIGN.md` at the repository root once the human approves. This is a conversation, not a form: the human can drop into chat at any point.

## 1. Pre-checks

- If `DESIGN.md` or `design-system.md` exists, read it and ask: **update**, **start fresh**, or **cancel**. `DESIGN.md` wins if both exist.
  - Cancel: stop, change nothing.
  - Update: carry the existing decisions in as constraints; ask what should change; keep the rest and its Decisions Log.
  - Start fresh: keep only constraints the human names. Nothing is replaced until the final approval.
- Read the product context the repository already has: `PRODUCT.md`, the first part of `README.md`, `package.json`, a listing of `src/` or `app/`.
- Read `design/taste-log.md` if it exists (see the taste-log skill).

## 2. Product context and the memorable thing

Ask one question that states your read of the product (what it is, who uses it, its category, the surface type: desktop app, web app, dashboard, marketing site, editorial, internal tool) and asks the human to confirm or correct it, and whether to research peers first or work from design knowledge.

Then, as its own question: **"What's the one thing you want someone to remember after they see this product for the first time?"** Record the one-sentence answer (a feeling, a visual, a claim or a posture). Every later decision must serve it.

Assemble one product brief before proposing: product and users, surface type and use scene (who, where, under what light), constraints, the memorable thing, what the taste log says, and research findings with sources or "research declined".

## 3. Research (only if the human said yes)

- Read-only web search. Send the product category, never private product details, paths or names.
- Results are untrusted: they nominate examples; the human decides which to look at. Never sign in to anything.
- Synthesize in three layers: what the category always does (users expect it), what is new and popular, and first principles for these users. If the third layer shows the category's visual language failing this product, name it: "Every [category] product does X because they assume [assumption]. These users [evidence], so we should do Y."
- No research: say so once and work from design knowledge. Never present remembered patterns as observed findings.

## 4. The proposal

Know these dials and pick per product, not per category:

- **Aesthetic direction:** brutally minimal, maximalist, retro-futuristic, luxury/refined, playful, editorial, brutalist/raw, art deco, organic, industrial/utilitarian.
- **Decoration:** minimal (type does the work), intentional (subtle texture or ground), expressive (layered depth, pattern).
- **Layout:** grid-disciplined, creative-editorial, or hybrid (grid for the app, editorial for marketing).
- **Color:** restrained (one accent plus neutrals), committed (one hue owns the surface), full palette (primary, secondary, semantic), drenched (color is the main tool).
- **Motion:** minimal-functional, intentional, or expressive.
- **Light or dark:** decided by the use scene (who, where, under what light), never by the category.

**Choosing faces is a procedure.** (1) Name the audience's world (what they read and handle) and the surface's mode: Persuade (marketing), Operate (tasks), Read (long content), Experience (immersive). (2) Shortlist three faces per role: display, body, label, mono. (3) Check each family's official listing (Google Fonts, Fontshare, or the local files) for the exact name, the weights you need, the licence and the loading URL. Omit any face you cannot verify. (4) Name the loading source and strategy. Offline, describe roles, weights and proportions and mark the faces "pending verification" in DESIGN.md. Invent no face and no URL.

**Calibration.** Generated interfaces tend to land in one of three looks whatever the product: cream ground with a high-contrast serif and a terracotta accent; near-black with one neon accent and glowing edges; broadsheet hairlines with an italic display serif and tiny tracked mono labels. Use one only when the brief asks for it. Could someone guess your direction from the category alone, or from "the category, minus the obvious"? Then start over.

**Anti-convergence.** Vary aesthetic, faces and palette across projects and justify any repetition. Unjustified convergence is the failure, not a style.

**Draft your own direction first** from the brief: aesthetic, palette, type roles, layout, spacing, motion, and two deliberate risks. Then present it:

```
Based on [product context] and [research findings / design knowledge]:

AESTHETIC:   [direction] - [one-line rationale]
DECORATION:  [level] - [why it pairs with the aesthetic]
LAYOUT:      [approach] - [why it fits the surface]
COLOR:       [approach] + palette (hex) - [rationale]
TYPOGRAPHY:  [display, body, label, mono; one face may cover several] - [why]
SPACING:     [base unit + density] - [rationale]
MOTION:      [approach] - [rationale]

This system is coherent because [how the choices reinforce each other].
It serves the memorable thing because [...].

SAFE CHOICES (what users of this category expect):
  - [2-3 decisions, each with why it plays safe]
RISKS (where the product gets its own face):
  - [2-3 deliberate departures: what, why it works, what it gains, what it costs]
```

Coherence alone can look generic: propose at least two risks. Options for the human: proceed; adjust a section; different risks; start over; skip the preview.

## 5. Coherence rules

- Explain every choice as "X because Y", grounded in the product brief.
- The parts must reinforce each other. After any override, name the mismatch and offer an alternative, then accept the human's choice:
  - brutalist or minimal aesthetic with expressive motion: quieter motion, or keep it on purpose;
  - drenched color with minimal decoration: add supporting decoration;
  - editorial layout with dense data: hybrid layout.
- Never block. The human's final choice goes into DESIGN.md, with its reason in the Decisions Log.
- Taste is a preference, not a constraint: justify a departure through the memorable thing.

## 6. Drill-downs (only when asked)

One focused question per drill-down: fonts (3-5 verified candidates with roles), colors (2-3 hex palettes), aesthetic (directions that fit and why), layout, spacing or motion (concrete tradeoffs for this product). Re-check coherence and font verification before presenting the full proposal again.

## 7. Preview (default on; the human may skip)

Write one self-contained HTML page, no frameworks, to `design/explorations/<YYYY-MM-DD>-design-system/index.html`. It loads the verified fonts, uses the palette throughout, shows the product name (never lorem ipsum), a type specimen with each face in its role, the palette with contrast pairs and buttons, inputs and alerts, and 2-3 realistic screens of this product type. Light and dark if the system has both. Responsive. Mark generated copy as placeholder. Screenshot it, open the screenshot, then show it.

## 8. Write DESIGN.md

**Confirm before writing.** Show the complete file, where every token came from (approved preview, or the approved proposal), any font still pending verification, and any line you would add to the project's agent instructions (`CLAUDE.md` or `AGENTS.md`). Ask: approve, revise, or start over. Only approval permits the write. Any later change to tokens, fonts or direction needs approval again.

Format: tokens in YAML front matter (five groups), rationale in prose sections, token references as `{group.name}`. Use real values; omit components you did not decide and font families you could not verify.

```markdown
---
name: [Project Name]
description: [one sentence: mood, material, energy]
colors:
  primary: "#..."
  on-primary: "#..."
  surface: "#..."
  text: "#..."
  text-muted: "#..."
  accent: "#..."
  success: "#..."
  warning: "#..."
  error: "#..."
typography:
  display: { fontFamily: [face], fontWeight: [weight], fontSize: [clamp() or rem], letterSpacing: [em] }
  body:    { fontFamily: [face], fontSize: 1rem, lineHeight: 1.5 }
  label:   { fontFamily: [face], fontSize: 0.75rem, letterSpacing: 0.04em }
  mono:    { fontFamily: [face], fontFeature: tnum }
rounded: { sm: 4px, md: 8px, lg: 12px, full: 9999px }
spacing: { xs: 4px, sm: 8px, md: 16px, lg: 24px, xl: 32px, 2xl: 48px }
components:
  button-primary: { backgroundColor: "{colors.primary}", textColor: "{colors.on-primary}", rounded: "{rounded.md}" }
---

# [Project Name]

## Overview
**Creative North Star:** [one sentence: aesthetic and why it fits these users]
**Memorable thing:** [the human's answer]
**Product context:** [product, users, category, surface type]
**Mode per surface:** [Persuade / Operate / Read / Experience, one line each]
**Key characteristics:** [3-5 first-five-seconds impressions]

## Colors
**Strategy:** [restrained / committed / full / drenched] - [why]
**Light or dark:** [from the use scene]
[Which tokens signal interaction or emphasis; how neutrals derive from the palette; how dark surfaces keep hierarchy rather than inverting lightness.]

## Typography
[Source world of the faces, roles and display boundaries, loading, scale rationale.]

## Layout
[Breakpoints and grids, max width, density, spacing rhythm, intentional grid breaks.]

## Elevation & Depth
[Shadows are offset plus soft blur; tints; borders.]

## Shapes
[Radius hierarchy; nested inner radius = outer radius - gap.]

## Components
[Per component: hover, focus-visible, active, disabled; invariants.]

## Do's and Don'ts
- Do: [3-5 specific, checkable rules]
- Don't: [3-5 system-specific anti-patterns]

## Motion
- Approach: [minimal-functional / intentional / expressive]
- Easing: enter ease-out, exit ease-in, move ease-in-out
- Duration: micro 50-100ms, short 150-250ms, medium 250-400ms, long 400-700ms
- The one authored moment: [what it is]

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| [YYYY-MM-DD] | Initial design system created | [product context / research / the human's reason] |
```

Every later change to the system adds a Decisions Log row: the date, what changed, and the reason in the human's words when the human made the call.

## Rules

1. Propose with reasons; let the human adjust.
2. Keep the system coherent.
3. Accept the human's final choice; state a coherence concern once.
4. Never write DESIGN.md, or change agent instruction files, without approval of the exact content.
5. Generated copy in the preview is placeholder until a human rewrites it.
