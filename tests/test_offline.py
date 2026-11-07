"""Offline tests for the build: licences, overlays, the scaffold and the public export. No model calls.

    python3 -m unittest discover -s tests -v

Tests that build need every kit to match kits.lock; they are skipped otherwise.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "holler_roles"))

import common  # noqa: E402
from common import BuildError  # noqa: E402


def kits_ready():
    try:
        from kits import load_kits
        load_kits(verify=True)
        return True
    except BuildError:
        return False


class Overlay:
    """A temporary overlay folder, set for the duration of a with-block."""

    def __enter__(self):
        self.dir = tempfile.mkdtemp(prefix="holler-roles-test-overlay-")
        common.set_overlay(self.dir)
        return self

    def write(self, rel, text):
        path = os.path.join(self.dir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)

    def __exit__(self, *exc):
        common.set_overlay(None)
        shutil.rmtree(self.dir, ignore_errors=True)


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args)


class LicenceTests(unittest.TestCase):
    def test_allowed_and_refused(self):
        from kits import check_licence
        for ok in ("MIT", "Apache-2.0", "MIT AND Apache-2.0", "(MIT OR BSD-3-Clause)", "LicenseRef-acme"):
            check_licence(ok, "test")
        for bad in ("NOASSERTION", "GPL-3.0-only", "MIT AND AGPL-3.0", "", None, "CC-BY-NC-4.0"):
            with self.assertRaises(BuildError, msg=bad):
                check_licence(bad, "test")


class KitTests(unittest.TestCase):
    def kit(self, ov, name, licence="MIT"):
        ov.write(f"kits/{name}/LICENSE", "MIT License\n")
        ov.write(f"kits/{name}/NOTICE.md", "notice\n")
        ov.write(f"kits/{name}/skills/hello/SKILL.md", "---\nname: hello\ndescription: Say hello.\n---\nHello.\n")
        ov.write(f"kits/{name}/kit.json", json.dumps({
            "kit_format": 1, "name": name, "version": "1.0.0", "description": "Test kit.", "upstream": "https://example.com",
            "sha": "0" * 40, "licence": licence, "upstreams": [{"name": name, "url": "https://example.com", "sha": "0" * 40,
                                                              "licence": licence, "path": "."}],
            "licence_files": ["LICENSE"], "notices": ["NOTICE.md"], "bundle": "skills",
            "skills": [{"name": "hello", "path": "skills/hello", "description": "Say hello."}]}))

    @unittest.skipUnless(kits_ready(), "kits do not match kits.lock")
    def test_overlay_kit_is_loaded_and_licence_checked(self):
        from kits import load_kits
        with Overlay() as ov:
            self.kit(ov, "mine")
            self.assertEqual(load_kits()["mine"][2], "overlay")
            self.kit(ov, "mine", licence="NOASSERTION")
            with self.assertRaises(BuildError):
                load_kits()

    @unittest.skipUnless(kits_ready(), "kits do not match kits.lock")
    def test_kit_cannot_take_the_platform_plugin_name(self):
        from kits import load_kits
        with Overlay() as ov:
            self.kit(ov, "holler-platform")
            with self.assertRaisesRegex(BuildError, "can't use it"):
                load_kits()

    @unittest.skipUnless(kits_ready(), "kits do not match kits.lock")
    def test_overlay_kit_cannot_shadow_a_repository_kit(self):
        from kits import load_kits
        with Overlay() as ov:
            self.kit(ov, "pstack")
            with self.assertRaisesRegex(BuildError, "two sources"):
                load_kits()

    def test_tampered_kit_fails_the_hash(self):
        import kits as kits_mod
        lock = kits_mod.load_lock()
        name = sorted(lock["kits"])[0]
        tmp = tempfile.mkdtemp(prefix="holler-roles-test-kits-")
        self.addCleanup(shutil.rmtree, tmp, True)
        shutil.copytree(os.path.join(ROOT, "kits", name), os.path.join(tmp, "kits", name))
        self.assertEqual(kits_mod.kit_hash(os.path.join(tmp, "kits", name)), lock["kits"][name]["content_hash"])
        with open(os.path.join(tmp, "kits", name, "NOTICE.md"), "a") as f:
            f.write("an unrecorded change\n")
        self.assertNotEqual(kits_mod.kit_hash(os.path.join(tmp, "kits", name)), lock["kits"][name]["content_hash"])


class OverlayTeamTests(unittest.TestCase):
    def test_release_team_has_no_local_version(self):
        team = common.load_team()
        self.assertEqual(team["name"], "starter-team")
        self.assertNotIn("+local", team["version"])

    def test_overlay_team_version_and_agents(self):
        with Overlay() as ov:
            ov.write("profiles/extra.md", "---\n---\n")
            team = common.load_team()
            self.assertTrue(team["version"].startswith(team["release_version"] + "+local."))
            self.assertEqual(team["agents"][-1], "extra")
            ov.write("team.json", json.dumps({"agents": ["eng"]}))
            self.assertEqual(common.load_team()["agents"], ["eng"])
            ov.write("team.json", json.dumps({"agents": ["eng"], "name": "mine"}))
            with self.assertRaises(BuildError):
                common.load_team()

    def test_overlay_must_be_outside_the_repository(self):
        with self.assertRaises(BuildError):
            common.set_overlay(os.path.join(ROOT, "profiles"))
        common.set_overlay(None)

    def test_overlay_wins_over_repository(self):
        with Overlay() as ov:
            self.assertEqual(common.source_path("layers", "base.md"), os.path.join(ROOT, "layers", "base.md"))
            ov.write("layers/base.md", "mine")
            self.assertEqual(common.source_path("layers", "base.md"), os.path.join(common.OVERLAY, "layers", "base.md"))


@unittest.skipUnless(kits_ready(), "kits do not match kits.lock")
class OverlayBuildTests(unittest.TestCase):
    def build(self, ov):
        from build import build_all
        out = tempfile.mkdtemp(prefix="holler-roles-test-dist-")
        self.addCleanup(shutil.rmtree, out, True)
        results, tar, bundle = quiet(build_all, common.load_team()["agents"], out, False)
        return results, tar, bundle

    def test_new_role_with_personal_layer(self):
        from scaffold import cmd_new
        with Overlay() as ov:
            quiet(cmd_new, ["helper", "--display", "Helper"])
            ov.write("team.json", json.dumps({"agents": ["helper"]}))
            ov.write("personal/helper.md", "Answer in short paragraphs.\n")
            results, tar, bundle = self.build(ov)
            self.assertIsNotNone(tar, "a whole-team build writes the tarball")
            man = json.loads(common.read(os.path.join(bundle, "manifest.json")))
            launch = json.loads(common.read(os.path.join(bundle, "helper", "launch.json")))
            self.assertIn("+local.", man["version"])
            self.assertEqual(launch["version"], man["version"])
            self.assertEqual(man["agents"][0]["version"], man["version"])
            self.assertEqual(man["source"]["overlay"], common.overlay_hash())
            brief = common.read(os.path.join(bundle, "helper", "claude", "plugins", "helper", "brief.md"))
            self.assertTrue(brief.rstrip().endswith("Answer in short paragraphs."))
            self.assertIn("## Personal layer", brief)
            agents_md = common.read(os.path.join(bundle, "helper", "codex", "home-template", "AGENTS.md"))
            self.assertIn("Answer in short paragraphs.", agents_md)

    def test_overlay_dotfiles_are_not_built(self):
        from scaffold import cmd_new
        with Overlay() as ov:
            quiet(cmd_new, ["helper"])
            prof = os.path.join(ov.dir, "profiles", "helper.md")
            text = common.read(prof).replace("  - holler/holler-handoff\n", "  - holler/holler-handoff\n  - own/notes\n")
            ov.write("profiles/helper.md", text)
            ov.write("skills/notes/SKILL.md", "---\nname: notes\ndescription: Take notes.\n---\nNotes.\n")
            ov.write("skills/notes/.env", "TOKEN=private\n")
            ov.write("skills/notes/.cache/x.txt", "private\n")
            ov.write("team.json", json.dumps({"agents": ["helper"]}))
            results, tar, bundle = self.build(ov)
            files = [os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(bundle, "helper")) for f in fs]
            self.assertTrue(any(f.endswith(os.path.join("notes", "SKILL.md")) for f in files))
            self.assertFalse([f for f in files if ".env" in f or ".cache" in f], "overlay dotfiles must not be built")

    def test_symlink_inside_an_ignored_dot_folder_is_ignored(self):
        with Overlay() as ov:
            ov.write(".venv/lib/x.py", "x = 1\n")
            os.symlink("lib", os.path.join(ov.dir, ".venv", "lib64"))
            ov.write("personal/eng.md", "Short replies.\n")
            common.load_team()          # no "symlinked directory" error
            self.assertTrue(common.overlay_hash().startswith("sha256:"))

    def test_ignored_files_in_an_overlay_kit_change_nothing(self):
        from build import build_all
        with Overlay() as ov:
            KitTests.kit(None, ov, "mine")
            quiet(__import__("scaffold").cmd_new, ["helper"])
            prof = os.path.join(ov.dir, "profiles", "helper.md")
            ov.write("profiles/helper.md", common.read(prof).replace("  - holler/holler-handoff\n", "  - holler/holler-handoff\n  - mine/hello\n"))
            ov.write("team.json", json.dumps({"agents": ["helper"]}))
            shas = []
            for secret in ("", "TOKEN=one\n"):
                if secret:
                    ov.write("kits/mine/.env", secret)
                    ov.write("kits/mine/skills/hello/.cache/x", secret)
                out = tempfile.mkdtemp(prefix="holler-roles-test-dist-")
                self.addCleanup(shutil.rmtree, out, True)
                _, tar, bundle = quiet(build_all, ["helper"], out, False)
                shas.append(tar[1])
                self.assertFalse([f for dp, _, fs in os.walk(bundle) for f in fs if f == ".env" or dp.endswith(".cache")])
            self.assertEqual(shas[0], shas[1], "a change to ignored overlay files must not change the bundle")

    def test_overlay_hash_covers_the_executable_bit(self):
        with Overlay() as ov:
            ov.write("skills/notes/run.sh", "#!/bin/sh\n")
            before = common.overlay_hash()
            os.chmod(os.path.join(ov.dir, "skills", "notes", "run.sh"), 0o755)
            self.assertNotEqual(common.overlay_hash(), before)

    def test_hidden_overlay_profiles_are_ignored(self):
        with Overlay() as ov:
            ov.write("profiles/.draft.md", "not a profile\n")
            from build import agent_names
            self.assertNotIn(".draft", common.load_team()["agents"])
            self.assertNotIn(".draft", agent_names())

    def test_role_names_that_collide_are_refused(self):
        from scaffold import cmd_new
        with Overlay():
            for taken in ("holler-platform", "pstack"):
                with self.subTest(taken), self.assertRaisesRegex(BuildError, "taken"):
                    quiet(cmd_new, [taken])

    def test_actor_must_equal_the_name(self):
        from build import read_profile
        from scaffold import cmd_new
        with Overlay() as ov:
            quiet(cmd_new, ["helper"])
            prof = os.path.join(ov.dir, "profiles", "helper.md")
            ov.write("profiles/helper.md", common.read(prof).replace("  actor: helper", "  actor: eng"))
            with self.assertRaisesRegex(BuildError, "must equal the name"):
                read_profile("helper")

    def test_scaffold_refuses_to_overwrite(self):
        from scaffold import cmd_new
        with Overlay():
            quiet(cmd_new, ["helper"])
            with self.assertRaises(BuildError):
                quiet(cmd_new, ["helper"])

    def test_absolute_overlay_path_is_refused(self):
        from scaffold import cmd_new
        with Overlay() as ov:
            quiet(cmd_new, ["helper"])
            ov.write("team.json", json.dumps({"agents": ["helper"]}))
            ov.write("personal/helper.md", f"My notes are in {ov.dir}/notes.\n")
            with self.assertRaisesRegex(BuildError, "absolute build path"):
                self.build(ov)


MCP_GOOD = """mcp:
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github@2025.4.8"]
    env: [GITHUB_PERSONAL_ACCESS_TOKEN]
  fetch:
    command: uvx
    args: ["mcp-server-fetch==2025.4.7", "--ignore-robots-txt"]
  git:
    command: uvx
    args: ["--from", "mcp-server-git==2025.1.14", "mcp-server-git"]
    env: [GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL]
