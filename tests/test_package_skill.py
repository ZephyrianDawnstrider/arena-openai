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
            "arena/strategies.json", "arena/LICENSE", "arena/CREDITS.md"}


class PackageSkill(unittest.TestCase):
    def test_versioned_zip_contains_installable_payload(self):
        with tempfile.TemporaryDirectory(prefix="arena-package-") as temp:
            result = subprocess.run([sys.executable, PACKAGER, "--tag", "v0.3.1",
                                     "--output-dir", temp], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            archive = os.path.join(temp, "arena-skill-v0.3.1.zip")
            with zipfile.ZipFile(archive) as package:
                self.assertEqual(set(package.namelist()), EXPECTED)
                for name in ("LICENSE", "CREDITS.md"):
                    with open(os.path.join(REPO, name), "rb") as source:
                        self.assertEqual(package.read("arena/" + name), source.read())

    def test_rejects_tag_that_does_not_match_manifest(self):
        with tempfile.TemporaryDirectory(prefix="arena-package-") as temp:
            result = subprocess.run([sys.executable, PACKAGER, "--tag", "v0.0.0",
                                     "--output-dir", temp], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not match plugin version", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
