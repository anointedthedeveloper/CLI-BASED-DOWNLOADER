"""
Log / Activity page — full scrollable log with filters and export.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime

from ui.theme import FONT, FONT_SM, FONT_BOLD, FONT_MONO, FONT_XS, FONT_LG
from ui.widgets import Spinner


class LogPage(tk.Frame):
    def __init__(self, parent, app):
        self.app = app
        t = app.t
        super().__init__(parent, bg=t["BG"])
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._entries = []   # list of (tag, text) tuples — full history
        self._build(t)

    def _build(self, t):
        self._build_header(t)
        self._build_log_area(t)

    # ── header ────────────────────────────────────────────────────────────────

    def _build_header(self, t):
        hdr = tk.Frame(self, bg=t["CARD"], padx=18, pady=12)
        hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        hdr.grid_columnconfigure(2, weight=1)
        self._hdr = hdr

        tk.Label(hdr, text="Activity Log", font=FONT_LG,
                 bg=t["CARD"], fg=t["TEXT"]).grid(row=0, column=0, sticky="w")

        tk.Label(hdr, text="Full history of fetches, downloads and errors.",
                 bg=t["CARD"], fg=t["SUBTEXT"], font=FONT_SM).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(2, 0))

        # Filter buttons
        btn_row = tk.Frame(hdr, bg=t["CARD"])
        btn_row.grid(row=0, column=3, sticky="e")
        self._btn_row = btn_row

        self._filter_var = tk.StringVar(value="all")
        filters = [("All", "all"), ("✓ Success", "success"),
                   ("✗ Errors", "error"), ("ℹ Info", "info")]
        self._filter_btns = {}
        for label, val in filters:
            b = tk.Button(btn_row, text=label,
                          bg=t["HDR_BTN"], fg=t["TEXT"],
                          activebackground=t["ACCENT"], activeforeground="white",
                          relief="flat", font=FONT_XS, cursor="hand2",
                          bd=0, padx=10, pady=5,
                          command=lambda v=val: self._set_filter(v))
            b.pack(side="left", padx=(0, 4))
            self._filter_btns[val] = b

        # Export + Clear
        tk.Frame(btn_row, bg=t["CARD"], width=12).pack(side="left")
        self._export_btn = tk.Button(btn_row, text="💾 Export",
                                     bg=t["HDR_BTN"], fg=t["TEXT"],
                                     activebackground=t["SUCCESS"],
                                     activeforeground="white",
                                     relief="flat", font=FONT_XS,
                                     cursor="hand2", bd=0, padx=10, pady=5,
                                     command=self._export)
        self._export_btn.pack(side="left", padx=(0, 4))

        self._clear_btn = tk.Button(btn_row, text="🗑 Clear",
                                    bg=t["HDR_BTN"], fg=t["TEXT"],
                                    activebackground=t["DANGER"],
                                    activeforeground="white",
                                    relief="flat", font=FONT_XS,
                                    cursor="hand2", bd=0, padx=10, pady=5,
                                    command=self._clear)
        self._clear_btn.pack(side="left")

        # Stats row
        stats_frame = tk.Frame(hdr, bg=t["CARD"])
        stats_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        self._stats_frame = stats_frame

        self._stat_vars = {}
        for key, label, color_key in [
            ("total",   "Total",    "SUBTEXT"),
            ("success", "Success",  "SUCCESS"),
            ("error",   "Errors",   "DANGER"),
            ("info",    "Info",     "ACCENT"),
        ]:
            v = tk.StringVar(value="0")
            self._stat_vars[key] = v
            cell = tk.Frame(stats_frame, bg=t["CARD"], padx=10, pady=4)
            cell.pack(side="left", padx=(0, 6))
            tk.Label(cell, textvariable=v, bg=t["CARD"],
                     fg=t[color_key], font=FONT_BOLD).pack()
            tk.Label(cell, text=label, bg=t["CARD"],
                     fg=t["SUBTEXT"], font=FONT_XS).pack()

    # ── log area ──────────────────────────────────────────────────────────────

    def _build_log_area(self, t):
        outer = tk.Frame(self, bg=t["BG"])
        outer.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        self._log_outer = outer

        border = tk.Frame(outer, bg=t["BORDER"], padx=1, pady=1)
        border.grid(row=0, column=0, sticky="nsew")
        border.grid_rowconfigure(0, weight=1)
        border.grid_columnconfigure(0, weight=1)
        self._log_border = border

        self.log_box = tk.Text(
            border, bg=t["TERMINAL"], fg=t["TERM_FG"],
            insertbackground=t["ACCENT"],
            font=FONT_MONO, relief="flat",
            state="disabled", wrap="word", padx=14, pady=12)

        self.log_box.tag_config("error",     foreground=t["DANGER"])
        self.log_box.tag_config("success",   foreground=t["SUCCESS"])
        self.log_box.tag_config("info",      foreground=t["SUBTEXT"])
        self.log_box.tag_config("header",    foreground=t["ACCENT"], font=FONT_BOLD)
        self.log_box.tag_config("timestamp", foreground=t["BORDER"])
        self.log_box.tag_config("warn",      foreground=t.get("WARN", t["SUBTEXT"]))

        sb = ttk.Scrollbar(border, orient="vertical", command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=sb.set)
        self.log_box.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

        self._active_filter = "all"
        self._update_filter_btns()

    # ── public API ────────────────────────────────────────────────────────────

    def append(self, msg: str, tag: str = ""):
        """Add a log entry and display it if it passes the current filter."""
        ts = datetime.now().strftime("%H:%M:%S")
        self._entries.append((tag, ts, msg))
        self._update_stats()
        if self._passes_filter(tag):
            self._write(ts, msg, tag)

    def _write(self, ts: str, msg: str, tag: str):
        def _do():
            self.log_box.config(state="normal")
            self.log_box.insert("end", f"[{ts}]  ", "timestamp")
            self.log_box.insert("end", msg + "\n", tag if tag else ())
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        self.after(0, _do)

    def _passes_filter(self, tag: str) -> bool:
        f = self._active_filter
        if f == "all":
            return True
        return tag == f

    def _set_filter(self, val: str):
        self._active_filter = val
        self._update_filter_btns()
        self._redraw_filtered()

    def _update_filter_btns(self):
        t = self.app.t
        for key, btn in self._filter_btns.items():
            if key == self._active_filter:
                btn.configure(bg=t["ACCENT"], fg="white")
            else:
                btn.configure(bg=t["HDR_BTN"], fg=t["TEXT"])

    def _redraw_filtered(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        for tag, ts, msg in self._entries:
            if self._passes_filter(tag):
                self.log_box.insert("end", f"[{ts}]  ", "timestamp")
                self.log_box.insert("end", msg + "\n", tag if tag else ())
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _update_stats(self):
        counts = {"total": len(self._entries), "success": 0, "error": 0, "info": 0}
        for tag, _, _ in self._entries:
            if tag in counts:
                counts[tag] += 1
        for key, v in self._stat_vars.items():
            v.set(str(counts.get(key, 0)))

    def _clear(self):
        self._entries.clear()
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")
        self._update_stats()

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")],
            initialfile=f"animepahe_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                for tag, ts, msg in self._entries:
                    f.write(f"[{ts}] [{tag.upper():7s}] {msg}\n")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Export Failed", str(e))

    # ── theme ─────────────────────────────────────────────────────────────────

    def apply_theme(self):
        t = self.app.t
        self.configure(bg=t["BG"])
        self._hdr.configure(bg=t["CARD"])
        self._btn_row.configure(bg=t["CARD"])
        self._stats_frame.configure(bg=t["CARD"])
        for child in self._stats_frame.winfo_children():
            child.configure(bg=t["CARD"])
            for sub in child.winfo_children():
                try:
                    sub.configure(bg=t["CARD"])
                except Exception:
                    pass
        self._log_outer.configure(bg=t["BG"])
        self._log_border.configure(bg=t["BORDER"])
        self.log_box.configure(bg=t["TERMINAL"], fg=t["TERM_FG"],
                               insertbackground=t["ACCENT"])
        self.log_box.tag_config("error",     foreground=t["DANGER"])
        self.log_box.tag_config("success",   foreground=t["SUCCESS"])
        self.log_box.tag_config("info",      foreground=t["SUBTEXT"])
        self.log_box.tag_config("header",    foreground=t["ACCENT"])
        self.log_box.tag_config("timestamp", foreground=t["BORDER"])
        self._update_filter_btns()
        for btn in (self._export_btn, self._clear_btn):
            btn.configure(bg=t["HDR_BTN"], fg=t["TEXT"])
