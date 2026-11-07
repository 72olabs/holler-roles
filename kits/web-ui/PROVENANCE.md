# Provenance: web-ui

Kit `web-ui` 1.0.0, licence Apache-2.0. Assembled on 2026-10-24 by 72o Labs from the upstream
repository below at the pinned commit. Contents keep their original licences.

| Upstream | URL | Commit | Licence | Path |
| --- | --- | --- | --- | --- |
| anthropics/skills | https://github.com/anthropics/skills | `dbd4588f9e1033efb41dad4bef2f7947c8993d44` | Apache-2.0 | `skills/frontend-design` |

## Changes

- `patches/upstream/<skill>.patch`: diff from the pristine upstream files at the pinned commit to this kit.
  Apply with `patch -p1` from the root of an upstream checkout at that commit.
- Files not named in a patch are byte-identical to upstream.
- NOTICE.md and the records below state every change in prose.

## Item records

## frontend-design

| Field | Value |
| --- | --- |
| Source | https://github.com/anthropics/skills (path `skills/frontend-design`) |
| Commit | `dbd4588f9e1033efb41dad4bef2f7947c8993d44` (repo HEAD 2026-10-09; this directory last changed in `41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f`, 2026-09-03) |
| Licence | Apache-2.0 (`LICENSE.txt`) |
| Licence note | Apache-2.0: carry `LICENSE.txt`; the modified copy carries a change notice |
| Fetched | 2026-10-23, `git clone` of the source, HEAD as above |
| Copied | Whole directory from a clone at the commit above; then `patches/upstream/frontend-design.patch` |

### Reviewed

`SKILL.md` (prose guidance on visual direction) and `LICENSE.txt`. No scripts, no hooks, no network calls, no writes.

### Edit (2026-10-23)

One change by 72o Labs: the persona paragraph "Approach this as the design lead at a design studio ... take aesthetic risk if justified." is removed, so the skill carries no persona text. An HTML comment after the frontmatter records the change, as Apache-2.0 §4(b) requires. `LICENSE.txt` is unchanged.

`patches/upstream/frontend-design.patch` is the diff from the upstream `SKILL.md` to this kit (2 lines added, 2 removed).

## webapp-testing

| Field | Value |
| --- | --- |
| Source | https://github.com/anthropics/skills (path `skills/webapp-testing`) |
| Commit | `dbd4588f9e1033efb41dad4bef2f7947c8993d44` (repo HEAD 2026-10-09; this directory last changed in `41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f`, 2026-09-03) |
| Licence | Apache-2.0 (`LICENSE.txt`) |
| Licence note | Apache-2.0: carry `LICENSE.txt` |
| Fetched | 2026-10-23, `git clone` of the source, HEAD as above |
| Copied | Whole directory from a clone at the commit above, unchanged |

### Security review (2026-10-23)

No hooks.

| File | Executes | Network | Writes outside the repo |
| --- | --- | --- | --- |
| `scripts/with_server.py` | **Runs each `--server` string with `shell=True`**, then runs the trailing command, then terminates the servers. By design: it starts dev servers the agent names | Polls `localhost:<port>` only | None by itself; the commands it runs can do anything the shell can |
| `examples/element_discovery.py`, `examples/static_html_automation.py` | Playwright Chromium, headless | Loads `localhost:5173` or a `file://` URL | None |
| `examples/console_logging.py` | Playwright Chromium, headless | Loads `localhost:5173` | **Writes `/mnt/user-data/outputs/console.log`** (a claude.ai sandbox path; on macOS the open fails). Example only; not run by the skill |

Requires the Python `playwright` package and its browsers, which are not installed by the skill. `with_server.py` gives no more power than the Bash tool already has, but it hides the server commands inside one call: review the `--server` strings before approving it.
