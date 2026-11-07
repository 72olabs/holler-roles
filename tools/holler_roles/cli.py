"""holler-roles: build Holler's agents from role profiles and pinned kits, and link them into Claude Code or Codex.

  holler-roles list                              agents, versions, listing sizes
  holler-roles new <name> [--display NAME]       scaffold a role: profiles/<name>.md and layers/function/<name>.md
                                                  (in the overlay when one is set; refuses to overwrite)
  holler-roles lock                              pin kits.lock to the kits checkout's HEAD and kit hashes
  holler-roles build [agent...|all] [--force]    dist/<bundle>/ and, for the whole team, dist/<bundle>.tar.gz
  holler-roles verify [--no-codex]               kits pin and licences, bundle hashes, launch contract, plugins,
                                                  Codex listing, reproducibility
  holler-roles home <agent> <dest> [--project DIR]
                                                  make a per-agent Codex home from the template (reference launcher)
  holler-roles launch <agent> claude|codex [--home DIR] [--print] [-- args...]
                                                  start the agent with its launch.json environment
  holler-roles export <dest> [--deny FILE]       copy the public tree (PUBLIC.txt) into an empty folder, then scan it
                                                  for home paths, secrets and denied words

Every command takes --overlay DIR (or HOLLER_ROLES_OVERLAY): your own profiles, layers, skills and personal layers,
kept outside this repository (spec/OVERLAY.md). Overlay builds go to dist/local/ and never replace a release.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common  # noqa: E402
from common import BuildError, DIST, set_overlay  # noqa: E402


def cmd_list(argv):
    from build import agent_names, dist_root, read_profile
    for n in agent_names():
        p, _ = read_profile(n)
        built = sorted(os.listdir(os.path.join(DIST, n))) if os.path.isdir(os.path.join(DIST, n)) else []
        pres = p.get("presentation") or {}
        print(f"{n:9} {p['version']:7} {pres.get('display_name') or p['display_name']:9} listed {len(p['skills']):2}  manual {len(p['manual']):2}  "
              f"hooks {','.join(p['hooks']) or '-':24} actor {p['holler']['actor']:9} built {','.join(built) or '-'}")
    if common.OVERLAY:
        print(f"overlay {common.OVERLAY}; builds go to {os.path.relpath(dist_root(), common.ROOT)}/")
    return 0


def take_overlay(argv):
    """Strip --overlay DIR from argv; the flag wins over HOLLER_ROLES_OVERLAY."""
    path = os.environ.get("HOLLER_ROLES_OVERLAY") or None
    out = []
    i = 0
    while i < len(argv):
        if argv[i] == "--overlay":
            if i + 1 >= len(argv):
                common.die("--overlay needs a folder")
            path = argv[i + 1]
            i += 2
            continue
        if argv[i].startswith("--overlay="):
            path = argv[i].split("=", 1)[1]
            i += 1
            continue
        out.append(argv[i])
        i += 1
    set_overlay(path)
    return out


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0 if argv else 2
    cmd = argv[0]
    try:
        rest = take_overlay(argv[1:])
        if cmd == "list":
            return cmd_list(rest)
        if cmd == "new":
            from scaffold import cmd_new
            return cmd_new(rest)
        if cmd == "lock":
            from kits import cmd_lock
            return cmd_lock(rest)
        if cmd == "build":
            from build import cmd_build
            return cmd_build(rest)
        if cmd == "verify":
            from verify import cmd_verify
            return cmd_verify(rest)
        if cmd == "home":
            from home import cmd_home
            return cmd_home(rest)
        if cmd == "launch":
            from home import cmd_launch
            return cmd_launch(rest)
        if cmd == "export":
            from export import cmd_export
            return cmd_export(rest)
    except BuildError as e:
        print(e.code, file=sys.stderr)
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
