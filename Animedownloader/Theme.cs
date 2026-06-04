using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace Animedownloader
{
    public static class Theme
    {
        // ── Palette ───────────────────────────────────────────────────────────
        public static readonly Color BG         = Color.FromArgb(240, 245, 255);
        public static readonly Color BGDeep      = Color.FromArgb(225, 235, 252);
        public static readonly Color Sidebar     = Color.FromArgb(13,  71,  161);
        public static readonly Color SidebarDark = Color.FromArgb(8,   48,  120);
        public static readonly Color NavSel      = Color.FromArgb(21, 101, 192);
        public static readonly Color NavHover    = Color.FromArgb(25,  90,  170);
        public static readonly Color NavText     = Color.FromArgb(187, 222, 251);
        public static readonly Color Card        = Color.White;
        public static readonly Color CardHover   = Color.FromArgb(248, 251, 255);
        public static readonly Color Panel       = Color.FromArgb(232, 242, 255);
        public static readonly Color Accent      = Color.FromArgb(25,  118, 210);
        public static readonly Color AccentLight = Color.FromArgb(66,  165, 245);
        public static readonly Color AccentHv    = Color.FromArgb(13,   71, 161);
        public static readonly Color Text        = Color.FromArgb(13,   27,  62);
        public static readonly Color SubText     = Color.FromArgb(84,  110, 162);
        public static readonly Color Border      = Color.FromArgb(187, 214, 246);
        public static readonly Color Success     = Color.FromArgb(27,  153,  85);
        public static readonly Color Danger      = Color.FromArgb(198,  40,  40);
        public static readonly Color Warning     = Color.FromArgb(230, 120,  20);
        public static readonly Color Terminal    = Color.FromArgb(10,   18,  42);
        public static readonly Color TermFg      = Color.FromArgb(187, 222, 251);
        public static readonly Color RowAlt      = Color.FromArgb(232, 242, 255);
        public static readonly Color Shadow      = Color.FromArgb(30, 25, 118, 210);

        // ── Fonts ─────────────────────────────────────────────────────────────
        public static readonly Font FontDefault = new Font("Segoe UI", 9.5f);
        public static readonly Font FontSm      = new Font("Segoe UI", 8.5f);
        public static readonly Font FontBold    = new Font("Segoe UI", 9.5f, FontStyle.Bold);
        public static readonly Font FontLg      = new Font("Segoe UI", 14f,  FontStyle.Bold);
        public static readonly Font FontXl      = new Font("Segoe UI", 20f,  FontStyle.Bold);
        public static readonly Font FontXs      = new Font("Segoe UI", 8f);
        public static readonly Font FontMono    = new Font("Consolas",  9.5f);
        public static readonly Font FontNav     = new Font("Segoe UI", 10f,  FontStyle.Bold);
        public static readonly Font FontHero    = new Font("Segoe UI", 11f);

        // ── Helpers ───────────────────────────────────────────────────────────
        public static Color Blend(Color a, Color b, float t) =>
            Color.FromArgb(
                (int)(a.R + (b.R - a.R) * t),
                (int)(a.G + (b.G - a.G) * t),
                (int)(a.B + (b.B - a.B) * t));

        public static void DrawRoundRect(Graphics g, Color color, Rectangle rect, int radius, float width = 1f)
        {
            using var pen = new Pen(color, width);
            using var path = RoundedPath(rect, radius);
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.DrawPath(pen, path);
        }

        public static void FillRoundRect(Graphics g, Color color, Rectangle rect, int radius)
        {
            using var brush = new SolidBrush(color);
            using var path  = RoundedPath(rect, radius);
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.FillPath(brush, path);
        }

        public static GraphicsPath RoundedPath(Rectangle rect, int radius)
        {
            int d = radius * 2;
            var path = new GraphicsPath();
            path.AddArc(rect.X, rect.Y, d, d, 180, 90);
            path.AddArc(rect.Right - d, rect.Y, d, d, 270, 90);
            path.AddArc(rect.Right - d, rect.Bottom - d, d, d, 0, 90);
            path.AddArc(rect.X, rect.Bottom - d, d, d, 90, 90);
            path.CloseFigure();
            return path;
        }

        public static void DrawGradientBar(Graphics g, Rectangle rect, Color from, Color to, bool vertical = false)
        {
            using var brush = new LinearGradientBrush(rect,
                from, to,
                vertical ? LinearGradientMode.Vertical : LinearGradientMode.Horizontal);
            g.FillRectangle(brush, rect);
        }
    }
}
