# Provenance: pm-skills

Kit `pm-skills` 1.0.0, licence MIT. Assembled on 2026-10-24 by 72o Labs from the upstream repository
below at the pinned commit. Contents keep their original licences.

| Upstream | URL | Commit | Licence | Path |
| --- | --- | --- | --- | --- |
| pm-skills | https://github.com/phuryn/pm-skills | `07b34f64ee828df08953f505b7f747aef85ae7c6` | MIT | `pm-execution/skills/create-prd` |

## Changes

- `patches/upstream/<skill>.patch`: diff from the pristine upstream file at the pinned commit to this kit.
  Skills without a patch are unchanged.
- NOTICE.md states every change in prose.
- Unchanged, verified byte-identical to upstream: `skills/interview-script/SKILL.md`,
  `skills/opportunity-solution-tree/SKILL.md`, `LICENSE`.
- Patches regenerated on 2026-11-07 as direct diffs from upstream; each applies to the pristine upstream
  file and reproduces the kit file byte for byte.

## Item records

Each record gives the upstream commit, the review (scripts, network, writes) and the changes.

## interview-script

| Field | Value |
| --- | --- |
| Source | https://github.com/phuryn/pm-skills (path `pm-product-discovery/skills/interview-script`, plus root `LICENSE`) |
| Commit | `07b34f64ee828df08953f505b7f747aef85ae7c6` (committed 2026-10-16T14:28:37+02:00; upstream HEAD on 2026-10-23: yes) |
| Licence | MIT (`LICENSE`, © 2026 Pawel Huryn) |
| Fetched | 2026-10-23, fetch of the commit above into a fresh directory; SHA re-verified |
| Copied | whole directory from a clone at the commit above, plus `LICENSE` |
| Changes | none |
| Licence note | MIT; no third-party text inside |

### Reviewed (2026-10-23)

Files: `LICENSE`, `SKILL.md`.

