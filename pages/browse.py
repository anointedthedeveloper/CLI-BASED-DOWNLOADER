import threading
import tkinter as tk
from tkinter import ttk

import animepahe
import session as _sess
from ui.theme import (FONT, FONT_SM, FONT_BOLD, FONT_LG, FONT_XS,
                      parse_range)


class BrowsePage(tk.Frame):
    def __init__(self, parent, app):
        self.app = app
        t = app.t
        super().__init__(parent, bg=t["BG"])
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build(t)

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

        self._poster_lbl = tk.Label(
            hdr, text="No\nPoster", bg=t["BORDER"], fg=t["SUBTEXT"],
            font=FONT_XS, width=10, height=5, relief="flat")
        self._poster_lbl.grid(row=0, column=0, rowspan=2, padx=(0, 14))

        name_frame = tk.Frame(hdr, bg=t["CARD"])
        name_frame.grid(row=0, column=1, sticky="ew")
        name_frame.grid_columnconfigure(0, weight=1)

        self._title_lbl = tk.Label(
            name_frame, text="AnimePahe Downloader v2.0",
            bg=t["CARD"], fg=t["TEXT"], font=FONT_LG, anchor="w")
        self._title_lbl.grid(row=0, column=0, sticky="w")

        self._meta_lbl = tk.Label(
            name_frame, text="Paste a URL and click Fetch to load episodes.",
            bg=t["CARD"], fg=t["SUBTEXT"], font=FONT_SM, anchor="w")
        self._meta_lbl.grid(row=1, column=0, sticky="w")

    def _update_anime_header(self, title: str, meta_str: str, poster_url: str):
        self._title_lbl.config(text=title)
        self._meta_lbl.config(text=meta_str if meta_str else "")
        if poster_url:
            threading.Thread(
                target=self._load_poster, args=(poster_url,), daemon=True
            ).start()

    def _load_poster(self, url: str):
        try:
            from PIL import Image, ImageTk
            import io
            resp = _sess.request("GET", url, headers={"Referer": "https://animepahe.pw"})
            data = resp.content
            if not data:
                raise ValueError("empty")
            img = Image.open(io.BytesIO(data))
            img = img.resize((72, 100), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._poster_photo = photo
            self.after(0, lambda: self._poster_lbl.config(
                image=photo, text="", width=72, height=100, relief="flat"))
        except Exception:
            pass

    # ── URL card ──────────────────────────────────────────────────────────────

    def _build_url_card(self, t):
        card = tk.Frame(self, bg=t["CARD"], padx=16, pady=12)
        card.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))
        card.grid_columnconfigure(1, weight=1)
        self._url_card = card

        # Row 0: URL label + entry + range + buttons
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

        # Row 1: status
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

    def set_url_status(self, msg: str, color: str):
        self._url_status_var.set(msg)
        self._url_status_lbl.config(fg=color)

    def set_fetching(self, active: bool):
        if active:
            self._fetch_btn.config(state="disabled", text="⏳ Fetching…")
            self._stop_fetch_btn.config(state="normal")
        else:
            self._fetch_btn.config(state="normal", text="🔄 Fetch")
            self._stop_fetch_btn.config(state="disabled")

    def _ph_clear(self, event):
        if self._url_entry.get() == "Paste AnimePahe series or episode URL…":
            self._url_entry.delete(0, "end")
            self._url_entry.config(fg=self.app.t["TEXT"])

    def _ph_restore(self, event):
        if not self._url_entry.get():
            self._url_entry.insert(0, "Paste AnimePahe series or episode URL…")
            self._url_entry.config(fg=self.app.t["SUBTEXT"])

    # ── episode section ───────────────────────────────────────────────────────

    def _build_episode_section(self, t):
        outer = tk.Frame(self, bg=t["BG"])
        outer.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 14))
        outer.grid_rowconfigure(1, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        self._ep_outer = outer

        # Controls bar
        ctrl = tk.Frame(outer, bg=t["CARD"], padx=14, pady=8)
        ctrl.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ctrl.grid_columnconfigure(3, weight=1)
        self._ep_ctrl = ctrl

        tk.Label(ctrl, text="Episodes", fg=t["SUBTEXT"], bg=t["CARD"],
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
        list_border = tk.Frame(outer, bg=t["BORDER"], padx=1, pady=1)
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
        self._ep_win = self._ep_canvas.create_window((0, 0), window=self._ep_inner, anchor="nw")

        self._ep_inner.bind("<Configure>", self._on_inner_cfg)
        self._ep_canvas.bind("<Configure>", self._on_canvas_cfg)
        self._ep_canvas.bind("<MouseWheel>", self._on_scroll)
        self._ep_canvas.bind("<Button-4>", lambda e: self._ep_canvas.yview_scroll(-1, "units"))
        self._ep_canvas.bind("<Button-5>", lambda e: self._ep_canvas.yview_scroll(1, "units"))

        self._ep_canvas.grid(row=0, column=0, sticky="nsew")
        self._ep_sb.grid(row=0, column=1, sticky="ns")

        self._ep_placeholder = tk.Label(
            self._ep_inner,
            text="📺  Paste an AnimePahe URL above and click  🔄 Fetch  to load episodes.",
            fg=t["SUBTEXT"], bg=t["LIST_BG"], font=FONT_SM)
        self._ep_placeholder.grid(row=0, column=0, padx=24, pady=24)

    def _on_inner_cfg(self, event):
        self._ep_canvas.configure(scrollregion=self._ep_canvas.bbox("all"))

    def _on_canvas_cfg(self, event):
        self._ep_canvas.itemconfig(self._ep_win, width=event.width)

    def _on_scroll(self, event):
        self._ep_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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

    # ── episode list population ───────────────────────────────────────────────

    def populate_episodes(self, raw_episodes: list, title: str, series_id: str):
        t = self.app.t
        self.app.series_title = title
        self.app.series_id    = series_id
        self.app.episode_data = raw_episodes
        self.app.thumb_images = {}

        for w in self._ep_inner.winfo_children():
            w.destroy()
        self.app.episode_vars.clear()

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
        self._ep_count_lbl = tk.Label(sel_row, text=f"{len(raw_episodes)} episodes",
                                      bg=t["CARD"], fg=t["SUBTEXT"], font=FONT_XS)
        self._ep_count_lbl.pack(side="left")

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

            row.bind("<Enter>",  lambda e, f=row: f.config(highlightbackground=t["ACCENT"]))
            row.bind("<Leave>",  lambda e, f=row, bg=row_bg: f.config(highlightbackground=bg))

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
                audio_col, audio_txt = t["ACCENT"], "JPN"
            elif "eng" in audio_norm or audio_norm == "en":
                audio_col, audio_txt = t["SUCCESS"], "ENG"
            else:
                audio_col, audio_txt = t["WARN"] if "WARN" in t else t["SUBTEXT"], audio.upper()[:3]
            tk.Label(row, text=audio_txt, fg="white", bg=audio_col,
                     font=FONT_XS, padx=6, pady=2, width=4).grid(
                row=0, column=3, padx=(0, 6), pady=5)

            tag_txt = "Filler" if filler else ""
            tag_col = "#f97316" if filler else row_bg
            tag_fg  = "white"   if filler else row_bg
            tk.Label(row, text=tag_txt, fg=tag_fg, bg=tag_col,
                     font=FONT_XS, padx=4, pady=2, width=5).grid(
                row=0, column=4, padx=(0, 8), pady=5)

            if snap_url:
                threading.Thread(
                    target=self._load_thumbnail,
                    args=(snap_url, thumb_lbl, i, row_bg),
                    daemon=True
                ).start()

        self._ep_canvas.yview_moveto(0)

    def _load_thumbnail(self, url: str, label: tk.Label, index: int, row_bg: str):
        try:
            from PIL import Image, ImageTk
            import io
            resp = _sess.request("GET", url, headers={"Referer": "https://animepahe.pw"})
            data = resp.content
            if not data:
                raise ValueError("empty")
            img   = Image.open(io.BytesIO(data))
            img   = img.resize((88, 50), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.app.thumb_images[index] = photo

            def _apply(lbl=label, ph=photo):
                lbl.config(image=ph, text="", width=88, height=50)
                lbl.image = ph

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
        self._poster_lbl.configure(bg=t["BORDER"], fg=t["SUBTEXT"])
        self._title_lbl.configure(bg=t["CARD"], fg=t["TEXT"])
        self._meta_lbl.configure(bg=t["CARD"], fg=t["SUBTEXT"])

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
        self._last5_chk.configure(bg=t["CARD"], fg=t["TEXT"], selectcolor=t["CHK_BG"])
        self._filter_entry.configure(bg=t["PANEL"], fg=t["TEXT"],
                                     insertbackground=t["ACCENT"],
                                     highlightbackground=t["BORDER"])
        self._list_border.configure(bg=t["BORDER"])
        self._list_bg.configure(bg=t["LIST_BG"])
        self._ep_canvas.configure(bg=t["LIST_BG"])
        self._ep_inner.configure(bg=t["LIST_BG"])
        for child in self._ep_inner.winfo_children():
            try:
                child.configure(bg=t["LIST_BG"])
            except Exception:
                pass
