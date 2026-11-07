# Notices

`skills/growth-gate` is a pre-publish draft gate written by 72o Labs that adapts MIT-licensed material,
so it is distributed under the MIT License with both upstream licences:

- AI-tell pattern names and the ban/cap split, re-expressed as regular expressions, from marketingskills
  `skills/copywriting/references/ai-tells.md` (https://github.com/coreyhaines31/marketingskills, commit
  `e85f3cbc2e4a79bf33b2a12e9bdd9087d414735b`), MIT, Copyright (c) 2025 Corey Haines
  (`LICENSE-marketingskills`).
- Word tiers, the "risky number without a nearby source marker" rule and the Four U's rubric with its
  thresholds, from kai-cmo-harness `scripts/quality_gates/` (`banned_word_check.py`,
  `audit_provenance_lint.py`, `four_us_score.py`; https://github.com/cgallic/kai-cmo-harness, commit
  `5f2dab2453069277d133ae1b19df22f6e173152f`, the MIT-licensed directory of a dual-licensed repository),
  MIT, Copyright (c) 2026 Connor Gallic (`LICENSE-kai-quality-gates`). No kai code was copied and
  nothing from kai's Elastic-licensed directories was used.

The script is Python 3 standard library only, reads the files it is given, writes nothing and makes no
network calls. The skill is new work by 72o Labs, not an edited copy of an upstream file, so there are no
patches; PROVENANCE.md describes what was taken from each source. `LICENSE-marketingskills` and
`LICENSE-kai-quality-gates` are the upstream licence files, unchanged.
