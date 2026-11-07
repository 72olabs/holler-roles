---
name: design-review-passes
description: "Review passes for rendered or planned UI: name the surface mode (persuade, operate, read, experience), then information architecture, state coverage, journey, AI-slop risk, design-system alignment, responsive and accessibility, unresolved decisions, plus the trunk test and audit categories. Use when reviewing someone else's design work from screenshots or a plan."
---

## Review passes and audit categories

<!-- Modified by 72o Labs: extracted from garrytan/gstack@b04cc35 plan-design-review/sections/review-sections.md (Passes 1-7) and design-review/SKILL.md (Phase 1 first impression, Phase 3 trunk test and audit categories), MIT. Cut: plan editing, per-issue questions, mockup regeneration, the fix loop, browser scripts and detector commands; the AI-slop blacklist moved to the slop tells. The surface classifier, the reflexes and the three-looks calibration are derived from pbakaus/impeccable (Apache-2.0) via gstack. See ../../NOTICE.md. -->

Evaluate every pass. A pass with no findings says "no issues found"; it is never skipped.

### Surface classifier: name the mode before applying rules

The mode is what the visitor's win looks like on this surface, not what the product is.

- **PERSUADE** (marketing, landing, pricing): they decide and act. Apply the landing rules.
- **OPERATE** (app UI: dashboards, inboxes, settings, editors, tools): they finish a task. Scanability and native expectations beat expression; the brand lives in the details. Apply the app UI rules.
- **READ** (docs, articles, changelogs): they understand something. Apply the read rules.
- **EXPERIENCE** (portfolios, galleries): the work owns the first viewport.
- **HYBRID**: classify per section.

### Pass 1: Information architecture

What does the user see first, second, third? Is there one clear hierarchy per screen? If only three things could be shown, which three, and are they the ones shown? Navigation answers: what is this, where am I, what can I do here.

### Pass 2: Interaction state coverage

Loading, empty, error, success and partial states for every feature, described as what the user sees, not backend behaviour. Empty states are features: warmth, a primary action, context. Report them in the five-state matrix (loading, empty, error, populated, edge).

### Pass 3: User journey and emotional arc

Step by step: what the user does, what they feel, and whether the design supports that feeling. Check three horizons: the 5-second visceral reaction, 5-minute behaviour, 5-year reflection.

### Pass 4: AI slop risk

Specific, intentional UI or generic patterns?

**Hard rejections** (any one is a finding): generic SaaS card grid as the first impression; a beautiful image with a weak brand; a strong headline with no clear action; busy imagery behind text; sections repeating the same mood statement; a carousel with no narrative purpose; app UI made of stacked cards instead of layout.

**Litmus checks** (answer yes or no with evidence; they support findings, they are not a score): brand or product unmistakable in the first screen? One strong visual anchor? Understandable by scanning headlines only? Each section has one job? Are the cards necessary? Does motion improve hierarchy or atmosphere? Would it feel premium with every decorative shadow removed?

**Landing rules** (PERSUADE): the first viewport reads as one composition, not a dashboard; brand > headline > body > CTA; expressive, purposeful type, no default stacks; texture from the brand or a real asset, never a halo, spotlight, stripe or grid-paper gradient; hero budget: brand, one headline, one supporting sentence, one CTA group, one image; no cards in the hero; one job per section; one authored motion moment; one accent color; product language, not design commentary; display type under 6rem.

**App UI rules** (OPERATE): calm surface hierarchy, strong typography, few colors; dense but readable, minimal chrome; primary workspace, navigation, secondary context, one accent; no dashboard-card mosaics, thick borders, decorative gradients or ornamental icons; utility copy (orientation, status, action), not mood; cards only when the card is the interaction; section headings say what the area is or what the user can do.

**Read rules** (READ): measure 65-75ch, one reading column, headings closer to what follows than to what precedes; wayfinding is a feature; a docs index has no hero and no CTA theatre.

**Experience rules**: the work fills the first viewport; one authored transition; never crop the work to fit a template.

**Universal rules**: color system as variables or tokens; no default font stack as the display voice; one job per section; if deleting 30% of the copy improves it, keep deleting; cards earn their existence; never body text under 16px or under 4.5:1 contrast; never a placeholder as the only label; visited links distinct; a heading sits closer to its section than to the one before.

