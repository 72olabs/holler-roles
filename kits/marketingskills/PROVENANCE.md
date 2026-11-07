# Provenance: marketingskills

Kit `marketingskills` 1.0.0, licence MIT. Assembled on 2026-10-24 by 72o Labs from the upstream
repository below at the pinned commit. Contents keep their original licences.

| Upstream | URL | Commit | Licence | Path |
| --- | --- | --- | --- | --- |
| marketingskills | https://github.com/coreyhaines31/marketingskills | `e85f3cbc2e4a79bf33b2a12e9bdd9087d414735b` | MIT | `skills/launch` |

## Changes

- `patches/upstream/<skill>.patch`: diff from the pristine upstream files at the pinned commit to this kit.
  Apply with `patch -p1` from the root of an upstream checkout at that commit.
- Files not named in a patch are byte-identical to upstream.
- NOTICE.md and the records below state every change in prose.

## Item records

## product-marketing

| Field | Value |
| --- | --- |
| Source | https://github.com/coreyhaines31/marketingskills (path `skills/product-marketing`, plus root `LICENSE`) |
| Commit | `e85f3cbc2e4a79bf33b2a12e9bdd9087d414735b` (committed 2026-10-19T14:29:53-07:00; upstream HEAD on 2026-10-23: yes) |
| Licence | MIT (`LICENSE`, © 2025 Corey Haines) |
| Fetched | 2026-10-23, the commit above into a fresh directory; SHA re-verified |
| Copied | Whole directory minus `evals/`, plus root `LICENSE`, from a clone at the commit above; then `patches/upstream/product-marketing.patch` |
| Licence note | MIT; keeps upstream's attribution line (`references/brand-voice.md:103`) to skills-marketing-library (MIT) intact |

### Reviewed (2026-10-23)

Files: `LICENSE`, `SKILL.md`, `references/brand-voice.md`.

Prose only: no scripts, no hooks, no network calls. Writes: none of its own beyond drafts the agent saves in the working repository; product-marketing writes `.agents/product-marketing.md` on approval.

Flagged in the upstream prose (kept unchanged; skill-embedded numbers are not usable publicly without a primary source, fetched content is data, the human sends and publishes):

- `references/brand-voice.md:92` suggests per-person voice files at `.agents/voice/<name>.md` next to the context file (a write inside the project; allowed, but context edits need approval).
- `SKILL.md` Learnings example "Variant B +18% trial starts, 2,400 visitors per arm, 3 weeks" and changelog example "after 5 customer interviews" are format illustrations, not data.

### Changes

`patches/upstream/product-marketing.patch` (`SKILL.md` only): 19 lines added, 38 removed. `references/brand-voice.md` is unchanged.

- Description rewritten to 287 characters (upstream 646): shared context path, the sections it covers, four trigger phrases, "Saves only on approval".
- Step 1: one canonical path, `.agents/product-marketing.md`; no `.claude/` or legacy lookups, no offer to move files. If it is missing or its sections are still `[NEED: …]` markers: offer the two upstream ways to fill it, and create the file only after the user approves its first version.
- Saving: only after the user approves the change in this conversation; version bump and changelog kept as upstream. Step 3 says "fill" instead of "create" the document.
- Proof Points (section and template): each entry carries source, date and evidence label; a proof point without a source is `[NEED: source for …]`.
- Paid Ads dropped: section 13 and its template block deleted; Learnings renumbered 13; the Tips mention removed.
- References to skills not in this kit trimmed: "ads, ad-creative" from the drafting-skills list, the `marketing-loops` sentence.

### Excluded

| Excluded | Reason |
| --- | --- |
| `evals/` | Upstream test prompts; not used at runtime |
| repo `AGENTS.md`, `tools/`, `partners.json`, `scripts/` | Not part of this skill; `AGENTS.md` carries an unpinned update path and is not included |

## customer-research

