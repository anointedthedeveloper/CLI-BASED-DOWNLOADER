import os
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import animepahe
import kwik
import downloader
import session as _sess
import flaresolverr as _flaresolverr


def _get_play_ids(url: str):
    """Extract (series_id, session) from a play URL."""
    import re
    m = re.search(r"play/([a-f0-9\-]{36})/([a-f0-9]{64})", url)
    if not m:
        raise ValueError(f"Cannot extract play IDs from: {url}")
    return m.group(1), m.group(2)

# ── themes ─────────────────────────────────────────────────────────────────────

LIGHT = {
    "BG":        "#f0f4f8",
    "CARD":      "#ffffff",
    "PANEL":     "#f8fafc",
    "BORDER":    "#cbd5e1",
    "ACCENT":    "#4f46e5",
    "ACCENT_HV": "#4338ca",
    "SUCCESS":   "#059669",
    "DANGER":    "#dc2626",
    "TEXT":      "#1e293b",
    "SUBTEXT":   "#64748b",
    "TERMINAL":  "#f8fafc",
    "TERM_FG":   "#1e293b",
    "PROG_BG":   "#e2e8f0",
    "HDR_BG":    "#ffffff",
    "HDR_BTN":   "#e2e8f0",
    "CHK_BG":    "#ffffff",
    "LIST_BG":   "#f8fafc",
    "LIST_SEL":  "#ede9fe",
    "ROW_ALT":   "#f1f5f9",
    "BADGE_BG":  "#4f46e5",
}

DARK = {
    "BG":        "#0d1117",
    "CARD":      "#161b22",
    "PANEL":     "#161b22",
    "BORDER":    "#30363d",
    "ACCENT":    "#58a6ff",
    "ACCENT_HV": "#388bfd",
    "SUCCESS":   "#3fb950",
    "DANGER":    "#f85149",
    "TEXT":      "#e6edf3",
    "SUBTEXT":   "#8b949e",
    "TERMINAL":  "#0d1117",
    "TERM_FG":   "#c9d1d9",
    "PROG_BG":   "#21262d",
    "HDR_BG":    "#161b22",
    "HDR_BTN":   "#21262d",
    "CHK_BG":    "#161b22",
    "LIST_BG":   "#0d1117",
    "LIST_SEL":  "#1f2d3d",
    "ROW_ALT":   "#161b22",
    "BADGE_BG":  "#58a6ff",
}

MIDNIGHT = {
    "BG":        "#1a1033",
    "CARD":      "#231945",
    "PANEL":     "#231945",
    "BORDER":    "#3d2e6e",
    "ACCENT":    "#a78bfa",
    "ACCENT_HV": "#8b5cf6",
    "SUCCESS":   "#34d399",
    "DANGER":    "#f87171",
    "TEXT":      "#ede9fe",
    "SUBTEXT":   "#9ca3af",
    "TERMINAL":  "#1a1033",
    "TERM_FG":   "#ddd6fe",
    "PROG_BG":   "#2d1f5e",
    "HDR_BG":    "#231945",
    "HDR_BTN":   "#2d1f5e",
    "CHK_BG":    "#231945",
    "LIST_BG":   "#1a1033",
    "LIST_SEL":  "#2d1f5e",
    "ROW_ALT":   "#231945",
    "BADGE_BG":  "#7c3aed",
}

FONT      = ("Segoe UI", 10)
FONT_SM   = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_MONO = ("Consolas", 9)
FONT_LG   = ("Segoe UI", 12, "bold")
FONT_XS   = ("Segoe UI", 8)

# ── helpers ────────────────────────────────────────────────────────────────────

def _fmt_size(b: float) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"

