"""Validate the release archive output without publishing it."""
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGER = os.path.join(REPO, "scripts", "package_skill.py")
EXPECTED = {"arena/SKILL.md", "arena/rubric.md", "arena/bracket.py",
            "arena/strategies.json", "arena/VERSION", "arena/LICENSE", "arena/CREDITS.md"}
VERSION = "0.3.3"


class PackageSkill(unittest.TestCase):
    def test_versioned_zip_contains_installable_payload(self):
        with tempfile.TemporaryDirectory(prefix="arena-package-") as temp:
            result = subprocess.run([sys.executable, PACKAGER, "--tag", "v" + VERSION,
                                     "--output-dir", temp], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            archive = os.path.join(temp, "arena-skill-v" + VERSION + ".zip")
            with zipfile.ZipFile(archive) as package:
                self.assertEqual(set(package.namelist()), EXPECTED)
                for member in EXPECTED:
                    name = member.removeprefix("arena/")
                    source_path = os.path.join(REPO, name) if name in ("LICENSE", "CREDITS.md") else os.path.join(REPO, "skills", "arena", name)
                    with open(source_path, "rb") as source:
                        self.assertEqual(package.read(member), source.read())

    def test_rejects_tag_that_does_not_match_manifest(self):
        with tempfile.TemporaryDirectory(prefix="arena-package-") as temp:
            result = subprocess.run([sys.executable, PACKAGER, "--tag", "v0.0.0",
                                     "--output-dir", temp], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not match plugin version", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
