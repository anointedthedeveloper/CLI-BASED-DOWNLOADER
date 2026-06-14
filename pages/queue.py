"""
pages/queue.py — Download queue page.
Shows queued anime downloads, lets the user start/stop/manage the queue.
"""
import tkinter as tk
from tkinter import ttk

from ui.theme import (FONT, FONT_SM, FONT_BOLD, FONT_XS, FONT_LG,
                      blend_hex, fmt_size)
from ui.widgets import Spinner, PulseButton


class QueuePage(tk.Frame):
    def __init__(self, parent, app):
        self.app = app
        t = app.t
        super().__init__(parent, bg=t["BG"])
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._card_frames   = {}   # item.id → tk.Frame
        self._prog_vars     = {}   # item.id → DoubleVar
        self._build(t)

        app._queue.on_update = self._schedule_refresh

    def _schedule_refresh(self):
        self.after(0, self.refresh)

    # ── build ─────────────────────────────────────────────────────────────────

    def _build(self, t):
        self._build_header(t)
        self._build_list_area(t)
        self.refresh()

    def _build_header(self, t):
        hdr = tk.Frame(self, bg=t["CARD"], padx=16, pady=12)
        hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        hdr.grid_columnconfigure(1, weight=1)
        self._hdr = hdr

        tk.Label(hdr, text="Download Queue", fg=t["ACCENT"],
                 bg=t["CARD"], font=FONT_LG).grid(row=0, column=0, sticky="w")

        btn_row = tk.Frame(hdr, bg=t["CARD"])
        btn_row.grid(row=0, column=2, sticky="e")
        self._btn_row = btn_row

        self._clear_btn = tk.Button(
            btn_row, text="🗑  Clear Done",
            bg=t["HDR_BTN"], fg=t["TEXT"],
            relief="flat", font=FONT_SM, cursor="hand2",
            bd=0, padx=12, pady=6,
            command=self._clear_done)
        self._clear_btn.pack(side="left", padx=(0, 8))

        self._stop_btn = tk.Button(
            btn_row, text="⬛  Stop",
            bg=t["DANGER"], fg="white",
            activebackground=t["DANGER"], activeforeground="white",
            relief="flat", font=FONT_SM, cursor="hand2",
            bd=0, padx=12, pady=6, state="disabled",
            command=self._stop_queue)
        self._stop_btn.pack(side="left", padx=(0, 8))

        self._start_btn = PulseButton(
            btn_row, accent=t["ACCENT"],
            text="▶  Start Queue",
            bg=t["ACCENT"], fg="white",
            activebackground=t["ACCENT_HV"], activeforeground="white",
            relief="flat", font=FONT_BOLD, cursor="hand2",
            bd=0, padx=14, pady=6,
            command=self._start_queue)
        self._start_btn.pack(side="left")

        self._spinner = Spinner(btn_row, size=18, color=t["ACCENT"],
                                bg=t["CARD"], thickness=2, speed=35)
        self._spinner.pack(side="left", padx=(8, 0))
        self._spinner.pack_forget()

        self._count_var = tk.StringVar(value="")
        tk.Label(hdr, textvariable=self._count_var,
                 bg=t["CARD"], fg=t["SUBTEXT"], font=FONT_SM).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))

    def _build_list_area(self, t):
        outer = tk.Frame(self, bg=t["BG"])
        outer.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        self._list_outer = outer

        # Empty-state banner
        self._empty = tk.Frame(outer, bg=t["CARD"], padx=24, pady=24)
        self._empty.grid(row=0, column=0, sticky="nsew")
        inner = tk.Frame(self._empty, bg=t["CARD"])
        inner.place(relx=0.5, rely=0.5, anchor="center")
        self._empty_inner = inner
        tk.Label(inner, text="📋", font=("Segoe UI", 36),
                 bg=t["CARD"], fg=t["ACCENT"]).pack()
        tk.Label(inner, text="Queue is empty",
                 font=FONT_BOLD, bg=t["CARD"], fg=t["TEXT"]).pack(pady=(6, 2))
        tk.Label(inner,
                 text="Browse anime → select episodes → click 'Add to Queue'",
                 font=FONT_SM, bg=t["CARD"], fg=t["SUBTEXT"]).pack()
        self._empty.lift()

        # Scrollable card list
        border = tk.Frame(outer, bg=t["BORDER"], padx=1, pady=1)
        border.grid(row=0, column=0, sticky="nsew")
        border.grid_rowconfigure(0, weight=1)
        border.grid_columnconfigure(0, weight=1)
        self._list_border = border

        canvas = tk.Canvas(border, bg=t["BG"], highlightthickness=0)
        vsb    = ttk.Scrollbar(border, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self._canvas = canvas
        self._vsb    = vsb

        self._list_frame = tk.Frame(canvas, bg=t["BG"])
        self._list_frame.grid_columnconfigure(0, weight=1)
        self._cwin = canvas.create_window((0, 0), window=self._list_frame, anchor="nw")

        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(self._cwin, width=e.width))
        self._list_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

    # ── queue actions ─────────────────────────────────────────────────────────

    def _start_queue(self):
        q = self.app._queue
        if q.pending_count() == 0:
            import tkinter.messagebox as mb
            mb.showwarning("Queue Empty",
                           "No pending items in the queue.\n"
                           "Browse anime and click 'Add to Queue' to add downloads.")
            return
        q.start(self.app._queue_download_fn)
        self.refresh()

    def _stop_queue(self):
        self.app._queue.stop()

    def _clear_done(self):
        self.app._queue.clear_done()

    # ── refresh ───────────────────────────────────────────────────────────────

    def refresh(self):
        q     = self.app._queue
        items = list(q.items)
        t     = self.app.t

        # Header summary
        pending = sum(1 for i in items if i.status == "pending")
        active  = sum(1 for i in items if i.status == "active")
        done    = sum(1 for i in items if i.status in ("done", "error", "cancelled"))
        parts = []
        if pending: parts.append(f"{pending} pending")
        if active:  parts.append(f"{active} active")
        if done:    parts.append(f"{done} finished")
        self._count_var.set("  ·  ".join(parts) if parts else "No items")

        running = q.is_active()
        self._start_btn.config(
            state="disabled" if running else "normal",
            bg=t["BORDER"] if running else t["ACCENT"])
        self._stop_btn.config(state="normal" if running else "disabled")
        if running:
            self._spinner.pack(side="left", padx=(8, 0))
            self._spinner.start()
        else:
            self._spinner.stop()
            self._spinner.pack_forget()

        # Show empty state or list
        if items:
            self._list_border.tkraise()
        else:
            self._empty.tkraise()

        # Reconcile cards
        current_ids  = {i.id for i in items}
        existing_ids = set(self._card_frames.keys())

        for iid in existing_ids - current_ids:
            f = self._card_frames.pop(iid, None)
            if f and f.winfo_exists():
                f.destroy()
            self._prog_vars.pop(iid, None)

        for row_idx, item in enumerate(items):
            if item.id not in self._card_frames:
                self._card_frames[item.id] = self._build_card(item, t)
            self._update_card(item, t)
            frame = self._card_frames[item.id]
            if frame.winfo_exists():
                frame.grid(row=row_idx, column=0, sticky="ew",
                           padx=4, pady=(0, 6))

    # ── card builders ─────────────────────────────────────────────────────────

    def _build_card(self, item, t) -> tk.Frame:
        card = tk.Frame(self._list_frame, bg=t["CARD"],
                        padx=14, pady=10,
                        highlightthickness=1,
                        highlightbackground=t["BORDER"])
        card.grid_columnconfigure(1, weight=1)

        # Badge (top-right)
        badge = tk.Label(card, text="", bg=t["BORDER"], fg=t["SUBTEXT"],
                         font=FONT_XS, padx=6, pady=2)
        badge.grid(row=0, column=2, sticky="ne", padx=(8, 0))
        card._badge = badge

        # Title
        title_lbl = tk.Label(card, text=item.title, bg=t["CARD"],
                             fg=t["TEXT"], font=FONT_BOLD, anchor="w")
        title_lbl.grid(row=0, column=0, columnspan=2, sticky="w")
        card._title_lbl = title_lbl

        # Info line
        info_lbl = tk.Label(card, text="", bg=t["CARD"],
                            fg=t["SUBTEXT"], font=FONT_XS, anchor="w")
        info_lbl.grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 4))
        card._info_lbl = info_lbl

        # Progress bar
        pvar = tk.DoubleVar(value=0)
        pbar = ttk.Progressbar(card, variable=pvar, maximum=100,
                               style="Accent.Horizontal.TProgressbar")
        pbar.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(2, 4))
        pbar.grid_remove()
        card._pbar = pbar
        self._prog_vars[item.id] = pvar

        # Error label
        err_lbl = tk.Label(card, text="", bg=t["CARD"], fg=t["DANGER"],
                           font=FONT_XS, anchor="w", wraplength=480,
                           justify="left")
        err_lbl.grid(row=3, column=0, columnspan=3, sticky="w")
        err_lbl.grid_remove()
        card._err_lbl = err_lbl

        # Remove button (pending only)
        rem_btn = tk.Button(card, text="✕",
                            bg=t["BORDER"], fg=t["SUBTEXT"],
                            activebackground=t["DANGER"],
                            activeforeground="white",
                            relief="flat", font=FONT_XS,
                            cursor="hand2", bd=0, padx=8, pady=2,
                            command=lambda: self.app._queue.remove(item.id))
        rem_btn.grid(row=0, column=3, sticky="ne", padx=(4, 0))
        card._rem_btn = rem_btn

        return card

    def _update_card(self, item, t):
        card = self._card_frames.get(item.id)
        if not card or not card.winfo_exists():
            return

        pv = self._prog_vars.get(item.id)
        if pv:
            pv.set(item.progress)

        eps = item.ep_count
        ep_str = f"Ep {item.current_ep}/{eps}" if item.status == "active" else f"{eps} ep(s)"
        info = f"{ep_str}  ·  {item.quality_label}  ·  {item.audio_label}"
        if item.status == "active":
            info += f"  ·  {item.progress:.0f}%"
        card._info_lbl.config(text=info)

        STATUS = {
            "pending":   (t["BORDER"],                                  t["SUBTEXT"], "⏳  Pending"),
            "active":    (blend_hex(t["ACCENT"],  t["CARD"], 0.20),     t["ACCENT"],  "⬇  Downloading"),
            "done":      (blend_hex(t["SUCCESS"], t["CARD"], 0.20),     t["SUCCESS"], "✓  Done"),
            "error":     (blend_hex(t["DANGER"],  t["CARD"], 0.20),     t["DANGER"],  "✗  Error"),
            "cancelled": (t["BORDER"],                                  t["SUBTEXT"], "—  Cancelled"),
        }
        bg, fg, text = STATUS.get(item.status, (t["BORDER"], t["SUBTEXT"], item.status))
        card._badge.config(text=text, bg=bg, fg=fg)
        border_col = fg if item.status in ("active", "done", "error") else t["BORDER"]
        card.config(highlightbackground=border_col)

        card._pbar.grid() if item.status == "active" else card._pbar.grid_remove()

        if item.status == "error" and item.error:
            card._err_lbl.config(text=f"Error: {item.error}")
            card._err_lbl.grid()
        else:
            card._err_lbl.grid_remove()

        if item.status == "pending":
            card._rem_btn.grid()
        else:
            card._rem_btn.grid_remove()

    # ── theme ─────────────────────────────────────────────────────────────────

    def apply_theme(self):
        t = self.app.t
        self.configure(bg=t["BG"])
        self._hdr.configure(bg=t["CARD"])
        self._btn_row.configure(bg=t["CARD"])
        self._clear_btn.configure(bg=t["HDR_BTN"], fg=t["TEXT"])
        self._stop_btn.configure(bg=t["DANGER"])
        if hasattr(self._start_btn, "_accent"):
            self._start_btn._accent = t["ACCENT"]
        self._spinner.set_color(t["ACCENT"])
        self._spinner.set_bg(t["CARD"])
        self._list_outer.configure(bg=t["BG"])
        self._list_border.configure(bg=t["BORDER"])
        self._canvas.configure(bg=t["BG"])
        self._list_frame.configure(bg=t["BG"])
        self._empty.configure(bg=t["CARD"])
        self._empty_inner.configure(bg=t["CARD"])
        for ch in self._empty_inner.winfo_children():
            try: ch.configure(bg=t["CARD"])
            except Exception: pass
        # Rebuild all cards with new colours
        for f in list(self._card_frames.values()):
            if f.winfo_exists():
                f.destroy()
        self._card_frames.clear()
        self._prog_vars.clear()
        self.refresh()
