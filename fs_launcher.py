"""
fs_launcher.py — Dedicated FlareSolverr launcher for AnimePahe Downloader.

Place flaresolverr.exe (and its 'internal' folder) inside the 'fs/' directory
next to this script:

    fs/
        flaresolverr.exe
        internal/
            ...

This module is automatically called by app.py on startup.
You can also run it as a standalone script:
    python fs_launcher.py

Download FlareSolverr from:
    https://github.com/FlareSolverr/FlareSolverr/releases
"""

import os
import subprocess
import sys
import time
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))

# Candidate locations for the FlareSolverr executable, in priority order.
_EXE_CANDIDATES = [
    os.path.join(_HERE, "fs", "flaresolverr.exe"),           # Windows — fs/ folder (preferred)
    os.path.join(_HERE, "fs", "flaresolverr"),                # Linux/macOS — fs/ folder
    os.path.join(_HERE, "flaresolverr_bin", "flaresolverr.exe"),  # legacy Windows
    os.path.join(_HERE, "flaresolverr_bin", "flaresolverr"),      # legacy Linux/macOS
]

_process: subprocess.Popen = None
_log_fn = print


# ── logging ───────────────────────────────────────────────────────────────────

def set_log(fn):
    global _log_fn
    _log_fn = fn


def _log(msg: str):
    _log_fn(msg)


# ── helpers ───────────────────────────────────────────────────────────────────

def _find_exe() -> str:
    """Return the first candidate executable that exists on disk."""
    for path in _EXE_CANDIDATES:
        if os.path.isfile(path):
            return path
    return ""


def is_running() -> bool:
    """Return True if FlareSolverr is already responding on localhost:8191."""
    try:
        urllib.request.urlopen("http://localhost:8191/", timeout=2)
        return True
    except Exception:
        return False


# ── public API ────────────────────────────────────────────────────────────────

def launch() -> bool:
    """
    Start FlareSolverr if it is not already running.
    Looks for the executable in fs/ (preferred) then flaresolverr_bin/.

    Returns True  if FlareSolverr is (or becomes) available on port 8191.
    Returns False if the executable was not found or failed to start.
    """
    global _process

    if is_running():
        _log("FlareSolverr already running on port 8191.")
        return True

    exe = _find_exe()
    if not exe:
        _log(
            "FlareSolverr executable not found.\n"
            f"Place flaresolverr.exe inside the 'fs/' folder:\n"
            f"  {os.path.join(_HERE, 'fs', 'flaresolverr.exe')}\n"
            "Download from: https://github.com/FlareSolverr/FlareSolverr/releases"
        )
        return False

    _log(f"Starting FlareSolverr from: {exe}")
    try:
        # CREATE_NO_WINDOW keeps the console hidden on Windows
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        _process = subprocess.Popen(
            [exe, "--max-timeout", "180000"],
            cwd=os.path.dirname(exe),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
    except Exception as e:
        _log(f"Failed to launch FlareSolverr: {e}")
        return False

    # Wait up to 20 s for it to respond
    for _ in range(40):
        time.sleep(0.5)
        if is_running():
            _log("FlareSolverr is up on port 8191.")
            return True

    _log("FlareSolverr launched but did not respond within 20 s.")
    return False


def shutdown():
    """Terminate the FlareSolverr process that was started by launch()."""
    global _process
    if _process is not None:
        try:
            _process.terminate()
            _process.wait(timeout=5)
        except Exception:
            try:
                _process.kill()
            except Exception:
                pass
        _process = None
        _log("FlareSolverr process terminated.")


# ── standalone entry point ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("AnimePahe Downloader — FlareSolverr Launcher")
    print("=" * 50)
    ok = launch()
    if ok:
        print("FlareSolverr is running on http://localhost:8191")
        print("Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping FlareSolverr…")
            shutdown()
    else:
        print("Failed to start FlareSolverr. See messages above.")
        sys.exit(1)