"""


def with_mcp(ov, block):
    """Scaffold the helper role in the overlay with an mcp block in its profile."""
    from scaffold import cmd_new
    if not os.path.isfile(os.path.join(ov.dir, "profiles", "helper.md")):
        quiet(cmd_new, ["helper", "--display", "Helper"])
        ov.write("team.json", json.dumps({"agents": ["helper"]}))
    path = os.path.join(ov.dir, "profiles", "helper.md")
    text = common.read(path)
    if "\nmcp:" in text:
        text = text[:text.index("\nmcp:") + 1] + text[text.index("\nholler:") + 1:]
    ov.write("profiles/helper.md", text.replace("\nholler:", "\n" + block + "\nholler:", 1))


class McpRuleTests(unittest.TestCase):
    """Every refusal of the bundled-MCP contract (spec/AGENT-PROFILE.md), checked when the profile is read."""

    def refuse(self, block, pattern):
        from build import read_profile
        with Overlay() as ov:
            with_mcp(ov, block)
            with self.assertRaisesRegex(BuildError, pattern):
                read_profile("helper")

    def server(self, command, args, env=None, name="srv", extra=""):
        lines = [f"mcp:", f"  {name}:", f"    command: {command}", f"    args: {json.dumps(args)}"]
        if env is not None:
            lines.append(f"    env: {json.dumps(env)}")
        return "\n".join(lines) + ("\n" + extra if extra else "") + "\n"

    def test_valid_servers_read(self):
        from build import read_profile
        with Overlay() as ov:
            with_mcp(ov, MCP_GOOD)
            p, _ = read_profile("helper")
            self.assertEqual(sorted(p["mcp"]), ["fetch", "git", "github"])
            self.assertEqual(p["mcp"]["git"]["env"], ["GIT_AUTHOR_EMAIL", "GIT_AUTHOR_NAME"])
            self.assertEqual(p["mcp"]["fetch"]["env"], [])

    def test_npx_refusals(self):
        cases = {
            "unpinned": ["-y", "@modelcontextprotocol/server-github"],
            "latest": ["-y", "@modelcontextprotocol/server-github@latest"],
            "caret range": ["-y", "server-x@^1.2.3"],
            "x range": ["-y", "server-x@1.x"],
            "partial": ["-y", "server-x@1.2"],
            "url": ["-y", "https://example.com/x.tgz"],
            "git ref": ["-y", "github:owner/repo"],
            "path": ["-y", "./local-server"],
            "option before package": ["--registry=https://example.com", "server-x@1.2.3"],
            "package flag": ["-y", "-p", "server-x@1.2.3", "x"],
            "registry after": ["-y", "server-x@1.2.3", "--registry", "https://example.com"],
            "prefix after": ["-y", "server-x@1.2.3", "--prefix=/tmp"],
            "double dash": ["-y", "server-x@1.2.3", "--"],
            "no package": ["-y"],
            "archive .tgz": ["-y", "foo@1.0.0-x.tgz"],
            "archive .tar scoped": ["-y", "@s/foo@1.0.0-a.tar"],
            "archive .tar.gz": ["-y", "foo@1.0.0-x.tar.gz"],
            "archive .TGZ": ["-y", "foo@1.0.0-x.TGZ"],
            "leading zero": ["-y", "server-x@01.2.3"],
            "build metadata": ["-y", "server-x@1.2.3+build.1"],
            "empty prerelease identifier": ["-y", "server-x@1.2.3-rc..1"],
            "trailing newline": ["-y", "server-x@1.2.3\n"],
            "uppercase name": ["-y", "Server-X@1.2.3"],
            "--package after": ["-y", "server-x@1.2.3", "--package=y@1.0.0"],
            "--userconfig after": ["-y", "server-x@1.2.3", "--userconfig=/x"],
            "major above safe integer": ["-y", "server-x@99999999999999999999.0.0"],
            "patch above safe integer": ["-y", "server-x@1.0.99999999999999999999"],
            "16-digit minor": ["-y", "server-x@1.1000000000000000.0"],
            "leading-zero numeric prerelease": ["-y", "server-x@1.0.0-01"],
            "-c shell command": ["-y", "server-x@1.2.3", "-c", "echo hi"],
            "--call shell command": ["-y", "server-x@1.2.3", "--call", "echo hi"],
            "--call= shell command": ["-y", "server-x@1.2.3", "--call=echo hi"],
        }
        for label, args in cases.items():
            with self.subTest(label):
                self.refuse(self.server("npx", args), "mcp server srv: npx")

    def test_rule_edges_at_the_check_level(self):
        import mcp_servers
        npx = ["-y", "server-x@1.2.3"]
        ok = {"command": "npx", "args": npx + ["\u00e9" * 128]}          # 256 bytes: allowed
        self.assertIsNone(mcp_servers.server_problem("srv", ok))
        self.assertIsNone(mcp_servers.server_problem("s" * 32, {"command": "npx", "args": npx}))
        for ok_version in ("999999999999999.0.999999999999999", "1.0.0-99999999999999999999", "1.0.0-rc.1", "1.0.0-0.3.7"):
            self.assertIsNone(mcp_servers.server_problem("srv", {"command": "npx", "args": ["-y", "server-x@" + ok_version]}), ok_version)
        self.assertIsNone(mcp_servers.server_problem("srv", {"command": "npx", "args": npx, "env": ["A" * 64]}))
        for label, spec in {"NUL in arg": {"command": "npx", "args": npx + ["a\x00b"]},
                            "257 bytes": {"command": "npx", "args": npx + ["\u00e9" * 129]},
                            "empty arg": {"command": "npx", "args": npx + [""]},
                            "args not a list": {"command": "npx", "args": "-y server-x@1.2.3"},
                            "env not a list": {"command": "npx", "args": npx, "env": "A"}}.items():
            with self.subTest(label):
                self.assertIsNotNone(mcp_servers.server_problem("srv", spec))

    def test_uvx_refusals(self):
        cases = {
            "unpinned": (["mcp-server-fetch"], "exact version"),
            "range": (["mcp-server-fetch>=1.0.0"], "exact version"),
            "extra flag": (["--python", "3.12", "mcp-server-fetch==1.0.0"], "not allowed"),
            "flag after from": (["--from", "mcp-server-git==1.0.0", "--with", "x"], "plain executable"),
            "from unpinned": (["--from", "mcp-server-git", "mcp-server-git"], "exact version"),
            "from without command": (["--from", "mcp-server-git==1.0.0"], "needs"),
            "extras": (["mcp-server-fetch[cli]==1.0.0"], "exact version"),
            "pep 440 prerelease": (["mcp-server-fetch==1.0.0rc1"], "exact version"),
            "semver prerelease": (["mcp-server-fetch==1.0.0-rc.1"], "exact version"),
            "leading zero": (["mcp-server-fetch==1.02.0"], "exact version"),
            "16-digit major": (["mcp-server-fetch==1000000000000000.0.0"], "exact version"),
            "trailing newline": (["mcp-server-fetch==1.0.0\n"], "exact version"),
            "long from command": (["--from", "mcp-server-git==1.0.0", "x" * 65], "plain executable"),
            "git url": (["git+https://example.com/x"], "exact version"),
        }
        for label, (args, pattern) in cases.items():
            with self.subTest(label):
                self.refuse(self.server("uvx", args), pattern)

    def test_command_env_name_and_shape_refusals(self):
        npx = ["-y", "server-x@1.2.3"]
        cases = {
            "path command": (self.server("/usr/local/bin/npx", npx), "exactly npx or uvx"),
            "node": (self.server("node", ["server.js"]), "exactly npx or uvx"),
            "bunx": (self.server("bunx", npx), "exactly npx or uvx"),
            "lowercase env": (self.server("npx", npx, ["github_token"]), "env name"),
            "env value": (self.server("npx", npx, ["TOKEN=abc"]), "env name"),
            "repeated env": (self.server("npx", npx, ["A", "A"]), "repeat"),
            "HOLLER_ env": (self.server("npx", npx, ["HOLLER_ACTOR"]), "reserved"),
            "CLAUDE_CODE_ env": (self.server("npx", npx, ["CLAUDE_CODE_ENTRYPOINT"]), "reserved"),
            "CLAUDECODE env": (self.server("npx", npx, ["CLAUDECODE"]), "reserved"),
            "CODEX_HOME env": (self.server("npx", npx, ["CODEX_HOME"]), "reserved"),
            "${ in npx arg": (self.server("npx", npx + ["--token=${GITHUB_TOKEN}"]), "would expand"),
            "${ in uvx arg": (self.server("uvx", ["mcp-server-fetch==1.0.0", "${HOME}"]), "would expand"),
            "too many env": (self.server("npx", npx, [f"V{i}" for i in range(17)]), "at most 16"),
            "holler": (self.server("npx", npx, name="holler"), "reserved"),
            "bad name": (self.server("npx", npx, name="Git_Hub"), "server name"),
            "unknown key": (self.server("npx", npx, extra="    cwd: /tmp"), "unknown keys"),
            "too many args": (self.server("npx", npx + ["a"] * 31), "at most 32"),
            "long arg": (self.server("npx", npx + ["a" * 257]), "1 to 256"),
            "number arg": ("mcp:\n  srv:\n    command: npx\n    args: [-y, server-x@1.2.3, 3000]\n", "1 to 256"),
            "too many servers": ("mcp:\n" + "".join(f"  s{i}:\n    command: npx\n    args: [-y, s@1.0.0]\n" for i in range(9)),
                                 "at most 8"),
            "not a mapping": ("mcp: [github]\n", "must be a mapping"),
            "empty list": ("mcp: []\n", "must be a mapping"),
            "empty string": ("mcp: ''\n", "must be a mapping"),
            "false": ("mcp: false\n", "must be a mapping"),
            "empty arg": (self.server("npx", npx + [""]), "1 to 256"),
            "257-byte multibyte arg": (self.server("npx", npx + ["\u00e9" * 129]), "1 to 256"),
            "long env name": (self.server("npx", npx, ["A" * 65]), "env name"),
            "long server name": (self.server("npx", npx, name="s" * 33), "server name"),
            "no args": (self.server("npx", []), "args must be a non-empty list"),
            "env not a list": ("mcp:\n  srv:\n    command: npx\n    args: [-y, server-x@1.2.3]\n    env: A\n", "env"),
        }
        for label, (block, pattern) in cases.items():
            with self.subTest(label):
                self.refuse(block, pattern)


MCP_REMOTE = """mcp:
  linear:
    url: https://mcp.linear.app/mcp
    bearer_token_env: LINEAR_API_KEY
  docs:
    url: https://docs.example.com
