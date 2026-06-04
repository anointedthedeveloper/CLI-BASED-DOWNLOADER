import os
import tkinter as tk
from tkinter import ttk, filedialog

from ui.theme import (FONT, FONT_SM, FONT_BOLD, FONT_MONO, FONT_XS,
                      fmt_size, shorten_path)


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

    # ── top controls bar ──────────────────────────────────────────────────────

    def _build_controls(self, t):
        ctrl = tk.Frame(self, bg=t["CARD"], padx=16, pady=12)
        ctrl.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        ctrl.grid_columnconfigure(1, weight=1)
        self._ctrl = ctrl

        # Save-to row
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

        self._browse_btn = self._btn(ctrl, "📁 Browse", self._browse,
                                     t["HDR_BTN"], t["TEXT"])
        self._browse_btn.grid(row=0, column=2, padx=(0, 8))

        self._solve_btn = self._btn(ctrl, "🛡 Solve CF", self.app.solve_cf,
                                    "#7c3aed", "white")
        self._solve_btn.grid(row=0, column=3, padx=(0, 6))

        self.start_btn = self._btn(ctrl, "⬇  Start Download", self.app.start_download,
                                   t["ACCENT"], "white", bold=True)
        self.start_btn.grid(row=0, column=4, padx=(0, 6))

        self.stop_btn = self._btn(ctrl, "🟥 Stop", self.app.stop_download,
                                  t["DANGER"], "white", bold=True)
        self.stop_btn.config(state="disabled")
        self.stop_btn.grid(row=0, column=5)

        # Disk space label
        self._disk_var = tk.StringVar(value=self._get_disk_space())
        self._disk_lbl = tk.Label(ctrl, textvariable=self._disk_var,
                                  fg=t["SUBTEXT"], bg=t["CARD"], font=FONT_XS, anchor="w")
        self._disk_lbl.grid(row=1, column=1, columnspan=4, sticky="w", pady=(4, 0))

    def _btn(self, parent, text, cmd, bg, fg, bold=False):
        f = FONT_BOLD if bold else FONT_SM
        b = tk.Button(parent, text=text, command=cmd,
                      bg=bg, fg=fg,
                      activebackground=self.app.t["ACCENT_HV"],
                      activeforeground="white",
                      relief="flat", font=f, cursor="hand2",
                      bd=0, padx=13, pady=7)
        return b

    def _browse(self):
        d = filedialog.askdirectory()
        if d:
            self.app.dir_var.set(d)
            self._refresh_disk()

    def _get_disk_space(self):
        try:
            import shutil
            path = self.app.dir_var.get() if hasattr(self.app, "dir_var") else os.path.expanduser("~/Downloads")
            if not os.path.exists(path):
                path = os.path.expanduser("~/Downloads")
            st = shutil.disk_usage(path)
            return f"💾  {fmt_size(st.free)} free of {fmt_size(st.total)}"
        except Exception:
            return "Disk space unavailable"

    def _refresh_disk(self):
        self._disk_var.set(self._get_disk_space())

    # ── main area (progress + log) ────────────────────────────────────────────

    def _build_main_area(self, t):
        area = tk.Frame(self, bg=t["BG"])
        area.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        area.grid_rowconfigure(1, weight=1)
        area.grid_columnconfigure(0, weight=1)
        self._area = area

        self._build_progress(area, t)
        self._build_log(area, t)

    def _build_progress(self, parent, t):
        card = tk.Frame(parent, bg=t["CARD"], padx=16, pady=12)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        card.grid_columnconfigure(1, weight=1)
        self._prog_card = card

        # Section label
        tk.Label(card, text="Progress", fg=t["ACCENT"], bg=t["CARD"],
                 font=FONT_BOLD).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

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
            fg=t["SUBTEXT"], bg=t["CARD"], font=FONT_SM, anchor="e", width=24)
        self._overall_info_lbl.grid(row=1, column=2, sticky="e")

        # File bar
        tk.Label(card, text="File", fg=t["SUBTEXT"], bg=t["CARD"],
                 font=FONT_SM, width=7, anchor="w").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.file_var = tk.DoubleVar()
        self.file_bar = ttk.Progressbar(
            card, variable=self.file_var, maximum=100,
            style="Success.Horizontal.TProgressbar")
        self.file_bar.grid(row=2, column=1, sticky="ew", padx=(0, 10), pady=(6, 0))
        self._file_info_var = tk.StringVar(value="")
        self._file_info_lbl = tk.Label(
            card, textvariable=self._file_info_var,
            fg=t["SUCCESS"], bg=t["CARD"], font=FONT_SM, anchor="e", width=24)
        self._file_info_lbl.grid(row=2, column=2, sticky="e", pady=(6, 0))

    def _build_log(self, parent, t):
        log_outer = tk.Frame(parent, bg=t["BG"])
        log_outer.grid(row=1, column=0, sticky="nsew")
        log_outer.grid_rowconfigure(1, weight=1)
        log_outer.grid_columnconfigure(0, weight=1)
        self._log_outer = log_outer

        # Header row
        log_hdr = tk.Frame(log_outer, bg=t["BG"])
        log_hdr.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        tk.Label(log_hdr, text="Activity Log", fg=t["ACCENT"], bg=t["BG"],
                 font=FONT_BOLD).pack(side="left")
        self._clear_btn = tk.Button(
            log_hdr, text="Clear", bg=t["HDR_BTN"], fg=t["TEXT"],
            relief="flat", font=FONT_XS, cursor="hand2", bd=0, padx=8, pady=3,
            command=self._clear_log)
        self._clear_btn.pack(side="right")
        self._log_hdr = log_hdr

        border = tk.Frame(log_outer, bg=t["BORDER"], padx=1, pady=1)
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
        self.log_box.tag_config("header",  foreground=t["ACCENT"], font=FONT_BOLD)

        log_sb = ttk.Scrollbar(border, orient="vertical", command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=log_sb.set)
        self.log_box.grid(row=0, column=0, sticky="nsew")
        log_sb.grid(row=0, column=1, sticky="ns")

    def _clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")

    # ── public helpers ────────────────────────────────────────────────────────

    def log(self, msg: str, tag: str = ""):
        def _do():
            self.log_box.config(state="normal")
            self.log_box.insert("end", msg + "\n", tag if tag else ())
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        self.after(0, _do)

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
            self.start_btn.config(
                state="disabled" if running else "normal",
                bg=t["BORDER"] if running else t["ACCENT"])
            self.stop_btn.config(state="normal" if running else "disabled")
        self.after(0, _do)

    def set_solve_btn(self, active: bool, text: str = "🛡 Solve CF"):
        def _do():
            self._solve_btn.config(
                state="normal" if active else "disabled",
                text=text)
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
        self.stop_btn.configure(bg=t["DANGER"], fg="white")
        self._disk_lbl.configure(bg=t["CARD"], fg=t["SUBTEXT"])

        self._area.configure(bg=t["BG"])
        self._prog_card.configure(bg=t["CARD"])
        self._overall_info_lbl.configure(bg=t["CARD"], fg=t["SUBTEXT"])
        self._file_info_lbl.configure(bg=t["CARD"], fg=t["SUCCESS"])

        self._log_outer.configure(bg=t["BG"])
        self._log_hdr.configure(bg=t["BG"])
        self._clear_btn.configure(bg=t["HDR_BTN"], fg=t["TEXT"])
        self._log_border.configure(bg=t["BORDER"])
        self.log_box.configure(bg=t["TERMINAL"], fg=t["TERM_FG"],
                               insertbackground=t["ACCENT"])
        self.log_box.tag_config("error",   foreground=t["DANGER"])
        self.log_box.tag_config("success", foreground=t["SUCCESS"])
        self.log_box.tag_config("info",    foreground=t["SUBTEXT"])
        self.log_box.tag_config("header",  foreground=t["ACCENT"])
        # re-apply labels inside prog_card
        for child in self._prog_card.winfo_children():
            try:
                child.configure(bg=t["CARD"])
            except Exception:
                pass
