"""
Reusable animated widgets for AnimePahe Downloader.
"""
import io
import math
import threading
import tkinter as tk
from tkinter import ttk
from ui.theme import FONT, FONT_SM, FONT_BOLD, FONT_XS, dim_hex, blend_hex


# ── Animated Loading Spinner ───────────────────────────────────────────────────

class Spinner(tk.Canvas):
    """Smooth rotating arc spinner drawn on a Canvas."""

    def __init__(self, parent, size=32, color="#a78bfa", bg="#1a1033",
                 thickness=3, speed=20, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=bg, highlightthickness=0, **kw)
        self._size      = size
        self._color     = color
        self._thickness = thickness
        self._speed     = speed          # ms per frame
        self._angle     = 0
        self._running   = False
        self._arc_id    = None
        self._job       = None

        # draw initial arc
        self._draw()

    def _draw(self):
        self.delete("arc")
        pad = self._thickness + 2
        x0, y0 = pad, pad
        x1, y1 = self._size - pad, self._size - pad
        # arc spans ~270° — looks like a "C"
        self.create_arc(x0, y0, x1, y1,
                        start=self._angle,
                        extent=270,
                        style="arc",
                        outline=self._color,
                        width=self._thickness,
                        tags="arc")
        # Faint track ring
        self.create_arc(x0, y0, x1, y1,
                        start=0, extent=359,
                        style="arc",
                        outline=dim_hex(self._color, 0.22),
                        width=self._thickness,
                        tags="arc")

    def _tick(self):
        self._angle = (self._angle + 12) % 360
        self._draw()
        if self._running:
            self._job = self.after(self._speed, self._tick)

    def start(self):
        if not self._running:
            self._running = True
            self._tick()

    def stop(self):
        self._running = False
        if self._job:
            self.after_cancel(self._job)
            self._job = None

    def set_color(self, color: str):
        self._color = color
        self._draw()

    def set_bg(self, bg: str):
        self.configure(bg=bg)
        self._draw()


# ── Pulse dot row (3 bouncing dots) ───────────────────────────────────────────

class PulseDots(tk.Canvas):
    """Three bouncing dots — compact loading indicator."""

    def __init__(self, parent, color="#a78bfa", bg="#1a1033",
                 dot_r=4, spacing=14, **kw):
        w = spacing * 3 + dot_r * 2
        h = dot_r * 2 + 10
        super().__init__(parent, width=w, height=h,
                         bg=bg, highlightthickness=0, **kw)
        self._color   = color
        self._dot_r   = dot_r
        self._spacing = spacing
        self._frame   = 0
        self._running = False
        self._job     = None
        self._w, self._h = w, h
        self._draw(0)

    def _draw(self, frame):
        self.delete("dot")
        cy = self._h // 2
        for i in range(3):
            phase  = (frame + i * 8) % 24
            offset = int(4 * math.sin(phase / 24 * 2 * math.pi))
            cx = self._dot_r + 2 + i * self._spacing
            col = self._color
            r = self._dot_r + (1 if abs(offset) > 2 else 0)
            self.create_oval(cx - r, cy - r + offset,
                             cx + r, cy + r + offset,
                             fill=col, outline="", tags="dot")

    def _tick(self):
        self._frame = (self._frame + 1) % 24
        self._draw(self._frame)
        if self._running:
            self._job = self.after(60, self._tick)

    def start(self):
        if not self._running:
            self._running = True
            self._tick()

    def stop(self):
        self._running = False
        if self._job:
            self.after_cancel(self._job)
            self._job = None
        self._draw(0)

    def set_bg(self, bg: str):
        self.configure(bg=bg)


# ── Auto-Suggest Dropdown ─────────────────────────────────────────────────────

_POSTER_W = 40   # px width of poster thumbnail inside suggestion rows
_POSTER_H = 56   # px height
_ROW_H    = 60   # fixed row height in the suggestion popup

