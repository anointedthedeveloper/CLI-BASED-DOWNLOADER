"""
Auto-updater: checks GitHub releases and prompts user to download.
Set GITHUB_REPO to your  owner/repo  before publishing.
"""
import threading
import tkinter as tk
from tkinter import messagebox
import webbrowser

import requests

from version import __version__

GITHUB_REPO = "anointedthedeveloper/CLI-BASED-DOWNLOADER"
API_URL     = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def _parse_version(tag: str) -> tuple:
    tag = tag.lstrip("v")
    try:
        return tuple(int(x) for x in tag.split("."))
    except ValueError:
        return (0,)


def check_for_updates(app: tk.Tk, silent: bool = True):
    """Call this from the main thread; spawns a daemon thread to do the check."""
    threading.Thread(target=_check, args=(app, silent), daemon=True).start()


def _check(app: tk.Tk, silent: bool):
    try:
        r = requests.get(API_URL, timeout=8,
                         headers={"Accept": "application/vnd.github+json"})
        r.raise_for_status()
        data        = r.json()
        latest_tag  = data.get("tag_name", "")
        html_url    = data.get("html_url", "")
        body        = data.get("body", "")

        # Find a Windows .exe asset if present
        assets      = data.get("assets", [])
        exe_url     = next(
            (a["browser_download_url"] for a in assets
             if a["name"].lower().endswith(".exe")),
            html_url,
        )

        if not latest_tag:
            return

        current = _parse_version(__version__)
        latest  = _parse_version(latest_tag)

        if latest > current:
            app.after(0, lambda: _prompt(app, latest_tag, exe_url, body))
        elif not silent:
            app.after(0, lambda: messagebox.showinfo(
                "Up to date",
                f"You are running the latest version ({__version__})."))
    except Exception:
        if not silent:
            app.after(0, lambda: messagebox.showwarning(
                "Update check failed",
                "Could not reach GitHub to check for updates."))


def _prompt(app: tk.Tk, new_tag: str, url: str, notes: str):
    win = tk.Toplevel(app)
    win.title("Update Available")
    win.resizable(False, False)
    win.grab_set()

    try:
        t = app.t
    except Exception:
        t = {"BG": "#1e1e2e", "TEXT": "#cdd6f4", "ACCENT": "#cba6f7",
             "PANEL": "#313244", "BORDER": "#45475a", "SUCCESS": "#a6e3a1",
             "SUBTEXT": "#a6adc8", "CARD": "#181825"}

    win.configure(bg=t["BG"])

    tk.Label(win, text="🎉  Update Available!", font=("Segoe UI", 13, "bold"),
             bg=t["BG"], fg=t["ACCENT"]).pack(pady=(18, 4), padx=24)

    tk.Label(win, text=f"v{__version__}  →  {new_tag}",
             font=("Segoe UI", 10), bg=t["BG"], fg=t["TEXT"]).pack()

    if notes:
        frame = tk.Frame(win, bg=t["PANEL"], bd=0)
        frame.pack(fill="x", padx=18, pady=(10, 4))
        txt = tk.Text(frame, height=8, width=52, bg=t["PANEL"], fg=t["SUBTEXT"],
                      relief="flat", font=("Segoe UI", 9), wrap="word",
                      state="normal", bd=6)
        txt.insert("1.0", notes)
        txt.configure(state="disabled")
        txt.pack()

    btn_frame = tk.Frame(win, bg=t["BG"])
    btn_frame.pack(pady=(8, 18), padx=24)

    def _download():
        webbrowser.open(url)
        win.destroy()

    tk.Button(btn_frame, text="⬇  Download Now", font=("Segoe UI", 10, "bold"),
              bg=t["ACCENT"], fg="#1e1e2e", activebackground=t["SUCCESS"],
              relief="flat", padx=14, pady=6, cursor="hand2",
              command=_download).pack(side="left", padx=(0, 8))

    tk.Button(btn_frame, text="Later", font=("Segoe UI", 10),
              bg=t["PANEL"], fg=t["TEXT"], activebackground=t["BORDER"],
              relief="flat", padx=14, pady=6, cursor="hand2",
              command=win.destroy).pack(side="left")

    # Centre on parent
    win.update_idletasks()
    x = app.winfo_x() + (app.winfo_width()  - win.winfo_width())  // 2
    y = app.winfo_y() + (app.winfo_height() - win.winfo_height()) // 2
    win.geometry(f"+{x}+{y}")
