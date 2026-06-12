import threading
import tkinter as tk
from tkinter import ttk

import animepahe
import session as _sess
from ui.theme import (FONT, FONT_SM, FONT_BOLD, FONT_LG, FONT_XS,
                      parse_range)
from ui.widgets import Spinner, AutoSuggest, FadeLabel


# ── Hero slideshow data ────────────────────────────────────────────────────────
_SLIDES = [
    {
        "icon": "🎌",
        "title": "Welcome to AnimePahe Downloader",
        "body": "Paste a series or episode URL in the field above, then click Fetch.\nYour episode list will appear here with thumbnails.",
    },
    {
        "icon": "🔍",
        "title": "Search while you type",
        "body": "Type an anime name (not a URL) in the search field and\nauto-complete suggestions will appear instantly.",
    },
    {
        "icon": "⬇",
        "title": "Flexible quality & language",
        "body": "Choose Max / Min or a specific resolution (1080p, 720p…).\nSelect Japanese, English dub, or Chinese audio.",
    },
    {
        "icon": "🛡",
        "title": "Cloudflare bypass built-in",
        "body": "If the site is blocked, head to Settings and choose\nundetected-chromedriver (best) or FlareSolverr.",
    },
    {
        "icon": "📦",
        "title": "Batch downloads",
        "body": "Fetch a full series, cherry-pick episodes with checkboxes,\nthen start up to 5 concurrent downloads.",
    },
]

# How many rows above/below the viewport to keep loaded (lazy-load buffer)
_LAZY_BUFFER_PX = 300


