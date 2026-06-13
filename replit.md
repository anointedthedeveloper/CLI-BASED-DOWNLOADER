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
- `downloader.py` — File download management
- `session.py` — Network session and Cloudflare bypass state
- `flaresolverr.py` — FlareSolverr proxy integration
- `browser.py` — Selenium-based browser automation
- `pages/` — GUI page modules (browse, downloads, settings, log)
- `ui/` — Reusable UI components and theming

## Running

The app runs as a VNC desktop application:

```
python app.py
```

## User Preferences
