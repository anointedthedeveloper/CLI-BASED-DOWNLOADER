import tkinter as tk
from tkinter import ttk

import session as _sess
import flaresolverr as _flaresolverr
from ui.theme import (FONT, FONT_SM, FONT_BOLD, FONT_LG, FONT_XS,
                      LIGHT, DARK, MIDNIGHT)


class SettingsPage(tk.Frame):
    def __init__(self, parent, app):
        self.app = app
        t = app.t
        super().__init__(parent, bg=t["BG"])
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build(t)

    def _build(self, t):
        scroll_canvas = tk.Canvas(self, bg=t["BG"], highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=sb.set)
        scroll_canvas.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self._scroll_canvas = scroll_canvas
        self._sb = sb

        inner = tk.Frame(scroll_canvas, bg=t["BG"])
        self._inner_win = scroll_canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", self._on_inner_cfg)
        scroll_canvas.bind("<Configure>", self._on_canvas_cfg)
        scroll_canvas.bind("<MouseWheel>", self._on_scroll)
        scroll_canvas.bind("<Button-4>", lambda e: scroll_canvas.yview_scroll(-1, "units"))
        scroll_canvas.bind("<Button-5>", lambda e: scroll_canvas.yview_scroll(1, "units"))
        self._inner = inner

        content = tk.Frame(inner, bg=t["BG"], padx=32, pady=20)
        content.pack(fill="both", expand=True)
        self._content = content

        tk.Label(content, text="Settings", font=FONT_LG,
                 bg=t["BG"], fg=t["TEXT"]).pack(anchor="w", pady=(0, 18))

        self._build_cf_section(content, t)
        self._build_download_section(content, t)
        self._build_theme_section(content, t)
        self._build_about_section(content, t)

    def _on_inner_cfg(self, event):
        self._scroll_canvas.configure(scrollregion=self._scroll_canvas.bbox("all"))

    def _on_canvas_cfg(self, event):
        self._scroll_canvas.itemconfig(self._inner_win, width=event.width)

    def _on_scroll(self, event):
        self._scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── section card ──────────────────────────────────────────────────────────

    def _section(self, parent, title: str):
        t = self.app.t
        wrap = tk.Frame(parent, bg=t["BG"])
        wrap.pack(fill="x", pady=(0, 14))

        hdr = tk.Frame(wrap, bg=t["BORDER"], height=1)
        hdr.pack(fill="x", pady=(0, 1))

        card = tk.Frame(wrap, bg=t["CARD"], padx=20, pady=14)
        card.pack(fill="x")

        tk.Label(card, text=title, fg=t["ACCENT"], bg=t["CARD"],
                 font=FONT_BOLD).pack(anchor="w", pady=(0, 10))

        return card, wrap

    def _label(self, parent, text, small=False):
        t = self.app.t
        f = FONT_SM if small else FONT
        return tk.Label(parent, text=text, fg=t["TEXT"], bg=t["CARD"], font=f)

    def _sublabel(self, parent, text):
        t = self.app.t
        return tk.Label(parent, text=text, fg=t["SUBTEXT"], bg=t["CARD"], font=FONT_XS)

    # ── CF bypass section ─────────────────────────────────────────────────────

    def _build_cf_section(self, parent, t):
        card, wrap = self._section(parent, "⚡  Cloudflare Bypass")
        self._cf_card = card
        self._cf_wrap = wrap

        bypass_var = tk.StringVar(value=self.app.bypass_method)
        self._bypass_var = bypass_var

        options = [
            ("curl  (Fast, default)",                        "curl"),
            ("undetected-chromedriver  ⭐ (Most reliable)", "uc"),
            ("FlareSolverr  (External solver service)",       "flaresolverr"),
            ("Cloudscraper  (Python library)",                "cloudscraper"),
            ("Browser Automation  (Selenium)",                "browser"),
        ]

        self._bypass_radios = []
        for label, val in options:
            rb = tk.Radiobutton(
                card, text=label, variable=bypass_var, value=val,
                bg=t["CARD"], fg=t["TEXT"], selectcolor=t["ACCENT"],
                font=FONT, activebackground=t["CARD"], cursor="hand2",
                command=self._save_bypass)
            rb.pack(anchor="w", pady=2)
            self._bypass_radios.append(rb)

        # Browser options
        sep = tk.Frame(card, bg=t["BORDER"], height=1)
        sep.pack(fill="x", pady=(10, 8))
        self._cf_sep = sep

        row = tk.Frame(card, bg=t["CARD"])
        row.pack(fill="x", pady=(0, 6))
        self._cf_row = row
        tk.Label(row, text="Browser:", bg=t["CARD"], fg=t["TEXT"], font=FONT).pack(side="left")
        bt_var = tk.StringVar(value=self.app.browser_type)
        self._bt_var = bt_var
        bt_cb = ttk.Combobox(row, textvariable=bt_var, values=["chrome", "edge"],
                             state="readonly", width=10, font=FONT_SM)
        bt_cb.pack(side="left", padx=(8, 0))
        bt_cb.bind("<<ComboboxSelected>>", lambda e: self._save_bypass())

        chk_row = tk.Frame(card, bg=t["CARD"])
        chk_row.pack(fill="x", pady=(0, 6))
        self._chk_row = chk_row

        hl_var = tk.BooleanVar(value=self.app.browser_headless)
        self._hl_var = hl_var
        hl_chk = tk.Checkbutton(chk_row, text="Headless mode", variable=hl_var,
                                 bg=t["CARD"], fg=t["TEXT"], selectcolor=t["ACCENT"],
                                 font=FONT_SM, activebackground=t["CARD"],
                                 command=self._save_bypass)
        hl_chk.pack(side="left", padx=(0, 16))
        self._hl_chk = hl_chk

        ic_var = tk.BooleanVar(value=self.app.browser_incognito)
        self._ic_var = ic_var
        ic_chk = tk.Checkbutton(chk_row, text="Incognito mode", variable=ic_var,
                                 bg=t["CARD"], fg=t["TEXT"], selectcolor=t["ACCENT"],
                                 font=FONT_SM, activebackground=t["CARD"],
                                 command=self._save_bypass)
        ic_chk.pack(side="left")
        self._ic_chk = ic_chk

        # Status labels
        status_frame = tk.Frame(card, bg=t["CARD"])
        status_frame.pack(fill="x", pady=(8, 0))
        self._status_frame = status_frame
        self._refresh_cf_status()

    def _refresh_cf_status(self):
        t = self.app.t
        for w in self._status_frame.winfo_children():
            w.destroy()

        uc_ok  = _sess.HAS_UC
        cs_ok  = _sess.HAS_CLOUDSCRAPER
        br_ok  = _sess.HAS_BROWSER
        fs_ok  = _flaresolverr.is_running()

        items = [
            ("undetected-chromedriver", uc_ok, "✓ Available" if uc_ok else "✗  pip install undetected-chromedriver"),
            ("FlareSolverr",            fs_ok, "✓ Running on :8191" if fs_ok else "✗  Not running (start flaresolverr.exe)"),
            ("Cloudscraper",            cs_ok, "✓ Available" if cs_ok else "✗  pip install cloudscraper"),
            ("Browser automation",      br_ok, "✓ Available" if br_ok else "✗  pip install selenium webdriver-manager"),
        ]
        for lib, ok, msg in items:
            row = tk.Frame(self._status_frame, bg=t["CARD"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=f"  {lib}:", bg=t["CARD"], fg=t["SUBTEXT"],
                     font=FONT_XS, width=28, anchor="w").pack(side="left")
            tk.Label(row, text=msg, bg=t["CARD"],
                     fg=t["SUCCESS"] if ok else t["SUBTEXT"],
                     font=FONT_XS).pack(side="left")

    def _save_bypass(self):
        self.app.bypass_method      = self._bypass_var.get()
        self.app.browser_type       = self._bt_var.get()
        self.app.browser_headless   = self._hl_var.get()
        self.app.browser_incognito  = self._ic_var.get()
        self.app.use_flaresolverr   = (self.app.bypass_method in ("flaresolverr", "uc"))
        self.app.update_bypass_indicator()

    # ── download section ──────────────────────────────────────────────────────

    def _build_download_section(self, parent, t):
        card, wrap = self._section(parent, "⬇  Downloads")
        self._dl_card = card
        self._dl_wrap = wrap

        row = tk.Frame(card, bg=t["CARD"])
        row.pack(fill="x")
        self._dl_row = row
        tk.Label(row, text="Max concurrent downloads:", bg=t["CARD"],
                 fg=t["TEXT"], font=FONT).pack(side="left")

        threads_var = tk.StringVar(value=str(self.app.max_concurrent_downloads))
        self._threads_var = threads_var
        threads_cb = ttk.Combobox(row, textvariable=threads_var,
                                  values=["1", "2", "3", "4", "5"],
                                  state="readonly", width=6, font=FONT)
        threads_cb.pack(side="left", padx=(10, 0))
        threads_cb.bind("<<ComboboxSelected>>", self._save_downloads)
        self._threads_cb = threads_cb

        self._dl_hint = tk.Label(card,
            text="More workers = faster batch downloads, but uses more bandwidth and memory.",
            fg=t["SUBTEXT"], bg=t["CARD"], font=FONT_XS)
        self._dl_hint.pack(anchor="w", pady=(6, 0))

    def _save_downloads(self, event=None):
        try:
            self.app.max_concurrent_downloads = int(self._threads_var.get())
        except Exception:
            pass

    # ── theme section ─────────────────────────────────────────────────────────

    def _build_theme_section(self, parent, t):
        card, wrap = self._section(parent, "🎨  Appearance")
        self._theme_card = card
        self._theme_wrap = wrap

        btn_row = tk.Frame(card, bg=t["CARD"])
        btn_row.pack(fill="x", pady=(0, 8))
        self._theme_btn_row = btn_row

        def mk(label, theme_obj):
            b = tk.Button(btn_row, text=label,
                          bg=t["HDR_BTN"], fg=t["TEXT"],
                          activebackground=t["ACCENT"], activeforeground="white",
                          relief="flat", font=FONT_SM, cursor="hand2",
                          bd=0, padx=14, pady=7,
                          command=lambda th=theme_obj: self.app.set_theme(th))
            b.pack(side="left", padx=(0, 8))
            return b

        self._light_btn    = mk("☀  Light",    LIGHT)
        self._dark_btn     = mk("🌙  Dark",     DARK)
        self._midnight_btn = mk("✦  Midnight", MIDNIGHT)
        self._update_active_theme_btn()

        self._theme_hint = tk.Label(
            card,
            text="Theme changes take effect immediately across all pages.",
            fg=t["SUBTEXT"], bg=t["CARD"], font=FONT_XS)
        self._theme_hint.pack(anchor="w")

    def _update_active_theme_btn(self):
        t = self.app.t
        for btn, th in [(self._light_btn, LIGHT),
                        (self._dark_btn, DARK),
                        (self._midnight_btn, MIDNIGHT)]:
            if self.app._theme is th:
                btn.config(bg=t["ACCENT"], fg="white")
            else:
                btn.config(bg=t["HDR_BTN"], fg=t["TEXT"])

    # ── about section ─────────────────────────────────────────────────────────

    def _build_about_section(self, parent, t):
        card, wrap = self._section(parent, "ℹ  About")
        self._about_card = card
        self._about_wrap = wrap

        lines = [
            ("AnimePahe Downloader", FONT_BOLD),
            ("Version 2.0", FONT_SM),
            ("", FONT_SM),
            ("Download anime from AnimePahe easily.", FONT_SM),
            ("  1. Browse page → paste URL → Fetch episodes", FONT_XS),
            ("  2. Select episodes, choose quality & audio", FONT_XS),
            ("  3. Downloads page → set save folder → Start Download", FONT_XS),
            ("", FONT_SM),
            ("If Cloudflare blocks you:", FONT_SM),
            ("  • Use undetected-chromedriver (best success rate)", FONT_XS),
            ("  • Or run FlareSolverr and use the Solve CF button", FONT_XS),
        ]
        self._about_labels = []
        for text, font in lines:
            lbl = tk.Label(card, text=text, fg=t["TEXT"] if font != FONT_XS else t["SUBTEXT"],
                           bg=t["CARD"], font=font, anchor="w")
            lbl.pack(anchor="w")
            self._about_labels.append(lbl)

    # ── theme ─────────────────────────────────────────────────────────────────

    def apply_theme(self):
        t = self.app.t
        self.configure(bg=t["BG"])
        self._scroll_canvas.configure(bg=t["BG"])
        self._inner.configure(bg=t["BG"])
        self._content.configure(bg=t["BG"])

        def _recard(card):
            card.configure(bg=t["CARD"])
            for child in card.winfo_children():
                cls = child.winfo_class()
                try:
                    if cls in ("Frame",):
                        child.configure(bg=t["CARD"])
                    elif cls == "Label":
                        child.configure(bg=t["CARD"])
                    elif cls in ("Checkbutton", "Radiobutton"):
                        child.configure(bg=t["CARD"], fg=t["TEXT"],
                                        selectcolor=t["ACCENT"],
                                        activebackground=t["CARD"])
                except Exception:
                    pass

        for card in [self._cf_card, self._dl_card, self._theme_card, self._about_card]:
            _recard(card)

        for wrap in [self._cf_wrap, self._dl_wrap, self._theme_wrap, self._about_wrap]:
            wrap.configure(bg=t["BG"])

        self._dl_hint.configure(bg=t["CARD"], fg=t["SUBTEXT"])
        self._theme_hint.configure(bg=t["CARD"], fg=t["SUBTEXT"])
        self._refresh_cf_status()
        self._update_active_theme_btn()
