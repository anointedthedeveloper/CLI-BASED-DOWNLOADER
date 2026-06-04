"""
flaresolverr.py — FlareSolverr integration for Cloudflare bypass.

FlareSolverr is a free local proxy that solves CF challenges automatically.
It runs as a Docker container or standalone executable.

Start it with:
    docker run -d -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest
OR download from: https://github.com/FlareSolverr/FlareSolverr/releases
"""

import json
import subprocess
import urllib.request
import urllib.error

FLARESOLVERR_URL = "http://localhost:8191/v1"


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
    """Check if FlareSolverr is running on localhost:8191."""
    try:
        req = urllib.request.Request(
            "http://localhost:8191/",
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=3)
        return True
    except Exception:
        return False


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