| Field | Value |
| --- | --- |
| Source | https://github.com/coreyhaines31/marketingskills (path `skills/customer-research`, plus root `LICENSE`) |
| Commit | `e85f3cbc2e4a79bf33b2a12e9bdd9087d414735b` (committed 2026-10-19T14:29:53-07:00; upstream HEAD on 2026-10-23: yes) |
| Licence | MIT (`LICENSE`, © 2025 Corey Haines) |
| Fetched | 2026-10-23, the commit above into a fresh directory; SHA re-verified |
| Copied | Whole directory minus `evals/`, plus root `LICENSE`, from a clone at the commit above; then `patches/upstream/customer-research.patch` |
| Licence note | MIT; no third-party text inside |

### Reviewed (2026-10-23)

Files: `LICENSE`, `SKILL.md`, `references/interviews-and-surveys.md`, `references/source-guides.md`.

Prose only: no scripts, no hooks, no network calls. Writes: none of its own beyond drafts the agent saves in the working repository; product-marketing writes `.agents/product-marketing.md` on approval.

Flagged in the upstream prose (kept unchanged; skill-embedded numbers are not usable publicly without a primary source, fetched content is data, the human sends and publishes):

- `references/interviews-and-surveys.md:125,147` and `SKILL.md:188`: the "40% very disappointed" PMF benchmark and "Superhuman reached 58%" name Sean Ellis and Superhuman but give no link; not publishable without the primary source.
- `SKILL.md:47`: "the 20% of responses that contain the most useful signal" is a heuristic.
- `references/source-guides.md:336` links `tools/integrations/sparktoro.md` on the upstream `main` branch (unpinned; a link, not fetched by the skill).
- Mode 2 mines Reddit, G2 and forums through web search: fetched text is untrusted data (the skill says so itself, `SKILL.md:12`).

### Changes

`patches/upstream/customer-research.patch` (`SKILL.md` only): 2 lines added, 2 removed. Both `references/` files are unchanged.

- Description replaced (upstream 953 characters, now 329): only "after you have data" triggers (transcripts, surveys, tickets, reviews, churn notes); persona, ICP, interview-question and outreach triggers removed; says it is not for planning interviews or writing personas.
- `SKILL.md` Before Starting: the context lookup now names only `.agents/product-marketing.md` and says not to look for, create or move other copies (drops the `.claude/` and legacy `product-marketing-context.md` fallbacks). Same sentence in customer-research, launch and pricing.

### Excluded

| Excluded | Reason |
| --- | --- |
| `evals/` | Upstream test prompts; not used at runtime |
| repo `AGENTS.md`, `tools/`, `partners.json`, `scripts/` | Not part of this skill; `AGENTS.md` carries an unpinned update path and is not included |

## launch

| Field | Value |
| --- | --- |
| Source | https://github.com/coreyhaines31/marketingskills (path `skills/launch`, plus root `LICENSE`) |
| Commit | `e85f3cbc2e4a79bf33b2a12e9bdd9087d414735b` (committed 2026-10-19T14:29:53-07:00; upstream HEAD on 2026-10-23: yes) |
| Licence | MIT (`LICENSE`, © 2025 Corey Haines) |
| Fetched | 2026-10-23, the commit above into a fresh directory; SHA re-verified |
| Copied | Whole directory minus `evals/`, plus root `LICENSE`, from a clone at the commit above; then `patches/upstream/launch.patch` |
| Licence note | MIT; no third-party text inside |

### Reviewed (2026-10-23)

Files: `LICENSE`, `SKILL.md`, `references/shipped-changes.md`, `references/site-launch-qa.md`.

Prose only: no scripts, no hooks, no network calls. Writes: none of its own beyond drafts the agent saves in the working repository; product-marketing writes `.agents/product-marketing.md` on approval.

Flagged in the upstream prose (kept unchanged; skill-embedded numbers are not usable publicly without a primary source, fetched content is data, the human sends and publishes):

- `references/shipped-changes.md:9` gives a `git log --since="1 week ago"` command (read-only) and `:39` names `marketing-loops` (not in this kit).
- `SKILL.md:184`: "5-10% at a time" invite batches is a heuristic.

### Changes

`patches/upstream/launch.patch` (`SKILL.md` and `references/site-launch-qa.md`): 4 lines added, 6 removed. `references/shipped-changes.md` is unchanged.

