using System.ComponentModel;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace Animedownloader
{
    // ── Rounded card panel ────────────────────────────────────────────────────
    public class CardPanel : Panel
    {
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public int  CornerRadius { get; set; } = 12;
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public bool ShowShadow   { get; set; } = true;

        public CardPanel()
        {
            BackColor   = Theme.Card;
            DoubleBuffered = true;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            var g    = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            var rect = new Rectangle(2, 2, Width - 5, Height - 5);

            if (ShowShadow)
            {
                for (int i = 3; i >= 1; i--)
                {
                    var sr = new Rectangle(rect.X + i, rect.Y + i, rect.Width, rect.Height);
                    Theme.FillRoundRect(g, Color.FromArgb(18 * i, 25, 118, 210), sr, CornerRadius);
                }
            }
            Theme.FillRoundRect(g, BackColor, rect, CornerRadius);
            Theme.DrawRoundRect(g, Theme.Border, rect, CornerRadius, 1.2f);
        }

        protected override void OnResize(EventArgs e) { base.OnResize(e); Invalidate(); }
    }

    // ── Accent button with hover/press animation ───────────────────────────
    public class AccentButton : Button
    {
        private float _hoverAlpha;
        private System.Windows.Forms.Timer? _hoverTimer;
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public  Color BaseColor   { get; set; } = Theme.Accent;
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public  Color HoverColor  { get; set; } = Theme.AccentHv;
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public  int   CornerRadius{ get; set; } = 8;

        public AccentButton()
        {
            FlatStyle  = FlatStyle.Flat;
            FlatAppearance.BorderSize = 0;
            BackColor  = Color.Transparent;
            ForeColor  = Color.White;
            Font       = Theme.FontBold;
            Height     = 36;
            Cursor     = Cursors.Hand;
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer, true);
        }

        protected override void OnMouseEnter(EventArgs e)
        {
            base.OnMouseEnter(e); StartTimer(true);
        }
        protected override void OnMouseLeave(EventArgs e)
        {
            base.OnMouseLeave(e); StartTimer(false);
        }

        private void StartTimer(bool enter)
        {
            _hoverTimer?.Stop(); _hoverTimer?.Dispose();
            _hoverTimer = new System.Windows.Forms.Timer { Interval = 16 };
            _hoverTimer.Tick += (s, e) =>
            {
                _hoverAlpha = enter
                    ? Math.Min(1f, _hoverAlpha + 0.12f)
                    : Math.Max(0f, _hoverAlpha - 0.12f);
                Invalidate();
                if ((_hoverAlpha >= 1f && enter) || (_hoverAlpha <= 0f && !enter))
                    _hoverTimer?.Stop();
            };
            _hoverTimer.Start();
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            var g    = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            var rect = new Rectangle(1, 1, Width - 3, Height - 3);

            var col = Enabled
                ? Theme.Blend(BaseColor, HoverColor, _hoverAlpha)
                : Theme.BGDeep;

            Theme.FillRoundRect(g, col, rect, CornerRadius);

            // subtle gradient sheen
            using var sheen = new LinearGradientBrush(rect,
                Color.FromArgb(40, Color.White), Color.Transparent, LinearGradientMode.Vertical);
            using var sheenPath = Theme.RoundedPath(rect, CornerRadius);
            g.FillPath(sheen, sheenPath);

            var tf = new StringFormat { Alignment = StringAlignment.Center, LineAlignment = StringAlignment.Center };
            using var brush = new SolidBrush(Enabled ? ForeColor : Theme.SubText);
            g.DrawString(Text, Font, brush, new RectangleF(0, 0, Width, Height), tf);
        }
    }

    // ── Ghost (outline) button ─────────────────────────────────────────────
    public class GhostButton : AccentButton
    {
        public GhostButton()
        {
            BaseColor  = Color.Transparent;
            HoverColor = Color.FromArgb(30, 25, 118, 210);
            ForeColor  = Theme.Accent;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            var g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            var rect = new Rectangle(1, 1, Width - 3, Height - 3);
            Theme.FillRoundRect(g, Theme.Blend(Color.Transparent, HoverColor, _hoverAlpha > 0 ? _hoverAlpha : 0f), rect, CornerRadius);
            Theme.DrawRoundRect(g, Theme.Accent, rect, CornerRadius, 1.5f);
            var tf = new StringFormat { Alignment = StringAlignment.Center, LineAlignment = StringAlignment.Center };
            using var brush = new SolidBrush(ForeColor);
            g.DrawString(Text, Font, brush, new RectangleF(0, 0, Width, Height), tf);
        }

        // expose _hoverAlpha for subclass paint
        protected float _hoverAlpha;
        protected new void StartTimer(bool enter)
        {
            var t = new System.Windows.Forms.Timer { Interval = 16 };
            t.Tick += (s, e) =>
            {
                _hoverAlpha = enter ? Math.Min(1f, _hoverAlpha + 0.12f) : Math.Max(0f, _hoverAlpha - 0.12f);
                Invalidate();
                if ((_hoverAlpha >= 1 && enter) || (_hoverAlpha <= 0 && !enter)) t.Stop();
            };
            t.Start();
        }
    }

    // ── Spinning loader ────────────────────────────────────────────────────
    public class SpinnerControl : Control
    {
        private int   _angle;
        private System.Windows.Forms.Timer? _timer;
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public  Color SpinColor { get; set; } = Theme.Accent;
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public  int   Thickness { get; set; } = 4;

        public SpinnerControl()
        {
            Size = new Size(32, 32);
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.SupportsTransparentBackColor, true);
            BackColor = Color.Transparent;
        }

        public void Start()
        {
            _timer = new System.Windows.Forms.Timer { Interval = 16 };
            _timer.Tick += (s, e) => { _angle = (_angle + 8) % 360; Invalidate(); };
            _timer.Start();
            Visible = true;
        }

        public void Stop() { _timer?.Stop(); _timer?.Dispose(); _timer = null; Visible = false; }

        protected override void OnPaint(PaintEventArgs e)
        {
            var g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            int pad = Thickness + 2;
            var rect = new Rectangle(pad, pad, Width - pad * 2, Height - pad * 2);
            using var bgPen = new Pen(Color.FromArgb(50, SpinColor), Thickness);
            g.DrawEllipse(bgPen, rect);
            using var pen = new Pen(SpinColor, Thickness) { StartCap = LineCap.Round, EndCap = LineCap.Round };
            g.DrawArc(pen, rect, _angle, 260);
        }
    }

    // ── Animated progress bar ──────────────────────────────────────────────
    public class SmoothProgressBar : Control
    {
        private float _current;
        private float _target;
        private System.Windows.Forms.Timer? _anim;
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public  Color BarColor   { get; set; } = Theme.Accent;
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public  Color TrackColor { get; set; } = Theme.Panel;
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public  int   CornerRadius{ get; set; } = 6;
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public  int   Maximum    { get; set; } = 100;

        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public int Value
        {
            set
            {
                _target = Math.Clamp(value, 0, Maximum);
                _anim?.Stop(); _anim?.Dispose();
                _anim = new System.Windows.Forms.Timer { Interval = 16 };
                _anim.Tick += (s, e) =>
                {
                    _current += (_target - _current) * 0.18f;
                    if (Math.Abs(_target - _current) < 0.3f) { _current = _target; _anim?.Stop(); }
                    Invalidate();
                };
                _anim.Start();
            }
        }

        public SmoothProgressBar()
        {
            Height = 10;
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer, true);
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            var g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            var track = new Rectangle(0, 0, Width, Height);
            Theme.FillRoundRect(g, TrackColor, track, CornerRadius);

            int fillW = (int)(Width * _current / Maximum);
            if (fillW > CornerRadius * 2)
            {
                var fill = new Rectangle(0, 0, fillW, Height);
                using var grad = new LinearGradientBrush(fill, Theme.AccentLight, BarColor, LinearGradientMode.Horizontal);
                using var path = Theme.RoundedPath(fill, CornerRadius);
                g.FillPath(grad, path);
            }
        }
    }

    // ── Hover-glow nav button ──────────────────────────────────────────────
    public class NavButton : Button
    {
        private float _alpha;
        private bool  _active;
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public  bool  Active { get => _active; set { _active = value; Invalidate(); } }
        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public  string Icon  { get; set; } = "";

        public NavButton()
        {
            FlatStyle  = FlatStyle.Flat;
            FlatAppearance.BorderSize = 0;
            BackColor  = Color.Transparent;
            ForeColor  = Theme.NavText;
            Font       = Theme.FontNav;
            Height     = 46;
            Cursor     = Cursors.Hand;
            TextAlign  = ContentAlignment.MiddleLeft;
            Padding    = new Padding(16, 0, 0, 0);
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.SupportsTransparentBackColor, true);
        }

        protected override void OnMouseEnter(EventArgs e) { base.OnMouseEnter(e); Animate(true); }
        protected override void OnMouseLeave(EventArgs e) { base.OnMouseLeave(e); Animate(false); }

        private void Animate(bool enter)
        {
            var t = new System.Windows.Forms.Timer { Interval = 16 };
            t.Tick += (s, e) =>
            {
                _alpha = enter ? Math.Min(1f, _alpha + 0.15f) : Math.Max(0f, _alpha - 0.15f);
                Invalidate();
                if ((_alpha >= 1 && enter) || (_alpha <= 0 && !enter)) t.Stop();
            };
            t.Start();
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            var g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;

            if (_active)
            {
                var ar = new Rectangle(4, 4, Width - 8, Height - 8);
                Theme.FillRoundRect(g, Theme.NavSel, ar, 8);
                // left accent bar
                using var bar = new SolidBrush(Theme.AccentLight);
                g.FillRectangle(bar, new Rectangle(4, 10, 3, Height - 20));
            }
            else if (_alpha > 0)
            {
                var hr = new Rectangle(4, 4, Width - 8, Height - 8);
                Theme.FillRoundRect(g, Color.FromArgb((int)(40 * _alpha), Color.White), hr, 8);
            }

            using var brush = new SolidBrush(_active ? Color.White : Color.FromArgb((int)(187 + 68 * _alpha), 222, 251));
            var tf = new StringFormat { LineAlignment = StringAlignment.Center };
            g.DrawString(Text, Font, brush, new RectangleF(Padding.Left, 0, Width - Padding.Left, Height), tf);
        }
    }

    // ── Fade-transition overlay ────────────────────────────────────────────
    public class FadeOverlay : Panel
    {
        private int   _alpha;
        private bool  _fadeIn;
        private System.Windows.Forms.Timer? _timer;
        public  event Action? FadeOutDone;

        public FadeOverlay()
        {
            BackColor = Theme.BG;
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.SupportsTransparentBackColor, true);
        }

        public void DoTransition(Action midpoint)
        {
            _alpha = 0; _fadeIn = true; Visible = true; BringToFront();
            _timer?.Stop(); _timer?.Dispose();
            _timer = new System.Windows.Forms.Timer { Interval = 16 };
            _timer.Tick += (s, e) =>
            {
                if (_fadeIn)
                {
                    _alpha = Math.Min(220, _alpha + 40);
                    Invalidate();
                    if (_alpha >= 220) { _fadeIn = false; midpoint(); }
                }
                else
                {
                    _alpha = Math.Max(0, _alpha - 40);
                    Invalidate();
                    if (_alpha <= 0) { Visible = false; _timer?.Stop(); FadeOutDone?.Invoke(); }
                }
            };
            _timer.Start();
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            using var b = new SolidBrush(Color.FromArgb(_alpha, Theme.BG));
            e.Graphics.FillRectangle(b, ClientRectangle);
        }
    }
}
