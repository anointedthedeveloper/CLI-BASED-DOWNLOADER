"""
Generate the app logo programmatically using PIL.
Returns PhotoImage objects suitable for Tkinter.
"""
import io
import math
import tkinter as tk


def _generate_logo_pil(size: int = 64, bg_color="#1a1033", accent="#a78bfa",
                        accent2="#58a6ff", text_color="#ffffff"):
    from PIL import Image, ImageDraw

    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer glow ring
    glow_margin = max(2, size // 32)
    r0 = size // 2 - glow_margin
    cx = cy = size // 2
    draw.ellipse(
        [cx - r0 - 3, cy - r0 - 3, cx + r0 + 3, cy + r0 + 3],
        fill=accent + "44"
    )

    # Main circle background
    draw.ellipse([glow_margin, glow_margin,
                  size - glow_margin, size - glow_margin],
                 fill=bg_color)

    # Inner accent ring
    ring_w = max(2, size // 20)
    r1 = r0 - ring_w
    draw.ellipse([cx - r0, cy - r0, cx + r0, cy + r0], fill=bg_color)
    # Draw ring by drawing two circles
    for i in range(ring_w):
        alpha = int(255 * (1 - i / ring_w))
        rr = r0 - i
        try:
            draw.arc([cx - rr, cy - rr, cx + rr, cy + rr],
                     0, 360, fill=accent, width=1)
        except TypeError:
            draw.ellipse([cx - rr - 1, cy - rr - 1, cx + rr + 1, cy + rr + 1],
                         outline=accent)

    # Stylised "A" shape (play triangle + crossbar = anime + play)
    # Draw a bold play triangle pointing right
    tri_r  = int(r1 * 0.62)
    tri_ox = int(cx + tri_r * 0.12)      # slight right shift to visually centre
    pts = [
        (tri_ox - int(tri_r * 0.65), cy - tri_r),
        (tri_ox - int(tri_r * 0.65), cy + tri_r),
        (tri_ox + tri_r,              cy),
    ]
    # Triangle fill
    draw.polygon(pts, fill=accent)

    # Highlight sliver on triangle
    hi_pts = [
        (tri_ox - int(tri_r * 0.65), cy - tri_r),
        (tri_ox - int(tri_r * 0.65), cy - tri_r + int(tri_r * 0.7)),
        (tri_ox + int(tri_r * 0.15), cy - int(tri_r * 0.15)),
    ]
    draw.polygon(hi_pts, fill=accent2 + "99")

    # Small dot accent top-right
    dot_r = max(2, size // 18)
    dot_x = cx + int(r1 * 0.52)
    dot_y = cy - int(r1 * 0.52)
    draw.ellipse([dot_x - dot_r, dot_y - dot_r,
                  dot_x + dot_r, dot_y + dot_r],
                 fill=accent2)

    return img


def get_logo(root: tk.Tk, size: int = 48,
             theme: dict = None) -> tk.PhotoImage:
    """Return a Tkinter PhotoImage of the logo at the given size."""
    bg      = theme.get("SIDEBAR", "#1a1033") if theme else "#1a1033"
    accent  = theme.get("ACCENT",  "#a78bfa") if theme else "#a78bfa"
    accent2 = theme.get("ACCENT_HV", "#58a6ff") if theme else "#58a6ff"
    try:
        from PIL import ImageTk
        img   = _generate_logo_pil(size, bg, accent, accent2)
        photo = ImageTk.PhotoImage(img)
        return photo
    except Exception:
        return None


def set_window_icon(window: tk.Tk, theme: dict = None):
    """Set the window titlebar/taskbar icon."""
    try:
        from PIL import ImageTk
        img   = _generate_logo_pil(256, "#1a1033",
                                   theme.get("ACCENT", "#a78bfa") if theme else "#a78bfa",
                                   theme.get("ACCENT_HV", "#58a6ff") if theme else "#58a6ff")
        photo = ImageTk.PhotoImage(img)
        window._icon_photo = photo          # keep reference
        window.iconphoto(True, photo)
    except Exception:
        pass