class AutoSuggest:
    """
    Attaches to an Entry widget and shows a popup list of suggestions with
    poster thumbnails, a loading indicator, and episode/type metadata.

    `fetch_fn(query)` must return a list of dicts in the AnimePahe search
    result format (keys: title, session, type, episodes, poster).
    """

    def __init__(self, entry: tk.Entry, app, fetch_fn, on_select):
        self._entry     = entry
        self._app       = app
        self._fetch_fn  = fetch_fn
        self._on_select = on_select
        self._popup     = None
        self._results   = []
        self._debounce  = None
        self._last_q    = ""
        self._loading   = False
        self._row_frames: list[tk.Frame] = []
        self._poster_images: dict[int, object] = {}   # idx → PhotoImage (keep refs)
        self._fetch_token  = 0   # incremented per query so stale results are dropped

        entry.bind("<KeyRelease>",  self._on_key)
        entry.bind("<FocusOut>",    self._on_focus_out)
        entry.bind("<Escape>",      lambda e: self.hide())
        entry.bind("<Down>",        self._focus_next)
        entry.bind("<Up>",          self._focus_prev)

    # ── keystroke handling ────────────────────────────────────────────────────

    def _on_key(self, event):
        if event.keysym in ("Escape", "Return", "Down", "Up",
                            "Left", "Right", "Tab"):
            return
        q = self._entry.get().strip()
        if len(q) < 2 or q.startswith("http"):
            self.hide()
            return
        if q == self._last_q:
            return
        self._last_q = q
        if self._debounce:
            self._entry.after_cancel(self._debounce)
        self._debounce = self._entry.after(350, lambda: self._start_fetch(q))

    def _start_fetch(self, q):
        self._fetch_token += 1
        token = self._fetch_token
        self._show_loading()
        threading.Thread(target=self._fetch_thread, args=(q, token),
                         daemon=True).start()

    def _fetch_thread(self, q: str, token: int):
        try:
            results = self._fetch_fn(q)[:10]
        except Exception:
            results = []
        # Only update if this is still the most recent query
        self._entry.after(0, lambda r=results, t=token: self._on_results(r, t))

    def _on_results(self, results: list, token: int):
        if token != self._fetch_token:
            return
        if not results:
            self.hide()
            return
        self._show(results)

    # ── loading indicator ─────────────────────────────────────────────────────

    def _show_loading(self):
        t = self._app.t
        self._ensure_popup()
        for w in self._popup.winfo_children():
            w.destroy()
        self._row_frames.clear()
        self._poster_images.clear()

        f = tk.Frame(self._popup, bg=t["CARD"], padx=14, pady=10)
        f.pack(fill="x")
        tk.Label(f, text="⏳  Searching…", bg=t["CARD"], fg=t["SUBTEXT"],
                 font=FONT_SM).pack(side="left")
        spin = Spinner(f, size=16, color=t["ACCENT"], bg=t["CARD"],
                       thickness=2, speed=35)
        spin.pack(side="left", padx=(8, 0))
        spin.start()
        self._resize_popup(1)
        self._popup.deiconify()

    # ── results display ───────────────────────────────────────────────────────

    def _ensure_popup(self):
        t = self._app.t
        if self._popup is None or not self._popup.winfo_exists():
            self._popup = tk.Toplevel(self._app)
            self._popup.wm_overrideredirect(True)
            self._popup.configure(bg=t["BORDER"])
            self._popup.attributes("-topmost", True)
        self._reposition_base()

    def _show(self, results: list):
        t = self._app.t
        self._results = results
        self._ensure_popup()

        for w in self._popup.winfo_children():
            w.destroy()
        self._row_frames.clear()
        self._poster_images.clear()

        outer = tk.Frame(self._popup, bg=t["BORDER"])
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=t["CARD"], highlightthickness=0,
                           width=1, height=1)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        inner = tk.Frame(canvas, bg=t["CARD"])
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_cfg(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_cfg(e):
            canvas.itemconfig(win_id, width=e.width)
        inner.bind("<Configure>", _on_inner_cfg)
        canvas.bind("<Configure>", _on_canvas_cfg)
        canvas.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._selected_idx = -1

        for idx, r in enumerate(results):
            title = r.get("title", "?")
            ep    = r.get("episodes", "")
            typ   = r.get("type", "")
            meta  = "  ·  ".join(x for x in [typ, f"{ep} eps" if ep else ""] if x)

            is_alt = idx % 2 == 1
            row_bg = t["PANEL"] if is_alt else t["CARD"]

            row = tk.Frame(inner, bg=row_bg, cursor="hand2",
                           highlightthickness=1, highlightbackground=row_bg)
            row.pack(fill="x", padx=1, pady=0)
            row.grid_columnconfigure(1, weight=1)
            self._row_frames.append(row)

            # Poster thumbnail area
            poster_frame = tk.Frame(row, bg=row_bg, width=_POSTER_W+8,
                                    height=_ROW_H)
            poster_frame.grid(row=0, column=0, rowspan=2, padx=(6, 6), pady=4,
                              sticky="ns")
            poster_frame.grid_propagate(False)

            poster_lbl = tk.Label(poster_frame, text="🎌", bg=row_bg,
                                  fg=t["SUBTEXT"],
                                  font=("Segoe UI", 12), width=_POSTER_W,
                                  height=_POSTER_H)
            poster_lbl.place(relx=0.5, rely=0.5, anchor="center")

            # Text area
            txt_frame = tk.Frame(row, bg=row_bg)
            txt_frame.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(8, 2))
            tk.Label(txt_frame, text=title, bg=row_bg, fg=t["TEXT"],
                     font=FONT_SM, anchor="w", wraplength=260,
                     justify="left").pack(anchor="w")
            if meta:
                tk.Label(txt_frame, text=meta, bg=row_bg, fg=t["SUBTEXT"],
                         font=FONT_XS, anchor="w").pack(anchor="w")

            # Click / hover bindings
            def _enter(e, f=row, bg=row_bg, i=idx):
                f.config(highlightbackground=t["ACCENT"])
                self._selected_idx = i
            def _leave(e, f=row, bg=row_bg):
                f.config(highlightbackground=bg)
            def _click(e, i=idx):
                self._pick(i)

            for widget in (row, poster_lbl, poster_frame, txt_frame):
                widget.bind("<Enter>",          _enter)
                widget.bind("<Leave>",          _leave)
                widget.bind("<ButtonRelease-1>", _click)
            for child in txt_frame.winfo_children():
                child.bind("<Enter>",          _enter)
                child.bind("<Leave>",          _leave)
                child.bind("<ButtonRelease-1>", _click)

            # Schedule poster load
            poster_url = r.get("poster", "") or r.get("cover", "")
            if poster_url:
                self.after_idle(lambda url=poster_url, lbl=poster_lbl,
                                       bg=row_bg, i=idx:
                    threading.Thread(target=self._load_poster,
                                     args=(url, lbl, bg, i),
                                     daemon=True).start())

        n = min(len(results), 8)
        self._resize_popup(n)
        self._popup.deiconify()

    def _load_poster(self, url: str, label: tk.Label,
                     bg: str, idx: int):
        try:
            from PIL import Image, ImageTk
            import session as _sess
            resp = _sess.request("GET", url,
                                 headers={"Referer": "https://animepahe.pw"})
            data = resp.content
            if not data:
                return
            img   = Image.open(io.BytesIO(data))
            img   = img.resize((_POSTER_W, _POSTER_H), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._poster_images[idx] = photo
            label.after(0, lambda lbl=label, ph=photo, bg=bg:
                        lbl.config(image=ph, text="", width=_POSTER_W,
                                   height=_POSTER_H, bg=bg))
        except Exception:
            pass

    # ── sizing / positioning ──────────────────────────────────────────────────

    def _reposition_base(self):
        if not self._popup or not self._popup.winfo_exists():
            return
        entry = self._entry
        entry.update_idletasks()
        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height() + 2
        w = max(entry.winfo_width(), 360)
        self._popup_x = x
        self._popup_y = y
        self._popup_w = w

    def _resize_popup(self, n_rows: int):
        h = min(n_rows * _ROW_H + 4, 8 * _ROW_H)
        x = getattr(self, "_popup_x", 0)
        y = getattr(self, "_popup_y", 0)
        w = getattr(self, "_popup_w", 360)
        self._popup.geometry(f"{w}x{h}+{x}+{y}")

    # ── keyboard navigation ───────────────────────────────────────────────────

    def _focus_next(self, event=None):
        if not self._row_frames:
            return
        t = self._app.t
        prev = self._selected_idx
        self._selected_idx = (prev + 1) % len(self._row_frames)
        self._highlight_row(prev, False)
        self._highlight_row(self._selected_idx, True)

    def _focus_prev(self, event=None):
        if not self._row_frames:
            return
        prev = self._selected_idx
        self._selected_idx = (prev - 1) % len(self._row_frames)
        self._highlight_row(prev, False)
        self._highlight_row(self._selected_idx, True)

    def _highlight_row(self, idx: int, on: bool):
        if idx < 0 or idx >= len(self._row_frames):
            return
        t   = self._app.t
        row = self._row_frames[idx]
        row.config(highlightbackground=t["ACCENT"] if on else row.cget("bg"))

    def _pick(self, idx: int):
        if 0 <= idx < len(self._results):
            self._on_select(self._results[idx])
        self.hide()

    # ── enter-key on entry while popup open ──────────────────────────────────

    def pick_selected(self):
        if self._selected_idx >= 0:
            self._pick(self._selected_idx)

    # ── focus-out / hide / destroy ────────────────────────────────────────────

    def _on_focus_out(self, event):
        self._entry.after(200, self._maybe_hide)

    def _maybe_hide(self):
        try:
            focus = self._app.focus_get()
            if self._popup and self._popup.winfo_exists():
                if str(focus).startswith(str(self._popup)):
                    return
        except Exception:
            pass
        self.hide()

    def hide(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.withdraw()

    def destroy(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()

    # ── after_idle helper ────────────────────────────────────────────────────

    def after_idle(self, fn):
        try:
            self._app.after_idle(fn)
        except Exception:
            pass


# ── Animated "Fade-in" Frame ───────────────────────────────────────────────────

class FadeLabel(tk.Label):
    """Label that fades in its text by stepping opacity using colour interpolation."""

    def __init__(self, parent, target_fg="#ffffff", bg="#1a1033", **kw):
        self._target_fg = target_fg
        self._bg_hex    = bg
        self._step      = 0
        self._steps     = 12
        self._job       = None
        super().__init__(parent, bg=bg, fg=bg, **kw)

    def fade_in(self, delay_ms=0):
        if self._job:
            self.after_cancel(self._job)
        self._step = 0
        self.after(delay_ms, self._tick)

    def _interp_color(self, step):
        """Interpolate from bg colour to target_fg."""
        def _hex(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        try:
            r0, g0, b0 = _hex(self._bg_hex)
            r1, g1, b1 = _hex(self._target_fg)
        except Exception:
            return self._target_fg
        t = step / self._steps
        r = int(r0 + (r1 - r0) * t)
        g = int(g0 + (g1 - g0) * t)
        b = int(b0 + (b1 - b0) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _tick(self):
        if self._step <= self._steps:
            self.configure(fg=self._interp_color(self._step))
            self._step += 1
            self._job = self.after(18, self._tick)


# ── Animated action button ────────────────────────────────────────────────────

class PulseButton(tk.Button):
    """Button that subtly pulses when set to active state."""

    def __init__(self, parent, accent="#a78bfa", **kw):
        self._accent      = accent
        self._pulsing     = False
        self._pulse_job   = None
        self._pulse_step  = 0
        super().__init__(parent, **kw)

    def start_pulse(self):
        if not self._pulsing:
            self._pulsing = True
            self._pulse_tick()

    def stop_pulse(self):
        self._pulsing = False
        if self._pulse_job:
            self.after_cancel(self._pulse_job)
            self._pulse_job = None
        try:
            self.configure(bg=self._accent)
        except Exception:
            pass

    def _pulse_tick(self):
        if not self._pulsing:
            return
        self._pulse_step = (self._pulse_step + 1) % 20
        t = self._pulse_step / 20
        # oscillate brightness
        factor = 0.85 + 0.15 * math.sin(t * 2 * math.pi)
        col = self._dim(self._accent, factor)
        try:
            self.configure(bg=col)
        except Exception:
            pass
        self._pulse_job = self.after(60, self._pulse_tick)

    @staticmethod
    def _dim(hex_col: str, factor: float) -> str:
        hex_col = hex_col.lstrip("#")
        r, g, b = (int(hex_col[i:i+2], 16) for i in (0, 2, 4))
        return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"


# ── Tooltip ───────────────────────────────────────────────────────────────────

class Tooltip:
    def __init__(self, widget, text: str, theme: dict = None):
        self._widget = widget
        self._text   = text
        self._theme  = theme or {}
        self._popup  = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event):
        t = self._theme
        bg = t.get("CARD", "#161b22")
        fg = t.get("TEXT", "#e6edf3")

        self._popup = tk.Toplevel(self._widget)
        self._popup.wm_overrideredirect(True)
        self._popup.attributes("-topmost", True)
        self._popup.configure(bg=t.get("BORDER", "#30363d"))

        lbl = tk.Label(self._popup, text=f"  {self._text}  ",
                       bg=bg, fg=fg, font=FONT_XS, padx=4, pady=4)
        lbl.pack()

        self._popup.update_idletasks()
        x = self._widget.winfo_rootx() + 10
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._popup.geometry(f"+{x}+{y}")

    def _hide(self, event):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
        self._popup = None
