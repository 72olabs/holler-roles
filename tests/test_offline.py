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
