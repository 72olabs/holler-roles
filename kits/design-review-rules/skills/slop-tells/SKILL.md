---
name: slop-tells
description: "Visual tells of generated, default-looking UI (indigo accents, trust gradients, emoji icons, template chrome, overused faces, card soup), with ids and severities. Use when reviewing screenshots or a plan for AI-slop and template defaults; DESIGN.md and the brief win over any tell."
---

## Slop tells

<!-- Modified by 72o Labs: deduplicated union of (1) OpenDesign craft/anti-ai-slop.md "seven cardinal sins" (nexu-io/open-design@e03d5c2, Apache-2.0, itself adapted from referodesign/refero_skill, MIT); (2) gstack review/design-checklist.md category 1 (garrytan/gstack@b04cc35, MIT; its rule ids and names come from pbakaus/impeccable, Apache-2.0); (3) the calibration clusters and default typographic treatments in anthropics/skills frontend-design (@dbd4588, Apache-2.0). Rewritten as visual checks: grep instructions and confidence tags removed, overlapping items merged. See ../../NOTICE.md. -->

These are evidence of defaults, not proof of bad design. The brief's own words win, and a pattern DESIGN.md explicitly blesses is not a finding. Report a tell only when it is visible in your evidence, and name the `[id]`.

### P0: fix before approval

1. `[P0-1 indigo-accent]` Default Tailwind indigo or violet as the accent (#6366f1, #4f46e5, #4338ca, #3730a3, #8b5cf6, #7c3aed, #a855f7), or a purple, violet or blue-to-purple scheme.
2. `[P0-2 trust-gradient]` A two-stop purple-to-blue, blue-to-cyan or indigo-to-pink gradient on the hero or as a page background.
3. `[P0-3 emoji-icons]` Emoji as feature icons, bullets or heading decoration.
4. `[P0-4 display-face]` Sans-serif display text where DESIGN.md binds a serif, or system-ui / -apple-system as the primary display or body face ("gave up on typography").
5. `[P0-5 side-tab]` A rounded card with a colored left-border accent.
6. `[P0-6 invented-metrics]` Invented numbers: "10x faster", "99.9% uptime", "10k+ users", three big numbers with tiny labels under the hero.
7. `[P0-7 filler-copy]` Lorem ipsum, "feature one / two / three", "placeholder text", or generic hero copy ("Welcome to X", "Unlock the power of", "Your all-in-one solution", "Revolutionize your").

### Look clusters (frontend-design calibration)

8. `[look-cream]` Warm cream ground (near #F4F1EA) with a high-contrast serif display and a terracotta or warm-clay accent (near #D97757).
9. `[look-neon]` Near-black ground with a single acid-green or vermilion accent; glowing zero-offset edges (`[dark-glow]`).
10. `[look-broadsheet]` Hairline rules, zero radius, dense newspaper columns, italic display serif (`[italic-serif-display]`), tiny tracked mono labels.
11. `[look-saas-kit]` Content chopped into identical rounded cards with one radius everywhere, the same soft grey shadow under each, gradient washes as decoration; cards nested in cards (`[nested-cards]`).
12. `[template-chrome]` A tracked ALL-CAPS eyebrow above every heading (`[kicker-above-heading]`, `[hero-eyebrow-chip]`); meta strings joined with middle dots; "WORD - fragment" labels; tinted near-black (#0B0B0B, #111) standing in for black; monospace on labels and body to look technical; a "→" appended to every link and button.

### Typography

13. `[accent-word]` One word or phrase in a headline singled out in italic, bold or a different color.
14. `[gradient-text]` Gradient-filled text used for emphasis.
15. `[overused-font]` A training-data default as the display voice: Inter, Roboto, Arial, Helvetica, Open Sans, Lato, Montserrat, Poppins, Space Grotesk, Space Mono, Fraunces, Playfair Display, Cormorant, Lora, Crimson, Newsreader, Syne, IBM Plex Sans/Serif, DM Sans/Serif, Outfit, Plus Jakarta Sans, Instrument Sans, Geist. As body or UI text on an OPERATE or READ surface several are fine when DESIGN.md says so.
16. `[oversized-h1]` Display type past 6rem on a page that is not a poster. `[extreme-negative-tracking]` tracking tighter than -0.04em.
17. `[numbered-labels]` 01 / 02 / 03 markers on content that is not a sequence.

### Layout and decoration

18. `[feature-grid]` The three-column feature grid: icon in a colored circle, bold title, two-line description, three times; icons in colored circles or rounded-square tiles above every heading (`[icon-tile-stack]`).
19. `[centered-everything]` Center alignment on nearly all headings, text and cards.
20. `[bubbly-radius]` One large radius on nearly every element.
21. `[decoration]` Blobs, floating circles, wavy dividers, radial halos or a spotlight glow behind the hero (`[radial-halo]`, `[radial-spotlight-glow]`), grid-paper or stripe backgrounds, shapes assembled into a fake illustration.
22. `[section-rhythm]` Hero, three features, testimonials, pricing, CTA, every section the same height.
23. `[cookie-hero]` Headline left, screenshot right, two buttons; "Get Started" and "Learn More" as the only calls to action.
24. `[glass]` Frosted-glass panels with blurred backdrops as the default surface.
25. `[gradient-cta]` Gradient buttons as the primary call to action.
26. `[marketing-buzzword]` "Seamless", "effortless", "supercharge", "streamline", "elevate", "empower"; launch theatre ("Built for the way you work", "Meet your new..."); every sentence a punchy fragment.
27. `[fake-data]` Sparklines, progress rings, fake avatars or testimonials nobody said, filling space where content or an honest empty state should be.
28. `[motion-tells]` A dot pulsing forever next to "Live", bounce or overshoot easing, the same fade-and-slide entrance on every section, image zoom on hover. Needs a recording or prototype; otherwise Not checked.
29. `[unthemed-surfaces]` Selection color, caret, scrollbars and focus rings left at browser defaults.
30. `[only-happy-path]` Only the populated state designed.
