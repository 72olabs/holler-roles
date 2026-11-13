# Contributing

Thanks for helping. Three kinds of change are welcome: a new or better role (a profile and its layers), an
original skill or guard, and fixes to the build, the specs or the reference launcher.

## How this repository is made

This repository is a generated copy. Its files are kept in a private source repository together with the rest of
Holler, and each update here is one commit exported from there (`bin/holler-roles export` makes the copy and scans it
for leaks). Pull requests are welcome all the same: a maintainer reviews yours here, applies it to the source by hand
with you credited as co-author, and closes it when the next export carries the change. Issues are read here too.

## Before you open a pull request

```sh
bin/holler-roles build && bin/holler-roles verify --no-codex
python3 -m unittest discover -s tests -v
```

`verify` without `--no-codex` also renders Codex's skill listing offline when `codex` is installed. For a change
to a brief or a skill's wording, also run the one-model load check on the cheapest model:
`python3 -I tests/live_check.py <agent> claude <out-dir>`.

## Rules for each kind of change

- **A role.** A profile in `profiles/` (spec/AGENT-PROFILE.md) and its function layer in `layers/function/`.
  `holler-roles new <name>` scaffolds both. Briefs are rules and done criteria, never persona or backstory, and
  name no user, company or product. Keep every listed skill earning its place: at most about 16.
- **A version.** Any change that alters the build output bumps `team.json` and every profile to the same new
  version: Holler's runtime accepts a bundle only when every agent carries the bundle's version.
- **An original skill or guard.** `skills/<name>/SKILL.md` or `hooks/<name>/` with `hook.json` and tests
  (`tests/run_cases.py`). A guard without tests does not ship. Guards are convenience, not a security boundary:
  say what they do not catch in their `SPEC.md`.
- **A third-party skill.** It goes under `kits/<kit>/` as a kit (spec/KIT.md), with its upstream licence files,
  NOTICE.md, PROVENANCE.md and patches, never into `skills/`. Then `bin/holler-roles lock`. A change to an
  existing kit updates its patch and NOTICE.md in the same pull request. The build accepts only permissive
  licences (`tools/holler_roles/kits.py`).
- **The coordination layer** (`layers/platform/holler.md`, `skills/holler-*`) follows the Holler release that
  introduces a capability. Propose changes to it in an issue first.

Never include personal configuration, transcripts, tokens or absolute paths from your machine. Your own
preferences belong in an overlay (spec/OVERLAY.md), which stays on your machine.

Contributions to this repository are provided under Apache-2.0. The separately distributed Holler core keeps
its own licence.