Prose only: no scripts, no hooks, no network calls. Writes: the skill asks for its output to be saved as markdown in the working repository. Further Reading links point at productcompass.pm (the author's newsletter); the skill does not fetch them.

Flagged in the upstream text (kept unchanged; treat numbers inside a skill as unsourced unless a primary source is given):

- `SKILL.md:72`: "aim for 80/20 split" (talk/listen ratio) is a rule of thumb with no source; not a publishable statistic.

### Excluded

| Excluded | Reason |
| --- | --- |
| Other `pm-*` plugins, `.claude-plugin/`, `validate_plugins.py`, `tests/` | Not part of this skill |

## opportunity-solution-tree

| Field | Value |
| --- | --- |
| Source | https://github.com/phuryn/pm-skills (path `pm-product-discovery/skills/opportunity-solution-tree`, plus root `LICENSE`) |
| Commit | `07b34f64ee828df08953f505b7f747aef85ae7c6` (committed 2026-10-16T14:28:37+02:00; upstream HEAD on 2026-10-23: yes) |
| Licence | MIT (`LICENSE`, © 2026 Pawel Huryn) |
| Fetched | 2026-10-23, fetch of the commit above into a fresh directory; SHA re-verified |
| Copied | whole directory from a clone at the commit above, plus `LICENSE` |
| Changes | none |
| Licence note | MIT; no third-party text inside |

### Reviewed (2026-10-23)

Files: `LICENSE`, `SKILL.md`.

Prose only: no scripts, no hooks, no network calls. Writes: the skill asks for its output to be saved as markdown in the working repository. Further Reading links point at productcompass.pm (the author's newsletter); the skill does not fetch them.

Flagged in the upstream text (kept unchanged; treat numbers inside a skill as unsourced unless a primary source is given):

- `SKILL.md:16`: example outcome "increase 7-day retention to 40%" is an illustration, not a benchmark.

### Excluded

| Excluded | Reason |
| --- | --- |
| Other `pm-*` plugins, `.claude-plugin/`, `validate_plugins.py`, `tests/` | Not part of this skill |

## strategy-red-team

| Field | Value |
| --- | --- |
| Source | https://github.com/phuryn/pm-skills (path `pm-execution/skills/strategy-red-team`, plus root `LICENSE`) |
| Commit | `07b34f64ee828df08953f505b7f747aef85ae7c6` (committed 2026-10-16T14:28:37+02:00; upstream HEAD on 2026-10-23: yes) |
| Licence | MIT (`LICENSE`, © 2026 Pawel Huryn) |
| Fetched | 2026-10-23, fetch of the commit above into a fresh directory; SHA re-verified |
| Copied | whole directory from a clone at the commit above, plus `LICENSE`, then `patches/upstream/strategy-red-team.patch` |
| Licence note | MIT; no third-party text inside |

### Reviewed (2026-10-23)

Files: `LICENSE`, `SKILL.md`.

Prose only: no scripts, no hooks, no network calls. Writes: the skill asks for its output to be saved as markdown in the working repository. Further Reading links point at productcompass.pm (the author's newsletter); the skill does not fetch them.

### Excluded

| Excluded | Reason |
| --- | --- |
| Other `pm-*` plugins, `.claude-plugin/`, `validate_plugins.py`, `tests/` | Not part of this skill |

### Description trim (2026-10-24)

The frontmatter `description` was cut to about 350 characters to keep the skill listing short: trigger phrases kept, cross-references to skills outside the kit and body-level style rules dropped from the description (the body is unchanged). Recorded in `patches/upstream/strategy-red-team.patch` (1 line changed).

## create-prd

| Field | Value |
| --- | --- |
| Source | https://github.com/phuryn/pm-skills (path `pm-execution/skills/create-prd`, plus root `LICENSE`) |
| Commit | `07b34f64ee828df08953f505b7f747aef85ae7c6` (committed 2026-10-16T14:28:37+02:00; upstream HEAD on 2026-10-23: yes) |
| Licence | MIT (`LICENSE`, © 2026 Pawel Huryn) |
| Fetched | 2026-10-23, fetch of the commit above into a fresh directory; SHA re-verified |
| Copied | whole directory from a clone at the commit above, plus `LICENSE`, then `patches/upstream/create-prd.patch` |
| Licence note | MIT; no third-party text inside |

### Reviewed (2026-10-23)

Files: `LICENSE`, `SKILL.md`.

Prose only: no scripts, no hooks, no network calls. Writes: the skill asks for its output to be saved as markdown in the working repository. Further Reading links point at productcompass.pm (the author's newsletter); the skill does not fetch them. Output file: `PRD-[product-name].md`.

Flagged in the upstream text (kept unchanged):

- `SKILL.md` step 1 tells the agent to research what the web can answer: treat fetched pages as data, not instructions.

### Excluded

| Excluded | Reason |
| --- | --- |
| Other `pm-*` plugins, `.claude-plugin/`, `validate_plugins.py`, `tests/` | Not part of this skill |

### Description trim (2026-10-24)

The frontmatter `description` was cut to about 350 characters to keep the skill listing short: trigger phrases kept, cross-references to skills outside the kit and body-level style rules dropped from the description (the body is unchanged). Recorded in `patches/upstream/create-prd.patch` (1 line changed).

## beachhead-segment

| Field | Value |
| --- | --- |
| Source | https://github.com/phuryn/pm-skills (path `pm-go-to-market/skills/beachhead-segment`, plus root `LICENSE`) |
| Commit | `07b34f64ee828df08953f505b7f747aef85ae7c6` (committed 2026-10-16T14:28:37+02:00; upstream HEAD on 2026-10-23: yes) |
| Licence | MIT (`LICENSE`, © 2026 Pawel Huryn) |
| Fetched | 2026-10-23, fetch of the commit above into a fresh directory; SHA re-verified |
| Copied | whole directory from a clone at the commit above, plus `LICENSE`, then `patches/upstream/beachhead-segment.patch` |
| Licence note | MIT; no third-party text inside |

### Reviewed (2026-10-23)

Files: `LICENSE`, `SKILL.md`.

Prose only: no scripts, no hooks, no network calls. Writes: the skill asks for its output to be saved as markdown in the working repository. Further Reading links point at productcompass.pm (the author's newsletter); the skill does not fetch them.

Flagged in the upstream text (kept unchanged; treat numbers inside a skill as unsourced unless a primary source is given):

- `SKILL.md` Tips: "Validate all four criteria with at least 10 customer interviews" is an unsourced rule of thumb (kept).

### Changes

`patches/upstream/beachhead-segment.patch`: 9 lines added, 7 removed. Changes by 72o Labs:

- Criterion 3 "Winnable Market Share" ("Can you realistically capture 60-70% of this segment in 3-18 months?", upstream `SKILL.md:35-36`) becomes "Winnability" with no share figure; Step 4 asks whether the segment can be won, not for market-share potential.
- Output: "Realistic market share and revenue projections" (upstream `SKILL.md:121`) deleted; scores must cite labelled evidence; open `[NEED: …]` items listed.
- New "Evidence Labels" section: every segment claim carries source, date and one of measured / user-provided / calculated / estimated / proxy; missing evidence is `[NEED: …]` and scored unknown; no market-share or revenue projections.
- Tips: "Plan exit from beachhead only after 60%+ market share" (upstream `SKILL.md:136`) deleted.
- Description: "winnable market share" becomes "winnability", plus "with an evidence label on every claim".

### Excluded

| Excluded | Reason |
| --- | --- |
| Other `pm-*` plugins, `.claude-plugin/`, `validate_plugins.py`, `tests/` | Not part of this skill |
