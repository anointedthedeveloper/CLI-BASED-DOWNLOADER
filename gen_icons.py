"""
Run once: python gen_icons.py
Generates appico.ico and logo.ico. Uses only stdlib.
"""
import struct, os, math


def _make_ico(sizes, draw_fn):
    """
    Build a valid .ico file containing one 32-bit BGRA DIB per requested size.
    sizes : list of ints, e.g. [16, 32, 48, 256]
    draw_fn(sz) -> bytes of length sz*sz*4 in top-down RGBA order
    """
    images = []
    for sz in sizes:
        rgba = draw_fn(sz)          # top-down RGBA
        images.append((sz, rgba))

    n = len(images)
    # ICO header: reserved(2) type(2) count(2)
    header = struct.pack("<HHH", 0, 1, n)

    dir_size   = n * 16            # each directory entry = 16 bytes
    data_offset = 6 + dir_size

    entries = bytearray()
    dib_blobs = []

    for (sz, rgba) in images:
        dib = _rgba_to_dib(sz, rgba)
        bmp_size = len(dib)

        w = sz if sz < 256 else 0
        h = sz if sz < 256 else 0
        entries += struct.pack("<BBBBHHII",
            w,          # width  (0 means 256)
            h,          # height (0 means 256)
            0,          # color count  (0 = truecolor)
            0,          # reserved
            1,          # color planes
            32,         # bits per pixel
            bmp_size,   # size of DIB data
            data_offset,# offset from start of file
        )
        data_offset += bmp_size
        dib_blobs.append(dib)

    return header + bytes(entries) + b"".join(dib_blobs)


