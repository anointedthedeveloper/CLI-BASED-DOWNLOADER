using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace Animedownloader
{
    public class MainForm : Form
    {
        private readonly AppState _state = new();
        private BrowsePage    _browsePage    = null!;
        private DownloadsPage _downloadsPage = null!;
        private LogPage       _logPage       = null!;
        private SettingsPage  _settingsPage  = null!;
        private Panel         _pageHost      = null!;
        private Panel         _sidebar       = null!;
        private Panel         _sidebarInner  = null!;
        private FadeOverlay   _overlay       = null!;
        private Button        _toggleBtn     = null!;
        private readonly Dictionary<string, NavButton> _navBtns = new();
        private string        _currentPage   = "";
        private bool          _sidebarOpen   = true;
        private System.Windows.Forms.Timer? _slideTimer;
        private const int SIDEBAR_OPEN  = 220;
        private const int SIDEBAR_CLOSE = 58;

        public MainForm()
        {
            Text          = "AnimePahe Downloader";
            MinimumSize   = new Size(960, 640);
            Size          = new Size(1280, 800);
            BackColor     = Theme.BG;
            StartPosition = FormStartPosition.CenterScreen;
            WindowState   = FormWindowState.Maximized;
            Font          = Theme.FontDefault;
            DoubleBuffered = true;

            BuildLayout();
            ShowPage("browse");
        }

        private void BuildLayout()
        {
            // ── sidebar ───────────────────────────────────────────────────
            _sidebar = new Panel
            {
                Dock = DockStyle.Left, Width = SIDEBAR_OPEN,
                BackColor = Theme.Sidebar
            };
            _sidebar.Paint += DrawSidebarGradient;

            _sidebarInner = new Panel { Dock = DockStyle.Fill, BackColor = Color.Transparent };

            // logo
            var logoPanel = new Panel { Dock = DockStyle.Top, Height = 88, BackColor = Color.Transparent };
            logoPanel.Paint += (s, e) => { };
            var logoIcon = MakeSideLabel("🎌", new Font("Segoe UI", 26), Color.White, 0, 8,  220, ContentAlignment.MiddleCenter);
            var logoName = MakeSideLabel("AnimePahe",       new Font("Segoe UI", 11, FontStyle.Bold), Color.White,                         0, 50, 220, ContentAlignment.MiddleCenter);
            var logoVer  = MakeSideLabel("Downloader v1.0", Theme.FontXs,                             Color.FromArgb(160, 200, 255),        0, 70, 220, ContentAlignment.MiddleCenter);
            logoPanel.Controls.AddRange(new Control[] { logoIcon, logoName, logoVer });

            var sep0 = MakeSep();

            // search
            var searchWrap = new Panel { Dock = DockStyle.Top, Height = 44, BackColor = Color.Transparent, Padding = new Padding(10, 8, 10, 0) };
            var searchBox  = new TextBox
            {
                Dock = DockStyle.Fill,
                Text = "🔎  Search anime…", ForeColor = Color.FromArgb(160, 200, 255),
                BackColor = Color.FromArgb(10, 55, 150), Font = Theme.FontSm,
                BorderStyle = BorderStyle.None
            };
            searchBox.Enter += (s, e) => { if (searchBox.ForeColor != Color.White) { searchBox.Text = ""; searchBox.ForeColor = Color.White; } };
            searchBox.Leave += (s, e) => { if (searchBox.Text == "") { searchBox.Text = "🔎  Search anime…"; searchBox.ForeColor = Color.FromArgb(160, 200, 255); } };
            searchWrap.Controls.Add(searchBox);

            var sep1 = MakeSep();

            // nav buttons
            var navPanel = new Panel { Dock = DockStyle.Top, Height = 4 * 50, BackColor = Color.Transparent };
            (string key, string label)[] items =
            {
                ("browse",    "🔍  Browse"),
                ("downloads", "⬇  Downloads"),
                ("log",       "📋  Log"),
                ("settings",  "⚙  Settings"),
            };
            int ny = 4;
            foreach (var (key, label) in items)
            {
                string k = key;
                var btn = new NavButton { Text = label, Left = 4, Top = ny, Width = SIDEBAR_OPEN - 8 };
                btn.Click += (s, e) => ShowPage(k);
                navPanel.Controls.Add(btn);
                _navBtns[key] = btn;
                ny += 50;
            }

            var sep2 = MakeSep();

            // bypass badge
            var bypassPanel = new Panel { Dock = DockStyle.Bottom, Height = 52, BackColor = Color.Transparent };
            var bypassLbl = new Label { Text = "🛡  FlareSolverr active", Font = Theme.FontXs, ForeColor = Theme.Success, BackColor = Color.Transparent, Left = 14, Top = 8,  AutoSize = true };
            var hintLbl   = new Label { Text = "Settings → configure bypass", Font = new Font("Segoe UI", 7f), ForeColor = Color.FromArgb(120, 170, 230), BackColor = Color.Transparent, Left = 14, Top = 28, AutoSize = true };
            bypassPanel.Controls.AddRange(new Control[] { bypassLbl, hintLbl });

            _sidebarInner.Controls.Add(bypassPanel);
            _sidebarInner.Controls.Add(navPanel);
            _sidebarInner.Controls.Add(sep2);
            _sidebarInner.Controls.Add(searchWrap);
            _sidebarInner.Controls.Add(sep1);
            _sidebarInner.Controls.Add(sep0);
            _sidebarInner.Controls.Add(logoPanel);
            _sidebar.Controls.Add(_sidebarInner);

            // ── top bar ───────────────────────────────────────────────────
            var topBar = new Panel { Dock = DockStyle.Top, Height = 48, BackColor = Theme.Card };
            topBar.Paint += (s, e) =>
            {
                e.Graphics.DrawLine(new Pen(Theme.Border, 1), 0, topBar.Height - 1, topBar.Width, topBar.Height - 1);
            };

            _toggleBtn = new Button
            {
                Text = "☰", Font = new Font("Segoe UI", 14), ForeColor = Theme.Accent,
                BackColor = Color.Transparent, FlatStyle = FlatStyle.Flat,
                FlatAppearance = { BorderSize = 0, MouseOverBackColor = Theme.Panel },
                Left = 8, Top = 6, Width = 40, Height = 36, Cursor = Cursors.Hand
            };
            _toggleBtn.Click += (s, e) => ToggleSidebar();

            var appTitle = new Label { Text = "AnimePahe Downloader", Font = Theme.FontBold, ForeColor = Theme.Text, BackColor = Color.Transparent, Left = 56, Top = 14, AutoSize = true };

            topBar.Controls.AddRange(new Control[] { _toggleBtn, appTitle });

            // ── page host ─────────────────────────────────────────────────
            _pageHost = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG };

            _browsePage    = new BrowsePage(_state);
            _downloadsPage = new DownloadsPage(_state);
            _logPage       = new LogPage(_state);
            _settingsPage  = new SettingsPage(_state);

            var origCb = _state.LogCallback;
            _state.LogCallback = (msg, tag) => { origCb?.Invoke(msg, tag); _logPage.Append(msg, tag); };

            _overlay = new FadeOverlay { Dock = DockStyle.Fill, Visible = false };

            foreach (var page in new Control[] { _browsePage, _downloadsPage, _logPage, _settingsPage })
            {
                page.Visible = false;
                _pageHost.Controls.Add(page);
            }
            _pageHost.Controls.Add(_overlay);

            // host wrapper (below top bar)
            var hostWrap = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG };
            hostWrap.Controls.Add(_pageHost);

            Controls.Add(hostWrap);
            Controls.Add(topBar);
            Controls.Add(_sidebar);
        }

        // ── sidebar gradient ──────────────────────────────────────────────────
        private void DrawSidebarGradient(object? s, PaintEventArgs e)
        {
            var r = _sidebar.ClientRectangle;
            using var brush = new LinearGradientBrush(r, Theme.Sidebar, Theme.SidebarDark, LinearGradientMode.Vertical);
            e.Graphics.FillRectangle(brush, r);
        }

        // ── sidebar toggle with animation ─────────────────────────────────────
        private void ToggleSidebar()
        {
            _sidebarOpen = !_sidebarOpen;
            int target = _sidebarOpen ? SIDEBAR_OPEN : SIDEBAR_CLOSE;
            _slideTimer?.Stop(); _slideTimer?.Dispose();
            _slideTimer = new System.Windows.Forms.Timer { Interval = 10 };
            _slideTimer.Tick += (s, e) =>
            {
                int diff = target - _sidebar.Width;
                int step = Math.Max(1, Math.Abs(diff) / 3);
                _sidebar.Width += diff > 0 ? step : -step;
                foreach (NavButton btn in _navBtns.Values) btn.Width = _sidebar.Width - 8;
                _sidebarInner.Visible = _sidebar.Width > SIDEBAR_CLOSE + 10;
                if (Math.Abs(_sidebar.Width - target) <= 1)
                {
                    _sidebar.Width = target;
                    _sidebarInner.Visible = _sidebarOpen;
                    _slideTimer?.Stop();
                }
            };
            _slideTimer.Start();
        }

        // ── page switch with fade transition ──────────────────────────────────
        private void ShowPage(string key)
        {
            if (key == _currentPage) return;

            _overlay.DoTransition(() =>
            {
                _currentPage = key;
                Control page = key switch
                {
                    "browse"    => _browsePage,
                    "downloads" => _downloadsPage,
                    "log"       => _logPage,
                    "settings"  => _settingsPage,
                    _           => _browsePage
                };
                foreach (Control c in _pageHost.Controls)
                    if (c != _overlay) c.Visible = false;
                page.Visible = true;
                page.BringToFront();
                _overlay.BringToFront();

                foreach (var (k, btn) in _navBtns)
                    btn.Active = k == key;
            });
        }

        // ── helpers ───────────────────────────────────────────────────────────
        private static Panel MakeSep() => new Panel { Dock = DockStyle.Top, Height = 1, BackColor = Color.FromArgb(40, 255, 255, 255) };
        private static Label MakeSideLabel(string text, Font font, Color fg, int x, int y, int w, ContentAlignment align) =>
            new Label { Text = text, Font = font, ForeColor = fg, BackColor = Color.Transparent, Left = x, Top = y, Width = w, TextAlign = align, AutoSize = false };
    }
}