"""


class McpRemoteRuleTests(unittest.TestCase):
    def refuse(self, block, pattern):
        from build import read_profile
        with Overlay() as ov:
            with_mcp(ov, block)
            with self.assertRaisesRegex(BuildError, pattern):
                read_profile("helper")

    def test_remote_servers_read(self):
        from build import read_profile
        with Overlay() as ov:
            with_mcp(ov, MCP_REMOTE)
            p, _ = read_profile("helper")
            with_mcp(ov, "mcp:\n  deep:\n    url: https://mcp.eu-1.api.example-corp.co.uk/v1/mcp%2Fstream\n")
            self.assertEqual(read_profile("helper")[0]["mcp"]["deep"]["url"],
                             "https://mcp.eu-1.api.example-corp.co.uk/v1/mcp%2Fstream")
            self.assertEqual(p["mcp"], {"docs": {"url": "https://docs.example.com"},
                                        "linear": {"url": "https://mcp.linear.app/mcp", "bearer_token_env": "LINEAR_API_KEY"}})

    def test_remote_refusals(self):
        def remote(url, extra=""):
            return f"mcp:\n  srv:\n    url: {json.dumps(url)}\n" + extra
        cases = {
            "http": (remote("http://mcp.example.com/mcp"), "must start with https://"),
            "ipv4 host": (remote("https://203.0.113.7/mcp"), "DNS host"),
            "ipv6 host": (remote("https://[2001:db8::1]/mcp"), "IPv6"),
            "localhost": (remote("https://localhost/mcp"), "this machine"),
            "hex ipv4 last label": (remote("https://127.0x1/mcp"), "DNS host"),
            "hex ipv4 parts": (remote("https://0x7f.0x1/mcp"), "DNS host"),
            "hex metadata": (remote("https://169.254.169.0xfe/x"), "DNS host"),
            "digit-led tld": (remote("https://mcp.example.1com/mcp"), "DNS host"),
            "sub.localhost": (remote("https://mcp.localhost/mcp"), "this machine"),
            "userinfo": (remote("https://user:pw@mcp.example.com/mcp"), "@ or a backslash"),
            "uppercase host": (remote("https://MCP.Example.com/mcp"), "lowercase DNS host"),
            "single-label host": (remote("https://intranet/mcp"), "two or more labels"),
            "trailing-dot host": (remote("https://mcp.example.com./mcp"), "trailing dot"),
            "@ in path": (remote("https://mcp.example.com/@team/mcp"), "@ or a backslash"),
            "? alone": (remote("https://mcp.example.com/mcp?"), "query or fragment"),
            "backslash": (remote("https://mcp.example.com\\@evil.example/mcp"), "@ or a backslash"),
            "backslash in path": (remote("https://mcp.example.com/a\\b"), "@ or a backslash"),
            "bad percent-escape": (remote("https://mcp.example.com/a%zz"), "path"),
            "query": (remote("https://mcp.example.com/mcp?token=x"), "query or fragment"),
            "fragment": (remote("https://mcp.example.com/mcp#x"), "query or fragment"),
            "placeholder": (remote("https://mcp.example.com/${PATH_PART}"), "would expand"),
            "too long": (remote("https://mcp.example.com/" + "a" * 2030), "over 2048 bytes"),
            "mixed": (remote("https://mcp.example.com/mcp", "    command: npx\n    args: [-y, s@1.0.0]\n"), "mixes a remote"),
            "reserved bearer": (remote("https://mcp.example.com/mcp", "    bearer_token_env: HOLLER_TOKEN\n"), "reserved"),
            "bad bearer name": (remote("https://mcp.example.com/mcp", "    bearer_token_env: linear_key\n"), "bearer_token_env"),
            "bearer without url": ("mcp:\n  srv:\n    bearer_token_env: LINEAR_API_KEY\n", "needs url"),
            "unknown key": (remote("https://mcp.example.com/mcp", "    headers: {X: y}\n"), "unknown keys"),
        }
        for label, (block, pattern) in cases.items():
            with self.subTest(label):
                self.refuse(block, pattern)


@unittest.skipUnless(kits_ready(), "kits do not match kits.lock")
class McpBuildTests(unittest.TestCase):
    def build(self):
        from build import build_all
        out = tempfile.mkdtemp(prefix="holler-roles-test-dist-")
        self.addCleanup(shutil.rmtree, out, True)
        return quiet(build_all, common.load_team()["agents"], out, False)[2]

    def test_servers_reach_both_harnesses_and_the_manifest(self):
        import tomllib
        import verify
        with Overlay() as ov:
            with_mcp(ov, MCP_GOOD)
            bundle = self.build()
            agent = os.path.join(bundle, "helper")
            mcp_json = common.read(os.path.join(agent, "claude", "plugins", "helper", ".mcp.json"))
            servers = json.loads(mcp_json)["mcpServers"]
            self.assertEqual(servers["github"], {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github@2025.4.8"],
                                                 "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"}})
            self.assertEqual(servers["fetch"], {"command": "uvx", "args": ["mcp-server-fetch==2025.4.7", "--ignore-robots-txt"]})
            self.assertEqual(mcp_json, json.dumps(json.loads(mcp_json), indent=2, sort_keys=True) + "\n")
            found = [os.path.relpath(os.path.join(d, f), agent) for d, _, fs in os.walk(agent) for f in fs if f == ".mcp.json"]
            self.assertEqual(found, [os.path.join("claude", "plugins", "helper", ".mcp.json")])
            cfg_text = common.read(os.path.join(agent, "codex", "home-template", "config.toml"))
            cfg = tomllib.loads(cfg_text)
            self.assertEqual(cfg["mcp_servers"]["github"], {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github@2025.4.8"],
                                                            "env_vars": ["GITHUB_PERSONAL_ACCESS_TOKEN"]})
            self.assertEqual(cfg["mcp_servers"]["fetch"], {"command": "uvx", "args": ["mcp-server-fetch==2025.4.7", "--ignore-robots-txt"]})
            self.assertEqual(cfg["mcp_servers"]["git"]["args"], ["--from", "mcp-server-git==2025.1.14", "mcp-server-git"])
            self.assertEqual(cfg["features"], {"remote_plugin": False})
            # nothing pre-approves the servers' tools: no approval keys in the tables or at the top level
            self.assertTrue(all(set(s) <= {"command", "args", "env_vars"} for s in cfg["mcp_servers"].values()))
            self.assertNotIn("approval_policy", cfg)
            man = json.loads(common.read(os.path.join(agent, "MANIFEST.json")))
            self.assertEqual(man["mcp"]["github"], {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github@2025.4.8"],
                                                    "env": ["GITHUB_PERSONAL_ACCESS_TOKEN"]})
            launch = json.loads(common.read(os.path.join(agent, "launch.json")))
            self.assertNotIn("mcp", launch)
            self.assertNotIn("mcp", json.dumps(launch["harnesses"]))
            bad = []
            quiet(verify.check_mcp, bundle, "helper", os.path.join(agent, "claude", "plugins"), cfg, bad)
            self.assertEqual(bad, [])
            # verify catches a .mcp.json that drifts from the manifest
            with open(os.path.join(agent, "claude", "plugins", "helper", ".mcp.json"), "w") as f:
                f.write(json.dumps({"mcpServers": {"github": servers["github"]}}))
            quiet(verify.check_mcp, bundle, "helper", os.path.join(agent, "claude", "plugins"), cfg, bad)
            self.assertEqual(len(bad), 1)
            # ... and a plugin.json that declares mcpServers
            bad = []
            with open(os.path.join(agent, "claude", "plugins", "helper", ".mcp.json"), "w") as f:
                f.write(mcp_json)
            with open(os.path.join(agent, "claude", "plugins", "holler-platform", ".claude-plugin", "plugin.json"), "w") as f:
                f.write(json.dumps({"name": "holler-platform", "MCPServers": {}}))
            quiet(verify.check_mcp, bundle, "helper", os.path.join(agent, "claude", "plugins"), cfg, bad)
            self.assertEqual(len(bad), 1)
            self.assertIn("mcpServers", bad[0])
            # ... and an unparseable .mcp.json is reported, not a crash
            bad = []
            with open(os.path.join(agent, "claude", "plugins", "holler-platform", ".claude-plugin", "plugin.json"), "w") as f:
                f.write(json.dumps({"name": "holler-platform"}))
            with open(os.path.join(agent, "claude", "plugins", "helper", ".mcp.json"), "w") as f:
                f.write("{not json")
            quiet(verify.check_mcp, bundle, "helper", os.path.join(agent, "claude", "plugins"), cfg, bad)
            self.assertEqual(len(bad), 1)
            self.assertIn("not valid JSON", bad[0])

    def test_reference_launcher_locks_the_env_for_local_servers(self):
        import home
        for block, want in ((MCP_GOOD, {"CLAUDE_CODE_MCP_ALLOWLIST_ENV": "1"}), (MCP_REMOTE, {}), ("", {})):
            with self.subTest(block[:20] or "no mcp"), Overlay() as ov:
                with_mcp(ov, block)
                bundle = self.build()
                self.assertEqual(home.claude_mcp_env(bundle, "helper"), want)
        with Overlay() as ov:   # a .mcp.json that can't be read fails closed
            with_mcp(ov, MCP_REMOTE)
            bundle = self.build()
            with open(os.path.join(bundle, "helper", "claude", "plugins", "helper", ".mcp.json"), "w") as f:
                f.write("{not json")
            self.assertEqual(home.claude_mcp_env(bundle, "helper"), {"CLAUDE_CODE_MCP_ALLOWLIST_ENV": "1"})

    def test_remote_servers_exact_outputs(self):
        import tomllib
        import verify
        with Overlay() as ov:
            with_mcp(ov, MCP_REMOTE)
            bundle = self.build()
            agent = os.path.join(bundle, "helper")
            plugins = os.path.join(agent, "claude", "plugins")
            self.assertEqual(common.read(os.path.join(plugins, "helper", ".mcp.json")), json.dumps({"mcpServers": {
                "docs": {"type": "http", "url": "https://docs.example.com"},
                "linear": {"type": "http", "url": "https://mcp.linear.app/mcp",
                           "headers": {"Authorization": "Bearer ${LINEAR_API_KEY}"}}}}, indent=2, sort_keys=True) + "\n")
            cfg_text = common.read(os.path.join(agent, "codex", "home-template", "config.toml"))
            self.assertTrue(cfg_text.endswith('\n[mcp_servers.docs]\nurl = "https://docs.example.com"\n\n'
                                              '[mcp_servers.linear]\nurl = "https://mcp.linear.app/mcp"\n'
                                              'bearer_token_env_var = "LINEAR_API_KEY"\n'), cfg_text)
            cfg = tomllib.loads(cfg_text)
            man = json.loads(common.read(os.path.join(agent, "MANIFEST.json")))
            self.assertEqual(man["mcp"], {"docs": {"url": "https://docs.example.com"},
                                          "linear": {"url": "https://mcp.linear.app/mcp", "bearer_token_env": "LINEAR_API_KEY"}})
            bad = []
            quiet(verify.check_mcp, bundle, "helper", plugins, cfg, bad)
            self.assertEqual(bad, [])
            # verify checks remote servers by the same rules: a Codex table pointing at localhost is refused
            drift = dict(cfg, mcp_servers={"docs": {"url": "https://localhost/mcp"}, "linear": cfg["mcp_servers"]["linear"]})
            quiet(verify.check_mcp, bundle, "helper", plugins, drift, bad)
            self.assertEqual(len(bad), 1)
            self.assertIn("this machine", bad[0])
            # ... and a Claude header that carries anything but a passed-through bearer token
            bad = []
            mcp_path = os.path.join(plugins, "helper", ".mcp.json")
            good = common.read(mcp_path)
            with open(mcp_path, "w") as f:
                f.write(good.replace("Bearer ${LINEAR_API_KEY}", "Bearer lin_api_value"))
            quiet(verify.check_mcp, bundle, "helper", plugins, cfg, bad)
            self.assertEqual(len(bad), 1)
            self.assertIn("Authorization", bad[0])
            # an unreadable .claude-plugin/plugin.json in another plugin is refused, not skipped
            bad = []
            with open(mcp_path, "w") as f:
                f.write(good)
            with open(os.path.join(plugins, "holler-platform", ".claude-plugin", "plugin.json"), "w") as f:
                f.write("{not json")
            quiet(verify.check_mcp, bundle, "helper", plugins, cfg, bad)
            self.assertEqual(len(bad), 1)
            self.assertIn("not a readable JSON object", bad[0])

    def test_build_refuses_mcp_declared_outside_the_profile(self):
        # Overlay dotfiles are never built (spec/OVERLAY.md), so a dot-named declaration in an overlay skill does
        # not reach the output at all; a visible one is refused.
        for rel, text, refused in ((".MCP.json", '{"mcpServers": {}}', False),
                                   ("plugin.json", '{"mcpServers": {"x": {}}}', True),
                                   (".claude-plugin/plugin.json", "not json", False)):
            with self.subTest(rel), Overlay() as ov:
                with_mcp(ov, "")
                ov.write("skills/extra/SKILL.md", "---\nname: extra\ndescription: An extra skill.\n---\nExtra.\n")
                ov.write(f"skills/extra/{rel}", text)
                path = os.path.join(ov.dir, "profiles", "helper.md")
                ov.write("profiles/helper.md", common.read(path).replace("skills:", "skills:\n  - own/extra", 1))
                if refused:
                    with self.assertRaisesRegex(BuildError, "MCP servers declared outside the profile"):
                        self.build()
                    continue
                out = os.path.join(self.build(), "helper")
                built = [os.path.relpath(os.path.join(dp, f), out) for dp, _, fs in os.walk(out) for f in fs]
                self.assertFalse([b for b in built if b.endswith(os.path.join("extra", rel))],
                                 f"{rel} from an overlay skill must not be built")
                self.assertTrue([b for b in built if b.endswith(os.path.join("extra", "SKILL.md"))])

    def test_profile_without_mcp_has_no_servers(self):
        import tomllib
        with Overlay() as ov:
            with_mcp(ov, "")
            agent = os.path.join(self.build(), "helper")
            found = [f for _, _, fs in os.walk(agent) for f in fs if f == ".mcp.json"]
            self.assertEqual(found, [])
            self.assertNotIn("mcp_servers", tomllib.loads(common.read(os.path.join(agent, "codex", "home-template", "config.toml"))))
            self.assertNotIn("mcp", json.loads(common.read(os.path.join(agent, "MANIFEST.json"))))


class ExportScanTests(unittest.TestCase):
    def test_scan_flags_paths_secrets_private_names_and_words(self):
        from export import scan
        d = tempfile.mkdtemp(prefix="holler-roles-test-export-")
        self.addCleanup(shutil.rmtree, d, True)
        # built at run time so this file itself stays clean for the export scan
        lines = ["/" + "Users/" + "someone/x", "token " + "gh" + "p_" + "A" * 36, "see " + "SECRET" + "-PLAN.md",
                 "a " + "codename" + " here", "/" + "Users/you/fine and /" + "home/<user>/fine"]
        with open(os.path.join(d, "f.md"), "w") as f:
            f.write("\n".join(lines) + "\n")
        hits = scan(d, ["f.md"], {"SECRET-PLAN.md"}, ["codename"])
        kinds = sorted({h[2] for h in hits})
        self.assertEqual(kinds, ["credential-shaped", "denied word", "home path", "names a private file"])
        self.assertFalse([h for h in hits if h[1] == 5], "placeholders are allowed")

    def test_scan_reads_non_utf8_files_and_paths(self):
        from export import scan
        d = tempfile.mkdtemp(prefix="holler-roles-test-export-")
        self.addCleanup(shutil.rmtree, d, True)
        token = ("gh" + "p_" + "B" * 36).encode()
        with open(os.path.join(d, "latin1.txt"), "wb") as f:
            f.write(b"caf\xe9 " + token + b"\n")
        folder = "codename" + "-notes"
        os.makedirs(os.path.join(d, folder))
        with open(os.path.join(d, folder, "SKILL.md"), "w") as f:
            f.write("clean text\n")
        with open(os.path.join(d, "ids.md"), "w") as f:
            f.write("relayed as " + "msg" + "_a2b3038a" + "ff\n")
        hits = scan(d, ["latin1.txt", folder + "/SKILL.md", "ids.md"], set(), ["codename"])
        self.assertIn(("latin1.txt", "credential-shaped"), {(h[0], h[2]) for h in hits})
        self.assertIn((folder + "/SKILL.md", 0, "denied word"), {(h[0], h[1], h[2]) for h in hits})
        self.assertIn(("ids.md", "internal Holler id"), {(h[0], h[2]) for h in hits})

    def test_scan_finds_openai_keys_with_url_safe_characters(self):
        from export import scan
        d = tempfile.mkdtemp(prefix="holler-roles-test-export-")
        self.addCleanup(shutil.rmtree, d, True)
        body = "A" * 12
        with open(os.path.join(d, "keys.md"), "w") as f:
            f.write("sk-" + "proj-" + body + "_" + "B" * 30 + "\n" + "sk-" + body + "-" + "C" * 30 + "\n")
        hits = [h for h in scan(d, ["keys.md"], set(), []) if h[2] == "credential-shaped"]
        self.assertEqual(sorted(h[1] for h in hits), [1, 2])


if __name__ == "__main__":
    unittest.main()