def _fmt_time(s: float) -> str:
    s = int(s)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def _sanitize_dir(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.rstrip(" .")
    return name or "_unnamed"

def _parse_range(ep_str: str, total: int) -> tuple:
    ep_str = ep_str.strip()
    if ep_str.lower() == "all":
        return 1, total
    if re.fullmatch(r"\d+", ep_str):
        n = int(ep_str)
        return n, n
    m = re.fullmatch(r"(\d+)-(\d+)", ep_str)
    if m:
        return int(m.group(1)), int(m.group(2))
    raise ValueError(f"Invalid episode format: '{ep_str}'  (use: all / 3 / 1-12)")

def _shorten_path(p: str, max_len: int = 40) -> str:
    if len(p) <= max_len:
        return p
    parts = p.replace("\\", "/").split("/")
    if len(parts) >= 3:
        return f"{parts[0]}/…/{parts[-1]}"
    return "…" + p[-(max_len - 1):]


# ── rounded rectangle canvas helper ───────────────────────────────────────────

def _round_rect(canvas, x1, y1, x2, y2, r=10, **kw):
    pts = [
        x1+r, y1, x2-r, y1,
        x2, y1, x2, y1+r,
        x2, y2-r, x2, y2,
        x2-r, y2, x1+r, y2,
        x1, y2, x1, y2-r,
        x1, y1+r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


# ── main window ────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self._theme = DARK
        self.title("AnimePahe Downloader (v2.0)")
        self.configure(bg=DARK["BG"])
        self.minsize(860, 640)
        self.resizable(True, True)

        self._ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appico.ico")
        self._stop = threading.Event()
        self._stop_fetch_flag = threading.Event()

        # CF bypass state — FlareSolverr is default
        self._bypass_method   = "flaresolverr"
        self._browser_type    = "chrome"
        self._browser_headless  = True
        self._browser_incognito = False
        self._use_cloudscraper  = tk.BooleanVar(value=False)
        self._use_flaresolverr  = True
        self._max_concurrent_downloads = 3

        # Set session logger to route Flaresolverr and connection logs to the GUI
        _sess.set_log_callback(self._log_dim)

        # episode list state
        self._episode_vars  = []   # list of (BooleanVar, label_str, play_url)
        self._episode_data  = []   # raw API episode dicts
        self._series_id     = ""
        self._series_title  = ""
        self._thumb_images  = {}   # ep_index → PhotoImage (keep refs)
        self._ep_filter_var = tk.StringVar()
        self._ep_filter_var.trace_add("write", lambda *_: self._filter_episodes())

        self._apply_ttk_style()
        self._build_ui()
        self.after(0, self._maximize)
        self.after(200, self._set_icon)
        
        # Pre-solve CF on app launch
        threading.Thread(target=self._presolve_cf, daemon=True).start()

    def _presolve_cf(self):
        self._log_dim("Pre-solving Cloudflare for animepahe.pw...")
        try:
            _sess.solve_cf_once(url="https://animepahe.pw", force=False, log_fn=self._log_dim)
        except Exception as e:
            self._log_err(f"Pre-solve animepahe failed: {e}")
            
        self._log_dim("Pre-solving Cloudflare for kwik.cx...")
        try:
            # We use /f/invalid because the root domain doesn't trigger Cloudflare challenge
            _sess.solve_cf_once(url="https://kwik.cx/f/invalid", force=False, log_fn=self._log_dim)
        except Exception as e:
            self._log_err(f"Pre-solve kwik failed: {e}")

    def _maximize(self):
        try:
            self.state("zoomed")
        except tk.TclError:
            self.attributes("-zoomed", True)

    def _set_icon(self):
        if os.path.exists(self._ico_path):
            try:
                self.iconbitmap(self._ico_path)
            except Exception:
                pass

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

    # ── build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        outer = tk.Frame(self, bg=self._theme["BG"])
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        self._outer = outer

        self._build_body(outer)

    def _build_body(self, parent):
        t = self._theme
        body = tk.Frame(parent, bg=t["BG"])
        body.grid(row=0, column=0, sticky="nsew", padx=20, pady=16)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(3, weight=1)   # episode list
        body.grid_rowconfigure(5, weight=1)   # log
        self._body = body

        self._build_header(body)          # row 0
        self._build_url_row(body)         # row 1
        self._build_episode_section(body) # row 2-3
        self._build_saveto_row(body)      # row 4
        self._build_progress_section(body)# row 5
        self._build_log_section(body)     # row 6

    # ── header ────────────────────────────────────────────────────────────────

    def _build_header(self, parent):
        t = self._theme
        hdr = tk.Frame(parent, bg=t["HDR_BG"], pady=10)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        hdr.grid_columnconfigure(1, weight=1)
        self._hdr_frame = hdr

        # Left: Poster Image placeholder
        self._poster_lbl = tk.Label(hdr, text="No Poster", bg=t["HDR_BG"], fg=t["SUBTEXT"], font=FONT_SM, width=12, height=6, relief="solid", borderwidth=1)
        self._poster_lbl.grid(row=0, column=0, padx=(16, 8), rowspan=2)

        # Title Label
        self._title_lbl = tk.Label(hdr, text="AnimePahe Downloader", bg=t["HDR_BG"],
                                   fg=t["TEXT"], font=FONT_LG, anchor="w")
        self._title_lbl.grid(row=0, column=1, sticky="w", pady=(0, 2))

        # Subtitle / Status Label
        self._subtitle_lbl = tk.Label(hdr, text="Ready to fetch.", bg=t["HDR_BG"],
                                      fg=t["SUBTEXT"], font=FONT_SM, anchor="w")
        self._subtitle_lbl.grid(row=1, column=1, sticky="nw")

        # Right: controls
        ctrl = tk.Frame(hdr, bg=t["HDR_BG"])
        ctrl.grid(row=0, column=2, rowspan=2, padx=(0, 16))

        self._light_btn = self._hdr_btn(ctrl, "☀ Light", lambda: self._set_theme(LIGHT))
        self._light_btn.pack(side="left", padx=(0, 4))

        self._dark_btn = self._hdr_btn(ctrl, "🌙 Dark", lambda: self._set_theme(DARK))
        self._dark_btn.pack(side="left", padx=(0, 4))

        settings_btn = self._hdr_btn(ctrl, "⚙", self._show_settings)
        settings_btn.pack(side="left", padx=(0, 4))

        info_btn = self._hdr_btn(ctrl, "ℹ", self._show_info)
        info_btn.pack(side="left", padx=(0, 8))

        # Active bypass method indicator
        self._bypass_indicator = tk.Label(
            ctrl, text="🛡 FlareSolverr", fg=t["SUCCESS"], bg=t["HDR_BG"],
            font=FONT_SM, cursor="hand2")
        self._bypass_indicator.pack(side="left")
        self._bypass_indicator.bind("<Button-1>", lambda e: self._show_settings())

        self._update_theme_buttons()

    def _update_header_info(self, title: str, poster_url: str):
        self._title_lbl.config(text=title)
        self._subtitle_lbl.config(text="Fetching poster...")
        if poster_url:
            threading.Thread(target=self._load_poster, args=(poster_url,), daemon=True).start()
        else:
            self._subtitle_lbl.config(text="No poster available.")

    def _load_poster(self, url: str):
        try:
            import urllib.request
            from PIL import Image, ImageTk
            import io
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = resp.read()
            img = Image.open(io.BytesIO(data))
            img = img.resize((70, 96), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.after(0, lambda: self._poster_lbl.config(image=photo, text="", width=70, height=96))
            self._poster_lbl.image = photo
            self.after(0, lambda: self._subtitle_lbl.config(text="Poster loaded."))
        except Exception:
            self.after(0, lambda: self._subtitle_lbl.config(text="Failed to load poster."))

    def _hdr_btn(self, parent, text, cmd):
        t = self._theme
        b = tk.Button(parent, text=text, command=cmd,
                      bg=t["HDR_BTN"], fg=t["TEXT"],
                      activebackground=t["ACCENT"], activeforeground="white",
                      relief="flat", font=FONT_SM, cursor="hand2",
                      bd=0, padx=10, pady=5)
        b.bind("<Enter>", lambda e, _b=b: _b.config(bg=t["ACCENT"], fg="white"))
        b.bind("<Leave>", lambda e, _b=b: _b.config(bg=t["HDR_BTN"], fg=t["TEXT"]))
        return b

    # ── URL row ───────────────────────────────────────────────────────────────

    def _build_url_row(self, parent):
        t = self._theme
        card = tk.Frame(parent, bg=t["CARD"], padx=16, pady=12)
        card.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        card.grid_columnconfigure(1, weight=1)
        self._url_card = card

        tk.Label(card, text="URL:", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_BOLD, width=7, anchor="w").grid(row=0, column=0, sticky="w")

        self.link_var = tk.StringVar()
        url_entry = tk.Entry(card, textvariable=self.link_var,
                             bg=t["PANEL"], fg=t["TEXT"],
                             insertbackground=t["ACCENT"],
                             relief="flat", font=FONT,
                             highlightthickness=1,
                             highlightbackground=t["BORDER"],
                             highlightcolor=t["ACCENT"])
        url_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        url_entry.insert(0, "Paste AnimePahe episode or series link...")
        url_entry.config(fg=t["SUBTEXT"])
        url_entry.bind("<FocusIn>",  lambda e: self._url_placeholder_clear(url_entry))
        url_entry.bind("<FocusOut>", lambda e: self._url_placeholder_restore(url_entry))
        url_entry.bind("<KeyRelease>", lambda e: self._validate_url())
        self._url_entry = url_entry

        # Fetch range entry
        tk.Label(card, text="Range:", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_BOLD, width=6, anchor="w").grid(row=0, column=2, padx=(8, 0))
        self.fetch_range_var = tk.StringVar(value="all")
        range_entry = tk.Entry(card, textvariable=self.fetch_range_var,
                               bg=t["PANEL"], fg=t["TEXT"],
                               insertbackground=t["ACCENT"],
                               relief="flat", font=FONT,
                               width=8,
                               highlightthickness=1,
                               highlightbackground=t["BORDER"],
                               highlightcolor=t["ACCENT"])
        range_entry.grid(row=0, column=3, padx=(0, 8))
        self._range_entry = range_entry

        paste_btn = tk.Button(card, text="📋 Paste", command=self._paste_url,
                              bg=t["HDR_BTN"], fg=t["TEXT"],
                              activebackground=t["ACCENT"], activeforeground="white",
                              relief="flat", font=FONT_SM, cursor="hand2",
                              bd=0, padx=12, pady=6)
        paste_btn.grid(row=0, column=4)
        self._paste_btn = paste_btn

        # Fetch Episodes button
        fetch_btn = tk.Button(card, text="🔄 Fetch", command=self._fetch_episodes,
                              bg=t["ACCENT"], fg="white",
                              activebackground=t["ACCENT_HV"], activeforeground="white",
                              relief="flat", font=FONT_SM, cursor="hand2",
                              bd=0, padx=12, pady=6)
        fetch_btn.grid(row=0, column=5, padx=(8, 0))
        self._fetch_btn = fetch_btn

        # Stop fetch button
        stop_fetch_btn = tk.Button(card, text="✕ Stop", command=self._stop_fetch,
                                   bg=t["DANGER"], fg="white",
                                   activebackground="#b91c1c", activeforeground="white",
                                   relief="flat", font=FONT_SM, cursor="hand2",
                                   bd=0, padx=10, pady=6, state="disabled")
        stop_fetch_btn.grid(row=0, column=6, padx=(4, 0))
        self._stop_fetch_btn = stop_fetch_btn

        # Status line
        self._url_status_var = tk.StringVar(value="")
        status_lbl = tk.Label(card, textvariable=self._url_status_var,
                              fg=t["SUBTEXT"], bg=t["CARD"], font=FONT_SM, anchor="w")
        status_lbl.grid(row=1, column=1, columnspan=5, sticky="w", pady=(4, 0))
        self._url_status = status_lbl

    def _url_placeholder_clear(self, entry):
        if entry.get() == "Paste AnimePahe episode or series link...":
            entry.delete(0, "end")
            entry.config(fg=self._theme["TEXT"])

    def _url_placeholder_restore(self, entry):
        if not entry.get():
            entry.insert(0, "Paste AnimePahe episode or series link...")
            entry.config(fg=self._theme["SUBTEXT"])

    # ── episode section ───────────────────────────────────────────────────────

    def _build_episode_section(self, parent):
        t = self._theme
        card = tk.Frame(parent, bg=t["CARD"], padx=16, pady=10)
        card.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        card.grid_columnconfigure(3, weight=1)
        self._ep_card = card

        # Label
        tk.Label(card, text="Episode:", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_BOLD, anchor="w", width=7).grid(row=0, column=0, sticky="w")

        # Last 5 checkbox
        self._last5_var = tk.BooleanVar(value=False)
        tk.Checkbutton(card, text="Last 5 Episodes", variable=self._last5_var,
                       bg=t["CARD"], fg=t["TEXT"], selectcolor=t["CHK_BG"],
                       activebackground=t["CARD"], font=FONT, cursor="hand2",
                       command=self._filter_episodes).grid(row=0, column=1, padx=(0, 8))

        # All Unwatched checkbox
        self._unwatched_var = tk.BooleanVar(value=False)
        tk.Checkbutton(card, text="All Unwatched", variable=self._unwatched_var,
                       bg=t["CARD"], fg=t["TEXT"], selectcolor=t["CHK_BG"],
                       activebackground=t["CARD"], font=FONT, cursor="hand2").grid(
            row=0, column=2, padx=(0, 12))

        # Text filter
        filter_entry = tk.Entry(card, textvariable=self._ep_filter_var,
                                bg=t["PANEL"], fg=t["TEXT"],
                                insertbackground=t["ACCENT"],
                                relief="flat", font=FONT,
                                highlightthickness=1,
                                highlightbackground=t["BORDER"],
                                highlightcolor=t["ACCENT"])
        filter_entry.insert(0, "Text Filter")
        filter_entry.config(fg=t["SUBTEXT"])
        filter_entry.bind("<FocusIn>",  lambda e: self._filter_placeholder_clear(filter_entry))
        filter_entry.bind("<FocusOut>", lambda e: self._filter_placeholder_restore(filter_entry))
        filter_entry.grid(row=0, column=3, sticky="ew", padx=(0, 12))
        self._filter_entry = filter_entry

        # Quality dropdown
        tk.Label(card, text="Quality", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_SM).grid(row=0, column=4, padx=(0, 4))
        self.quality_var = tk.StringVar(value="Max")
        q_cb = ttk.Combobox(card, textvariable=self.quality_var, width=9,
                            values=["Max", "Min", "1080", "720", "480", "360"],
                            state="readonly", font=FONT)
        q_cb.grid(row=0, column=5, padx=(0, 10))
        self._q_cb = q_cb

        # Audio dropdown
        tk.Label(card, text="Audio", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_SM).grid(row=0, column=6, padx=(0, 4))
        self.audio_var = tk.StringVar(value="jp")
        a_cb = ttk.Combobox(card, textvariable=self.audio_var, width=11,
                            values=["jp (Japanese)", "en (English)", "zh (Chinese)"],
                            state="readonly", font=FONT)
        a_cb.grid(row=0, column=7)
        self._a_cb = a_cb

        # Episode list area (row 3)
        list_card = tk.Frame(parent, bg=t["LIST_BG"],
                             highlightthickness=1, highlightbackground=t["BORDER"])
        list_card.grid(row=3, column=0, sticky="nsew", pady=(0, 8))
        list_card.grid_rowconfigure(0, weight=1)
        list_card.grid_columnconfigure(0, weight=1)
        self._list_card = list_card

        # Canvas + scrollbar for the episode checkboxes
        self._ep_canvas = tk.Canvas(list_card, bg=t["LIST_BG"],
                                    highlightthickness=0)
        self._ep_scrollbar = ttk.Scrollbar(list_card, orient="vertical",
                                           command=self._ep_canvas.yview)
        self._ep_canvas.configure(yscrollcommand=self._ep_scrollbar.set)

        self._ep_inner = tk.Frame(self._ep_canvas, bg=t["LIST_BG"])
        self._ep_window = self._ep_canvas.create_window(
            (0, 0), window=self._ep_inner, anchor="nw")

        self._ep_inner.bind("<Configure>", self._on_ep_configure)
        self._ep_canvas.bind("<Configure>", self._on_canvas_configure)
        self._ep_canvas.bind("<MouseWheel>", self._on_ep_scroll)

        self._ep_canvas.grid(row=0, column=0, sticky="nsew")
        self._ep_scrollbar.grid(row=0, column=1, sticky="ns")

        # Placeholder message
        self._ep_placeholder = tk.Label(self._ep_inner,
            text="Paste a URL above and click Start to load episodes",
            fg=t["SUBTEXT"], bg=t["LIST_BG"], font=FONT_SM)
        self._ep_placeholder.grid(row=0, column=0, padx=20, pady=16)

    def _on_ep_configure(self, event):
        self._ep_canvas.configure(scrollregion=self._ep_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._ep_canvas.itemconfig(self._ep_window, width=event.width)

    def _on_ep_scroll(self, event):
        self._ep_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _filter_placeholder_clear(self, entry):
        if entry.get() == "Text Filter":
            entry.delete(0, "end")
            entry.config(fg=self._theme["TEXT"])

    def _filter_placeholder_restore(self, entry):
        if not entry.get():
            entry.insert(0, "Text Filter")
            entry.config(fg=self._theme["SUBTEXT"])

    def _populate_episode_list(self, raw_episodes: list, title: str, series_id: str):
        """Fill the episode list with cards showing thumbnail, number, title, quality."""
        t = self._theme
        self._series_title = title
        self._series_id    = series_id
        self._episode_data = raw_episodes
        self._thumb_images = {}

        # clear old widgets
        for w in self._ep_inner.winfo_children():
            w.destroy()
        self._episode_vars.clear()

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
        tk.Label(hdr, text=" ✓ ", bg=t["BORDER"], fg=t["SUBTEXT"], font=FONT_SM).grid(row=0, column=0)
        tk.Label(hdr, text="Thumbnail", bg=t["BORDER"], fg=t["SUBTEXT"], font=FONT_SM, width=12).grid(row=0, column=1, padx=(0,8))
        tk.Label(hdr, text="Episode", bg=t["BORDER"], fg=t["SUBTEXT"], font=FONT_SM, anchor="w").grid(row=0, column=2, sticky="w")
        tk.Label(hdr, text="Audio", bg=t["BORDER"], fg=t["SUBTEXT"], font=FONT_SM, width=8).grid(row=0, column=3)
        tk.Label(hdr, text="Filler", bg=t["BORDER"], fg=t["SUBTEXT"], font=FONT_SM, width=5).grid(row=0, column=4, padx=(0,8))

        # Select-all row
        sel_row = tk.Frame(self._ep_inner, bg=t["LIST_BG"])
        sel_row.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 4))
        tk.Button(sel_row, text="✓ All", command=self._select_all_eps,
                  bg=t["HDR_BTN"], fg=t["TEXT"], relief="flat", font=FONT_SM,
                  cursor="hand2", bd=0, padx=8, pady=3).pack(side="left", padx=(8,4))
        tk.Button(sel_row, text="✗ None", command=self._deselect_all_eps,
                  bg=t["HDR_BTN"], fg=t["TEXT"], relief="flat", font=FONT_SM,
                  cursor="hand2", bd=0, padx=8, pady=3).pack(side="left")

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
            self._episode_vars.append((var, label, play_url))

            row_frame = tk.Frame(self._ep_inner, bg=t["LIST_BG"],
                                 highlightthickness=1, highlightbackground=t["LIST_BG"])
            row_frame.grid(row=i + 2, column=0, sticky="ew", padx=4, pady=1)
            row_frame.grid_columnconfigure(2, weight=1)

            # Hover highlight
            row_frame.bind("<Enter>",  lambda e, f=row_frame: f.config(highlightbackground=t["ACCENT"]))
            row_frame.bind("<Leave>",  lambda e, f=row_frame: f.config(highlightbackground=t["LIST_BG"]))

            # Checkbox
            cb = tk.Checkbutton(row_frame, variable=var,
                                bg=t["LIST_BG"], activebackground=t["LIST_BG"],
                                selectcolor=t["CHK_BG"], cursor="hand2",
                                relief="flat", bd=0)
            cb.grid(row=0, column=0, padx=(8, 4), pady=6)

            # Thumbnail placeholder (will be filled async)
            thumb_lbl = tk.Label(row_frame, text="🖼", bg=t["LIST_BG"],
                                 fg=t["SUBTEXT"], width=10, height=4,
                                 font=FONT_SM, relief="flat")
            thumb_lbl.grid(row=0, column=1, padx=(0, 8), pady=4)

            # Episode info
            info_frame = tk.Frame(row_frame, bg=t["LIST_BG"])
            info_frame.grid(row=0, column=2, sticky="ew", pady=4)
            tk.Label(info_frame, text=f"Ep {ep_num}", fg=t["ACCENT"],
                     bg=t["LIST_BG"], font=FONT_BOLD, anchor="w").pack(anchor="w")
            tk.Label(info_frame, text=ep_title, fg=t["TEXT"],
                     bg=t["LIST_BG"], font=FONT, anchor="w").pack(anchor="w")

            # Audio badge
            audio_color = t["ACCENT"] if "jpn" in audio.lower() or audio.lower() == "jp" else t["SUCCESS"]
            audio_lbl = "JPN" if "jpn" in audio.lower() or audio.lower() == "jp" else audio.upper()[:3]
            tk.Label(row_frame, text=audio_lbl, fg="white",
                     bg=audio_color, font=FONT_SM, padx=6, pady=2).grid(
                row=0, column=3, padx=(0, 8), pady=6)

            # Filler badge
            if filler:
                tk.Label(row_frame, text="Filler", fg="white",
                         bg="#f97316", font=FONT_SM, padx=4, pady=2).grid(
                    row=0, column=4, padx=(0, 8), pady=6)
            else:
                tk.Label(row_frame, text="", bg=t["LIST_BG"],
                         font=FONT_SM, width=5).grid(row=0, column=4, padx=(0, 8))

            # Load thumbnail async
            if snap_url:
                threading.Thread(
                    target=self._load_thumbnail,
                    args=(snap_url, thumb_lbl, i),
                    daemon=True
                ).start()

        self._filter_episodes()
        self._log_ok(f"Loaded {len(raw_episodes)} episodes for: {title}")

    def _load_thumbnail(self, url: str, label: tk.Label, index: int):
        """Download thumbnail in background and update the label."""
        try:
            import urllib.request
            from PIL import Image, ImageTk
            import io

            with urllib.request.urlopen(url, timeout=10) as resp:
                data = resp.read()

            img = Image.open(io.BytesIO(data))
            img = img.resize((80, 48), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._thumb_images[index] = photo  # keep reference

            def _apply(lbl=label, ph=photo):
                lbl.config(image=ph, text="", width=80, height=48)
                lbl.image = ph

            self.after(0, _apply)
        except ImportError:
            self.after(0, lambda lbl=label: lbl.config(text="📷", font=FONT_SM))
        except Exception:
            pass

    def _select_all_eps(self):
        for var, _, _ in self._episode_vars:
            var.set(True)

    def _deselect_all_eps(self):
        for var, _, _ in self._episode_vars:
            var.set(False)

    def _filter_episodes(self):
        flt      = self._ep_filter_var.get().strip().lower()
        is_last5 = self._last5_var.get()
        total    = len(self._episode_vars)

        for i, (var, label, url) in enumerate(self._episode_vars):
            rows = self._ep_inner.grid_slaves(row=i + 2)  # offset by 2 (header + select-all)
            frame = rows[0] if rows else None
            if frame is None:
                continue
            show = True
            if flt and flt != "text filter" and flt not in label.lower():
                show = False
            if is_last5 and i < total - 5:
                show = False
            if show:
                frame.grid()
            else:
                frame.grid_remove()

    # ── save-to row ───────────────────────────────────────────────────────────

    def _build_saveto_row(self, parent):
        t = self._theme
        card = tk.Frame(parent, bg=t["CARD"], padx=16, pady=10)
        card.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        card.grid_columnconfigure(1, weight=1)
        self._saveto_card = card

        tk.Label(card, text="Save to:", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_BOLD, anchor="w", width=7).grid(row=0, column=0, sticky="w")

        self.dir_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        dir_entry = tk.Entry(card, textvariable=self.dir_var,
                             bg=t["PANEL"], fg=t["TEXT"],
                             insertbackground=t["ACCENT"],
                             relief="flat", font=FONT,
                             highlightthickness=1,
                             highlightbackground=t["BORDER"],
                             highlightcolor=t["ACCENT"])
        dir_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        dir_entry.bind("<KeyRelease>", lambda e: self._update_disk_space())
        self._dir_entry = dir_entry

        browse_btn = tk.Button(card, text="Browse", command=self._browse,
                               bg=t["HDR_BTN"], fg=t["TEXT"],
                               activebackground=t["ACCENT"], activeforeground="white",
                               relief="flat", font=FONT_SM, cursor="hand2",
                               bd=0, padx=12, pady=6)
        browse_btn.grid(row=0, column=2, padx=(0, 8))
        self._browse_btn = browse_btn

        # Solve CF / Start / Stop buttons
        solve_btn = tk.Button(card, text="🛡 Solve CF", command=self._solve_cf,
                              bg="#7c3aed", fg="white",
                              activebackground="#6d28d9", activeforeground="white",
                              relief="flat", font=FONT_SM, cursor="hand2",
                              bd=0, padx=12, pady=7)
        solve_btn.grid(row=0, column=3, padx=(0, 6))
        self._solve_btn = solve_btn

        self.start_btn = tk.Button(card, text="⬇  Start / Resume",
                                   command=self._start,
                                   bg=t["ACCENT"], fg="white",
                                   activebackground=t["ACCENT_HV"], activeforeground="white",
                                   relief="flat", font=FONT_BOLD, cursor="hand2",
                                   bd=0, padx=16, pady=7)
        self.start_btn.grid(row=0, column=4, padx=(0, 6))

        self.stop_btn = tk.Button(card, text="🟥 Stop",
                                  command=self._stop_dl,
                                  bg=t["DANGER"], fg="white",
                                  activebackground="#b91c1c", activeforeground="white",
                                  relief="flat", font=FONT_BOLD, cursor="hand2",
                                  bd=0, padx=14, pady=7, state="disabled")
        self.stop_btn.grid(row=0, column=5)

        # Disk space
        self._disk_var = tk.StringVar(value=self._get_disk_space())
        tk.Label(card, textvariable=self._disk_var, fg=t["SUBTEXT"],
                 bg=t["CARD"], font=FONT_SM, anchor="w").grid(
            row=1, column=1, columnspan=4, sticky="w", pady=(4, 0))

    # ── progress section ──────────────────────────────────────────────────────

    def _build_progress_section(self, parent):
        t = self._theme
        card = tk.Frame(parent, bg=t["CARD"], padx=16, pady=10)
        card.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        card.grid_columnconfigure(1, weight=1)
        self._prog_card = card

        # Overall row
        tk.Label(card, text="Overall", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_SM, width=7, anchor="w").grid(row=0, column=0, sticky="w")
        self.overall_var = tk.DoubleVar()
        self.overall_bar = ttk.Progressbar(card, variable=self.overall_var,
                                           maximum=100,
                                           style="Accent.Horizontal.TProgressbar")
        self.overall_bar.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self._overall_info_var = tk.StringVar(value="")
        tk.Label(card, textvariable=self._overall_info_var, fg=t["SUBTEXT"],
                 bg=t["CARD"], font=FONT_SM, anchor="e", width=22).grid(
            row=0, column=2, sticky="e")

        # File row
        tk.Label(card, text="File", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_SM, width=7, anchor="w").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.file_var = tk.DoubleVar()
        self.file_bar = ttk.Progressbar(card, variable=self.file_var,
                                        maximum=100,
                                        style="Success.Horizontal.TProgressbar")
        self.file_bar.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(6, 0))
        self._file_info_var = tk.StringVar(value="")
        tk.Label(card, textvariable=self._file_info_var, fg=t["SUCCESS"],
                 bg=t["CARD"], font=FONT_SM, anchor="e", width=22).grid(
            row=1, column=2, sticky="e", pady=(6, 0))

    # ── log section ───────────────────────────────────────────────────────────

    def _build_log_section(self, parent):
        t = self._theme
        frame = tk.Frame(parent, bg=t["BG"])
        frame.grid(row=6, column=0, sticky="nsew", pady=(0, 4))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self._log_frame = frame

        border = tk.Frame(frame, bg=t["BORDER"], padx=1, pady=1)
        border.grid(row=0, column=0, sticky="nsew")
        border.grid_rowconfigure(0, weight=1)
        border.grid_columnconfigure(0, weight=1)
        self._log_border = border

        self.log_box = tk.Text(
            border, bg=t["TERMINAL"], fg=t["TERM_FG"],
            insertbackground=t["ACCENT"],
            font=FONT_MONO, relief="flat",
            state="disabled", wrap="word", padx=12, pady=10,
            height=8)
        self.log_box.tag_config("error",   foreground=t["DANGER"])
        self.log_box.tag_config("success", foreground=t["SUCCESS"])
        self.log_box.tag_config("info",    foreground=t["SUBTEXT"])
        self.log_box.tag_config("header",  foreground=t["ACCENT"], font=FONT_BOLD)

        scroll = ttk.Scrollbar(border, orient="vertical",
                               command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=scroll.set)
        self.log_box.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

    # ── theme ─────────────────────────────────────────────────────────────────

    def _set_theme(self, theme):
        self._theme = theme
        self._apply_ttk_style()
        self._full_repaint()
        self._update_theme_buttons()

    def _update_theme_buttons(self):
        t = self._theme
        if t is LIGHT:
            self._light_btn.config(bg=t["ACCENT"], fg="white")
            self._dark_btn.config(bg=t["HDR_BTN"], fg=t["TEXT"])
        else:
            self._light_btn.config(bg=t["HDR_BTN"], fg=t["TEXT"])
            self._dark_btn.config(bg=t["ACCENT"], fg="white")

    def _full_repaint(self):
        t = self._theme
        self.configure(bg=t["BG"])
        self._repaint_widget(self)

    def _repaint_widget(self, widget):
        t   = self._theme
        cls = widget.winfo_class()
        bg_map = {
            "Frame":     t["BG"],
            "Label":     None,   # handled per-context
            "Button":    None,
            "Checkbutton": None,
            "Text":      t["TERMINAL"],
            "Entry":     t["PANEL"],
            "Canvas":    t["HDR_BG"],
        }
        try:
            # per-widget overrides
            if widget is self._outer or widget is self._body or widget is self._log_frame:
                widget.configure(bg=t["BG"])
            elif widget is self._hdr_frame:
                widget.configure(bg=t["HDR_BG"])
            elif widget in (self._url_card, self._ep_card, self._saveto_card,
                            self._prog_card):
                widget.configure(bg=t["CARD"])
            elif widget is self._list_card:
                widget.configure(bg=t["LIST_BG"],
                                 highlightbackground=t["BORDER"])
            elif widget is self._ep_canvas:
                widget.configure(bg=t["LIST_BG"])
            elif widget is self._ep_inner:
                widget.configure(bg=t["LIST_BG"])
            elif widget is self._log_border:
                widget.configure(bg=t["BORDER"])
            elif widget is self.log_box:
                widget.configure(bg=t["TERMINAL"], fg=t["TERM_FG"],
                                 insertbackground=t["ACCENT"])
                widget.tag_config("error",   foreground=t["DANGER"])
                widget.tag_config("success", foreground=t["SUCCESS"])
                widget.tag_config("info",    foreground=t["SUBTEXT"])
                widget.tag_config("header",  foreground=t["ACCENT"])
            elif widget is self._url_entry or widget is self._dir_entry:
                widget.configure(bg=t["PANEL"], fg=t["TEXT"],
                                 insertbackground=t["ACCENT"],
                                 highlightbackground=t["BORDER"],
                                 highlightcolor=t["ACCENT"])
            elif widget is self._filter_entry:
                widget.configure(bg=t["PANEL"], fg=t["TEXT"],
                                 insertbackground=t["ACCENT"],
                                 highlightbackground=t["BORDER"])
            elif widget is self.start_btn:
                running = str(widget["state"]) == "disabled"
                widget.configure(bg=t["BORDER"] if running else t["ACCENT"],
                                 fg="white")
            elif widget is self.stop_btn:
                widget.configure(bg=t["DANGER"], fg="white")
            elif widget is self._paste_btn or widget is self._browse_btn:
                widget.configure(bg=t["HDR_BTN"], fg=t["TEXT"])
            elif cls == "Button":
                widget.configure(bg=t["HDR_BTN"], fg=t["TEXT"])
            elif cls in ("Label", "Frame", "Checkbutton"):
                pass  # handled by children loop
        except Exception:
            pass

        for child in widget.winfo_children():
            self._repaint_widget(child)

    # ── settings / info dialogs ───────────────────────────────────────────────

    def _show_settings(self):
        t   = self._theme
        win = tk.Toplevel(self)
        win.title("Settings")
        win.configure(bg=t["BG"])
        win.transient(self)
        win.grab_set()
        win.update_idletasks()
        w, h = 500, 620
        x = (self.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")
        win.minsize(w, h)

        container = tk.Frame(win, bg=t["BG"], padx=24, pady=24)
        container.pack(fill="both", expand=True)

        tk.Label(container, text="Settings", font=("Segoe UI", 16, "bold"),
                 bg=t["BG"], fg=t["TEXT"]).pack(anchor="w", pady=(0, 16))

        # CF bypass
        cf = tk.LabelFrame(container, text="Cloudflare Bypass",
                           bg=t["CARD"], fg=t["TEXT"], font=FONT_BOLD,
                           padx=16, pady=12)
        cf.pack(fill="x", pady=(0, 12))

        bypass_var = tk.StringVar(value=self._bypass_method)
        for label, val in [("curl (Default)", "curl"),
                           ("undetected-chromedriver ⭐ (Best)", "uc"),
                           ("FlareSolverr", "flaresolverr"),
                           ("Cloudscraper",   "cloudscraper"),
                           ("Browser Automation (Selenium)", "browser")]:
            tk.Radiobutton(cf, text=label, variable=bypass_var, value=val,
                           bg=t["CARD"], fg=t["TEXT"], selectcolor=t["ACCENT"],
                           font=FONT, activebackground=t["CARD"],
                           cursor="hand2").pack(anchor="w")

        bf = tk.Frame(cf, bg=t["CARD"])
        bf.pack(fill="x", pady=(10, 0))
        tk.Label(bf, text="Browser:", bg=t["CARD"], fg=t["TEXT"], font=FONT).pack(anchor="w")
        bt_var = tk.StringVar(value=self._browser_type)
        ttk.Combobox(bf, textvariable=bt_var, values=["chrome", "edge"],
                     state="readonly", width=12, font=FONT).pack(anchor="w", pady=(4, 0))
        hl_var = tk.BooleanVar(value=self._browser_headless)
        tk.Checkbutton(bf, text="Headless mode", variable=hl_var,
                       bg=t["CARD"], fg=t["TEXT"], selectcolor=t["ACCENT"],
                       font=FONT_SM, activebackground=t["CARD"]).pack(anchor="w", pady=(6, 0))
        ic_var = tk.BooleanVar(value=self._browser_incognito)
        tk.Checkbutton(bf, text="Incognito mode", variable=ic_var,
                       bg=t["CARD"], fg=t["TEXT"], selectcolor=t["ACCENT"],
                       font=FONT_SM, activebackground=t["CARD"]).pack(anchor="w", pady=(4, 0))

        cs_s  = "✓ Available" if _sess.HAS_CLOUDSCRAPER else "✗ pip install cloudscraper"
        br_s  = "✓ Available" if _sess.HAS_BROWSER      else "✗ pip install selenium webdriver-manager"
        uc_s  = "✓ Available" if _sess.HAS_UC            else "✗ pip install undetected-chromedriver"
        fs_running = _flaresolverr.is_running()
        fs_s  = "✓ Running on :8191" if fs_running else "✗ Not running"
        tk.Label(cf, text=f"undetected-chromedriver: {uc_s}", bg=t["CARD"],
                 fg=t["SUCCESS"] if _sess.HAS_UC else t["DANGER"],
                 font=FONT_SM).pack(anchor="w", pady=(10, 0))
        tk.Label(cf, text=f"FlareSolverr: {fs_s}", bg=t["CARD"],
                 fg=t["SUCCESS"] if fs_running else t["SUBTEXT"],
                 font=FONT_SM).pack(anchor="w", pady=(2, 0))
        tk.Label(cf, text=f"Cloudscraper: {cs_s}", bg=t["CARD"],
                 fg=t["SUCCESS"] if _sess.HAS_CLOUDSCRAPER else t["SUBTEXT"],
                 font=FONT_SM).pack(anchor="w", pady=(2, 0))
        tk.Label(cf, text=f"Browser auto: {br_s}", bg=t["CARD"],
                 fg=t["SUCCESS"] if _sess.HAS_BROWSER else t["SUBTEXT"],
                 font=FONT_SM).pack(anchor="w", pady=(2, 0))

        # Downloads section
        dl_frame = tk.LabelFrame(container, text="Downloads",
                                 bg=t["CARD"], fg=t["TEXT"], font=FONT_BOLD,
                                 padx=16, pady=12)
        dl_frame.pack(fill="x", pady=(0, 12))
        tk.Label(dl_frame, text="Max Concurrent Downloads:", bg=t["CARD"], fg=t["TEXT"], font=FONT).pack(anchor="w")
        threads_var = tk.StringVar(value=str(getattr(self, "_max_concurrent_downloads", 3)))
        threads_cb = ttk.Combobox(dl_frame, textvariable=threads_var, values=["1", "2", "3", "4", "5"],
                                  state="readonly", width=12, font=FONT)
        threads_cb.pack(anchor="w", pady=(4, 0))

        # buttons
        bf2 = tk.Frame(container, bg=t["BG"])
        bf2.pack(fill="x", pady=(16, 0))

        def _save():
            self._bypass_method    = bypass_var.get()
            self._browser_type     = bt_var.get()
            self._browser_headless  = hl_var.get()
            self._browser_incognito = ic_var.get()
            self._use_flaresolverr  = (bypass_var.get() == "flaresolverr")
            self._max_concurrent_downloads = int(threads_var.get())
            # Update header indicator
            icons = {
                "curl":         "🛡 curl",
                "flaresolverr": "🛡 FlareSolverr",
                "cloudscraper": "🛡 Cloudscraper",
                "browser":      "🛡 Browser",
                "uc":           "🛡 UC-Chrome",
            }
            self._bypass_indicator.config(
                text=icons.get(self._bypass_method, f"🛡 {self._bypass_method}"),
                fg=self._theme["SUCCESS"] if self._bypass_method != "curl" else self._theme["SUBTEXT"]
            )
            win.destroy()

        tk.Button(bf2, text="Save", command=_save,
                  bg=t["ACCENT"], fg="white", relief="flat",
                  font=FONT_BOLD, cursor="hand2", bd=0,
                  padx=16, pady=7).pack(side="right")
        tk.Button(bf2, text="Cancel", command=win.destroy,
                  bg=t["HDR_BTN"], fg=t["TEXT"], relief="flat",
                  font=FONT, cursor="hand2", bd=0,
                  padx=14, pady=7).pack(side="right", padx=(0, 8))

    def _show_info(self):
        messagebox.showinfo(
            "About AnimePahe Downloader",
            "AnimePahe Downloader v2.0\n\n"
            "Download anime from AnimePahe.\n\n"
            "• Paste a series or episode URL\n"
            "• Select episodes from the list\n"
            "• Choose quality and audio language\n"
            "• Click Start Download\n\n"
            "If blocked by Cloudflare:\n"
            "Open animepahe.pw in Chrome once,\n"
            "or configure bypass in Settings ⚙"
        )

    # ── actions ───────────────────────────────────────────────────────────────

    def _cf_kw(self) -> dict:
        """Return current CF bypass kwargs for animepahe/session calls."""
        m = self._bypass_method
        return dict(
            use_cloudscraper  = (m == "cloudscraper") or self._use_cloudscraper.get(),
            use_browser       = (m == "browser"),
            use_flaresolverr  = (m in ("flaresolverr", "uc")) or getattr(self, '_use_flaresolverr', False),
            browser_type      = self._browser_type,
            browser_headless  = self._browser_headless,
            browser_incognito = self._browser_incognito,
        )

    def _browse(self):
        d = filedialog.askdirectory()
        if d:
            self.dir_var.set(d)
            self._update_disk_space()

    def _paste_url(self):
        try:
            url = self.clipboard_get()
            if url:
                self.link_var.set(url)
                self._url_entry.config(fg=self._theme["TEXT"])
                self._validate_url()
                # Auto-fetch if valid URL
                if animepahe.is_series_url(url) or animepahe.is_episode_url(url):
                    self.after(200, self._fetch_episodes)
        except Exception:
            pass

    def _validate_url(self):
        url = self.link_var.get().strip()
        if url == "Paste AnimePahe episode or series link...":
            return
        if animepahe.is_series_url(url) or animepahe.is_episode_url(url):
            self._url_status_var.set("✓ Link recognized")
            self._url_status.config(fg=self._theme["SUCCESS"])
        elif url:
            self._url_status_var.set("Validating link...")
            self._url_status.config(fg=self._theme["SUBTEXT"])
        else:
            self._url_status_var.set("")

    def _update_disk_space(self):
        self._disk_var.set(self._get_disk_space())

    def _get_disk_space(self):
        try:
            import shutil
            path = self.dir_var.get() if hasattr(self, "dir_var") else os.path.expanduser("~/Downloads")
            if not os.path.exists(path):
                path = os.path.expanduser("~/Downloads")
            _, _, free = shutil.disk_usage(path)
            total = shutil.disk_usage(path).total
            return f"Available {_fmt_size(free)} of {_fmt_size(total)} space"
        except Exception:
            return "Disk space: N/A"

    def _log(self, msg: str, tag: str = ""):
        def _do():
            self.log_box.config(state="normal")
            self.log_box.insert("end", msg + "\n", tag if tag else ())
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        self.after(0, _do)

    def _log_ok(self, msg):     self._log(f"[SUCCESS] {msg}", "success")
    def _log_err(self, msg):    self._log(f"[ERROR]   {msg}", "error")
    def _log_dim(self, msg):    self._log(f"[INFO]    {msg}", "info")
    def _log_header(self, msg): self._log(f"{'─'*50}\n{msg}\n{'─'*50}", "header")

    def _set_file_progress(self, p, label=""):
        def _do():
            self.file_var.set(p)
            self._file_info_var.set(label)
        self.after(0, _do)

    def _set_overall_progress(self, p, label=""):
        def _do():
            self.overall_var.set(p)
            self._overall_info_var.set(label)
        self.after(0, _do)

    def _set_buttons(self, running: bool):
        t = self._theme
        def _do():
            self.start_btn.config(
                state="disabled" if running else "normal",
                bg=t["BORDER"] if running else t["ACCENT"])
            self.stop_btn.config(state="normal" if running else "disabled")
        self.after(0, _do)

    def _solve_cf(self):
        """Run FlareSolverr once to get CF cookies — shows live progress in log."""
        if not _sess.flaresolverr_running():
            messagebox.showerror("FlareSolverr Not Running",
                "Start FlareSolverr first:\n\n"
                "cd C:\\Users\\Admin\\Downloads\\flaresolverr_windows_x64\\flaresolverr\n"
                "flaresolverr.exe --max-timeout 180000")
            return
        self._solve_btn.config(state="disabled", text="⏳ Solving…")
        self._log_dim("Starting Cloudflare solve via FlareSolverr (~60-90s)…")
        self._log_dim("FlareSolverr is opening Chrome and solving the challenge…")
        threading.Thread(target=self._solve_cf_thread, daemon=True).start()

    def _solve_cf_thread(self):
        def log(msg):
            self._log_dim(msg)
        ok = _sess.solve_cf_once(log=log)
        def done():
            self._solve_btn.config(state="normal", text="🛡 Solve CF")
            if ok:
                self._log_ok("CF solved! Cookies cached for 2 hours. You can now Fetch Episodes.")
                self._bypass_indicator.config(
                    text="🛡 FlareSolverr ✓", fg=self._theme["SUCCESS"])
            else:
                self._log_err("CF solve failed. Check FlareSolverr is running with --max-timeout 180000")
        self.after(0, done)

    def _stop_fetch(self):
        self._stop_fetch_flag.set()
        self._log_dim("Stopping fetch…")
        self._stop_fetch_btn.config(state="disabled")

    def _fetch_episodes(self):
        """Triggered by 'Fetch' button — loads episode list + thumbnails."""
        url = self.link_var.get().strip()
        if url in ("", "Paste AnimePahe episode or series link..."):
            messagebox.showwarning("No URL", "Paste an AnimePahe series or episode URL first.")
            return
        if not (animepahe.is_series_url(url) or animepahe.is_episode_url(url)):
            messagebox.showerror("Invalid URL", "Paste a valid AnimePahe series or episode URL.")
            return

        self._stop_fetch_flag.clear()
        self._fetch_btn.config(state="disabled", text="⏳ Fetching…")
        self._stop_fetch_btn.config(state="normal")
        self._url_status_var.set("Fetching episodes…")
        self._url_status.config(fg=self._theme["SUBTEXT"])

        for w in self._ep_inner.winfo_children():
            w.destroy()
        self._episode_vars.clear()
        self._episode_data.clear()

        threading.Thread(target=self._fetch_episodes_thread, args=(url,), daemon=True).start()

    def _fetch_episodes_thread(self, url: str):
        """Background thread: fetch metadata + episode list."""
        cf_kw     = self._cf_kw()
        is_series = animepahe.is_series_url(url)

        def stopped():
            return self._stop_fetch_flag.is_set()

        cf_kw["stop_flag"] = stopped

        try:
            # ── Step 1: fetch metadata ────────────────────────────
            self._log_dim("Fetching anime info…")
            meta      = animepahe.fetch_metadata(url, is_series, log=self._log_dim, **cf_kw)
            title     = meta.get("title", "Unknown")
            series_id = meta.get("id") or (animepahe.get_series_id(url) if is_series else None)

            if stopped(): return

            self.after(0, lambda: self._url_status_var.set(
                f"✓ {title}  |  {meta.get('type','')}  |  {meta.get('episode_count','')} eps"))
            self.after(0, lambda: self._url_status.config(fg=self._theme["SUCCESS"]))
            self._log_ok(f"Title: {title}")

            # ── Step 2: get episode count ─────────────────────────
            if is_series:
                total_str = str(meta.get("episode_count") or "0")
                try:
                    total = int(total_str)
                except ValueError:
                    total = 0
                
                if total == 0:
                    self._log_dim("Fetching episode count…")
                    try:
                        total = animepahe.get_episode_count(series_id, url, **cf_kw)
                    except Exception as e:
                        self._log_err(f"Failed to get exact episode count: {e}. Assuming 1000 for range bounds.")
                        total = 1000

                # Parse range to fetch
                range_str = self.fetch_range_var.get().strip() or "all"
                try:
                    start_ep, end_ep = _parse_range(range_str, total)
                except Exception as e:
                    self._log_err(f"Range error: {e}. Defaulting to 'all'")
                    start_ep, end_ep = 1, total

                start_page = (start_ep - 1) // 30 + 1
                end_page = (end_ep - 1) // 30 + 1
                
                # Make sure pages are within bounds
                pages = (total + 29) // 30
                start_page = max(1, min(start_page, pages))
                end_page = max(1, min(end_page, pages))

                self._log_dim(f"Fetching episodes {start_ep}-{end_ep} (page {start_page} to {end_page})…")

                # ── Step 3: fetch pages in range ───────────────────
                raw_episodes = []
                for page in range(start_page, end_page + 1):
                    if stopped():
                        self._log_dim("Fetch stopped.")
                        return
                    self._log_dim(f"  Page {page}/{end_page}…")
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
                    self._log_dim(f"  Got {len(raw_episodes)} episodes in requested range")
            else:
                series_id2, session = _get_play_ids(url)
                raw_episodes = [{"episode": 1, "title": "Episode", "snapshot": "",
                                 "session": session, "filler": 0, "audio": "jpn"}]
                series_id = series_id2

            if stopped(): return

            self._log_ok(f"Loaded {len(raw_episodes)} episodes. Populating list…")
            self.after(0, lambda eps=raw_episodes, t=title, sid=series_id:
                       self._populate_episode_list(eps, t, sid))

        except Exception as e:
            self._log_err(f"Fetch failed: {e}")
            self.after(0, lambda: self._url_status_var.set(f"✗ {e}"))
            self.after(0, lambda: self._url_status.config(fg=self._theme["DANGER"]))
            if "403" in str(e):
                self.after(0, lambda: self._log_err(
                    "403 = Cloudflare blocked. Click '🛡 Solve CF' first, then Fetch again."))
        finally:
            self.after(0, lambda: self._fetch_btn.config(state="normal", text="🔄 Fetch"))
            self.after(0, lambda: self._stop_fetch_btn.config(state="disabled"))

    def _start(self):
        url = self.link_var.get().strip()
        if url == "Paste AnimePahe episode or series link...":
            url = ""
        if not (animepahe.is_series_url(url) or animepahe.is_episode_url(url)):
            messagebox.showerror("Invalid URL",
                                 "Paste a valid AnimePahe series or episode URL.")
            return
        self._stop.clear()
        self._set_buttons(True)
        self._set_overall_progress(0, "")
        self._set_file_progress(0, "")
        # clear log
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")
        threading.Thread(target=self._run, daemon=True).start()

    def _stop_dl(self):
        self._stop.set()
        self._log_dim("Stop requested…")

    # ── download thread ───────────────────────────────────────────────────────

    def _run(self):
        url      = self.link_var.get().strip()
        qual     = self.quality_var.get()
        audio    = self.audio_var.get().split()[0]
        save_dir = self.dir_var.get().strip()
        cf_kw    = self._cf_kw()

        target_res = 0
        if qual == "Min":    target_res = -1
        elif qual not in ("Max", ""): target_res = int(qual)

        is_series = animepahe.is_series_url(url)

        try:
            # Use pre-fetched episode list if available
            if self._episode_vars:
                play_links  = [u for var, _, u in self._episode_vars if var.get()]
                title       = self._series_title or "anime"
                total_count = len(play_links)
                self._log_dim(f"Downloading {total_count} selected episode(s)")
            else:
                # Fall back to fetching
                self._log_dim("Fetching episode list…")
                meta  = animepahe.fetch_metadata(url, is_series, log=self._log_dim, **cf_kw)
                title = meta.get("title", "anime") or "anime"
                if is_series:
                    total_eps = int(meta.get("episode_count") or 0)
                    if total_eps == 0:
                        total_eps = animepahe.get_episode_count(
                            animepahe.get_series_id(url), url, **cf_kw)
                    play_links = animepahe.fetch_series_episode_links(
                        url, (1, total_eps), log=self._log_dim, **cf_kw)
                else:
                    play_links = [url]
                total_count = len(play_links)

            if not play_links:
                raise RuntimeError("No episodes selected.")

            dest_dir = os.path.join(save_dir, _sanitize_dir(title))
            self._log_dim(f"Saving {total_count} episode(s) → {dest_dir}")
            self._set_overall_progress(0, f"0 / {total_count} episodes")

            import queue
            q = queue.Queue()
            for idx, play_url in enumerate(play_links):
                q.put((idx, play_url))

            progress_lock = threading.Lock()
            active_progress = {}  # play_url -> (done, total, speed, eta)
            completed_episodes = set()

            def worker():
                while not q.empty() and not self._stop.is_set():
                    try:
                        idx, play_url = q.get_nowait()
                    except queue.Empty:
                        break

                    ep_num = idx + 1
                    self._log_dim(f"[{ep_num}/{total_count}] Extracting link…")

                    try:
                        pahe   = animepahe.fetch_pahe_win_links(
                            play_url, target_res, audio, **cf_kw)
                        dl_map = kwik.extract_kwik_link(pahe["dPaheLink"])
                    except Exception as e:
                        self._log_err(f"EP{ep_num:02d} link error: {e}")
                        with progress_lock:
                            completed_episodes.add(play_url)
                            overall_pct = (len(completed_episodes) / total_count) * 100
                            self._set_overall_progress(overall_pct, f"{len(completed_episodes)} / {total_count} episodes")
                        q.task_done()
                        continue

                    direct  = dl_map["directLink"]
                    referer = dl_map["referer"]
                    res_lbl = f"{pahe['epRes']}p" if pahe.get("epRes") else "?"
                    self._log_dim(f"↓ EP{ep_num:02d} [{res_lbl}]")

                    def on_progress(done, total, speed, eta):
                        with progress_lock:
                            active_progress[play_url] = (done, total, speed, eta)
                            
                            # Sum up stats across all active downloads
                            total_done = 0
                            total_size = 0
                            total_speed = 0
                            etas = []
                            for d, t, s, e in active_progress.values():
                                total_done += d
                                total_size += t
                                total_speed += s
                                if e > 0:
                                    etas.append(e)
                            
                            pct = (total_done / total_size * 100) if total_size else 0
                            avg_eta = max(etas) if etas else 0
                            
                            completed_count = len(completed_episodes)
                            overall_pct = ((completed_count + (pct / 100)) / total_count) * 100
                            
                            size_str = f"{_fmt_size(total_done)} / {_fmt_size(total_size)}" if total_size else _fmt_size(total_done)
                            spd_str  = f"{_fmt_size(total_speed)}/s" if total_speed else "…"
                            eta_str  = f"ETA {_fmt_time(avg_eta)}" if avg_eta else ""
                            
                            self._set_file_progress(pct, f"{size_str}  {spd_str}  {eta_str}")
                            self._set_overall_progress(overall_pct, f"{completed_count} / {total_count} episodes")

                    try:
                        path = downloader.download(
                            url=direct, referer=referer, dest_dir=dest_dir,
                            on_progress=on_progress,
                            stop_flag=self._stop.is_set)
                        self._log_ok(f"EP{ep_num:02d} → {os.path.basename(path)}")
                        self.after(0, lambda u=play_url: self._uncheck_episode(u))
                    except InterruptedError:
                        self._log_dim(f"EP{ep_num:02d} stopped — partial file kept.")
                    except Exception as e:
                        self._log_err(f"EP{ep_num:02d} download error: {e}")
                    finally:
                        with progress_lock:
                            completed_episodes.add(play_url)
                            active_progress.pop(play_url, None)
                            overall_pct = (len(completed_episodes) / total_count) * 100
                            self._set_overall_progress(overall_pct, f"{len(completed_episodes)} / {total_count} episodes")
                        q.task_done()

            # Start thread pool
            num_workers = getattr(self, "_max_concurrent_downloads", 3)
            num_workers = min(num_workers, total_count)
            self._log_dim(f"Starting {num_workers} concurrent download workers…")
            
            threads = []
            for _ in range(num_workers):
                t_worker = threading.Thread(target=worker, daemon=True)
                t_worker.start()
                threads.append(t_worker)

            # Wait for all workers to finish
            for t_worker in threads:
                t_worker.join()

            if self._stop.is_set():
                self._log_dim("Stopped.")
            else:
                self._log_ok("All done.")
                self._set_overall_progress(100, f"{total_count} / {total_count} episodes")

        except Exception as e:
            msg = str(e)
            self._log_err(f"Fatal: {msg}")
            if "403" in msg:
                hint = (
                    "Cloudflare blocked the request.\n\n"
                    "Fix: Start FlareSolverr with:\n"
                    "  flaresolverr.exe --max-timeout 180000\n\n"
                    "Then select FlareSolverr in Settings ⚙"
                )
                self.after(0, lambda h=hint: messagebox.showwarning("Cloudflare", h))
            else:
                self.after(0, lambda m=msg: messagebox.showerror("Error", m))
        finally:
            self._set_buttons(False)

    def _uncheck_episode(self, url: str):
        for var, _, ep_url in self._episode_vars:
            if ep_url == url:
                var.set(False)
                break


if __name__ == "__main__":
    app = App()
    app.mainloop()