**Reflexes no detector catches**: browser surfaces (selection color, caret, scrollbars, focus rings, underline offset, tabular numerals) themed from the palette; one authored motion moment, not the same entrance everywhere; depth has an offset (a zero-offset colored halo is decoration); secondary text on a colored surface is tinted from that hue, never grey; more space above a heading than below it; light or dark comes from the use scene, never the category.

**Calibration: the three looks.** Generated interfaces land in one of three looks whatever the product: (1) cream ground, high-contrast serif display, terracotta or signal-red accent; (2) near-black, one neon accent, glowing edges; (3) broadsheet hairlines, italic display serif, tiny tracked mono labels. Each is fine when the brief asks for it. If the brief left the look open and the work landed in one anyway, that is a finding. Test: could someone guess this look from the category alone, or from "the category, minus the obvious"?

### Pass 5: Design system alignment

Does the work match DESIGN.md? Cite tokens by path (`{colors.primary}`, `{rounded.md}`). Flag any new component that does not fit the existing vocabulary. Without DESIGN.md, judge the explicit token and component choices and report the missing DESIGN.md as a finding.

### Pass 6: Responsive and accessibility

Intentional layout per viewport, not "stacked on mobile". Keyboard paths, landmarks, touch targets, contrast: see the accessibility floor.

### Pass 7: Unresolved design decisions

Choices that will haunt implementation, each tied to a real element you can see or a real line in the plan:

```
DECISION NEEDED                  | IF DEFERRED, WHAT HAPPENS
What does the empty state show?  | Engineer ships "No items found."
```

Report these as findings with severity fix, or under Not checked when the element's existence is unknown.

### First impression and page areas (render mode)

Form a gut reaction before analysing (the four lines in the procedure). Narrate it as a user scanning the page: name the specific element, its position and visual weight. Page area test: point at each clearly defined area; can you name its purpose in two seconds? List the ones you cannot.

### Trunk test (every page or screen)

Dropped here with no context, can you answer: what product is this; what page am I on; what are the major sections; what are my options here; where am I in the structure; how do I search? All six: pass. Four or five: partial. Three or fewer: fail, which is a block finding however polished the visuals are.

### Audit categories

Each item that the evidence can show is checked; the rest goes under Not checked.

1. **Visual hierarchy and composition**: a clear focal point and one primary action per view; natural eye flow; no competing elements; density right for the content; nothing overlapping unexpectedly; purpose clear in three seconds; hierarchy survives the squint test; white space intentional, not leftover.
2. **Typography**: at most three families; a scale with a ratio (1.25 or 1.333); line height about 1.5 for body and 1.15-1.25 for headings; measure 45-75 characters; no skipped heading levels; at least two weights doing hierarchy; balanced heading wraps; curly quotes; the ellipsis character; tabular numerals in number columns; body at least 16px; captions at least 12px; no letter-spacing on lowercase text.
3. **Color and contrast**: a coherent palette (at most about 12 non-grey colors); WCAG AA (body 4.5:1, large text 3:1, UI components 3:1); semantic colors consistent; never color alone; dark mode uses elevation, off-white text and a slightly desaturated accent; no red/green-only pairs; neutrals consistently warm or cool.
4. **Spacing and layout**: a consistent grid at every breakpoint; spacing on a scale (4 or 8px base); alignment holds; related items closer, sections further apart; a radius hierarchy, not one bubbly radius everywhere; inner radius = outer radius - gap; no horizontal scroll; a max content width; safe areas respected.
5. **Interaction states**: hover, visible focus, active and disabled states; skeletons shaped like the real content; empty states with a message, a primary action and context; specific error messages with a next step; confirmation on success; targets at least 44px where touch matters; every decision point a mindless click; browser surfaces themed.
6. **Responsive**: the small layout makes design sense, not stacked desktop columns; text readable without zoom; navigation collapses sensibly; forms usable; zoom not disabled.
7. **Motion**: ease-out to enter, ease-in to exit, ease-in-out to move; 50-700ms; every animation communicates something; reduced motion respected; one authored moment per page; content never hides behind animation timing. Motion cannot be judged from a still: without a recording or prototype, this goes under Not checked.
8. **Content and microcopy**: specific button labels ("Save API key", not "Continue"); errors say what happened, why and what to do; no lorem ipsum; truncation handled; active voice; loading text ends with "…"; destructive actions confirmed or undoable; happy talk flagged (count visible words and report the share that is happy talk); visible instructions longer than one sentence flagged together with the interaction they compensate for.
9. **AI slop**: see the slop tells.
10. **Performance as design**: layout shift, skeleton quality, font swap flash. Only from evidence you have; usually Not checked.
