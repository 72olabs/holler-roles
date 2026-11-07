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


if __name__ == "__main__":
    unittest.main()
