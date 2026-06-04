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

from ui.theme import (LIGHT, DARK, MIDNIGHT,
                      FONT, FONT_SM, FONT_BOLD, FONT_MONO, FONT_XL, FONT_NAV,
                      fmt_size, fmt_time, sanitize_dir, parse_range)
from pages.browse    import BrowsePage
from pages.downloads import DownloadsPage
from pages.settings  import SettingsPage


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
        self.minsize(900, 620)
        self.resizable(True, True)

        # ── shared state ──────────────────────────────────────────────────────
        self._ico_path   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appico.ico")
        self._stop       = threading.Event()
        self._stop_fetch = threading.Event()

        # bypass settings
        self.bypass_method      = "flaresolverr"
        self.browser_type       = "chrome"
        self.browser_headless   = True
        self.browser_incognito  = False
        self.use_flaresolverr   = True
        self.max_concurrent_downloads = 3

        # episode state
        self.episode_vars  = []   # [(BooleanVar, label, play_url)]
        self.episode_data  = []
        self.series_id     = ""
        self.series_title  = ""
        self.thumb_images  = {}

        # tk vars
        self.link_var        = tk.StringVar()
        self.fetch_range_var = tk.StringVar(value="all")
        self.quality_var     = tk.StringVar(value="Max")
        self.audio_var       = tk.StringVar(value="jp")
        self.dir_var         = tk.StringVar(value=os.path.expanduser("~/Downloads"))

        _sess.set_log_callback(self._log_info)

        self._apply_ttk_style()
        self._build_layout()
        self.after(0,   self._maximize)
        self.after(200, self._set_icon)
        threading.Thread(target=self._presolve_cf, daemon=True).start()

    @property
    def t(self):
        return self._theme

    # ── layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content()

    def _build_sidebar(self):
        t = self._theme
        sb = tk.Frame(self, bg=t["SIDEBAR"], width=190)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(10, weight=1)
        self._sidebar = sb

        # Logo / App name
        logo_frame = tk.Frame(sb, bg=t["SIDEBAR"], pady=18)
        logo_frame.grid(row=0, column=0, sticky="ew", padx=0)
        self._logo_frame = logo_frame
        tk.Label(logo_frame, text="🎌", font=("Segoe UI", 22),
                 bg=t["SIDEBAR"], fg=t["ACCENT"]).pack()
        tk.Label(logo_frame, text="AnimePahe", font=FONT_BOLD,
                 bg=t["SIDEBAR"], fg=t["TEXT"]).pack()
        tk.Label(logo_frame, text="Downloader v2.0", font=("Segoe UI", 7),
                 bg=t["SIDEBAR"], fg=t["SUBTEXT"]).pack()

        sep = tk.Frame(sb, bg=t["BORDER"], height=1)
        sep.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        self._sb_sep1 = sep

        # Nav buttons
        self._nav_btns = {}
        nav_items = [
            ("browse",    "🔍  Browse",    self._page_browse),
            ("downloads", "⬇  Downloads", self._page_downloads),
            ("settings",  "⚙  Settings",  self._page_settings),
        ]
        for row_idx, (key, label, cmd) in enumerate(nav_items, start=2):
            btn = tk.Button(
                sb, text=label, anchor="w",
                bg=t["SIDEBAR"], fg=t["NAV_TEXT"],
                activebackground=t["NAV_SEL"], activeforeground=t["ACCENT"],
                relief="flat", font=FONT_NAV, cursor="hand2",
                bd=0, padx=18, pady=10, width=18,
                command=cmd)
            btn.grid(row=row_idx, column=0, sticky="ew", padx=4, pady=2)
            self._nav_btns[key] = btn

        sep2 = tk.Frame(sb, bg=t["BORDER"], height=1)
        sep2.grid(row=10, column=0, sticky="ew", padx=12, pady=8)
        self._sb_sep2 = sep2

        # Bypass indicator at bottom
        self._bypass_var = tk.StringVar(value="🛡 FlareSolverr")
        bypass_lbl = tk.Label(sb, textvariable=self._bypass_var,
                              bg=t["SIDEBAR"], fg=t["SUCCESS"],
                              font=("Segoe UI", 8), cursor="hand2",
                              wraplength=160, justify="left")
        bypass_lbl.grid(row=11, column=0, sticky="ew", padx=14, pady=(0, 6))
        bypass_lbl.bind("<Button-1>", lambda e: self._page_settings())
        self._bypass_lbl = bypass_lbl

        status_lbl = tk.Label(sb, text="Click to configure →",
                              bg=t["SIDEBAR"], fg=t["SUBTEXT"],
                              font=("Segoe UI", 7))
        status_lbl.grid(row=12, column=0, sticky="ew", padx=14, pady=(0, 12))
        self._status_hint = status_lbl

    def _build_content(self):
        container = tk.Frame(self, bg=self._theme["BG"])
        container.grid(row=0, column=1, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self._container = container

        # All pages stacked in the same cell — tkraise() for instant switch
        self._browse_page    = BrowsePage(container, self)
        self._downloads_page = DownloadsPage(container, self)
        self._settings_page  = SettingsPage(container, self)

        for page in (self._browse_page, self._downloads_page, self._settings_page):
            page.grid(row=0, column=0, sticky="nsew")

        self._current_page = None
        self._page_browse()

    # ── page switching ────────────────────────────────────────────────────────

    def _show_page(self, key: str):
        pages = {
            "browse":    self._browse_page,
            "downloads": self._downloads_page,
            "settings":  self._settings_page,
        }
        page = pages[key]
        page.tkraise()
        self._current_page = key

        t = self._theme
        for k, btn in self._nav_btns.items():
            if k == key:
                btn.config(bg=t["NAV_SEL"], fg=t["ACCENT"])
            else:
                btn.config(bg=t["SIDEBAR"], fg=t["NAV_TEXT"])

    def _page_browse(self):    self._show_page("browse")
    def _page_downloads(self): self._show_page("downloads")
    def _page_settings(self):  self._show_page("settings")

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
        self._settings_page.apply_theme()
        if hasattr(self._settings_page, "_update_active_theme_btn"):
            self._settings_page._update_active_theme_btn()
        # re-highlight active nav button
        self._show_page(self._current_page)

    def _apply_sidebar_theme(self):
        t = self._theme
        self._sidebar.configure(bg=t["SIDEBAR"])
        self._logo_frame.configure(bg=t["SIDEBAR"])
        for child in self._logo_frame.winfo_children():
            try:
                child.configure(bg=t["SIDEBAR"])
                if child.winfo_class() == "Label":
                    child.configure(fg=t["TEXT"])
            except Exception:
                pass
        # fix logo icon colour
        children = self._logo_frame.winfo_children()
        if children:
            children[0].configure(fg=t["ACCENT"])
        if len(children) > 2:
            children[2].configure(fg=t["SUBTEXT"])

        self._sb_sep1.configure(bg=t["BORDER"])
        self._sb_sep2.configure(bg=t["BORDER"])
        self._bypass_lbl.configure(bg=t["SIDEBAR"], fg=t["SUCCESS"])
        self._status_hint.configure(bg=t["SIDEBAR"], fg=t["SUBTEXT"])
        for btn in self._nav_btns.values():
            btn.configure(bg=t["SIDEBAR"], fg=t["NAV_TEXT"],
                          activebackground=t["NAV_SEL"],
                          activeforeground=t["ACCENT"])
        self._container.configure(bg=t["BG"])

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

    # ── misc init ─────────────────────────────────────────────────────────────

    def _maximize(self):
        try:
            self.state("zoomed")
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)
            except Exception:
                pass

    def _set_icon(self):
        if os.path.exists(self._ico_path):
            try:
                self.iconbitmap(self._ico_path)
            except Exception:
                pass

    def _presolve_cf(self):
        self._log_info("Pre-solving Cloudflare for animepahe.pw…")
        try:
            _sess.solve_cf_once(url="https://animepahe.pw", force=False, log_fn=self._log_info)
        except Exception as e:
            self._log_err(f"Pre-solve animepahe failed: {e}")
        self._log_info("Pre-solving Cloudflare for kwik.cx…")
        try:
            _sess.solve_cf_once(url="https://kwik.cx/f/invalid", force=False, log_fn=self._log_info)
        except Exception as e:
            self._log_err(f"Pre-solve kwik failed: {e}")

    # ── logging ───────────────────────────────────────────────────────────────

    def _log(self, msg: str, tag: str = ""):
        self._downloads_page.log(msg, tag)

    def _log_ok(self, msg):     self._log(f"[SUCCESS] {msg}", "success")
    def _log_err(self, msg):    self._log(f"[ERROR]   {msg}", "error")
    def _log_info(self, msg):   self._log(f"[INFO]    {msg}", "info")
    def _log_header(self, msg):
        self._log(f"{'─'*50}\n{msg}\n{'─'*50}", "header")

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
            meta      = animepahe.fetch_metadata(url, is_series, log=self._log_info, **cf_kw)
            title     = meta.get("title", "Unknown")
            poster    = meta.get("poster", "")
            series_id = meta.get("id") or (animepahe.get_series_id(url) if is_series else None)

            if stopped(): return

            type_str  = meta.get("type", "")
            ep_count  = meta.get("episode_count", "")
            meta_str  = "  ·  ".join(x for x in [type_str, f"{ep_count} eps" if ep_count else ""] if x)

            self.after(0, lambda: self._browse_page._update_anime_header(title, meta_str, poster))
            self.after(0, lambda: self._browse_page.set_url_status(
                f"✓  {title}" + (f"  ·  {meta_str}" if meta_str else ""),
                self.t["SUCCESS"]))
            self._log_ok(f"Title: {title}")

            if is_series:
                total_str = str(meta.get("episode_count") or "0")
                try:
                    total = int(total_str)
                except ValueError:
                    total = 0

                if total == 0:
                    self._log_info("Fetching episode count…")
                    try:
                        total = animepahe.get_episode_count(series_id, url, **cf_kw)
                    except Exception as e:
                        self._log_err(f"Couldn't get exact count: {e}. Assuming 1000.")
                        total = 1000

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

                self._log_info(f"Fetching episodes {start_ep}–{end_ep}…")

                raw_episodes = []
                for page in range(start_page, end_page + 1):
                    if stopped():
                        self._log_info("Fetch stopped.")
                        return
                    self._log_info(f"  Page {page}/{end_page}…")
                    r = _sess.request(
                        "GET",
                        f"{animepahe.API_BASE}/api?m=release&id={series_id}"
                        f"&sort=episode_asc&page={page}",
                        headers={"Referer": "https://animepahe.pw/"},
                        **cf_kw,
                    )
                    r.raise_for_status()
                    batch = r.json().get("data", [])
                    for ep in batch:
                        ep_num = ep.get("episode", 0)
                        if start_ep <= ep_num <= end_ep:
                            raw_episodes.append(ep)
                    self._log_info(f"  {len(raw_episodes)} episodes in range so far.")
            else:
                series_id2, session = _get_play_ids(url)
                raw_episodes = [{"episode": 1, "title": "Episode", "snapshot": "",
                                 "session": session, "filler": 0, "audio": "jpn"}]
                series_id = series_id2

            if stopped(): return

            self._log_ok(f"Loaded {len(raw_episodes)} episodes.")
            self.after(0, lambda eps=raw_episodes, t=title, sid=series_id:
                       self._browse_page.populate_episodes(eps, t, sid))

        except Exception as e:
            self._log_err(f"Fetch failed: {e}")
            self.after(0, lambda: self._browse_page.set_url_status(f"✗  {e}", self.t["DANGER"]))
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

            import queue
            q = queue.Queue()
            for idx, play_url in enumerate(play_links):
                q.put((idx, play_url))

            lock = threading.Lock()
            active_progress  = {}
            completed_set    = set()

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
                            td = sum(d for d, _, _, _ in active_progress.values())
                            ts = sum(t for _, t, _, _ in active_progress.values())
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
                            dp.set_file_progress(pct, f"{size_s}   {spd_s}   {eta_s}")
                            dp.set_overall_progress(overall,
                                f"{n_done} / {total_count} episodes")

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
            else:
                self._log_ok("All done! ✓")
                dp.set_overall_progress(100, f"{total_count} / {total_count} episodes")

        except Exception as e:
            msg = str(e)
            self._log_err(f"Fatal: {msg}")
            if "403" in msg:
                self.after(0, lambda: messagebox.showwarning(
                    "Cloudflare Blocked",
                    "Cloudflare is blocking requests.\n\n"
                    "Go to Settings → choose undetected-chromedriver or FlareSolverr."))
            else:
                self.after(0, lambda m=msg: messagebox.showerror("Download Error", m))
        finally:
            dp.set_buttons(False)

    def _uncheck_episode(self, url: str):
        for var, _, ep_url in self.episode_vars:
            if ep_url == url:
                var.set(False)
                break


if __name__ == "__main__":
    app = App()
    app.mainloop()
