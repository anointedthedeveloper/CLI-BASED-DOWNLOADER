# AnimePahe Downloader v2.0

A Python desktop application for searching and downloading anime episodes from AnimePahe.

## Tech Stack

- **Language:** Python 3.12
- **GUI:** Tkinter (with ttk styling)
- **HTTP:** requests, cloudscraper
- **Cloudflare bypass:** FlareSolverr integration, Selenium browser automation
- **Image:** Pillow

## Project Structure

- `app.py` — Main application entry point (Tkinter GUI)
- `animepahe.py` — AnimePahe site interaction (search, episodes)
- `kwik.py` — Download link extraction from Kwik.cx
- `downloader.py` — File download management (sleep prevention, cookie fix)
- `session.py` — Network session and Cloudflare bypass state
- `flaresolverr.py` — FlareSolverr proxy integration (API communication)
- `fs_launcher.py` — Dedicated FlareSolverr process launcher (standalone + importable)
- `fs/` — Place `flaresolverr.exe` + `internal/` here (see `fs/README.txt`)
- `notifications.py` — Cross-platform desktop notifications (plyer → winotify → ctypes)
- `queue_manager.py` — Download queue data model and runner
- `browser.py` — Selenium-based browser automation
- `pages/` — GUI page modules (browse, downloads, queue, settings, log)
- `ui/` — Reusable UI components and theming
- `build.spec` — PyInstaller spec for standalone exe
- `build.bat` — One-click Windows build script

## Running

The app runs as a VNC desktop application:

```
python app.py
```

## User Preferences
