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

    # Build with Python 3.13
    print("Building with Python 3.13...")
    ret = subprocess.run(
        [PYTHON313, "-m", "PyInstaller", "app.spec", "--noconfirm"],
        check=False
    )
    if ret.returncode != 0:
        print("PyInstaller failed!")
        sys.exit(1)

    dist_exe_dir = os.path.join("dist", "AnimePaheDownloader")

    # Copy python DLLs next to exe (fixes "Failed to load Python DLL" error)
    python313_dir = os.path.dirname(PYTHON313)
    for dll in glob.glob(os.path.join(python313_dir, "python3*.dll")):
        dst = os.path.join(dist_exe_dir, os.path.basename(dll))
        shutil.copy2(dll, dst)
        print("Copied DLL: " + os.path.basename(dll))

    # Copy vcruntime DLLs if present
    for dll in glob.glob(os.path.join(python313_dir, "vcruntime*.dll")):
        dst = os.path.join(dist_exe_dir, os.path.basename(dll))
        shutil.copy2(dll, dst)
        print("Copied runtime: " + os.path.basename(dll))

    exe = os.path.join(dist_exe_dir, "AnimePaheDownloader.exe")
    size_mb = os.path.getsize(exe) / (1024 * 1024)
    print("\nBuild complete!")
    print("EXE: " + exe)
    print("Size: {:.1f} MB".format(size_mb))
    print("\nTo distribute: zip the entire dist\\AnimePaheDownloader\\ folder.")


if __name__ == "__main__":
    main()
