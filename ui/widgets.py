"""
Reusable animated widgets for AnimePahe Downloader.
"""
import math
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

class AutoSuggest:
    """
    Attaches to an Entry widget and shows a popup list of suggestions.
    `fetch_fn(query)` must return a list of dicts with 'title' and 'session' keys
    (the AnimePahe search result format).
    """

    def __init__(self, entry: tk.Entry, app, fetch_fn, on_select):
        self._entry    = entry
        self._app      = app
        self._fetch_fn = fetch_fn
        self._on_select = on_select
        self._popup    = None
        self._listbox  = None
        self._results  = []
        self._debounce = None
        self._last_q   = ""

        entry.bind("<KeyRelease>", self._on_key)
        entry.bind("<FocusOut>",   self._on_focus_out)
        entry.bind("<Escape>",     lambda e: self.hide())
        entry.bind("<Down>",       self._focus_list)

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
        self._debounce = self._entry.after(380, lambda: self._do_fetch(q))

    def _do_fetch(self, q):
        import threading
        threading.Thread(target=self._fetch_thread, args=(q,), daemon=True).start()

    def _fetch_thread(self, q):
        try:
            results = self._fetch_fn(q)[:8]
            self._entry.after(0, lambda r=results: self._show(r))
        except Exception:
            pass

    def _show(self, results):
        if not results:
            self.hide()
            return
        self._results = results
        t = self._app.t

        if self._popup is None or not self._popup.winfo_exists():
            self._popup = tk.Toplevel(self._app)
            self._popup.wm_overrideredirect(True)
            self._popup.configure(bg=t["BORDER"])
            self._popup.attributes("-topmost", True)

        for w in self._popup.winfo_children():
            w.destroy()

        outer = tk.Frame(self._popup, bg=t["BORDER"], padx=1, pady=1)
        outer.pack(fill="both", expand=True)

        sb = ttk.Scrollbar(outer, orient="vertical")
        lb = tk.Listbox(outer, bg=t["CARD"], fg=t["TEXT"],
                        selectbackground=t["ACCENT"],
                        selectforeground="white",
                        font=FONT_SM, relief="flat",
                        highlightthickness=0, bd=0,
                        activestyle="none",
                        yscrollcommand=sb.set,
                        height=min(len(results), 8))
        sb.configure(command=lb.yview)
        lb.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._listbox = lb

        for r in results:
            title = r.get("title", "?")
            ep    = r.get("episodes", "")
            typ   = r.get("type", "")
            line  = f"  {title}"
            if typ or ep:
                line += f"  [{typ}  {ep} eps]".replace("  ]", "]")
            lb.insert("end", line)

        lb.bind("<ButtonRelease-1>", self._on_pick)
        lb.bind("<Return>",          self._on_pick)

        # Position below the entry
        self._reposition()
        self._popup.deiconify()

    def _reposition(self):
        if not self._popup or not self._popup.winfo_exists():
            return
        entry = self._entry
        entry.update_idletasks()
        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height() + 2
        w = max(entry.winfo_width(), 320)
        self._popup.geometry(f"{w}x{min(len(self._results)*28+4, 240)}+{x}+{y}")

    def _on_pick(self, event):
        if not self._listbox:
            return
        sel = self._listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self._results):
            self._on_select(self._results[idx])
        self.hide()

    def _focus_list(self, event):
        if self._listbox and self._listbox.winfo_exists():
            self._listbox.focus_set()
            self._listbox.selection_set(0)

    def _on_focus_out(self, event):
        self._entry.after(200, self._maybe_hide)

    def _maybe_hide(self):
        try:
            focus = self._app.focus_get()
            if self._listbox and focus == self._listbox:
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