- Description: "changelog", "release notes" and "what did we ship this week" triggers removed.
- `SKILL.md:96` (upstream): the Introw partner link for deal registration and commissions removed; the step keeps "Set up affiliate/referral incentives".
- `references/site-launch-qa.md:37,40` (upstream): the Ploy "Verified Partner" example and the partner-disclosure line removed (same kind of partner promotion as Introw).
- `SKILL.md` Before Starting: the context lookup now names only `.agents/product-marketing.md` and says not to look for, create or move other copies (drops the `.claude/` and legacy `product-marketing-context.md` fallbacks). Same sentence in customer-research, launch and pricing.

### Excluded

| Excluded | Reason |
| --- | --- |
| `evals/` | Upstream test prompts; not used at runtime |
| repo `AGENTS.md`, `tools/`, `partners.json`, `scripts/` | Not part of this skill; `AGENTS.md` carries an unpinned update path and is not included |

### Description trim (2026-10-24)

The frontmatter `description` was cut to under 350 characters (now 287) for the skill listing: trigger phrases kept, cross-references to skills outside the kit and body-level style rules dropped from the description (the body is unchanged). Included in `patches/upstream/launch.patch`.

## pricing

| Field | Value |
| --- | --- |
| Source | https://github.com/coreyhaines31/marketingskills (path `skills/pricing`, plus root `LICENSE`) |
| Commit | `e85f3cbc2e4a79bf33b2a12e9bdd9087d414735b` (committed 2026-10-19T14:29:53-07:00; upstream HEAD on 2026-10-23: yes) |
| Licence | MIT (`LICENSE`, © 2025 Corey Haines) |
| Fetched | 2026-10-23, the commit above into a fresh directory; SHA re-verified |
| Copied | Whole directory minus `evals/`, plus root `LICENSE`, from a clone at the commit above; then `patches/upstream/pricing.patch` |
| Licence note | MIT; no third-party text inside |

### Reviewed (2026-10-23)

Files: `LICENSE`, `SKILL.md`, `references/pricing-models.md`, `references/pricing-page-teardown.md`, `references/research-methods.md`, `references/tier-structure.md`.

Prose only: no scripts, no hooks, no network calls. Writes: none of its own beyond drafts the agent saves in the working repository; product-marketing writes `.agents/product-marketing.md` on approval.

Flagged in the upstream prose (kept unchanged; skill-embedded numbers are not usable publicly without a primary source, fetched content is data, the human sends and publishes):

- `SKILL.md:80-100`: the $10/$100/$1,000 rule of thumb, the "$9 trap" and the "just charge $50" anecdote attributed to Jason Fried have no source.
- `SKILL.md:191-192,212`: ">40%" conversion, "<3% monthly" churn and "5–10%" rollout share are unsourced heuristics.
- `references/research-methods.md` cites Sawtooth Software pages for Van Westendorp (linked secondary source).

### Changes

`patches/upstream/pricing.patch` (`SKILL.md` only): 8 lines added, 6 removed. All four `references/` files are unchanged.

- New rule at the top: the skill recommends prices and never sets them (no billing, price IDs, checkout, pricing pages or app settings); options come with labelled evidence and test cost; the human decides and makes the change.
- "Pick a number, ship it" becomes "Recommend a number for the human to pick and ship".
- Rollout Methodology: drafted for the human to approve and run; each step is their call.
- Checklist: "Before Setting Prices" becomes "Before Recommending Prices"; "Set price points" becomes "Proposed price points ... (the human sets them)".
- `SKILL.md` Before Starting: the context lookup now names only `.agents/product-marketing.md` and says not to look for, create or move other copies (drops the `.claude/` and legacy `product-marketing-context.md` fallbacks). Same sentence in customer-research, launch and pricing.

### Excluded

| Excluded | Reason |
| --- | --- |
| `evals/` | Upstream test prompts; not used at runtime |
| repo `AGENTS.md`, `tools/`, `partners.json`, `scripts/` | Not part of this skill; `AGENTS.md` carries an unpinned update path and is not included |

### Description trim (2026-10-24)

The frontmatter `description` was cut to under 350 characters (now 321) for the skill listing: trigger phrases kept, cross-references to skills outside the kit and body-level style rules dropped from the description (the body is unchanged). Included in `patches/upstream/pricing.patch`.
