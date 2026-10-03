#!/usr/bin/env python3
"""Validate Arena release versions and build the installable skill ZIP."""
import argparse
import json
import os
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAYLOAD = ("SKILL.md", "rubric.md", "bracket.py", "strategies.json", "LICENSE", "CREDITS.md")


def package(tag, output_dir):
    with open(os.path.join(REPO, "plugin.json"), encoding="utf-8") as stream:
        version = json.load(stream)["version"]
    with open(os.path.join(REPO, ".codex-plugin", "plugin.json"), encoding="utf-8") as stream:
        installed_version = json.load(stream)["version"]
    if version != installed_version:
        raise ValueError("plugin.json and .codex-plugin/plugin.json versions differ")
    if tag.removeprefix("v") != version:
        raise ValueError("release tag %r does not match plugin version %r" % (tag, version))
    os.makedirs(output_dir, exist_ok=True)
    archive = os.path.join(output_dir, "arena-skill-v%s.zip" % version)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
        for name in PAYLOAD:
            source_root = REPO if name in ("LICENSE", "CREDITS.md") else os.path.join(REPO, "skills", "arena")
            source = os.path.join(source_root, name)
            if not os.path.isfile(source):
                raise FileNotFoundError("missing skill payload file: %s" % source)
            output.write(source, os.path.join("arena", name))
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="published release tag, such as v0.3.1")
    parser.add_argument("--output-dir", default="dist")
    args = parser.parse_args()
    print("Created " + package(args.tag, os.path.abspath(args.output_dir)))


if __name__ == "__main__":
    main()