def _rgba_to_dib(sz, rgba_top_down):
    """
    Convert top-down RGBA pixel data to a BITMAPINFOHEADER DIB suitable for ICO.
    ICO DIBs are bottom-up and store XOR mask (32bpp BGRA) + AND mask (1bpp).
    """
    # flip to bottom-up
    row_bytes = sz * 4
    rows = [rgba_top_down[r * row_bytes:(r + 1) * row_bytes] for r in range(sz)]
    rows_bu = list(reversed(rows))

    # convert RGBA -> BGRA
    xor_mask = bytearray(sz * sz * 4)
    for r, row in enumerate(rows_bu):
        for x in range(sz):
            src = x * 4
            dst = (r * sz + x) * 4
            xor_mask[dst + 0] = row[src + 2]   # B
            xor_mask[dst + 1] = row[src + 1]   # G
            xor_mask[dst + 2] = row[src + 0]   # R
            xor_mask[dst + 3] = row[src + 3]   # A

    # AND mask: 1-bit per pixel, row-padded to 4 bytes, all 0 (fully opaque)
    and_row_bytes = ((sz + 31) // 32) * 4
    and_mask = bytes(and_row_bytes * sz)

    xor_size = len(xor_mask)
    and_size = len(and_mask)

    # BITMAPINFOHEADER (40 bytes)
    # height is *doubled* for ICO (XOR + AND planes stacked)
    dib_header = struct.pack("<IiiHHIIiiII",
        40,            # header size
        sz,            # width
        sz * 2,        # height (doubled)
        1,             # color planes
        32,            # bits per pixel
        0,             # compression (BI_RGB)
        xor_size,      # raw bitmap size
        2835, 2835,    # pixels per meter (~72 dpi)
        0, 0,          # colors in table / important colors
    )
    return dib_header + bytes(xor_mask) + and_mask


# ── pixel drawing helpers ─────────────────────────────────────────────────────

def _new_canvas(sz):
    return bytearray(sz * sz * 4)   # RGBA, all transparent

def _px(buf, sz, x, y, r, g, b, a=255):
    if 0 <= x < sz and 0 <= y < sz:
        i = (y * sz + x) * 4
        buf[i], buf[i+1], buf[i+2], buf[i+3] = r, g, b, a

def _fill_rect(buf, sz, x0, y0, x1, y1, r, g, b, a=255):
    for y in range(max(0, y0), min(sz, y1)):
        for x in range(max(0, x0), min(sz, x1)):
            _px(buf, sz, x, y, r, g, b, a)

def _fill_circle(buf, sz, cx, cy, radius, r, g, b, a=255):
    r2 = radius * radius
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                _px(buf, sz, x, y, r, g, b, a)

def _fill_rounded_rect(buf, sz, x0, y0, x1, y1, corner, r, g, b, a=255):
    # fill body
    _fill_rect(buf, sz, x0 + corner, y0, x1 - corner, y1, r, g, b, a)
    _fill_rect(buf, sz, x0, y0 + corner, x1, y1 - corner, r, g, b, a)
    # four corner circles
    for cx, cy in ((x0+corner, y0+corner), (x1-corner-1, y0+corner),
                   (x0+corner, y1-corner-1), (x1-corner-1, y1-corner-1)):
        _fill_circle(buf, sz, cx, cy, corner, r, g, b, a)


# ── icon designs ──────────────────────────────────────────────────────────────

def _draw_appico(sz):
    """Modern blue gradient rounded square with a white play triangle."""
    buf = _new_canvas(sz)
    m   = max(1, sz // 8)
    cr  = max(1, sz // 4)

    # gradient blue background (lighter at top, darker at bottom)
    for y in range(m, sz - m):
        t = (y - m) / (sz - 2 * m) if sz > 2 * m else 0
        r = int(59 + t * (37 - 59))
        g = int(130 + t * (99 - 130))
        b = int(246 + t * (235 - 246))
        for x in range(m, sz - m):
            # check if within rounded corners
            if (x - m) < cr or (x - (sz - m - 1)) < cr:
                if (y - m) < cr or (y - (sz - m - 1)) < cr:
                    # corner area - skip for rounded effect
                    continue
            _px(buf, sz, x, y, r, g, b)

    # fill rounded corners properly
    _fill_rounded_rect(buf, sz, m, m, sz - m, sz - m, cr, 59, 130, 246)

    # add subtle shadow effect
    shadow_offset = max(1, sz // 16)
    for y in range(m + shadow_offset, sz - m):
        for x in range(m + shadow_offset, sz - m):
            if (x - m) < cr or (x - (sz - m - 1)) < cr:
                if (y - m) < cr or (y - (sz - m - 1)) < cr:
                    continue
            # darken slightly for shadow
            _px(buf, sz, x, y, 59, 130, 246)

    # white play triangle (pointing right) - more refined
    cx, cy  = sz // 2, sz // 2
    half_h  = sz // 4
    tip_x   = cx + sz // 6
    left_x  = cx - sz // 8

    for row in range(-half_h, half_h + 1):
        t = abs(row) / half_h if half_h else 1
        right = int(tip_x - t * (tip_x - left_x))
        for x in range(left_x, right + 1):
            _px(buf, sz, x, cy + row, 255, 255, 255)

    return bytes(buf)


def _draw_logo(sz):
    """Modern gradient blue circle with a white stylised 'A'."""
    buf = _new_canvas(sz)
    pad = max(1, sz // 10)
    r   = sz // 2 - pad
    cx, cy = sz // 2, sz // 2

    # gradient blue circle
    for y in range(cy - r, cy + r):
        for x in range(cx - r, cx + r):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dist <= r:
                # gradient from top-left to bottom-right
                t = ((x - (cx - r)) + (y - (cy - r))) / (2 * r) if r > 0 else 0
                t = max(0, min(1, t))
                red = int(59 + t * (37 - 59))
                green = int(130 + t * (99 - 130))
                blue = int(246 + t * (235 - 246))
                _px(buf, sz, x, y, red, green, blue)

    # white 'A' — more refined design
    lw  = max(2, sz // 12)
    top = (cx, cy - r * 2 // 3)   # apex (x, y)
    bl  = (cx - r * 3 // 5, cy + r * 2 // 3)   # bottom-left
    br  = (cx + r * 3 // 5, cy + r * 2 // 3)   # bottom-right

    def _line(buf, sz, p0, p1, lw, r, g, b):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        steps  = max(abs(dx), abs(dy), 1)
        for i in range(steps + 1):
            t  = i / steps
            x  = int(p0[0] + dx * t)
            y  = int(p0[1] + dy * t)
            for ox in range(-lw, lw + 1):
                for oy in range(-lw, lw + 1):
                    if ox * ox + oy * oy <= lw * lw:
                        _px(buf, sz, x + ox, y + oy, r, g, b)

    _line(buf, sz, bl,  top, lw, 255, 255, 255)
    _line(buf, sz, br,  top, lw, 255, 255, 255)

    # crossbar at ~50% of the way up
    cross_y = bl[1] - int((bl[1] - top[1]) * 0.5)
    t_left  = 0.4
    cx_l    = int(bl[0] + (top[0] - bl[0]) * t_left)
    cx_r    = int(br[0] + (top[0] - br[0]) * t_left)
    _line(buf, sz, (cx_l, cross_y), (cx_r, cross_y), lw, 255, 255, 255)

    return bytes(buf)


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    base   = os.path.dirname(os.path.abspath(__file__))
    sizes  = [16, 32, 48, 256]

    for name, fn in (("appico.ico", _draw_appico), ("logo.ico", _draw_logo)):
        path = os.path.join(base, name)
        data = _make_ico(sizes, fn)
        with open(path, "wb") as f:
            f.write(data)
        print(f"Created {path}  ({len(data):,} bytes)")
