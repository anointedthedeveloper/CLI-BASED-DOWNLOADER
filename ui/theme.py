import re

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
    "SIDEBAR":   "#e2e8f0",
    "NAV_SEL":   "#ede9fe",
    "NAV_TEXT":  "#1e293b",
    "WARN":      "#d97706",
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
    "SIDEBAR":   "#010409",
    "NAV_SEL":   "#1f2d3d",
    "NAV_TEXT":  "#e6edf3",
    "WARN":      "#e3b341",
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
    "SIDEBAR":   "#110b24",
    "NAV_SEL":   "#2d1f5e",
    "NAV_TEXT":  "#ede9fe",
    "WARN":      "#fbbf24",
}

FONT      = ("Segoe UI", 10)
FONT_SM   = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_MONO = ("Consolas", 9)
FONT_LG   = ("Segoe UI", 13, "bold")
FONT_XL   = ("Segoe UI", 15, "bold")
FONT_XS   = ("Segoe UI", 8)
FONT_NAV  = ("Segoe UI", 10, "bold")


def fmt_size(b: float) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"


def fmt_time(s: float) -> str:
    s = int(s)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def sanitize_dir(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.rstrip(" .")
    return name or "_unnamed"


def parse_range(ep_str: str, total: int) -> tuple:
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


def shorten_path(p: str, max_len: int = 42) -> str:
    if len(p) <= max_len:
        return p
    parts = p.replace("\\", "/").split("/")
    if len(parts) >= 3:
        return f"{parts[0]}/…/{parts[-1]}"
    return "…" + p[-(max_len - 1):]
