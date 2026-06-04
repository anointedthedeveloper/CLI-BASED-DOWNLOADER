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
        private readonly Dictionary<string, NavButton> _navBtns = new();
        private string        _currentPage   = "";
        private bool          _sidebarOpen   = true;
        private System.Windows.Forms.Timer? _animTimer;
        private const int SB_OPEN  = 260;
        private const int SB_CLOSE = 0;

        public MainForm()
        {
            Text           = "AnimePahe Downloader";
            MinimumSize    = new Size(1000, 680);
            Size           = new Size(1400, 900);
            BackColor      = Theme.BG;
            StartPosition  = FormStartPosition.CenterScreen;
            WindowState    = FormWindowState.Maximized;
            Font           = Theme.FontDefault;
            DoubleBuffered = true;
            BuildLayout();
            ShowPage("browse");
        }

        private void BuildLayout()
        {
            // ── sidebar ───────────────────────────────────────────────────
            _sidebar = new Panel { Dock = DockStyle.Left, Width = SB_OPEN, BackColor = Theme.Sidebar };
            _sidebar.Paint += (s, e) =>
            {
                using var br = new LinearGradientBrush(_sidebar.ClientRectangle,
                    Theme.Sidebar, Theme.SidebarDark, LinearGradientMode.Vertical);
                e.Graphics.FillRectangle(br, _sidebar.ClientRectangle);
            };

            _sidebarInner = new Panel { Dock = DockStyle.Fill, BackColor = Color.Transparent };

            // logo
            var logoPanel = new Panel { Dock = DockStyle.Top, Height = 110, BackColor = Color.Transparent };
            var logoIcon = SideLabel("🎌", new Font("Segoe UI", 28), Color.White, ContentAlignment.MiddleCenter, 0, 10, SB_OPEN, 48);
            var logoName = SideLabel("AnimePahe",       new Font("Segoe UI", 12, FontStyle.Bold), Color.White, ContentAlignment.MiddleCenter, 0, 58, SB_OPEN, 26);
            var logoVer  = SideLabel("Downloader v1.0", new Font("Segoe UI", 8f), Color.FromArgb(160, 200, 255), ContentAlignment.MiddleCenter, 0, 84, SB_OPEN, 20);
            logoPanel.Controls.AddRange(new Control[] { logoIcon, logoName, logoVer });

            // search box
            var searchWrap = new Panel { Dock = DockStyle.Top, Height = 56, BackColor = Color.Transparent, Padding = new Padding(16, 10, 16, 0) };
            var searchInner = new Panel { Dock = DockStyle.Fill, BackColor = Color.FromArgb(10, 50, 140), Padding = new Padding(10, 0, 4, 0) };
            var searchBox = new TextBox
            {
                Dock = DockStyle.Fill, Text = "🔎  Search anime…",
                ForeColor = Color.FromArgb(150, 190, 255), BackColor = Color.FromArgb(10, 50, 140),
                Font = Theme.FontDefault, BorderStyle = BorderStyle.None
            };
            searchBox.Enter += (s, e) => { if (searchBox.ForeColor != Color.White) { searchBox.Text = ""; searchBox.ForeColor = Color.White; } };
            searchBox.Leave += (s, e) => { if (searchBox.Text == "") { searchBox.Text = "🔎  Search anime…"; searchBox.ForeColor = Color.FromArgb(150, 190, 255); } };
            searchInner.Controls.Add(searchBox);
            searchWrap.Controls.Add(searchInner);

            // separator
            var sep1 = new Panel { Dock = DockStyle.Top, Height = 1, BackColor = Color.FromArgb(50, 255, 255, 255), Margin = new Padding(0, 6, 0, 6) };

            // nav label
            var navLbl = new Panel { Dock = DockStyle.Top, Height = 30, BackColor = Color.Transparent };
            var navLblTxt = SideLabel("NAVIGATION", new Font("Segoe UI", 7.5f, FontStyle.Bold), Color.FromArgb(100, 160, 230), ContentAlignment.MiddleLeft, 20, 0, 200, 30);
            navLbl.Controls.Add(navLblTxt);

            // nav buttons
            (string key, string label)[] items =
            {
                ("browse",    "🔍   Browse"),
                ("downloads", "⬇   Downloads"),
                ("log",       "📋   Activity Log"),
                ("settings",  "⚙   Settings"),
            };
            var navPanel = new Panel { Dock = DockStyle.Top, Height = items.Length * 54, BackColor = Color.Transparent };
            int ny = 4;
            foreach (var (key, label) in items)
            {
                string k = key;
                var btn = new NavButton { Text = label, Left = 10, Top = ny, Width = SB_OPEN - 20, Height = 48 };
                btn.Click += (s, e) => ShowPage(k);
                navPanel.Controls.Add(btn);
                _navBtns[key] = btn;
                ny += 54;
            }

            var sep2 = new Panel { Dock = DockStyle.Top, Height = 1, BackColor = Color.FromArgb(50, 255, 255, 255) };

            // bottom bypass
            var botPanel = new Panel { Dock = DockStyle.Bottom, Height = 72, BackColor = Color.Transparent, Padding = new Padding(18, 12, 18, 0) };
            var bypassLbl = SideLabel("🛡  FlareSolverr active",    new Font("Segoe UI", 9f), Theme.Success,                      ContentAlignment.MiddleLeft, 18, 14, SB_OPEN - 36, 22);
            var hintLbl   = SideLabel("Settings → configure bypass", new Font("Segoe UI", 7.5f), Color.FromArgb(110, 160, 220),  ContentAlignment.MiddleLeft, 18, 38, SB_OPEN - 36, 18);
            botPanel.Controls.AddRange(new Control[] { bypassLbl, hintLbl });

            _sidebarInner.Controls.Add(botPanel);
            _sidebarInner.Controls.Add(navPanel);
            _sidebarInner.Controls.Add(sep2);
            _sidebarInner.Controls.Add(navLbl);
            _sidebarInner.Controls.Add(sep1);
            _sidebarInner.Controls.Add(searchWrap);
            _sidebarInner.Controls.Add(logoPanel);
            _sidebar.Controls.Add(_sidebarInner);

            // ── top bar ───────────────────────────────────────────────────
            var topBar = new Panel { Dock = DockStyle.Top, Height = 56, BackColor = Theme.Card };
            topBar.Paint += (s, e) =>
                e.Graphics.DrawLine(new Pen(Theme.Border, 1), 0, topBar.Height - 1, topBar.Width, topBar.Height - 1);

            var toggleBtn = new Button
            {
                Text = "☰", Font = new Font("Segoe UI", 15), ForeColor = Theme.Accent,
                BackColor = Color.Transparent, FlatStyle = FlatStyle.Flat,
                FlatAppearance = { BorderSize = 0, MouseOverBackColor = Theme.Panel },
                Left = 14, Top = 10, Width = 44, Height = 38, Cursor = Cursors.Hand
            };
            toggleBtn.Click += (s, e) => ToggleSidebar();

            var appTitle = new Label
            {
                Text = "AnimePahe Downloader", Font = new Font("Segoe UI", 12f, FontStyle.Bold),
                ForeColor = Theme.Text, BackColor = Color.Transparent, Left = 68, Top = 15, AutoSize = true
            };
            topBar.Controls.AddRange(new Control[] { toggleBtn, appTitle });

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
            { page.Visible = false; _pageHost.Controls.Add(page); }
            _pageHost.Controls.Add(_overlay);

            var hostWrap = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG };
            hostWrap.Controls.Add(_pageHost);

            Controls.Add(hostWrap);
            Controls.Add(topBar);
            Controls.Add(_sidebar);
        }

        private void ToggleSidebar()
        {
            _sidebarOpen = !_sidebarOpen;
            int target = _sidebarOpen ? SB_OPEN : SB_CLOSE;
            _animTimer?.Stop(); _animTimer?.Dispose();
            _animTimer = new System.Windows.Forms.Timer { Interval = 10 };
            _animTimer.Tick += (s, e) =>
            {
                int diff = target - _sidebar.Width;
                int step = Math.Max(2, Math.Abs(diff) / 4);
                _sidebar.Width += diff > 0 ? step : -step;
                foreach (var btn in _navBtns.Values) btn.Width = Math.Max(0, _sidebar.Width - 20);
                _sidebarInner.Visible = _sidebar.Width > 30;
                if (Math.Abs(_sidebar.Width - target) <= 2)
                {
                    _sidebar.Width = target;
                    _sidebarInner.Visible = _sidebarOpen;
                    _animTimer?.Stop();
                }
            };
            _animTimer.Start();
        }

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
                foreach (var (k, btn) in _navBtns) btn.Active = k == key;
            });
        }

        private static Label SideLabel(string text, Font font, Color fg, ContentAlignment align, int x, int y, int w, int h) =>
            new Label { Text = text, Font = font, ForeColor = fg, BackColor = Color.Transparent, Left = x, Top = y, Width = w, Height = h, TextAlign = align, AutoSize = false };
    }
}
