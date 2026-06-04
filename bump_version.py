#!/usr/bin/env python
"""
Usage:
  python bump_version.py patch   # 1.0.0 → 1.0.1
  python bump_version.py minor   # 1.0.0 → 1.1.0
  python bump_version.py major   # 1.0.0 → 2.0.0
"""
import re
import subprocess
import sys
from pathlib import Path

VERSION_FILE = Path(__file__).parent / "version.py"


def read_version() -> str:
    m = re.search(r'__version__\s*=\s*"([\d.]+)"', VERSION_FILE.read_text())
    if not m:
        raise RuntimeError("Cannot find __version__ in version.py")
    return m.group(1)


def bump(version: str, part: str) -> str:
    major, minor, patch = (int(x) for x in version.split("."))
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def main():
    part = sys.argv[1] if len(sys.argv) > 1 else "patch"
    if part not in ("major", "minor", "patch"):
        print("Usage: bump_version.py [major|minor|patch]")
        sys.exit(1)

    old = read_version()
    new = bump(old, part)

    VERSION_FILE.write_text(f'__version__ = "{new}"\n')
    print(f"Bumped {old} → {new}")

    tag = f"v{new}"
    subprocess.run(["git", "add", "version.py"], check=True)
    subprocess.run(["git", "commit", "-m", f"chore: bump version to {new}"], check=True)
    subprocess.run(["git", "tag", tag], check=True)
    subprocess.run(["git", "push", "origin", "HEAD"], check=True)
    subprocess.run(["git", "push", "origin", tag], check=True)
    print(f"Tag {tag} pushed — GitHub Actions will build the release.")


if __name__ == "__main__":
    main()
