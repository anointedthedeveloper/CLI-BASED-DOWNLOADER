"""
flaresolverr.py — FlareSolverr integration for Cloudflare bypass.

FlareSolverr is a free local proxy that solves CF challenges automatically.
Drop flaresolverr.exe (and its accompanying internal/ folder) into the
`flaresolverr_bin/` folder next to this file — the app will start it
automatically on launch.

Download from: https://github.com/FlareSolverr/FlareSolverr/releases
"""

import json
import os
import subprocess
import urllib.request
import urllib.error

FLARESOLVERR_URL = "http://localhost:8191/v1"

# Path to the bundled executable (relative to this file)
_HERE = os.path.dirname(os.path.abspath(__file__))
FLARESOLVERR_EXE = os.path.join(_HERE, "flaresolverr_bin", "flaresolverr.exe")

_process: subprocess.Popen | None = None  # handle to the launched process


# ── logger callback ───────────────────────────────────────────────────────────
log_callback = None

def set_log_callback(cb):
    global log_callback
    log_callback = cb

def log(msg: str):
    if log_callback:
        log_callback(msg)
    else:
        print(msg)


def is_running() -> bool:
    """Check if FlareSolverr is responding on localhost:8191."""
    try:
        req = urllib.request.Request(
            "http://localhost:8191/",
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=3)
        return True
    except Exception:
        return False


def launch() -> bool:
    """
    Start flaresolverr.exe from flaresolverr_bin/ if it is not already running.

    Returns True if FlareSolverr is (or becomes) available, False otherwise.
    The launched process is kept as a daemon so it dies when the main app exits.
    """
    global _process

    if is_running():
        log("FlareSolverr already running on port 8191.")
        return True

    if not os.path.isfile(FLARESOLVERR_EXE):
        log(
            f"FlareSolverr executable not found at:\n  {FLARESOLVERR_EXE}\n"
            "Drop flaresolverr.exe (and its internal/ folder) into the "
            "flaresolverr_bin/ directory next to app.py."
        )
        return False

    log(f"Starting FlareSolverr from {FLARESOLVERR_EXE} …")
    try:
        # CREATE_NO_WINDOW keeps the console hidden on Windows
        flags = 0
        try:
            flags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        except AttributeError:
            pass  # non-Windows

        _process = subprocess.Popen(
            [FLARESOLVERR_EXE, "--max-timeout", "180000"],
            cwd=os.path.dirname(FLARESOLVERR_EXE),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
    except Exception as e:
        log(f"Failed to start FlareSolverr: {e}")
        return False

    # Wait up to 15 s for it to become responsive
    import time
    for _ in range(30):
        time.sleep(0.5)
        if is_running():
            log("FlareSolverr started successfully on port 8191.")
            return True

    log("FlareSolverr started but did not respond within 15 s.")
    return False


def shutdown():
    """Terminate the FlareSolverr process that was launched by this module."""
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
        log("FlareSolverr process terminated.")


def request_get(url: str, session_id: str = None) -> dict:
    """
    Send a GET request through FlareSolverr.
    Returns the full response dict from FlareSolverr.
    """
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 180000,   # 3 minutes — needed for modern Turnstile
    }
    if session_id:
        payload["session"] = session_id

    log(f"FlareSolverr request => POST /v1 url={url}")
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        FLARESOLVERR_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        import time
        start_time = time.monotonic()
        with urllib.request.urlopen(req, timeout=210) as resp:  # 3.5 min
            body = resp.read().decode("utf-8")
            elapsed = time.monotonic() - start_time
            res_data = json.loads(body)
            status = res_data.get("status")
            msg = res_data.get("message", "")
            log(f"FlareSolverr response => status={status} ({msg}) solved in {elapsed:.1f}s")
            return res_data
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            res_data = json.loads(body)
            msg = res_data.get("message", body)
        except Exception:
            msg = body
        err_msg = f"FlareSolverr HTTP {e.code}: {msg}"
        log(err_msg)
        raise RuntimeError(err_msg)
    except ConnectionRefusedError:
        err_msg = (
            "FlareSolverr is not running.\n"
            "Start it with:\n"
            "  flaresolverr.exe --max-timeout 180000"
        )
        log(err_msg)
        raise RuntimeError(err_msg)
    except Exception as e:
        log(f"FlareSolverr connection error: {e}")
        raise e


def get_cookies(url: str) -> dict:
    """
    Use FlareSolverr to load a URL and extract cookies (including cf_clearance).
    Returns a dict of {name: value} cookies.
    """
    resp = request_get(url)
    if resp.get("status") != "ok":
        raise RuntimeError(f"FlareSolverr failed: {resp.get('message', 'unknown error')}")

    cookies = {}
    for c in resp.get("solution", {}).get("cookies", []):
        cookies[c["name"]] = c["value"]
    return cookies


def fetch(url: str) -> tuple:
    """
    Fetch a URL via FlareSolverr.
    Returns (status_code, html_text, cookies_dict, user_agent).
    """
    resp = request_get(url)
    if resp.get("status") != "ok":
        raise RuntimeError(f"FlareSolverr failed: {resp.get('message', 'unknown error')}")

    sol         = resp.get("solution", {})
    status_code = sol.get("status", 200)
    html        = sol.get("response", "")
    cookies     = {c["name"]: c["value"] for c in sol.get("cookies", [])}
    user_agent  = sol.get("userAgent", "")
    return status_code, html, cookies, user_agent
