---
name: Cookie fix — downloader must use _build_cookie_str
description: The downloader was using Chrome-only cookies; FlareSolverr-solved cookies were never sent to curl.
---

## Rule
In `downloader.py`, always call `_sess._build_cookie_str(url)` (not `_sess._cookie_str_for(url)`) when building the cookie header for curl.

**Why:** `_cookie_str_for` reads only Chrome cookies. `_build_cookie_str` merges Chrome cookies with the FlareSolverr-solved cookie cache. Without this, curl gets 403 on every attempt after a CF challenge, even if FlareSolverr has already solved it.

**How to apply:** Any time the download retry loop needs fresh cookies, use `_build_cookie_str`. This ensures CF auto-resume works — each retry picks up the latest solved cookies.
