"""
test_cf_bypass.py — Test all Cloudflare bypass methods.
Run: python test_cf_bypass.py
"""

import session as _sess
import flaresolverr as _fs

TEST_URL = "https://animepahe.pw"

def check(label, fn):
    print(f"\n  Testing {label}...", end=" ", flush=True)
    try:
        resp = fn()
        code = resp.status_code
        if code == 200:
            print(f"✓  200 OK  →  WORKING")
            return True
        elif code == 403:
            print(f"✗  403 Forbidden  →  BLOCKED by Cloudflare")
        elif code == 503:
            print(f"✗  503  →  Cloudflare challenge active")
        elif code == 0:
            print(f"✗  No connection  →  Domain unreachable")
        else:
            print(f"✗  HTTP {code}")
        return False
    except Exception as e:
        print(f"✗  ERROR: {e}")
        return False


def main():
    print("=" * 58)
    print("  AnimePahe Cloudflare Bypass Tester")
    print("=" * 58)

    results = {}

    # ── Method 1: Default curl ─────────────────────────────────────
    print("\n[1] Default (curl + Chrome cookies)")
    results["curl"] = check(
        TEST_URL,
        lambda: _sess.request("GET", TEST_URL)
    )

    # ── Method 2: Cloudscraper ─────────────────────────────────────
    print(f"\n[2] Cloudscraper  ({'installed' if _sess.HAS_CLOUDSCRAPER else 'NOT installed — pip install cloudscraper'})")
    if _sess.HAS_CLOUDSCRAPER:
        results["cloudscraper"] = check(
            TEST_URL,
            lambda: _sess.request("GET", TEST_URL, use_cloudscraper=True)
        )
    else:
        print("     Skipped")
        results["cloudscraper"] = False

    # ── Method 3: FlareSolverr ─────────────────────────────────────
    fs_running = _fs.is_running()
    print(f"\n[3] FlareSolverr  ({'RUNNING ✓' if fs_running else 'NOT running — see instructions below'})")
    if fs_running:
        results["flaresolverr"] = check(
            TEST_URL,
            lambda: _sess.request("GET", TEST_URL, use_flaresolverr=True)
        )
    else:
        print("     Skipped")
        results["flaresolverr"] = False

    # ── Method 4: Browser Automation ──────────────────────────────
    print(f"\n[4] Browser Automation  ({'installed' if _sess.HAS_BROWSER else 'NOT installed — pip install selenium webdriver-manager'})")
    if _sess.HAS_BROWSER:
        results["browser"] = check(
            TEST_URL,
            lambda: _sess.request("GET", TEST_URL, use_browser=True, browser_headless=True)
        )
    else:
        print("     Skipped")
        results["browser"] = False

    # ── Summary ────────────────────────────────────────────────────
    print("\n" + "=" * 58)
    print("  RESULTS")
    print("=" * 58)

    working = [k for k, v in results.items() if v]

    if working:
        print(f"\n  ✓ Working: {', '.join(working)}")
        best = working[0]
        if "flaresolverr" in working:
            best = "flaresolverr"
        elif "browser" in working:
            best = "browser"
        elif "cloudscraper" in working:
            best = "cloudscraper"

        print(f"\n  RECOMMENDATION: use  →  {best}")
        if best == "flaresolverr":
            print("  In the app: Settings ⚙ → Cloudflare Bypass → FlareSolverr")
        elif best == "browser":
            print("  In the app: Settings ⚙ → Cloudflare Bypass → Browser Automation")
        elif best == "cloudscraper":
            print("  In the app: Settings ⚙ → Cloudflare Bypass → Cloudscraper")
        else:
            print("  Default curl is working — no changes needed!")
    else:
        print("\n  ✗ ALL methods blocked!\n")
        print("  ── RECOMMENDED FIX: FlareSolverr ──────────────────────")
        print()
        print("  Option A — Docker (easiest):")
        print("    docker run -d -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest")
        print()
        print("  Option B — Standalone EXE (no Docker needed):")
        print("    1. Go to: https://github.com/FlareSolverr/FlareSolverr/releases")
        print("    2. Download: flaresolverr_windows_x64.zip")
        print("    3. Extract and run: flaresolverr.exe")
        print("    4. Re-run this test")
        print()
        print("  Option C — Install Browser Automation:")
        print("    pip install selenium webdriver-manager")
        print("    Then re-run this test")
        print()

    print()


if __name__ == "__main__":
    main()
