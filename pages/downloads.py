"""
Downloads page — save-to controls, active download cards,
dual progress bars, and activity log.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog

from ui.theme import (FONT, FONT_SM, FONT_BOLD, FONT_MONO, FONT_XS, FONT_LG,
                      fmt_size, blend_hex, dim_hex)
from ui.widgets import Spinner, PulseButton


class DownloadsPage(tk.Frame):
    def __init__(self, parent, app):
        self.app = app
        t = app.t
        super().__init__(parent, bg=t["BG"])
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build(t)

    def _build(self, t):
        self._build_controls(t)
        self._build_main_area(t)

    # ── controls ──────────────────────────────────────────────────────────────

    def _build_controls(self, t):
        ctrl = tk.Frame(self, bg=t["CARD"], padx=16, pady=12)
        ctrl.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        ctrl.grid_columnconfigure(1, weight=1)
        self._ctrl = ctrl

        tk.Label(ctrl, text="Save to", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_BOLD, anchor="w", width=7).grid(row=0, column=0, sticky="w")

        self._dir_entry = tk.Entry(
            ctrl, textvariable=self.app.dir_var,
            bg=t["PANEL"], fg=t["TEXT"],
            insertbackground=t["ACCENT"], relief="flat", font=FONT,
            highlightthickness=1,
            highlightbackground=t["BORDER"], highlightcolor=t["ACCENT"])
        self._dir_entry.grid(row=0, column=1, sticky="ew", padx=(6, 8))
        self._dir_entry.bind("<KeyRelease>", lambda e: self._refresh_disk())

        self._browse_btn = self._mk_btn(ctrl, "📁 Browse", self._browse,
                                        t["HDR_BTN"], t["TEXT"])
        self._browse_btn.grid(row=0, column=2, padx=(0, 8))

        self._solve_btn = self._mk_btn(ctrl, "🛡 Solve CF", self.app.solve_cf,
                                       "#7c3aed", "white")
        self._solve_btn.grid(row=0, column=3, padx=(0, 6))

        self.start_btn = PulseButton(
            ctrl, accent=t["ACCENT"],
            text="⬇  Start Download", command=self.app.start_download,
            bg=t["ACCENT"], fg="white",
            activebackground=t["ACCENT_HV"], activeforeground="white",
            relief="flat", font=FONT_BOLD, cursor="hand2",
            bd=0, padx=14, pady=7)
        self.start_btn.grid(row=0, column=4, padx=(0, 6))

        self.stop_btn = self._mk_btn(ctrl, "🟥 Stop", self.app.stop_download,
                                     t["DANGER"], "white", bold=True)
        self.stop_btn.config(state="disabled")
        self.stop_btn.grid(row=0, column=5)

        # Disk info
        self._disk_var = tk.StringVar(value=self._get_disk_space())
        self._disk_lbl = tk.Label(ctrl, textvariable=self._disk_var,
                                  fg=t["SUBTEXT"], bg=t["CARD"], font=FONT_XS, anchor="w")
        self._disk_lbl.grid(row=1, column=1, columnspan=4, sticky="w", pady=(4, 0))

    def _mk_btn(self, parent, text, cmd, bg, fg, bold=False):
        f = FONT_BOLD if bold else FONT_SM
        return tk.Button(parent, text=text, command=cmd,
                         bg=bg, fg=fg,
                         activebackground=self.app.t["ACCENT_HV"],
                         activeforeground="white",
                         relief="flat", font=f, cursor="hand2",
                         bd=0, padx=12, pady=7)

    def _browse(self):
        d = filedialog.askdirectory()
        if d:
            self.app.dir_var.set(d)
            self._refresh_disk()

    def _get_disk_space(self):
        try:
            import shutil
            path = self.app.dir_var.get() if hasattr(self.app, "dir_var") \
                   else os.path.expanduser("~/Downloads")
            if not os.path.exists(path):
                path = os.path.expanduser("~/Downloads")
            st = shutil.disk_usage(path)
            return f"💾  {fmt_size(st.free)} free of {fmt_size(st.total)}"
        except Exception:
            return "Disk space unavailable"

    def _refresh_disk(self):
        self._disk_var.set(self._get_disk_space())

    # ── main area ─────────────────────────────────────────────────────────────

    def _build_main_area(self, t):
        area = tk.Frame(self, bg=t["BG"])
        area.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        area.grid_rowconfigure(1, weight=1)
        area.grid_columnconfigure(0, weight=1)
        self._area = area

        self._build_progress(area, t)
        self._build_status_area(area, t)

    # ── progress card ─────────────────────────────────────────────────────────

    def _build_progress(self, parent, t):
        card = tk.Frame(parent, bg=t["CARD"], padx=16, pady=14)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        card.grid_columnconfigure(1, weight=1)
        self._prog_card = card

        # Row 0 — header + spinner
        head_row = tk.Frame(card, bg=t["CARD"])
        head_row.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        self._prog_head = head_row
        tk.Label(head_row, text="Download Progress", fg=t["ACCENT"],
                 bg=t["CARD"], font=FONT_BOLD).pack(side="left")
        self._dl_spinner = Spinner(head_row, size=22,
                                   color=t["SUCCESS"], bg=t["CARD"],
                                   thickness=2, speed=35)
        self._dl_spinner.pack(side="left", padx=(8, 0))
        self._dl_spinner.pack_forget()        # hidden until download starts

        # Status badge
        self._status_badge = tk.Label(head_row, text="Idle",
                                      bg=t["BORDER"], fg=t["SUBTEXT"],
                                      font=FONT_XS, padx=8, pady=3)
        self._status_badge.pack(side="right")

        # Overall bar
        tk.Label(card, text="Overall", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_SM, width=7, anchor="w").grid(row=1, column=0, sticky="w")
        self.overall_var = tk.DoubleVar()
        self.overall_bar = ttk.Progressbar(
            card, variable=self.overall_var, maximum=100,
            style="Accent.Horizontal.TProgressbar")
        self.overall_bar.grid(row=1, column=1, sticky="ew", padx=(0, 10))
        self._overall_info_var = tk.StringVar(value="")
        self._overall_info_lbl = tk.Label(
            card, textvariable=self._overall_info_var,
            fg=t["SUBTEXT"], bg=t["CARD"], font=FONT_SM, anchor="e", width=26)
        self._overall_info_lbl.grid(row=1, column=2, sticky="e")

        # File bar
        tk.Label(card, text="File", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_SM, width=7, anchor="w").grid(
            row=2, column=0, sticky="w", pady=(8, 0))
        self.file_var = tk.DoubleVar()
        self.file_bar = ttk.Progressbar(
            card, variable=self.file_var, maximum=100,
            style="Success.Horizontal.TProgressbar")
        self.file_bar.grid(row=2, column=1, sticky="ew",
                           padx=(0, 10), pady=(8, 0))
        self._file_info_var = tk.StringVar(value="")
        self._file_info_lbl = tk.Label(
            card, textvariable=self._file_info_var,
            fg=t["SUCCESS"], bg=t["CARD"], font=FONT_SM, anchor="e", width=26)
        self._file_info_lbl.grid(row=2, column=2, sticky="e", pady=(8, 0))

    # ── status / log area ─────────────────────────────────────────────────────

    def _build_status_area(self, parent, t):
        area = tk.Frame(parent, bg=t["BG"])
        area.grid(row=1, column=0, sticky="nsew")
        area.grid_rowconfigure(1, weight=1)
        area.grid_columnconfigure(0, weight=1)
        self._status_area = area

        # Info banner (shown when idle)
        self._idle_banner = tk.Frame(area, bg=t["CARD"], padx=24, pady=24)
        self._idle_banner.grid(row=0, column=0, sticky="nsew")
        self._idle_inner = tk.Frame(self._idle_banner, bg=t["CARD"])
        self._idle_inner.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(self._idle_inner, text="⬇", font=("Segoe UI", 36),
                 bg=t["CARD"], fg=t["ACCENT"]).pack()
        tk.Label(self._idle_inner, text="No active downloads",
                 font=FONT_BOLD, bg=t["CARD"], fg=t["TEXT"]).pack(pady=(6, 2))
        tk.Label(self._idle_inner,
                 text="Browse page → Fetch episodes → select them → Start Download",
                 font=FONT_SM, bg=t["CARD"], fg=t["SUBTEXT"]).pack()

        # Compact log (shown when downloading)
        log_frame = tk.Frame(area, bg=t["BG"])
        log_frame.grid(row=0, column=0, sticky="nsew")
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        self._log_frame = log_frame

        log_hdr = tk.Frame(log_frame, bg=t["BG"])
        log_hdr.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        tk.Label(log_hdr, text="Recent Activity", fg=t["ACCENT"],
                 bg=t["BG"], font=FONT_BOLD).pack(side="left")
        self._clear_btn = tk.Button(
            log_hdr, text="Clear", bg=t["HDR_BTN"], fg=t["TEXT"],
            relief="flat", font=FONT_XS, cursor="hand2", bd=0, padx=8, pady=3,
            command=self._clear_log)
        self._clear_btn.pack(side="right")
        self._log_hdr = log_hdr

        border = tk.Frame(log_frame, bg=t["BORDER"], padx=1, pady=1)
        border.grid(row=1, column=0, sticky="nsew")
        border.grid_rowconfigure(0, weight=1)
        border.grid_columnconfigure(0, weight=1)
        self._log_border = border

        self.log_box = tk.Text(
            border, bg=t["TERMINAL"], fg=t["TERM_FG"],
            insertbackground=t["ACCENT"],
            font=FONT_MONO, relief="flat",
            state="disabled", wrap="word", padx=12, pady=10)
        self.log_box.tag_config("error",   foreground=t["DANGER"])
        self.log_box.tag_config("success", foreground=t["SUCCESS"])
        self.log_box.tag_config("info",    foreground=t["SUBTEXT"])
        self.log_box.tag_config("header",  foreground=t["ACCENT"],
                                font=FONT_BOLD)

        log_sb = ttk.Scrollbar(border, orient="vertical",
                               command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=log_sb.set)
        self.log_box.grid(row=0, column=0, sticky="nsew")
        log_sb.grid(row=0, column=1, sticky="ns")

        # Start with idle banner on top
        self._idle_banner.tkraise()

    # ── public helpers ────────────────────────────────────────────────────────

    def log(self, msg: str, tag: str = ""):
        def _do():
            self.log_box.config(state="normal")
            self.log_box.insert("end", msg + "\n", tag if tag else ())
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        self.after(0, _do)

    def _clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")

    def set_file_progress(self, pct: float, label: str = ""):
        def _do():
            self.file_var.set(pct)
            self._file_info_var.set(label)
        self.after(0, _do)

    def set_overall_progress(self, pct: float, label: str = ""):
        def _do():
            self.overall_var.set(pct)
            self._overall_info_var.set(label)
        self.after(0, _do)

    def set_buttons(self, running: bool):
        t = self.app.t
        def _do():
            if running:
                self.start_btn.config(state="disabled",
                                      bg=t["BORDER"])
                self.start_btn.stop_pulse()
                self.stop_btn.config(state="normal")
                self._dl_spinner.pack(side="left", padx=(8, 0))
                self._dl_spinner.start()
                self._status_badge.config(text=" Downloading… ",
                                          bg=blend_hex(t["SUCCESS"], t["CARD"], 0.18),
                                          fg=t["SUCCESS"])
                self._log_frame.tkraise()
            else:
                self.start_btn.config(state="normal", bg=t["ACCENT"])
                self.start_btn.stop_pulse()
                self.stop_btn.config(state="disabled")
                self._dl_spinner.stop()
                self._dl_spinner.pack_forget()
                self._status_badge.config(text="Idle",
                                          bg=t["BORDER"],
                                          fg=t["SUBTEXT"])
                self._idle_banner.tkraise()
        self.after(0, _do)

    def set_solve_btn(self, active: bool, text: str = "🛡 Solve CF"):
        def _do():
            self._solve_btn.config(
                state="normal" if active else "disabled", text=text)
        self.after(0, _do)

    # ── theme ─────────────────────────────────────────────────────────────────

    def apply_theme(self):
        t = self.app.t
        self.configure(bg=t["BG"])

        self._ctrl.configure(bg=t["CARD"])
        self._dir_entry.configure(bg=t["PANEL"], fg=t["TEXT"],
                                  insertbackground=t["ACCENT"],
                                  highlightbackground=t["BORDER"],
                                  highlightcolor=t["ACCENT"])
        self._browse_btn.configure(bg=t["HDR_BTN"], fg=t["TEXT"])
        self.start_btn.configure(fg="white")
        self.start_btn._accent = t["ACCENT"]
        self.stop_btn.configure(bg=t["DANGER"], fg="white")
        self._disk_lbl.configure(bg=t["CARD"], fg=t["SUBTEXT"])

        self._area.configure(bg=t["BG"])
        self._prog_card.configure(bg=t["CARD"])
        self._prog_head.configure(bg=t["CARD"])
        self._dl_spinner.set_color(t["SUCCESS"])
        self._dl_spinner.set_bg(t["CARD"])
        self._overall_info_lbl.configure(bg=t["CARD"], fg=t["SUBTEXT"])
        self._file_info_lbl.configure(bg=t["CARD"], fg=t["SUCCESS"])
        for child in self._prog_card.winfo_children():
            try:
                if child.winfo_class() == "Label":
                    child.configure(bg=t["CARD"])
            except Exception:
                pass

        self._idle_banner.configure(bg=t["CARD"])
        self._idle_inner.configure(bg=t["CARD"])
        for child in self._idle_inner.winfo_children():
            try:
                child.configure(bg=t["CARD"])
            except Exception:
                pass

        self._status_area.configure(bg=t["BG"])
        self._log_frame.configure(bg=t["BG"])
        self._log_hdr.configure(bg=t["BG"])
        self._clear_btn.configure(bg=t["HDR_BTN"], fg=t["TEXT"])
        self._log_border.configure(bg=t["BORDER"])
        self.log_box.configure(bg=t["TERMINAL"], fg=t["TERM_FG"],
                               insertbackground=t["ACCENT"])
        self.log_box.tag_config("error",   foreground=t["DANGER"])
        self.log_box.tag_config("success", foreground=t["SUCCESS"])
        self.log_box.tag_config("info",    foreground=t["SUBTEXT"])
        self.log_box.tag_config("header",  foreground=t["ACCENT"])
