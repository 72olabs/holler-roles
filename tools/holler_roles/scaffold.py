"""new <name> [--display NAME]: scaffold a role. Writes profiles/<name>.md and layers/function/<name>.md into the overlay
when one is set, else into this repository. Never overwrites. The result builds as-is; edit the role text, the skills
and the rules before you rely on it."""
import os

import common
from common import die, load_team, write
from kits import NAME_RE

PROFILE = """---
profile_format: 1
name: {name}
version: {version}                 # every agent in a bundle carries the team version (team.json)
display_name: {display}
role: One line on what {display} does.
harnesses: [claude, codex]

layers:                          # brief, in order: base rules, the Holler platform layer, this role's rules
  - base
  - platform/holler
  - function/{name}

skills:                          # listed: the model sees and may invoke them. <kit>/<skill>, own/<skill> or holler/<skill>
  - holler/holler-handoff
  - holler/holler-review-request
  - holler/holler-decision-request
manual:                          # user-invoked only (/name)
  - holler/holler-team-setup
  - holler/holler-teach

hooks: []                        # guards (Claude PreToolUse): own/<hook> or <kit>/<hook>
never: []                        # names the build refuses to ship

holler:                          # the Holler card the session publishes
  actor: {name}                  # must equal name: Holler's runtime starts the agent under this actor base
  role_text: >-
    {display} agent. Say what it does, what it never does, and what a request to it should contain.
  accepts:
    - "a request {display} handles, in a few words"
---

# {display}

## Responsibilities

- What this agent is for, one line each.

## Rules

- What it always or never does. Rules and done criteria only; no persona or backstory.

## Done criteria

- What has to be true, and reported, before it says a task is done.
"""

FUNCTION = """# {display} rules

Rules that make this role different from the others: its gate (what it may change), how it works, and which skills it
reaches for. Keep the whole brief under 9,800 characters (`holler-roles build` checks).

Brief marker: {name} agent brief.
"""


def cmd_new(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 1:
        die("usage: holler-roles new <name> [--display NAME]")
    name = args[0]
    if not NAME_RE.match(name) or len(name) > 64:
        die(f"bad role name {name!r}: lowercase letters, digits and dashes, starting with a letter")
    display = argv[argv.index("--display") + 1] if "--display" in argv else name.replace("-", " ").title()
    root = common.OVERLAY or common.ROOT
    profile = os.path.join(root, "profiles", f"{name}.md")
    layer = os.path.join(root, "layers", "function", f"{name}.md")
    for p in (profile, layer):
        if os.path.exists(p):
            die(f"{p} exists; not overwriting")
    if os.path.isfile(os.path.join(common.ROOT, "profiles", f"{name}.md")) and common.OVERLAY:
        print(f"note: the overlay's {name} replaces this repository's {name} profile in overlay builds")
    version = load_team()["release_version"]
    write(profile, PROFILE.format(name=name, display=display, version=version))
    write(layer, FUNCTION.format(name=name, display=display))
    print(profile)
    print(layer)
    if common.OVERLAY:
        print("next: holler-roles build --overlay <dir>; then home/launch with the same --overlay")
    else:
        print(f"next: add {name} to team.json agents, then holler-roles build")
    return 0
