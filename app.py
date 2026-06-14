import os
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import animepahe
import kwik
import downloader
import session as _sess
import flaresolverr as _flaresolverr
import notifications

from ui.theme import (LIGHT, DARK, MIDNIGHT,
                      FONT, FONT_SM, FONT_BOLD, FONT_MONO, FONT_XL, FONT_NAV,
                      FONT_XS, fmt_size, fmt_time, sanitize_dir, parse_range)
from ui.logo    import get_logo, set_window_icon
from ui.widgets import AutoSuggest, Spinner
from pages.browse    import BrowsePage
from pages.downloads import DownloadsPage
from pages.settings  import SettingsPage
from pages.log       import LogPage
from pages.queue     import QueuePage
from queue_manager   import DownloadQueue, QueueItem


def _get_play_ids(url: str):
    m = re.search(r"play/([a-f0-9\-]{36})/([a-f0-9]{64})", url)
    if not m:
        raise ValueError(f"Cannot extract play IDs from: {url}")
    return m.group(1), m.group(2)


# ── App ────────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self._theme = DARK
        self.title("AnimePahe Downloader v2.0")
        self.configure(bg=DARK["BG"])
        self.minsize(920, 640)
        self.resizable(True, True)

        # ── shared state ──────────────────────────────────────────────────────
        self._stop       = threading.Event()
        self._stop_fetch = threading.Event()

        self.bypass_method      = "flaresolverr"
        self.browser_type       = "chrome"
        self.browser_headless   = True
        self.browser_incognito  = False
        self.use_flaresolverr   = True
        self.max_concurrent_downloads = 3

        self.episode_vars  = []
        self.episode_data  = []
        self.series_id     = ""
        self.series_title  = ""
        self.thumb_images  = {}
        self._queue        = DownloadQueue()

        self.link_var        = tk.StringVar()
        self.fetch_range_var = tk.StringVar(value="all")
        self.quality_var     = tk.StringVar(value="Max")
        self.audio_var       = tk.StringVar(value="jp")
        self.dir_var         = tk.StringVar(value=os.path.expanduser("~/Downloads"))

        _sess.set_log_callback(self._log_info)
        _flaresolverr.set_log_callback(self._log_info)

        self._apply_ttk_style()
        self._build_layout()
        self.after(0,   self._maximize)
        self.after(100, lambda: set_window_icon(self, self._theme))
        threading.Thread(target=self._start_flaresolverr, daemon=True).start()
        threading.Thread(target=self._presolve_cf, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    @property
    def t(self):
        return self._theme

    # ── layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self._build_sidebar()
        self._build_content()

    # ── sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        t = self._theme
        sb = tk.Frame(self, bg=t["SIDEBAR"], width=200)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(8, weight=1)
        sb.grid_columnconfigure(0, weight=1)
        self._sidebar = sb

        # ── logo area ──────────────────────────────────────────────────────
        logo_frame = tk.Frame(sb, bg=t["SIDEBAR"], pady=16)
        logo_frame.grid(row=0, column=0, sticky="ew")
        self._logo_frame = logo_frame

        # PIL logo image in navbar
        self._logo_photo = get_logo(self, size=44, theme=t)
        logo_inner = tk.Frame(logo_frame, bg=t["SIDEBAR"])
        logo_inner.pack()
        self._logo_inner = logo_inner

        if self._logo_photo:
            self._logo_img_lbl = tk.Label(logo_inner, image=self._logo_photo,
                                          bg=t["SIDEBAR"], cursor="hand2")
        else:
            self._logo_img_lbl = tk.Label(logo_inner, text="🎌",
                                          font=("Segoe UI", 22),
                                          bg=t["SIDEBAR"], fg=t["ACCENT"],
                                          cursor="hand2")
        self._logo_img_lbl.pack()
        self._logo_img_lbl.bind("<Button-1>", lambda e: self._show_page("browse"))

        self._logo_name_lbl = tk.Label(logo_inner, text="AnimePahe",
                                       font=FONT_BOLD, bg=t["SIDEBAR"], fg=t["TEXT"])
        self._logo_name_lbl.pack()
        self._logo_ver_lbl = tk.Label(logo_inner, text="Downloader v2.0",
                                      font=("Segoe UI", 7),
                                      bg=t["SIDEBAR"], fg=t["SUBTEXT"])
        self._logo_ver_lbl.pack()

        # ── search bar ─────────────────────────────────────────────────────
        sep0 = tk.Frame(sb, bg=t["BORDER"], height=1)
        sep0.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
        self._sb_sep0 = sep0

        search_frame = tk.Frame(sb, bg=t["SIDEBAR"], padx=8, pady=0)
        search_frame.grid(row=2, column=0, sticky="ew")
        self._search_frame = search_frame

        # inner border effect
        search_border = tk.Frame(search_frame, bg=t["BORDER"],
                                 highlightthickness=0, padx=1, pady=1)
        search_border.pack(fill="x")
        self._search_border = search_border

        search_inner = tk.Frame(search_border, bg=t["PANEL"])
        search_inner.pack(fill="x")
        self._search_inner = search_inner

        self._search_icon = tk.Label(search_inner, text="🔍",
                                     font=("Segoe UI", 9),
                                     bg=t["PANEL"], fg=t["SUBTEXT"])
        self._search_icon.pack(side="left", padx=(6, 2), pady=4)

        self._search_var = tk.StringVar()
        self._search_entry = tk.Entry(search_inner, textvariable=self._search_var,
                                      bg=t["PANEL"], fg=t["SUBTEXT"],
                                      insertbackground=t["ACCENT"],
                                      relief="flat", font=FONT_SM, bd=0)
        self._search_entry.insert(0, "Search anime…")
        self._search_entry.pack(side="left", fill="x", expand=True, pady=5)
        self._search_entry.bind("<FocusIn>",  self._search_ph_clear)
        self._search_entry.bind("<FocusOut>", self._search_ph_restore)
        self._search_entry.bind("<Return>",   self._search_commit)

        # Attach auto-suggest to sidebar search
        self._search_suggest = AutoSuggest(
            entry=self._search_entry,
            app=self,
            fetch_fn=lambda q, page=1: animepahe.search_anime(
                q, log=lambda _: None, page=page, **self._cf_kw()),
            on_select=self._on_search_select,
        )

        # ── nav buttons ────────────────────────────────────────────────────
        sep1 = tk.Frame(sb, bg=t["BORDER"], height=1)
        sep1.grid(row=3, column=0, sticky="ew", padx=10, pady=(8, 4))
        self._sb_sep1 = sep1

        self._nav_btns = {}
        nav_items = [
            ("browse",    "🔍  Browse",    self._page_browse),
            ("downloads", "⬇  Downloads", self._page_downloads),
            ("queue",     "📋  Queue",     self._page_queue),
            ("log",       "🖹  Log",       self._page_log),
            ("settings",  "⚙  Settings",  self._page_settings),
        ]
        for row_idx, (key, label, cmd) in enumerate(nav_items, start=4):
            btn = tk.Button(
                sb, text=label, anchor="w",
                bg=t["SIDEBAR"], fg=t["NAV_TEXT"],
                activebackground=t["NAV_SEL"], activeforeground=t["ACCENT"],
                relief="flat", font=FONT_NAV, cursor="hand2",
                bd=0, padx=18, pady=10, width=18,
                command=cmd)
            btn.grid(row=row_idx, column=0, sticky="ew", padx=4, pady=1)
            self._nav_btns[key] = btn

        # ── download status mini progress ──────────────────────────────────
        sep2 = tk.Frame(sb, bg=t["BORDER"], height=1)
        sep2.grid(row=9, column=0, sticky="ew", padx=10, pady=(6, 4))
        self._sb_sep2 = sep2

        # Small spinner for active download
        dl_status_frame = tk.Frame(sb, bg=t["SIDEBAR"], padx=12)
        dl_status_frame.grid(row=10, column=0, sticky="ew")
        self._dl_status_frame = dl_status_frame

        self._sb_spinner = Spinner(dl_status_frame, size=14,
                                   color=t["SUCCESS"], bg=t["SIDEBAR"],
                                   thickness=2, speed=40)
        self._sb_spinner.grid(row=0, column=0, sticky="w")
        self._sb_spinner.grid_remove()

        self._sb_dl_var = tk.StringVar(value="")
        self._sb_dl_lbl = tk.Label(dl_status_frame, textvariable=self._sb_dl_var,
                                   bg=t["SIDEBAR"], fg=t["SUCCESS"],
                                   font=FONT_XS, anchor="w", wraplength=155)
        self._sb_dl_lbl.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        dl_status_frame.grid_columnconfigure(1, weight=1)

        # ── bypass indicator ───────────────────────────────────────────────
        self._bypass_var = tk.StringVar(value="🛡 FlareSolverr")
        bypass_lbl = tk.Label(sb, textvariable=self._bypass_var,
                              bg=t["SIDEBAR"], fg=t["SUCCESS"],
                              font=("Segoe UI", 8), cursor="hand2",
                              wraplength=160, justify="left")
        bypass_lbl.grid(row=11, column=0, sticky="ew", padx=14, pady=(6, 2))
        bypass_lbl.bind("<Button-1>", lambda e: self._page_settings())
        self._bypass_lbl = bypass_lbl

        status_lbl = tk.Label(sb, text="Click to configure →",
                              bg=t["SIDEBAR"], fg=t["SUBTEXT"],
                              font=("Segoe UI", 7))
        status_lbl.grid(row=12, column=0, sticky="ew", padx=14, pady=(0, 12))
        self._status_hint = status_lbl

    # ── sidebar search callbacks ───────────────────────────────────────────────

    def _search_ph_clear(self, event):
        if self._search_entry.get() == "Search anime…":
            self._search_entry.delete(0, "end")
            self._search_entry.config(fg=self.t["TEXT"])

    def _search_ph_restore(self, event):
        if not self._search_entry.get():
            self._search_entry.insert(0, "Search anime…")
            self._search_entry.config(fg=self.t["SUBTEXT"])

    def _search_commit(self, event=None):
        q = self._search_var.get().strip()
        if q and q != "Search anime…":
            self._show_page("browse")
            self._browse_page._suggest.hide()
            self.link_var.set(q)
            self._browse_page._url_entry.config(fg=self.t["TEXT"])

    def _on_search_select(self, result: dict):
        session = result.get("session", "")
        if session:
            url = f"https://animepahe.pw/anime/{session}"
        else:
            url = result.get("url", "")
        if url:
            self.link_var.set(url)
            self._show_page("browse")
            self._browse_page._url_entry.config(fg=self.t["TEXT"])
            self.validate_url()
            self.after(150, self.fetch_episodes)

    # ── content area ──────────────────────────────────────────────────────────

    def _build_content(self):
        container = tk.Frame(self, bg=self._theme["BG"])
        container.grid(row=0, column=1, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self._container = container

        # Transition overlay — plain Frame raised briefly on page switch
        self._overlay = tk.Frame(container, bg=self._theme["BG"])

        self._browse_page    = BrowsePage(container, self)
        self._downloads_page = DownloadsPage(container, self)
        self._log_page       = LogPage(container, self)
        self._settings_page  = SettingsPage(container, self)
        self._queue_page     = QueuePage(container, self)

        for page in (self._browse_page, self._downloads_page,
                     self._log_page, self._settings_page,
                     self._queue_page, self._overlay):
            page.grid(row=0, column=0, sticky="nsew")

        self._current_page = None
        self._page_browse()

    # ── page switching with quick flash transition ─────────────────────────────

    def _show_page(self, key: str):
        pages = {
            "browse":    self._browse_page,
            "downloads": self._downloads_page,
            "log":       self._log_page,
            "settings":  self._settings_page,
            "queue":     self._queue_page,
        }
        if key not in pages:
            return
        page = pages[key]

        # Quick flash animation — overlay blinks then fades
        self._flash_transition(page)

        self._current_page = key
        t = self._theme
        for k, btn in self._nav_btns.items():
            if k == key:
                btn.config(bg=t["NAV_SEL"], fg=t["ACCENT"],
                           font=FONT_NAV)
            else:
                btn.config(bg=t["SIDEBAR"], fg=t["NAV_TEXT"],
                           font=FONT_NAV)

    def _flash_transition(self, target_page):
        """Brief BG-flash: raise overlay, then immediately show target page."""
        self._overlay.configure(bg=self._theme["BG"])
        self._overlay.lift()

        def _reveal():
            target_page.lift()

        self.after(55, _reveal)

    def _page_browse(self):    self._show_page("browse")
    def _page_downloads(self): self._show_page("downloads")
    def _page_log(self):       self._show_page("log")
    def _page_settings(self):  self._show_page("settings")
    def _page_queue(self):     self._show_page("queue")

    # ── ttk style ─────────────────────────────────────────────────────────────

    def _apply_ttk_style(self):
        t = self._theme
        s = ttk.Style()
        s.theme_use("clam")
        for name, colour in (
            ("Accent.Horizontal.TProgressbar",  t["ACCENT"]),
            ("Success.Horizontal.TProgressbar", t["SUCCESS"]),
        ):
            s.configure(name,
                troughcolor=t["PROG_BG"], background=colour,
                troughrelief="flat", relief="flat",
                borderwidth=0, lightcolor=colour, darkcolor=colour)
        s.configure("TCombobox",
            fieldbackground=t["CARD"], background=t["CARD"],
            foreground=t["TEXT"], selectbackground=t["ACCENT"],
            selectforeground="white", arrowcolor=t["SUBTEXT"],
            borderwidth=0, relief="flat", padding=4)
        s.map("TCombobox",
            fieldbackground=[("readonly", t["CARD"])],
            foreground=[("readonly", t["TEXT"])])
        s.configure("Vertical.TScrollbar",
            background=t["BORDER"], troughcolor=t["BG"],
            bordercolor=t["BG"], arrowcolor=t["SUBTEXT"],
            relief="flat", width=8)

    # ── theme ─────────────────────────────────────────────────────────────────

    def set_theme(self, theme):
        self._theme = theme
        self.configure(bg=theme["BG"])
        self._apply_ttk_style()
        self._apply_sidebar_theme()
        self._browse_page.apply_theme()
        self._downloads_page.apply_theme()
        self._log_page.apply_theme()
        self._settings_page.apply_theme()
        self._queue_page.apply_theme()
        if hasattr(self._settings_page, "_update_active_theme_btn"):
            self._settings_page._update_active_theme_btn()
        self._show_page(self._current_page)

    def _apply_sidebar_theme(self):
        t = self._theme
        self._sidebar.configure(bg=t["SIDEBAR"])
        self._logo_frame.configure(bg=t["SIDEBAR"])
        self._logo_inner.configure(bg=t["SIDEBAR"])
        self._logo_img_lbl.configure(bg=t["SIDEBAR"])
        self._logo_name_lbl.configure(bg=t["SIDEBAR"], fg=t["TEXT"])
        self._logo_ver_lbl.configure(bg=t["SIDEBAR"], fg=t["SUBTEXT"])

        # Refresh logo image for new theme
        new_photo = get_logo(self, size=44, theme=t)
        if new_photo:
            self._logo_photo = new_photo
            self._logo_img_lbl.configure(image=new_photo)
            self._logo_img_lbl._image = new_photo   # keep ref

        self._sb_sep0.configure(bg=t["BORDER"])
        self._search_frame.configure(bg=t["SIDEBAR"])
        self._search_border.configure(bg=t["BORDER"])
        self._search_inner.configure(bg=t["PANEL"])
        self._search_icon.configure(bg=t["PANEL"], fg=t["SUBTEXT"])
        self._search_entry.configure(bg=t["PANEL"], fg=t["TEXT"],
                                     insertbackground=t["ACCENT"])

        self._sb_sep1.configure(bg=t["BORDER"])
        self._sb_sep2.configure(bg=t["BORDER"])

        self._dl_status_frame.configure(bg=t["SIDEBAR"])
        self._sb_spinner.set_color(t["SUCCESS"])
        self._sb_spinner.set_bg(t["SIDEBAR"])
        self._sb_dl_lbl.configure(bg=t["SIDEBAR"], fg=t["SUCCESS"])

        self._bypass_lbl.configure(bg=t["SIDEBAR"])
        self._status_hint.configure(bg=t["SIDEBAR"], fg=t["SUBTEXT"])
        for btn in self._nav_btns.values():
            btn.configure(bg=t["SIDEBAR"], fg=t["NAV_TEXT"],
                          activebackground=t["NAV_SEL"],
                          activeforeground=t["ACCENT"])
        self._container.configure(bg=t["BG"])
        self._overlay.configure(bg=t["BG"])

    def update_bypass_indicator(self):
        icons = {
            "curl":         "🛡 curl (default)",
            "flaresolverr": "🛡 FlareSolverr",
            "cloudscraper": "🛡 Cloudscraper",
            "browser":      "🛡 Browser",
            "uc":           "🛡 UC-Chrome ⭐",
        }
        self._bypass_var.set(icons.get(self.bypass_method, f"🛡 {self.bypass_method}"))
        ok = self.bypass_method != "curl"
        self._bypass_lbl.config(fg=self.t["SUCCESS"] if ok else self.t["SUBTEXT"])

    # ── FlareSolverr auto-launch ──────────────────────────────────────────────

    def _start_flaresolverr(self):
        """Launch FlareSolverr in the background when the app starts."""
        ok = _flaresolverr.launch()
        if ok:
            self.after(0, lambda: self._bypass_var.set("🛡 FlareSolverr ✓"))
            self.after(0, lambda: self._bypass_lbl.config(fg=self.t["SUCCESS"]))
        else:
            self.after(0, lambda: self._log_info(
                "FlareSolverr not started — place flaresolverr.exe inside the "
                "fs/ folder next to app.py, or start it manually on port 8191."))

    def _on_close(self):
        """Clean up FlareSolverr process then destroy the window."""
        _flaresolverr.shutdown()
        self.destroy()

    # ── misc init ─────────────────────────────────────────────────────────────

    def _maximize(self):
        try:
            self.state("zoomed")
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)
            except Exception:
                pass

    def _presolve_cf(self):
        self._log_info("Pre-solving Cloudflare for animepahe.pw…")
        try:
            _sess.solve_cf_once(url="https://animepahe.pw", force=False,
                                log_fn=self._log_info)
        except Exception as e:
            self._log_err(f"Pre-solve animepahe failed: {e}")
        self._log_info("Pre-solving Cloudflare for kwik.cx…")
        try:
            _sess.solve_cf_once(url="https://kwik.cx/f/invalid", force=False,
                                log_fn=self._log_info)
        except Exception as e:
            self._log_err(f"Pre-solve kwik failed: {e}")

    # ── logging ───────────────────────────────────────────────────────────────

    def _log(self, msg: str, tag: str = ""):
        self._downloads_page.log(msg, tag)
        if hasattr(self, "_log_page"):
            self._log_page.append(msg, tag)

    def _log_ok(self, msg):     self._log(f"[SUCCESS] {msg}", "success")
    def _log_err(self, msg):    self._log(f"[ERROR]   {msg}", "error")
    def _log_info(self, msg):   self._log(f"[INFO]    {msg}", "info")
    def _log_header(self, msg):
        sep = "─" * 50
        self._log(f"{sep}\n{msg}\n{sep}", "header")

    # ── sidebar download status ────────────────────────────────────────────────

    def _sb_show_downloading(self, active: bool, label: str = ""):
        if active:
            self._sb_dl_var.set(label or "Downloading…")
            self._sb_spinner.grid()
            self._sb_spinner.start()
        else:
            self._sb_dl_var.set("")
            self._sb_spinner.stop()
            self._sb_spinner.grid_remove()

    # ── CF kwargs ─────────────────────────────────────────────────────────────

    def _cf_kw(self) -> dict:
        m = self.bypass_method
        return dict(
            use_cloudscraper  = (m == "cloudscraper"),
            use_browser       = (m == "browser"),
            use_flaresolverr  = (m in ("flaresolverr", "uc")) or self.use_flaresolverr,
            browser_type      = self.browser_type,
            browser_headless  = self.browser_headless,
            browser_incognito = self.browser_incognito,
        )

    # ── URL actions ───────────────────────────────────────────────────────────

    def paste_url(self):
        try:
            url = self.clipboard_get()
            if url:
                self.link_var.set(url)
                self._browse_page._url_entry.config(fg=self.t["TEXT"])
                self.validate_url()
                if animepahe.is_series_url(url) or animepahe.is_episode_url(url):
                    self.after(200, self.fetch_episodes)
        except Exception:
            pass

    def validate_url(self):
        url = self.link_var.get().strip()
        if url in ("", "Paste AnimePahe series or episode URL…"):
            return
        bp = self._browse_page
        if animepahe.is_series_url(url) or animepahe.is_episode_url(url):
            bp.set_url_status("✓ Link recognised", self.t["SUCCESS"])
        elif url:
            bp.set_url_status("Validating…", self.t["SUBTEXT"])
        else:
            bp.set_url_status("", self.t["SUBTEXT"])

    def stop_fetch(self):
        self._stop_fetch.set()
        self._log_info("Stopping fetch…")

    # ── fetch episodes ────────────────────────────────────────────────────────

    def fetch_episodes(self):
        url = self.link_var.get().strip()
        if url in ("", "Paste AnimePahe series or episode URL…"):
            messagebox.showwarning("No URL", "Paste an AnimePahe series or episode URL first.")
            return
        if not (animepahe.is_series_url(url) or animepahe.is_episode_url(url)):
            messagebox.showerror("Invalid URL", "Paste a valid AnimePahe series or episode URL.")
            return

        self._stop_fetch.clear()
        self._browse_page.set_fetching(True)
        self._browse_page.set_url_status("Fetching episodes…", self.t["SUBTEXT"])

        for w in self._browse_page._ep_inner.winfo_children():
            w.destroy()
        self.episode_vars.clear()
        self.episode_data.clear()

        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def _fetch_thread(self, url: str):
        cf_kw     = self._cf_kw()
        is_series = animepahe.is_series_url(url)

        def stopped():
            return self._stop_fetch.is_set()

        cf_kw["stop_flag"] = stopped

        try:
            self._log_info("Fetching anime info…")
            meta      = animepahe.fetch_metadata(url, is_series,
                                                 log=self._log_info, **cf_kw)
            title     = meta.get("title", "Unknown")
            poster    = meta.get("poster", "")
            series_id = meta.get("id") or (
                animepahe.get_series_id(url) if is_series else None)

            if stopped():
                return

            type_str  = meta.get("type", "")
            # Don't show episode count in meta_str yet — we'll fetch it precisely
            meta_str  = type_str if type_str else ""

            self.after(0, lambda: self._browse_page._update_anime_header(
                title, meta_str, poster))
            self.after(0, lambda: self._browse_page.set_url_status(
                f"✓  {title}" + (f"  ·  {meta_str}" if meta_str else ""),
                self.t["SUCCESS"]))
            self._log_ok(f"Title: {title}")

            # Fire full-details fetch in background (genres, synopsis, studio, better poster)
            if is_series and series_id:
                _sid = series_id
                _cf  = dict(cf_kw)
                def _load_full_details(sid=_sid, kw=_cf):
                    try:
                        details = animepahe.fetch_anime_details_full(
                            sid, log=self._log_info, **{k: v for k, v in kw.items()
                                                        if k != "stop_flag"})
                        if details:
                            self.after(0, lambda d=details:
                                       self._browse_page.show_anime_details(d))
                    except Exception as e:
                        self._log_info(f"Full details fetch skipped: {e}")
                threading.Thread(target=_load_full_details, daemon=True).start()

            if is_series:
                # ── Always fetch the authoritative total from the API ──────
                # The metadata endpoint may return an outdated or blank count.
                # page=1 of the release API always has the correct `total` field.
                self._log_info("Fetching exact episode count from API…")
                total = 0
                try:
                    r = _sess.request(
                        "GET",
                        f"{animepahe.API_BASE}/api?m=release&id={series_id}"
                        f"&sort=episode_asc&page=1",
                        headers={"Referer": "https://animepahe.pw/"},
                        **cf_kw,
                    )
                    r.raise_for_status()
                    page1_data = r.json()
                    total = int(page1_data.get("total", 0))
                    self._log_info(f"Episode count: {total}")
                except Exception as e:
                    self._log_err(f"Couldn't get episode count: {e}")

                # Fallback to metadata value if API failed
                if total == 0:
                    try:
                        total = int(str(meta.get("episode_count") or "0"))
                    except ValueError:
                        total = 0

                if total == 0:
                    self._log_err("Could not determine episode count — defaulting to 9999.")
                    total = 9999

                # Update header with the correct count immediately
                self.after(0, lambda n=total:
                           self._browse_page.update_episode_count(n))

                range_str = self.fetch_range_var.get().strip() or "all"
                try:
                    start_ep, end_ep = parse_range(range_str, total)
                except Exception as e:
                    self._log_err(f"Range error: {e}. Using all.")
                    start_ep, end_ep = 1, total

                start_page = (start_ep - 1) // 30 + 1
                end_page   = (end_ep   - 1) // 30 + 1
                pages      = max(1, (total + 29) // 30)
                start_page = max(1, min(start_page, pages))
                end_page   = max(1, min(end_page,   pages))

                self._log_info(f"Fetching episodes {start_ep}–{end_ep} "
                               f"(pages {start_page}–{end_page})…")

                raw_episodes = []

                # Re-use page 1 data we already fetched (avoid a duplicate request)
                try:
                    first_batch = page1_data.get("data", [])
                except NameError:
                    first_batch = []

                for page in range(start_page, end_page + 1):
                    if stopped():
                        self._log_info("Fetch stopped.")
                        return
                    self._log_info(f"  Page {page}/{end_page}…")
                    if page == 1 and first_batch:
                        batch = first_batch
                    else:
                        r2 = _sess.request(
                            "GET",
                            f"{animepahe.API_BASE}/api?m=release&id={series_id}"
                            f"&sort=episode_asc&page={page}",
                            headers={"Referer": "https://animepahe.pw/"},
                            **cf_kw,
                        )
                        r2.raise_for_status()
                        batch = r2.json().get("data", [])
                    # Use 1-based position index (not episode number) so that
                    # series starting at e.g. ep 12 still work with range "1-4"
                    page_start_pos = (page - 1) * 30 + 1
                    for i, ep in enumerate(batch):
                        pos = page_start_pos + i
                        if start_ep <= pos <= end_ep:
                            raw_episodes.append(ep)
                    self._log_info(f"  {len(raw_episodes)} episodes in range so far.")
            else:
                total = 1
                series_id2, session = _get_play_ids(url)
                raw_episodes = [{"episode": 1, "title": "Episode", "snapshot": "",
                                 "session": session, "filler": 0, "audio": "jpn"}]
                series_id = series_id2

            if stopped():
                return

            self._log_ok(f"Loaded {len(raw_episodes)} episodes.")
            self.after(0, lambda eps=raw_episodes, t=title, sid=series_id, n=total:
                       self._browse_page.populate_episodes(eps, t, sid,
                                                           total_count=n))

        except Exception as e:
            self._log_err(f"Fetch failed: {e}")
            self.after(0, lambda: self._browse_page.set_url_status(
                f"✗  {e}", self.t["DANGER"]))
            if "403" in str(e):
                self.after(0, lambda: self._log_err(
                    "403 = Cloudflare blocked. Use 🛡 Solve CF on the Downloads page."))
        finally:
            self.after(0, lambda: self._browse_page.set_fetching(False))

    # ── CF solve ──────────────────────────────────────────────────────────────

    def solve_cf(self):
        if not _sess.flaresolverr_running():
            messagebox.showerror(
                "FlareSolverr Not Running",
                "Start FlareSolverr first:\n\n"
                "flaresolverr.exe --max-timeout 180000\n\n"
                "Or choose a different bypass method in Settings ⚙")
            return
        dp = self._downloads_page
        dp.set_solve_btn(False, "⏳ Solving…")
        self._log_info("Starting Cloudflare solve via FlareSolverr (~60-90 s)…")
        threading.Thread(target=self._solve_cf_thread, daemon=True).start()

    def _solve_cf_thread(self):
        ok = _sess.solve_cf_once(log=self._log_info)
        dp = self._downloads_page

        def done():
            dp.set_solve_btn(True, "🛡 Solve CF")
            if ok:
                self._log_ok("CF solved! Cookies cached for 2 hours.")
                self._bypass_var.set("🛡 FlareSolverr ✓")
                self._bypass_lbl.config(fg=self.t["SUCCESS"])
            else:
                self._log_err("CF solve failed. Check FlareSolverr is running.")

        self.after(0, done)

    # ── download ──────────────────────────────────────────────────────────────

    def start_download(self):
        url = self.link_var.get().strip()
        if url in ("", "Paste AnimePahe series or episode URL…"):
            messagebox.showwarning("No URL",
                "Go to Browse, paste a URL and Fetch episodes first.")
            return
        if not (animepahe.is_series_url(url) or animepahe.is_episode_url(url)):
            messagebox.showerror("Invalid URL",
                "Paste a valid AnimePahe series or episode URL on the Browse page.")
            return
        if not self.episode_vars:
            messagebox.showwarning("No Episodes",
                "Go to Browse, Fetch episodes, then come back to Start Download.")
            return

        self._stop.clear()
        dp = self._downloads_page
        dp.set_buttons(True)
        dp.set_overall_progress(0, "")
        dp.set_file_progress(0, "")
        dp._clear_log()

        threading.Thread(target=self._run_downloads, daemon=True).start()

    # ── queue ─────────────────────────────────────────────────────────────────

    def add_to_queue(self):
        """Add currently selected episodes to the download queue."""
        if not self.episode_vars:
            messagebox.showwarning("No Episodes",
                "Go to Browse, fetch episodes, then select them first.")
            return
        play_links = [u for var, _, u in self.episode_vars if var.get()]
        if not play_links:
            messagebox.showwarning("No Selection",
                "Select at least one episode checkbox first.")
            return

        qual = self.quality_var.get()
        target_res = 0
        if qual == "Min":    target_res = -1
        elif qual not in ("Max", ""): target_res = int(qual)
        audio    = self.audio_var.get().split()[0]
        save_dir = os.path.join(self.dir_var.get().strip(),
                                sanitize_dir(self.series_title or "anime"))
        title    = self.series_title or "Unknown Anime"

        item = QueueItem(
            title=title,
            play_urls=play_links,
            quality=target_res,
            audio=audio,
            save_dir=save_dir,
        )
        self._queue.add(item)
        self._log_info(f"Queued: {title}  ·  {len(play_links)} episode(s)")
        messagebox.showinfo("Added to Queue",
            f"Added {len(play_links)} episode(s) of {title} to the download queue.\n\n"
            "Open the Queue page to start processing.")
        self._page_queue()

    def _queue_download_fn(self, item: QueueItem, stop_ev):
        """Called by the queue runner in a background thread for one queue item."""
        def stopped():
            return stop_ev.is_set()

        cf_kw = self._cf_kw()
        cf_kw["stop_flag"] = stopped

        total_eps = len(item.play_urls)
        title     = item.title

        notifications.notify("Download Started",
                             f"{title}  ·  {total_eps} episode(s)")
        self._log_header(f"Queue: {title}  ·  {total_eps} ep(s)")

        downloader.prevent_sleep()
        try:
            for ep_idx, play_url in enumerate(item.play_urls):
                if stopped():
                    raise InterruptedError("Queue stopped")

                ep_num = ep_idx + 1
                item.current_ep = ep_num
                item.progress   = (ep_idx / total_eps) * 100
                self._queue._notify()

                self._log_info(f"Queue [{ep_num}/{total_eps}] Extracting link…")

                try:
                    pahe   = animepahe.fetch_pahe_win_links(
                        play_url, item.quality, item.audio, **cf_kw)
                    dl_map = kwik.extract_kwik_link(pahe["dPaheLink"])

                    def on_progress(done, total, speed, eta,
                                    _idx=ep_idx, _tot=total_eps):
                        if total > 0:
                            item.progress = (
                                _idx / _tot + (done / total) / _tot) * 100
                            self._queue._notify()

                    path = downloader.download(
                        url=dl_map["directLink"],
                        referer=dl_map["referer"],
                        dest_dir=item.save_dir,
                        on_progress=on_progress,
                        stop_flag=stopped,
                    )
                    self._log_ok(f"Queue EP{ep_num:02d} → {os.path.basename(path)}")

                except InterruptedError:
                    raise
                except Exception as e:
                    self._log_err(f"Queue EP{ep_num:02d} error: {e}")
                    if stopped():
                        raise InterruptedError("Queue stopped")
                    continue

            item.progress = 100.0
            notifications.notify("Download Complete",
                                 f"✓ {title}  ·  {total_eps} episode(s)")
            self._log_ok(f"Queue complete: {title}")

        except InterruptedError:
            notifications.notify("Download Cancelled", f"Cancelled: {title}")
            raise
        except Exception as exc:
            notifications.notify("Download Error", f"{title}: {exc}")
            raise
        finally:
            downloader.allow_sleep()

    # ── size estimation ────────────────────────────────────────────────────────

    def estimate_size(self):
        """Start a background thread to estimate total download size."""
        if not self.episode_vars:
            messagebox.showwarning("No Episodes", "Fetch episodes first.")
            return
        play_links = [u for var, _, u in self.episode_vars if var.get()]
        if not play_links:
            messagebox.showwarning("No Selection", "Select episodes first.")
            return
        dp = self._downloads_page
        dp._size_var.set("⏳ Estimating size…")
        self._log_info(f"Estimating size for {len(play_links)} episode(s)…")
        threading.Thread(
            target=self._estimate_size_thread,
            args=(play_links,),
            daemon=True
        ).start()

    def _estimate_size_thread(self, play_links: list):
        dp = self._downloads_page
        try:
            qual = self.quality_var.get()
            target_res = 0
            if qual == "Min":    target_res = -1
            elif qual not in ("Max", ""): target_res = int(qual)
            audio  = self.audio_var.get().split()[0]
            cf_kw  = {k: v for k, v in self._cf_kw().items()
                      if k != "stop_flag"}

            # Sample first episode
            sample_url = play_links[0]
            pahe   = animepahe.fetch_pahe_win_links(
                sample_url, target_res, audio, **cf_kw)
            dl_map = kwik.extract_kwik_link(pahe["dPaheLink"])

            # HEAD request via curl to get Content-Length
            import subprocess
            head = subprocess.run(
                ["curl", "-sI", "-L", "--max-redirs", "5",
                 "--connect-timeout", "12",
                 "-H", f"Referer: {dl_map['referer']}",
                 dl_map["directLink"]],
                capture_output=True, timeout=25)
            out = head.stdout.decode("utf-8", errors="replace").lower()
            m = re.search(r"content-length:\s*(\d+)", out)
            ep_bytes = int(m.group(1)) if m else 0

            if ep_bytes > 0:
                total = ep_bytes * len(play_links)
                msg = (f"~{fmt_size(total)} total"
                       f"  ·  {fmt_size(ep_bytes)}/ep"
                       f"  ·  {len(play_links)} ep(s)")
                self._log_info(f"Estimated size: {msg}")
                self.after(0, lambda s=msg: dp._size_var.set(s))
            else:
                self.after(0, lambda: dp._size_var.set(
                    "Could not determine size (server did not report it)"))
        except Exception as e:
            self._log_err(f"Size estimation failed: {e}")
            self.after(0, lambda: dp._size_var.set("Size estimate failed."))

    def stop_download(self):
        self._stop.set()
        self._log_info("Stop requested…")

    def _run_downloads(self):
        qual     = self.quality_var.get()
        audio    = self.audio_var.get().split()[0]
        save_dir = self.dir_var.get().strip()
        cf_kw    = self._cf_kw()
        dp       = self._downloads_page

        target_res = 0
        if qual == "Min":    target_res = -1
        elif qual not in ("Max", ""): target_res = int(qual)

        downloader.prevent_sleep()
        try:
            play_links  = [u for var, _, u in self.episode_vars if var.get()]
            title       = self.series_title or "anime"
            total_count = len(play_links)

            if not play_links:
                raise RuntimeError("No episodes selected — check the episode list on Browse.")

            dest_dir = os.path.join(save_dir, sanitize_dir(title))
            self._log_header(f"Starting {total_count} download(s)")
            self._log_info(f"Saving to: {dest_dir}")
            dp.set_overall_progress(0, f"0 / {total_count} episodes")
            notifications.notify("Download Started",
                                 f"{title}  ·  {total_count} episode(s)")

            # Show sidebar download status
            self.after(0, lambda: self._sb_show_downloading(True, f"⬇ {title}"))

            import queue
            q = queue.Queue()
            for idx, play_url in enumerate(play_links):
                q.put((idx, play_url))

            lock            = threading.Lock()
            active_progress = {}
            completed_set   = set()

            def worker():
                while not q.empty() and not self._stop.is_set():
                    try:
                        idx, play_url = q.get_nowait()
                    except queue.Empty:
                        break

                    ep_num = idx + 1
                    self._log_info(f"[{ep_num}/{total_count}] Extracting link…")

                    try:
                        pahe   = animepahe.fetch_pahe_win_links(
                            play_url, target_res, audio, **cf_kw)
                        dl_map = kwik.extract_kwik_link(pahe["dPaheLink"])
                    except Exception as e:
                        self._log_err(f"EP{ep_num:02d} link error: {e}")
                        with lock:
                            completed_set.add(play_url)
                            pct = len(completed_set) / total_count * 100
                            dp.set_overall_progress(pct,
                                f"{len(completed_set)} / {total_count} episodes")
                        q.task_done()
                        continue

                    direct  = dl_map["directLink"]
                    referer = dl_map["referer"]
                    res_lbl = f"{pahe['epRes']}p" if pahe.get("epRes") else "?"
                    self._log_info(f"↓ EP{ep_num:02d} [{res_lbl}]")

                    def on_progress(done, total, speed, eta, _url=play_url):
                        with lock:
                            active_progress[_url] = (done, total, speed, eta)
                            td   = sum(d for d, _, _, _ in active_progress.values())
                            ts   = sum(t for _, t, _, _ in active_progress.values())
                            tspd = sum(s for _, _, s, _ in active_progress.values())
                            etas = [e for _, _, _, e in active_progress.values() if e > 0]
                            pct  = (td / ts * 100) if ts else 0
                            avg_eta = max(etas) if etas else 0
                            n_done  = len(completed_set)
                            overall = ((n_done + pct / 100) / total_count) * 100
                            size_s = (f"{fmt_size(td)} / {fmt_size(ts)}"
                                      if ts else fmt_size(td))
                            spd_s  = f"{fmt_size(tspd)}/s" if tspd else "…"
                            eta_s  = f"ETA {fmt_time(avg_eta)}" if avg_eta else ""
                            dp.set_file_progress(pct,
                                f"{size_s}   {spd_s}   {eta_s}")
                            dp.set_overall_progress(overall,
                                f"{n_done} / {total_count} episodes")
                            self.after(0, lambda p=int(overall):
                                       self._sb_dl_var.set(
                                           f"⬇ {title[:16]}…  {p}%"))

                    try:
                        path = downloader.download(
                            url=direct, referer=referer, dest_dir=dest_dir,
                            on_progress=on_progress,
                            stop_flag=self._stop.is_set)
                        self._log_ok(f"EP{ep_num:02d} → {os.path.basename(path)}")
                        self.after(0, lambda u=play_url: self._uncheck_episode(u))
                    except InterruptedError:
                        self._log_info(f"EP{ep_num:02d} stopped — partial file kept.")
                    except Exception as e:
                        self._log_err(f"EP{ep_num:02d} error: {e}")
                    finally:
                        with lock:
                            completed_set.add(play_url)
                            active_progress.pop(play_url, None)
                            pct = len(completed_set) / total_count * 100
                            dp.set_overall_progress(pct,
                                f"{len(completed_set)} / {total_count} episodes")
                        q.task_done()

            num_workers = min(self.max_concurrent_downloads, total_count)
            self._log_info(f"Starting {num_workers} concurrent worker(s)…")
            threads = [threading.Thread(target=worker, daemon=True)
                       for _ in range(num_workers)]
            for th in threads:
                th.start()
            for th in threads:
                th.join()

            if self._stop.is_set():
                self._log_info("Stopped by user.")
                notifications.notify("Download Stopped",
                                     f"Stopped: {title}")
            else:
                self._log_ok("All done! ✓")
                dp.set_overall_progress(100,
                    f"{total_count} / {total_count} episodes")
                notifications.notify("Download Complete",
                                     f"✓ {title}  ·  {total_count} episode(s)")

        except Exception as e:
            msg = str(e)
            self._log_err(f"Fatal: {msg}")
            notifications.notify("Download Error", f"{title}: {msg[:80]}")
            if "403" in msg:
                self.after(0, lambda: messagebox.showwarning(
                    "Cloudflare Blocked",
                    "Cloudflare is blocking requests.\n\n"
                    "Go to Settings → choose undetected-chromedriver or FlareSolverr."))
            else:
                self.after(0, lambda m=msg: messagebox.showerror(
                    "Download Error", m))
        finally:
            downloader.allow_sleep()
            dp.set_buttons(False)
            self.after(0, lambda: self._sb_show_downloading(False))

    def _uncheck_episode(self, url: str):
        for var, _, ep_url in self.episode_vars:
            if ep_url == url:
                var.set(False)
                break


if __name__ == "__main__":
    app = App()
    app.mainloop()