class BrowsePage(tk.Frame):
    def __init__(self, parent, app):
        self.app = app
        t = app.t
        super().__init__(parent, bg=t["BG"])
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._slide_idx  = 0
        self._slide_job  = None
        self._hero_shown = True
        self._suggest    = None

        # Lazy-load state
        self._thumb_pending: dict[int, tuple] = {}   # row_idx → (url, label)
        self._thumb_loaded:  set[int]         = set()
        self._lazy_job = None

        self._build(t)
        self._start_slideshow()

    def _build(self, t):
        self._build_anime_header(t)
        self._build_url_card(t)
        self._build_episode_section(t)

    # ── anime header ──────────────────────────────────────────────────────────

    def _build_anime_header(self, t):
        hdr = tk.Frame(self, bg=t["CARD"], padx=16, pady=12)
        hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        hdr.grid_columnconfigure(1, weight=1)
        self._hdr = hdr

        # Poster placeholder — larger now that we're displaying it properly
        self._poster_lbl = tk.Label(
            hdr, text="📺", bg=t["CARD"], fg=t["SUBTEXT"],
            font=("Segoe UI", 26), width=6, height=4, relief="flat")
        self._poster_lbl.grid(row=0, column=0, rowspan=2, padx=(0, 14))

        name_frame = tk.Frame(hdr, bg=t["CARD"])
        name_frame.grid(row=0, column=1, sticky="ew")
        name_frame.grid_columnconfigure(0, weight=1)

        self._title_lbl = FadeLabel(
            name_frame,
            target_fg=t["TEXT"],
            bg=t["CARD"],
            text="AnimePahe Downloader",
            font=FONT_LG, anchor="w")
        self._title_lbl.grid(row=0, column=0, sticky="w")

        self._meta_lbl = FadeLabel(
            name_frame,
            target_fg=t["SUBTEXT"],
            bg=t["CARD"],
            text="Paste a URL and click Fetch to load episodes.",
            font=FONT_SM, anchor="w")
        self._meta_lbl.grid(row=1, column=0, sticky="w")

        # Episode count label (updated once exact count is known)
        self._epcount_lbl = tk.Label(
            name_frame, text="", bg=t["CARD"], fg=t["ACCENT"],
            font=FONT_SM, anchor="w")
        self._epcount_lbl.grid(row=2, column=0, sticky="w")

        # Fetching spinner
        self._spinner = Spinner(hdr, size=28,
                                color=t["ACCENT"], bg=t["CARD"],
                                thickness=3, speed=30)
        self._spinner.grid(row=0, column=2, rowspan=2, padx=(8, 0))
        self._spinner.grid_remove()

    def _update_anime_header(self, title: str, meta_str: str, poster_url: str):
        self._title_lbl.config(text=title, fg=self.app.t["TEXT"])
        self._title_lbl.fade_in()
        self._meta_lbl.config(
            text=meta_str if meta_str else "Loaded successfully.",
            fg=self.app.t["SUBTEXT"])
        self._meta_lbl.fade_in(delay_ms=120)
        self._epcount_lbl.config(text="")   # reset until exact count arrives
        if poster_url:
            threading.Thread(
                target=self._load_poster, args=(poster_url,), daemon=True
            ).start()

    def update_episode_count(self, total: int, series_title: str = ""):
        """Called from app thread once the exact episode count is known."""
        lbl = f"{total} episodes" + (f" — {series_title}" if series_title else "")
        self._epcount_lbl.config(text=lbl, fg=self.app.t["ACCENT"])

    def _load_poster(self, url: str):
        try:
            from PIL import Image, ImageTk
            import io
            resp = _sess.request("GET", url, headers={"Referer": "https://animepahe.pw"})
            data = resp.content
            if not data:
                raise ValueError("empty")
            img   = Image.open(io.BytesIO(data))
            img   = img.resize((72, 100), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._poster_photo = photo
            self.after(0, lambda: self._poster_lbl.config(
                image=photo, text="", width=72, height=100,
                font=FONT_SM, relief="flat"))
        except Exception:
            pass

    # ── URL card ──────────────────────────────────────────────────────────────

    def _build_url_card(self, t):
        card = tk.Frame(self, bg=t["CARD"], padx=16, pady=12)
        card.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))
        card.grid_columnconfigure(1, weight=1)
        self._url_card = card

        tk.Label(card, text="URL", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_BOLD, width=5, anchor="w").grid(row=0, column=0, sticky="w")

        self._url_entry = tk.Entry(
            card, textvariable=self.app.link_var,
            bg=t["PANEL"], fg=t["TEXT"],
            insertbackground=t["ACCENT"], relief="flat", font=FONT,
            highlightthickness=1,
            highlightbackground=t["BORDER"], highlightcolor=t["ACCENT"])
        self._url_entry.grid(row=0, column=1, sticky="ew", padx=(6, 8))
        self._url_entry.insert(0, "Paste AnimePahe series or episode URL…")
        self._url_entry.config(fg=t["SUBTEXT"])
        self._url_entry.bind("<FocusIn>",  self._ph_clear)
        self._url_entry.bind("<FocusOut>", self._ph_restore)
        self._url_entry.bind("<KeyRelease>", lambda e: self.app.validate_url())

        # Auto-suggest on URL entry
        self._suggest = AutoSuggest(
            entry=self._url_entry,
            app=self.app,
            fetch_fn=lambda q: animepahe.search_anime(
                q, log=lambda _: None,
                **self.app._cf_kw()),
            on_select=self._on_suggest_select,
        )

        tk.Label(card, text="Range", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_SM, anchor="w").grid(row=0, column=2, padx=(0, 4), sticky="w")
        self._range_entry = tk.Entry(
            card, textvariable=self.app.fetch_range_var,
            bg=t["PANEL"], fg=t["TEXT"],
            insertbackground=t["ACCENT"], relief="flat", font=FONT, width=8,
            highlightthickness=1,
            highlightbackground=t["BORDER"], highlightcolor=t["ACCENT"])
        self._range_entry.grid(row=0, column=3, padx=(0, 8))

        self._paste_btn = self._btn(card, "📋 Paste", self.app.paste_url,
                                    t["HDR_BTN"], t["TEXT"])
        self._paste_btn.grid(row=0, column=4, padx=(0, 4))

        self._fetch_btn = self._btn(card, "🔄 Fetch", self.app.fetch_episodes,
                                    t["ACCENT"], "white")
        self._fetch_btn.grid(row=0, column=5, padx=(0, 4))

        self._stop_fetch_btn = self._btn(card, "✕ Stop", self.app.stop_fetch,
                                         t["DANGER"], "white")
        self._stop_fetch_btn.grid(row=0, column=6)
        self._stop_fetch_btn.config(state="disabled")

        # Status row
        self._url_status_var = tk.StringVar(value="")
        self._url_status_lbl = tk.Label(
            card, textvariable=self._url_status_var,
            fg=t["SUBTEXT"], bg=t["CARD"], font=FONT_SM, anchor="w")
        self._url_status_lbl.grid(row=1, column=1, columnspan=5, sticky="w", pady=(4, 0))

    def _btn(self, parent, text, cmd, bg, fg):
        b = tk.Button(parent, text=text, command=cmd,
                      bg=bg, fg=fg,
                      activebackground=self.app.t["ACCENT_HV"],
                      activeforeground="white",
                      relief="flat", font=FONT_SM, cursor="hand2",
                      bd=0, padx=12, pady=6)
        return b

    def _on_suggest_select(self, result: dict):
        """Called when user picks an auto-suggest result."""
        session = result.get("session", "")
        if session:
            url = f"https://animepahe.pw/anime/{session}"
        else:
            url = result.get("url", "")
        if url:
            self.app.link_var.set(url)
            self._url_entry.config(fg=self.app.t["TEXT"])
            self.app.validate_url()
            self.after(100, self.app.fetch_episodes)

    def set_url_status(self, msg: str, color: str):
        self._url_status_var.set(msg)
        self._url_status_lbl.config(fg=color)

    def set_fetching(self, active: bool):
        if active:
            self._fetch_btn.config(state="disabled", text="⏳ Fetching…")
            self._stop_fetch_btn.config(state="normal")
            self._spinner.grid()
            self._spinner.start()
        else:
            self._fetch_btn.config(state="normal", text="🔄 Fetch")
            self._stop_fetch_btn.config(state="disabled")
            self._spinner.stop()
            self._spinner.grid_remove()

    def _ph_clear(self, event):
        if self._url_entry.get() == "Paste AnimePahe series or episode URL…":
            self._url_entry.delete(0, "end")
            self._url_entry.config(fg=self.app.t["TEXT"])

    def _ph_restore(self, event):
        if not self._url_entry.get():
            self._url_entry.insert(0, "Paste AnimePahe series or episode URL…")
            self._url_entry.config(fg=self.app.t["SUBTEXT"])

    # ── hero slideshow ────────────────────────────────────────────────────────

    def _start_slideshow(self):
        self._schedule_slide()

    def _schedule_slide(self):
        if self._slide_job:
            self.after_cancel(self._slide_job)
        self._slide_job = self.after(4200, self._next_slide)

    def _next_slide(self):
        if not self._hero_shown:
            return
        self._slide_idx = (self._slide_idx + 1) % len(_SLIDES)
        self._animate_slide()
        self._schedule_slide()

    def _animate_slide(self):
        if not (self._hero_shown and hasattr(self, "_slide_icon_lbl")):
            return
        slide = _SLIDES[self._slide_idx]
        self._slide_icon_lbl.config(text=slide["icon"])
        self._slide_title_lbl.config(text=slide["title"], fg=self.app.t["BG"])
        self._slide_body_lbl.config(text=slide["body"], fg=self.app.t["BG"])
        self._slide_title_lbl._target_fg = self.app.t["TEXT"]
        self._slide_body_lbl._target_fg  = self.app.t["SUBTEXT"]
        self._slide_title_lbl.fade_in()
        self._slide_body_lbl.fade_in(delay_ms=100)
        self._update_slide_dots()

    def _update_slide_dots(self):
        if not hasattr(self, "_slide_dots"):
            return
        t = self.app.t
        for i, dot in enumerate(self._slide_dots):
            dot.config(fg=t["ACCENT"] if i == self._slide_idx else t["BORDER"])

    # ── episode section ───────────────────────────────────────────────────────

    def _build_episode_section(self, t):
        outer = tk.Frame(self, bg=t["BG"])
        outer.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 14))
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        self._ep_outer = outer

        # ── Hero (shown when no episodes loaded) ──
        self._hero = tk.Frame(outer, bg=t["BG"])
        self._hero.grid(row=0, column=0, sticky="nsew")

        hero_inner = tk.Frame(self._hero, bg=t["CARD"], padx=32, pady=28)
        hero_inner.place(relx=0.5, rely=0.5, anchor="center")
        self._hero_inner = hero_inner

        s = _SLIDES[0]
        self._slide_icon_lbl = tk.Label(
            hero_inner, text=s["icon"],
            font=("Segoe UI", 42), bg=t["CARD"], fg=t["ACCENT"])
        self._slide_icon_lbl.pack(pady=(0, 8))

        self._slide_title_lbl = FadeLabel(
            hero_inner, target_fg=t["TEXT"], bg=t["CARD"],
            text=s["title"], font=FONT_LG)
        self._slide_title_lbl.pack()
        self._slide_title_lbl.fade_in()

        self._slide_body_lbl = FadeLabel(
            hero_inner, target_fg=t["SUBTEXT"], bg=t["CARD"],
            text=s["body"], font=FONT_SM, justify="center")
        self._slide_body_lbl.pack(pady=(6, 14))
        self._slide_body_lbl.fade_in(delay_ms=150)

        # Dot indicators
        dots_frame = tk.Frame(hero_inner, bg=t["CARD"])
        dots_frame.pack()
        self._slide_dots = []
        for i in range(len(_SLIDES)):
            d = tk.Label(dots_frame, text="●", font=("Segoe UI", 8),
                         bg=t["CARD"],
                         fg=t["ACCENT"] if i == 0 else t["BORDER"],
                         cursor="hand2")
            d.pack(side="left", padx=3)
            d.bind("<Button-1>", lambda e, idx=i: self._jump_slide(idx))
            self._slide_dots.append(d)

        # ── Episode list area ──
        ep_container = tk.Frame(outer, bg=t["BG"])
        ep_container.grid(row=0, column=0, sticky="nsew")
        ep_container.grid_rowconfigure(1, weight=1)
        ep_container.grid_columnconfigure(0, weight=1)
        self._ep_container = ep_container

        # Controls bar
        ctrl = tk.Frame(ep_container, bg=t["CARD"], padx=14, pady=8)
        ctrl.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ctrl.grid_columnconfigure(3, weight=1)
        self._ep_ctrl = ctrl

        self._ep_count_var = tk.StringVar(value="Episodes")
        tk.Label(ctrl, textvariable=self._ep_count_var,
                 fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_BOLD, anchor="w").grid(row=0, column=0, padx=(0, 10), sticky="w")

        self._last5_var = tk.BooleanVar(value=False)
        self._last5_chk = tk.Checkbutton(
            ctrl, text="Last 5", variable=self._last5_var,
            bg=t["CARD"], fg=t["TEXT"], selectcolor=t["CHK_BG"],
            activebackground=t["CARD"], font=FONT_SM, cursor="hand2",
            command=self._filter_episodes)
        self._last5_chk.grid(row=0, column=1, padx=(0, 8))

        self._ep_filter_var = tk.StringVar()
        self._ep_filter_var.trace_add("write", lambda *_: self._filter_episodes())
        self._filter_entry = tk.Entry(
            ctrl, textvariable=self._ep_filter_var,
            bg=t["PANEL"], fg=t["SUBTEXT"],
            insertbackground=t["ACCENT"], relief="flat", font=FONT_SM, width=16,
            highlightthickness=1,
            highlightbackground=t["BORDER"], highlightcolor=t["ACCENT"])
        self._filter_entry.insert(0, "Filter episodes…")
        self._filter_entry.bind("<FocusIn>",  self._filter_ph_clear)
        self._filter_entry.bind("<FocusOut>", self._filter_ph_restore)
        self._filter_entry.grid(row=0, column=2, padx=(0, 12), sticky="ew")

        tk.Label(ctrl, text="Quality", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_SM).grid(row=0, column=3, padx=(0, 4), sticky="e")
        self._q_cb = ttk.Combobox(
            ctrl, textvariable=self.app.quality_var, width=8,
            values=["Max", "Min", "1080", "720", "480", "360"],
            state="readonly", font=FONT_SM)
        self._q_cb.grid(row=0, column=4, padx=(0, 10))

        tk.Label(ctrl, text="Audio", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_SM).grid(row=0, column=5, padx=(0, 4))
        self._a_cb = ttk.Combobox(
            ctrl, textvariable=self.app.audio_var, width=13,
            values=["jp (Japanese)", "en (English)", "zh (Chinese)"],
            state="readonly", font=FONT_SM)
        self._a_cb.grid(row=0, column=6)

        # Episode list canvas area
        list_border = tk.Frame(ep_container, bg=t["BORDER"], padx=1, pady=1)
        list_border.grid(row=1, column=0, sticky="nsew")
        list_border.grid_rowconfigure(0, weight=1)
        list_border.grid_columnconfigure(0, weight=1)
        self._list_border = list_border

        list_bg = tk.Frame(list_border, bg=t["LIST_BG"])
        list_bg.grid(row=0, column=0, sticky="nsew")
        list_bg.grid_rowconfigure(0, weight=1)
        list_bg.grid_columnconfigure(0, weight=1)
        self._list_bg = list_bg

        self._ep_canvas = tk.Canvas(list_bg, bg=t["LIST_BG"], highlightthickness=0)
        self._ep_sb = ttk.Scrollbar(list_bg, orient="vertical",
                                    command=self._ep_canvas.yview)
        self._ep_canvas.configure(yscrollcommand=self._ep_sb.set)
        self._ep_inner = tk.Frame(self._ep_canvas, bg=t["LIST_BG"])
        self._ep_win = self._ep_canvas.create_window(
            (0, 0), window=self._ep_inner, anchor="nw")

        self._ep_inner.bind("<Configure>", self._on_inner_cfg)
        self._ep_canvas.bind("<Configure>", self._on_canvas_cfg)
        self._ep_canvas.bind("<MouseWheel>", self._on_scroll)
        self._ep_canvas.bind("<Button-4>",
                             lambda e: self._ep_canvas.yview_scroll(-1, "units"))
        self._ep_canvas.bind("<Button-5>",
                             lambda e: self._ep_canvas.yview_scroll(1, "units"))

        self._ep_canvas.grid(row=0, column=0, sticky="nsew")
        self._ep_sb.grid(row=0, column=1, sticky="ns")

        # Start with hero on top
        self._hero.tkraise()

    def _jump_slide(self, idx: int):
        self._slide_idx = idx
        self._animate_slide()
        self._schedule_slide()

    def _on_inner_cfg(self, event):
        self._ep_canvas.configure(scrollregion=self._ep_canvas.bbox("all"))

    def _on_canvas_cfg(self, event):
        self._ep_canvas.itemconfig(self._ep_win, width=event.width)

    def _on_scroll(self, event):
        self._ep_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self._schedule_lazy_load()

    def _filter_ph_clear(self, event):
        if self._filter_entry.get() == "Filter episodes…":
            self._filter_entry.delete(0, "end")
            self._filter_entry.config(fg=self.app.t["TEXT"])

    def _filter_ph_restore(self, event):
        if not self._filter_entry.get():
            self._filter_entry.insert(0, "Filter episodes…")
            self._filter_entry.config(fg=self.app.t["SUBTEXT"])

    def _filter_episodes(self):
        flt      = self._ep_filter_var.get().strip().lower()
        is_last5 = self._last5_var.get()
        total    = len(self.app.episode_vars)
        skip_flt = (flt in ("", "filter episodes…"))

        for i, (var, label, url) in enumerate(self.app.episode_vars):
            rows  = self._ep_inner.grid_slaves(row=i + 2)
            frame = rows[0] if rows else None
            if frame is None:
                continue
            show = True
            if not skip_flt and flt not in label.lower():
                show = False
            if is_last5 and i < total - 5:
                show = False
            if show:
                frame.grid()
            else:
                frame.grid_remove()

    # ── lazy thumbnail loading ────────────────────────────────────────────────

    def _schedule_lazy_load(self, delay_ms: int = 80):
        """Debounced trigger for viewport-based thumbnail loading."""
        if self._lazy_job:
            self.after_cancel(self._lazy_job)
        self._lazy_job = self.after(delay_ms, self._do_lazy_load)

    def _do_lazy_load(self):
        """Load thumbnails for rows currently visible in the canvas viewport."""
        self._lazy_job = None
        if not self._thumb_pending:
            return

        try:
            canvas   = self._ep_canvas
            inner    = self._ep_inner
            c_h      = canvas.winfo_height()
            total_h  = inner.winfo_reqheight()
            if total_h == 0:
                return

            # Fraction range of the scrolled region that is visible
            y_frac   = canvas.yview()
            top_px   = y_frac[0] * total_h
            bot_px   = y_frac[1] * total_h

            # Add buffer zone
            top_px  -= _LAZY_BUFFER_PX
            bot_px  += _LAZY_BUFFER_PX

            # Walk pending items and fire loads for visible ones
            to_load = []
            for row_idx, (url, label) in list(self._thumb_pending.items()):
                try:
                    y = label.winfo_y()
                    h = label.winfo_reqheight()
                except Exception:
                    continue
                if top_px <= y + h and y <= bot_px:
                    to_load.append(row_idx)

            for row_idx in to_load:
                if row_idx in self._thumb_pending:
                    url, label = self._thumb_pending.pop(row_idx)
                    self._thumb_loaded.add(row_idx)
                    threading.Thread(
                        target=self._load_thumbnail,
                        args=(url, label, row_idx),
                        daemon=True
                    ).start()
        except Exception:
            pass

    # ── episode list population ───────────────────────────────────────────────

    def populate_episodes(self, raw_episodes: list, title: str, series_id: str,
                          total_count: int = 0):
        """
        Render episode rows.  `total_count` is the authoritative episode count
        returned by the API (may be > len(raw_episodes) if a range was fetched).
        """
        t = self.app.t
        self.app.series_title = title
        self.app.series_id    = series_id
        self.app.episode_data = raw_episodes
        self.app.thumb_images = {}

        # Reset lazy-load state
        self._thumb_pending.clear()
        self._thumb_loaded.clear()
        if self._lazy_job:
            self.after_cancel(self._lazy_job)
            self._lazy_job = None

        for w in self._ep_inner.winfo_children():
            w.destroy()
        self.app.episode_vars.clear()

        # Switch from hero to episode list
        self._hero_shown = False
        if self._slide_job:
            self.after_cancel(self._slide_job)
        self._ep_container.tkraise()

        # Update control bar episode count
        count_label = (
            f"Episodes ({len(raw_episodes)} of {total_count})"
            if total_count and total_count != len(raw_episodes)
            else f"Episodes ({len(raw_episodes)})"
        )
        self._ep_count_var.set(count_label)

        # Update header episode count label
        if total_count:
            self._epcount_lbl.config(
                text=f"{total_count} episodes total",
                fg=self.app.t["ACCENT"])
        else:
            self._epcount_lbl.config(text="")

        if not raw_episodes:
            tk.Label(self._ep_inner, text="No episodes found.",
                     fg=t["DANGER"], bg=t["LIST_BG"], font=FONT_SM).grid(
                row=0, column=0, padx=20, pady=10)
            return

        self._ep_inner.grid_columnconfigure(0, weight=1)

        # Column header
        hdr = tk.Frame(self._ep_inner, bg=t["BORDER"])
        hdr.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))
        hdr.grid_columnconfigure(2, weight=1)
        for col, (txt, w) in enumerate([(" ✓ ", 4), ("Thumbnail", 12),
                                         ("Episode", 0), ("Audio", 8), ("Tag", 6)]):
            kw = {"sticky": "w"} if col == 2 else {}
            tk.Label(hdr, text=txt, bg=t["BORDER"], fg=t["SUBTEXT"],
                     font=FONT_XS, width=w).grid(row=0, column=col, **kw)

        # Select all/none row
        sel_row = tk.Frame(self._ep_inner, bg=t["CARD"])
        sel_row.grid(row=1, column=0, sticky="ew", padx=4, pady=(2, 4))
        tk.Button(sel_row, text="✓ All", command=self._select_all,
                  bg=t["HDR_BTN"], fg=t["TEXT"], relief="flat", font=FONT_XS,
                  cursor="hand2", bd=0, padx=8, pady=3).pack(side="left", padx=(8, 4))
        tk.Button(sel_row, text="✗ None", command=self._deselect_all,
                  bg=t["HDR_BTN"], fg=t["TEXT"], relief="flat", font=FONT_XS,
                  cursor="hand2", bd=0, padx=8, pady=3).pack(side="left", padx=(0, 8))
        ep_summary = (f"{len(raw_episodes)} episodes shown"
                      + (f" / {total_count} total" if total_count and
                         total_count != len(raw_episodes) else ""))
        tk.Label(sel_row, text=ep_summary,
                 bg=t["CARD"], fg=t["SUBTEXT"], font=FONT_XS).pack(side="left")

        # Build rows — thumbnails registered in _thumb_pending (lazy)
        for i, ep in enumerate(raw_episodes):
            ep_num   = ep.get("episode", i + 1)
            ep_title = ep.get("title") or f"Episode {ep_num}"
            session  = ep.get("session", "")
            snap_url = ep.get("snapshot", "")
            audio    = ep.get("audio", "jpn")
            filler   = ep.get("filler", 0)
            play_url = f"https://animepahe.pw/play/{series_id}/{session}"
            label    = f"Ep {ep_num} — {ep_title}"

            var = tk.BooleanVar(value=True)
            self.app.episode_vars.append((var, label, play_url))

            row_bg = t["LIST_BG"] if i % 2 == 0 else t["ROW_ALT"]
            row = tk.Frame(self._ep_inner, bg=row_bg,
                           highlightthickness=1, highlightbackground=row_bg)
            row.grid(row=i + 2, column=0, sticky="ew", padx=4, pady=1)
            row.grid_columnconfigure(2, weight=1)

            row.bind("<Enter>",
                     lambda e, f=row: f.config(highlightbackground=t["ACCENT"]))
            row.bind("<Leave>",
                     lambda e, f=row, bg=row_bg: f.config(highlightbackground=bg))

            cb = tk.Checkbutton(row, variable=var, bg=row_bg,
                                activebackground=row_bg, selectcolor=t["CHK_BG"],
                                cursor="hand2", relief="flat", bd=0)
            cb.grid(row=0, column=0, padx=(8, 4), pady=5)

            thumb_lbl = tk.Label(row, text="🖼", bg=row_bg, fg=t["SUBTEXT"],
                                 width=11, height=4, font=FONT_XS, relief="flat")
            thumb_lbl.grid(row=0, column=1, padx=(0, 8), pady=4)

            info = tk.Frame(row, bg=row_bg)
            info.grid(row=0, column=2, sticky="ew", padx=(0, 8), pady=4)
            tk.Label(info, text=f"Ep {ep_num}", fg=t["ACCENT"],
                     bg=row_bg, font=FONT_BOLD, anchor="w").pack(anchor="w")
            tk.Label(info, text=ep_title, fg=t["TEXT"],
                     bg=row_bg, font=FONT_SM, anchor="w").pack(anchor="w")

            audio_norm = audio.lower()
            if "jpn" in audio_norm or audio_norm == "jp":
                ac, at = t["ACCENT"], "JPN"
            elif "eng" in audio_norm or audio_norm == "en":
                ac, at = t["SUCCESS"], "ENG"
            else:
                ac, at = t.get("WARN", t["SUBTEXT"]), audio.upper()[:3]
            tk.Label(row, text=at, fg="white", bg=ac,
                     font=FONT_XS, padx=6, pady=2, width=4).grid(
                row=0, column=3, padx=(0, 6), pady=5)

            tag_txt = "Filler" if filler else ""
            tag_col = "#f97316" if filler else row_bg
            tk.Label(row, text=tag_txt,
                     fg="white" if filler else row_bg,
                     bg=tag_col, font=FONT_XS, padx=4, pady=2, width=5).grid(
                row=0, column=4, padx=(0, 8), pady=5)

            # Register thumbnail for lazy loading
            if snap_url:
                self._thumb_pending[i] = (snap_url, thumb_lbl)

        self._ep_canvas.yview_moveto(0)

        # Trigger initial lazy load after layout settles
        self.after(150, self._schedule_lazy_load)

        # Keep loading as the user scrolls
        self._ep_canvas.bind("<<ScrollbarMoved>>", lambda e: self._schedule_lazy_load())

    def _load_thumbnail(self, url: str, label: tk.Label, index: int):
        try:
            from PIL import Image, ImageTk
            import io
            resp = _sess.request("GET", url,
                                 headers={"Referer": "https://animepahe.pw"})
            data = resp.content
            if not data:
                raise ValueError("empty")
            img   = Image.open(io.BytesIO(data))
            img   = img.resize((88, 50), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.app.thumb_images[index] = photo

            def _apply(lbl=label, ph=photo):
                try:
                    lbl.config(image=ph, text="", width=88, height=50)
                    lbl.image = ph   # keep reference
                except Exception:
                    pass

            self.after(0, _apply)
        except Exception:
            pass

    def _select_all(self):
        for var, _, _ in self.app.episode_vars:
            var.set(True)

    def _deselect_all(self):
        for var, _, _ in self.app.episode_vars:
            var.set(False)

    # ── theme ─────────────────────────────────────────────────────────────────

    def apply_theme(self):
        t = self.app.t
        self.configure(bg=t["BG"])
        self._hdr.configure(bg=t["CARD"])
        self._poster_lbl.configure(bg=t["CARD"], fg=t["SUBTEXT"])
        self._title_lbl.configure(bg=t["CARD"], fg=t["TEXT"])
        self._title_lbl._target_fg = t["TEXT"]
        self._title_lbl._bg_hex    = t["CARD"]
        self._meta_lbl.configure(bg=t["CARD"], fg=t["SUBTEXT"])
        self._meta_lbl._target_fg  = t["SUBTEXT"]
        self._meta_lbl._bg_hex     = t["CARD"]
        self._epcount_lbl.configure(bg=t["CARD"], fg=t["ACCENT"])
        self._spinner.set_color(t["ACCENT"])
        self._spinner.set_bg(t["CARD"])

        self._url_card.configure(bg=t["CARD"])
        self._url_entry.configure(bg=t["PANEL"], fg=t["TEXT"],
                                  insertbackground=t["ACCENT"],
                                  highlightbackground=t["BORDER"],
                                  highlightcolor=t["ACCENT"])
        self._range_entry.configure(bg=t["PANEL"], fg=t["TEXT"],
                                    insertbackground=t["ACCENT"],
                                    highlightbackground=t["BORDER"],
                                    highlightcolor=t["ACCENT"])
        self._url_status_lbl.configure(bg=t["CARD"])
        self._paste_btn.configure(bg=t["HDR_BTN"], fg=t["TEXT"])
        self._fetch_btn.configure(bg=t["ACCENT"], fg="white")
        self._stop_fetch_btn.configure(bg=t["DANGER"], fg="white")

        self._ep_outer.configure(bg=t["BG"])
        self._ep_ctrl.configure(bg=t["CARD"])
        self._last5_chk.configure(bg=t["CARD"], fg=t["TEXT"],
                                  selectcolor=t["CHK_BG"])
        self._filter_entry.configure(bg=t["PANEL"], fg=t["TEXT"],
                                     insertbackground=t["ACCENT"],
                                     highlightbackground=t["BORDER"])
        self._list_border.configure(bg=t["BORDER"])
        self._list_bg.configure(bg=t["LIST_BG"])
        self._ep_canvas.configure(bg=t["LIST_BG"])
        self._ep_inner.configure(bg=t["LIST_BG"])

        # Hero
        self._hero.configure(bg=t["BG"])
        self._hero_inner.configure(bg=t["CARD"])
        self._slide_icon_lbl.configure(bg=t["CARD"], fg=t["ACCENT"])
        self._slide_title_lbl.configure(bg=t["CARD"], fg=t["TEXT"])
        self._slide_title_lbl._target_fg = t["TEXT"]
        self._slide_title_lbl._bg_hex    = t["CARD"]
        self._slide_body_lbl.configure(bg=t["CARD"], fg=t["SUBTEXT"])
        self._slide_body_lbl._target_fg  = t["SUBTEXT"]
        self._slide_body_lbl._bg_hex     = t["CARD"]
        for i, d in enumerate(self._slide_dots):
            d.configure(bg=t["CARD"],
                        fg=t["ACCENT"] if i == self._slide_idx else t["BORDER"])
        self._ep_container.configure(bg=t["BG"])
