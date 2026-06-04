"""
build.py - builds AnimePaheDownloader.exe using Python 3.13
Run: python build.py
"""
import os
import shutil
import subprocess
import sys
import glob

PYTHON313 = r"C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe"


def main():
    if not os.path.exists(PYTHON313):
        print("ERROR: Python 3.13 not found at " + PYTHON313)
        sys.exit(1)

    # Clean old artifacts
    for d in ("build", "dist"):
        if os.path.exists(d):
            shutil.rmtree(d)
            print("Removed: " + d)

    # Build with Python 3.13 using the spec file
    print("Building with Python 3.13 using the spec file...")
    ret = subprocess.run(
        [PYTHON313, "-m", "PyInstaller", "--clean", "app.spec", "--noconfirm"],
        check=False
    )
    if ret.returncode != 0:
        print("PyInstaller failed!")
        sys.exit(1)

    exe = os.path.join("dist", "AnimePaheDownloader.exe")
    if not os.path.exists(exe):
        print("ERROR: expected executable not found: " + exe)
        sys.exit(1)

    size_mb = os.path.getsize(exe) / (1024 * 1024)
    print("\nBuild complete!")
    print("EXE: " + exe)
    print("Size: {:.1f} MB".format(size_mb))
    print("\nTo distribute: use dist\\AnimePaheDownloader.exe. The exe now contains embedded dependencies.")


if __name__ == "__main__":
    main()
