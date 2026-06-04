"""
build.py — run this instead of PyInstaller directly.
Builds the exe and ensures python3xx.dll sits beside it.
"""
import os
import shutil
import subprocess
import sys
import glob

def main():
    # Clean
    for d in ("build", "dist"):
        if os.path.exists(d):
            shutil.rmtree(d)

    # Build
    ret = subprocess.run([sys.executable, "-m", "PyInstaller", "app.spec", "--noconfirm"])
    if ret.returncode != 0:
        print("PyInstaller failed!")
        sys.exit(1)

    # Find the python DLL (e.g. python314.dll, python312.dll, etc.)
    python_dir = os.path.dirname(sys.executable)
    dlls = glob.glob(os.path.join(python_dir, "python3*.dll"))
    if not dlls:
        print("WARNING: Could not find python3xx.dll — exe may fail to start.")
        return

    dist_exe_dir = os.path.join("dist", "AnimePaheDownloader")
    for dll in dlls:
        dst = os.path.join(dist_exe_dir, os.path.basename(dll))
        shutil.copy2(dll, dst)
        print(f"Copied {os.path.basename(dll)} → {dst}")

    print("\nBuild complete: dist\\AnimePaheDownloader\\AnimePaheDownloader.exe")

if __name__ == "__main__":
    main()
