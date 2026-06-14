---
name: FlareSolverr folder convention
description: User places flaresolverr.exe in fs/ folder; fs_launcher.py is the dedicated launcher.
---

## Rule
The preferred location for `flaresolverr.exe` (and its `internal/` companion) is the `fs/` folder next to `app.py`. The legacy location `flaresolverr_bin/` is still a fallback.

**Why:** User requested a dedicated, clearly named folder for the FS binary, separate from app code.

**How to apply:**
- `flaresolverr.py` searches candidates: `fs/flaresolverr.exe` → `fs/flaresolverr` → `flaresolverr_bin/flaresolverr.exe` → `flaresolverr_bin/flaresolverr`
- `fs_launcher.py` is a standalone script (also importable) that can launch/stop FS and be run directly for testing
- `fs/README.txt` explains to users where to place the exe
- Any path-related help messages should mention `fs/` as the primary location
