using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace Animedownloader
{
    public class BrowsePage : Panel
    {
        private readonly AppState _state;
        private TextBox         _urlBox    = null!;
        private Label           _status    = null!;
        private AccentButton    _fetchBtn  = null!;
        private AccentButton    _stopBtn   = null!;
        private TextBox         _rangeBox  = null!;
        private ComboBox        _qualCb    = null!;
        private ComboBox        _audioCb   = null!;
        private FlowLayoutPanel _epList    = null!;
        private Panel           _heroPanel = null!;
        private Panel           _listPanel = null!;
        private Label           _titleLbl  = null!;
        private Label           _metaLbl   = null!;
        private SpinnerControl  _spinner   = null!;
        private Label           _slideIcon  = null!;
        private Label           _slideTitle = null!;
        private Label           _slideBody  = null!;
        private Panel           _dotsPanel  = null!;
        private int             _slideIdx;
        private System.Windows.Forms.Timer? _slideTimer;

        private readonly (string icon, string title, string body)[] _slides =
        {
            ("🎌", "Welcome to AnimePahe Downloader",  "Paste a series URL above and click Fetch.\nYour episode list will appear here with thumbnails."),
            ("🔍", "Search while you type",             "Type an anime name in the search bar\nand suggestions will appear instantly."),
            ("⬇", "Flexible quality & language",       "Choose Max / Min or a specific resolution.\nSelect Japanese, English dub, or Chinese audio."),
            ("🛡", "Cloudflare bypass built-in",        "If the site is blocked, head to Settings\nand pick the bypass method that works for you."),
            ("📦", "Batch downloads",                   "Select episodes with checkboxes then hit\nStart Download — up to 5 concurrent workers."),
        };

        public BrowsePage(AppState state)
        {
            _state = state;
            Dock = DockStyle.Fill;
            BackColor = Theme.BG;
            DoubleBuffered = true;
            Build();
            StartSlideshow();
        }

        private void Build()
        {
            // ── anime header ───────────────────────────────────────────────
            var hdrCard = new CardPanel { Height = 90 };
            var icon      = new Label { Text = "📺", Font = new Font("Segoe UI", 26), ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 20, Top = 16, Width = 58, Height = 58, TextAlign = ContentAlignment.MiddleCenter };
            _spinner      = new SpinnerControl { Left = 20, Top = 20, Width = 48, Height = 48, SpinColor = Theme.Accent, Visible = false };
            _titleLbl     = Lbl("AnimePahe Downloader", Theme.FontLg, Theme.Text, 92, 18);
            _metaLbl      = Lbl("Paste a URL and click Fetch to load episodes.", Theme.FontDefault, Theme.SubText, 92, 52);
            hdrCard.Controls.AddRange(new Control[] { icon, _spinner, _titleLbl, _metaLbl });

            // ── url bar ────────────────────────────────────────────────────
            var urlCard = new CardPanel { Height = 90 };

            var urlLbl  = Lbl("URL", Theme.FontBold, Theme.SubText, 20, 30); urlLbl.Width = 36;
            _urlBox = StyledEntry(62, 20, 480, "Paste AnimePahe series or episode URL…");
            _urlBox.Enter += (s, e) => { if (_urlBox.ForeColor == Theme.SubText) { _urlBox.Text = ""; _urlBox.ForeColor = Theme.Text; } };
            _urlBox.Leave += (s, e) => { if (_urlBox.Text == "") { _urlBox.Text = "Paste AnimePahe series or episode URL…"; _urlBox.ForeColor = Theme.SubText; } };
            _urlBox.TextChanged += (s, e) => _state.Url = _urlBox.ForeColor == Theme.Text ? _urlBox.Text : "";

            var rngLbl  = Lbl("Range", Theme.FontSm, Theme.SubText, 556, 28); rngLbl.Width = 48;
            _rangeBox   = StyledEntry(606, 20, 90, "all"); _rangeBox.ForeColor = Theme.Text;
            _rangeBox.TextChanged += (s, e) => _state.FetchRange = _rangeBox.Text;

            _fetchBtn = new AccentButton { Text = "🔄  Fetch", Left = 710, Top = 18, Width = 130, Height = 40 };
            _fetchBtn.Click += (s, e) => OnFetch();
            _stopBtn = new AccentButton { Text = "✕  Stop", Left = 850, Top = 18, Width = 110, Height = 40, BaseColor = Theme.Danger, HoverColor = Color.FromArgb(155, 18, 18), Enabled = false };
            _stopBtn.Click += (s, e) => OnStop();

            _status = new Label { Text = "", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 62, Top = 62, AutoSize = true };
            urlCard.Controls.AddRange(new Control[] { urlLbl, _urlBox, rngLbl, _rangeBox, _fetchBtn, _stopBtn, _status });

            // ── episode controls bar ───────────────────────────────────────
            var ctrlCard = new CardPanel { Height = 60 };

            var epLbl  = Lbl("Episodes", Theme.FontBold, Theme.SubText, 20, 20); epLbl.Width = 80;
            var saBtn  = MiniBtn("✓ All");  saBtn.Left  = 106; saBtn.Top = 15;
            var snBtn  = MiniBtn("✗ None"); snBtn.Left  = 172; snBtn.Top = 15;
            saBtn.Click  += (s, e) => SetAllChecked(true);
            snBtn.Click  += (s, e) => SetAllChecked(false);

            var qLbl = Lbl("Quality", Theme.FontSm, Theme.SubText, 290, 20); qLbl.Width = 54;
            _qualCb  = StyledCombo(new[] { "Max", "Min", "1080", "720", "480", "360" }, 348, 16, 94);
            _qualCb.SelectedIndexChanged += (s, e) => _state.Quality = _qualCb.SelectedItem?.ToString() ?? "Max";

            var aLbl = Lbl("Audio", Theme.FontSm, Theme.SubText, 456, 20); aLbl.Width = 44;
            _audioCb = StyledCombo(new[] { "jp (Japanese)", "en (English)", "zh (Chinese)" }, 504, 16, 148);
            _audioCb.SelectedIndexChanged += (s, e) => _state.Audio = _audioCb.SelectedItem?.ToString() ?? "jp (Japanese)";

            ctrlCard.Controls.AddRange(new Control[] { epLbl, saBtn, snBtn, qLbl, _qualCb, aLbl, _audioCb });

            // ── hero ───────────────────────────────────────────────────────
            _heroPanel = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG };
            var heroCard = new CardPanel { Width = 560, Height = 280, CornerRadius = 18 };
            _slideIcon  = new Label { Text = _slides[0].icon, Font = new Font("Segoe UI", 48), ForeColor = Theme.Accent, BackColor = Color.Transparent, Left = 0, Top = 18, Width = 560, TextAlign = ContentAlignment.MiddleCenter };
            _slideTitle = new Label { Text = _slides[0].title, Font = new Font("Segoe UI", 14, FontStyle.Bold), ForeColor = Theme.Text, BackColor = Color.Transparent, Left = 30, Top = 96, Width = 500, TextAlign = ContentAlignment.MiddleCenter };
            _slideBody  = new Label { Text = _slides[0].body, Font = new Font("Segoe UI", 10), ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 30, Top = 136, Width = 500, Height = 52, TextAlign = ContentAlignment.TopCenter };
            _dotsPanel  = new Panel { Left = 0, Top = 214, Width = 560, Height = 24, BackColor = Color.Transparent };
            BuildDots();
            heroCard.Controls.AddRange(new Control[] { _slideIcon, _slideTitle, _slideBody, _dotsPanel });
            _heroPanel.Controls.Add(heroCard);
            _heroPanel.Resize += (s, e) => { heroCard.Left = (_heroPanel.Width - heroCard.Width) / 2; heroCard.Top = (_heroPanel.Height - heroCard.Height) / 2; };

            // ── episode list ───────────────────────────────────────────────
            _listPanel = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG, Visible = false };
            _epList = new FlowLayoutPanel { Dock = DockStyle.Fill, BackColor = Theme.BG, FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoScroll = true, Padding = new Padding(0, 6, 0, 24) };
            _listPanel.Controls.Add(_epList);

            var fillArea = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG };
            fillArea.Controls.Add(_listPanel);
            fillArea.Controls.Add(_heroPanel);

            // assemble with padding wrappers
            Controls.Add(fillArea);
            Controls.Add(Wrap(ctrlCard, 74));
            Controls.Add(Wrap(urlCard, 106));
            Controls.Add(Wrap(hdrCard, 106));
        }

        // ── slideshow ─────────────────────────────────────────────────────────
        private void StartSlideshow()
        {
            _slideTimer = new System.Windows.Forms.Timer { Interval = 4200 };
            _slideTimer.Tick += (s, e) => { _slideIdx = (_slideIdx + 1) % _slides.Length; AnimateSlide(); };
            _slideTimer.Start();
        }

        private void AnimateSlide()
        {
            var sl = _slides[_slideIdx];
            _slideIcon.ForeColor = _slideTitle.ForeColor = _slideBody.ForeColor = Color.Transparent;
            _slideIcon.Text = sl.icon; _slideTitle.Text = sl.title; _slideBody.Text = sl.body;
            BuildDots();
            float a = 0f;
            var t = new System.Windows.Forms.Timer { Interval = 16 };
            t.Tick += (s, e) =>
            {
                a = Math.Min(1f, a + 0.09f);
                int v = (int)(255 * a);
                _slideIcon.ForeColor  = Color.FromArgb(v, Theme.Accent);
                _slideTitle.ForeColor = Color.FromArgb(v, Theme.Text);
                _slideBody.ForeColor  = Color.FromArgb(v, Theme.SubText);
                if (a >= 1f) { t.Stop(); t.Dispose(); }
            };
            t.Start();
        }

        private void BuildDots()
        {
            _dotsPanel.Controls.Clear();
            int total = _slides.Length;
            int x = (_dotsPanel.Width - total * 18) / 2;
            for (int i = 0; i < total; i++)
            {
                int idx = i;
                bool active = i == _slideIdx;
                var dot = new Button
                {
                    Left = x, Top = 4, Width = active ? 24 : 10, Height = 10,
                    BackColor = active ? Theme.Accent : Theme.Border,
                    FlatStyle = FlatStyle.Flat, FlatAppearance = { BorderSize = 0 }, Cursor = Cursors.Hand
                };
                dot.Region = new Region(Theme.RoundedPath(new Rectangle(0, 0, dot.Width, dot.Height), 5));
                dot.Click += (s, e) => { _slideIdx = idx; AnimateSlide(); _slideTimer?.Stop(); StartSlideshow(); };
                _dotsPanel.Controls.Add(dot);
                x += (active ? 24 : 10) + 6;
            }
        }

        // ── fetch ─────────────────────────────────────────────────────────────
        private void OnFetch()
        {
            string url = _urlBox.ForeColor == Theme.Text ? _urlBox.Text.Trim() : "";
            if (string.IsNullOrEmpty(url)) { SetStatus("⚠  Paste a URL first.", Theme.Warning); return; }
            _state.Url = url;
            SetStatus("Fetching episodes…", Theme.SubText);
            SetFetching(true);
            Task.Run(async () =>
            {
                await Task.Delay(1400);
                var eps = Enumerable.Range(1, 24).Select(i => new EpisodeItem
                {
                    Number = i, Title = $"The Journey Begins — Part {i}",
                    Audio = i % 5 == 0 ? "eng" : "jpn", IsFiller = i % 7 == 0,
                    PlayUrl = $"https://animepahe.pw/play/demo/{i}", Selected = true
                }).ToList();
                _state.Episodes = eps; _state.SeriesTitle = "Demo Anime Series";
                BeginInvoke(() =>
                {
                    _titleLbl.Text = "Demo Anime Series"; _metaLbl.Text = "TV · 24 episodes · 1080p";
                    SetStatus("✓  Loaded 24 episodes", Theme.Success);
                    SetFetching(false); PopulateEpisodes(eps);
                });
            });
        }

        private void OnStop() { SetFetching(false); SetStatus("Fetch stopped.", Theme.SubText); }

        public void PopulateEpisodes(List<EpisodeItem> eps)
        {
            _slideTimer?.Stop();
            _epList.SuspendLayout();
            _epList.Controls.Clear();

            // select bar
            var selRow = new Panel { Width = 900, Height = 40, BackColor = Color.Transparent, Margin = new Padding(0, 0, 0, 4) };
            var saBtn = MiniBtn("✓ All");  saBtn.Left = 0; saBtn.Top = 6;
            var snBtn = MiniBtn("✗ None"); snBtn.Left = 68; snBtn.Top = 6;
            var cntLbl = Lbl($"{eps.Count} episodes found", Theme.FontSm, Theme.SubText, 146, 12);
            saBtn.Click += (s, e) => SetAllChecked(true);
            snBtn.Click += (s, e) => SetAllChecked(false);
            selRow.Controls.AddRange(new Control[] { saBtn, snBtn, cntLbl });
            _epList.Controls.Add(selRow);

            bool alt = false;
            foreach (var ep in eps)
            {
                var ep2 = ep;
                var row = new CardPanel
                {
                    Width = 900, Height = 64, CornerRadius = 10, ShowShadow = false,
                    BackColor = alt ? Theme.RowAlt : Theme.Card,
                    Margin = new Padding(0, 0, 0, 4)
                };
                alt = !alt;
                Color rowBg = row.BackColor;
                row.MouseEnter += (s, e) => { row.BackColor = Theme.Panel; row.Invalidate(); };
                row.MouseLeave += (s, e) => { row.BackColor = rowBg; row.Invalidate(); };

                var chk     = new CheckBox { Checked = ep2.Selected, Left = 14, Top = 22, Width = 22, BackColor = Color.Transparent };
                chk.CheckedChanged += (s, e) => ep2.Selected = chk.Checked;

                var numLbl   = Lbl($"Ep {ep2.Number,2}", Theme.FontBold, Theme.Accent, 44,  10); numLbl.Width = 58;
                var titleLbl = Lbl(ep2.Title, Theme.FontDefault, Theme.Text, 44, 34); titleLbl.Width = 340;
                var urlLbl2  = Lbl(ep2.PlayUrl, Theme.FontXs, Theme.SubText, 44, 34); // not shown
                // audio badge
                bool isEng = ep2.Audio.Contains("eng");
                var abadge = Badge(isEng ? "ENG" : "JPN", isEng ? Theme.Success : Theme.Accent, 414, 20);

                row.Controls.AddRange(new Control[] { chk, numLbl, titleLbl, abadge });
                if (ep2.IsFiller) row.Controls.Add(Badge("Filler", Theme.Warning, 466, 20));

                _epList.Controls.Add(row);
            }
            _epList.ResumeLayout();
            _heroPanel.Visible = false;
            _listPanel.Visible = true;
        }

        private void SetAllChecked(bool val)
        {
            foreach (var ep in _state.Episodes) ep.Selected = val;
            foreach (Control r in _epList.Controls)
                foreach (Control c in r.Controls)
                    if (c is CheckBox cb) cb.Checked = val;
        }

        public void SetStatus(string msg, Color col)
        {
            if (InvokeRequired) { Invoke(() => SetStatus(msg, col)); return; }
            _status.Text = msg; _status.ForeColor = col;
        }

        public void SetFetching(bool active)
        {
            if (InvokeRequired) { Invoke(() => SetFetching(active)); return; }
            _fetchBtn.Enabled = !active; _fetchBtn.Text = active ? "⏳  Fetching…" : "🔄  Fetch";
            _stopBtn.Enabled  = active;
            _spinner.Visible  = active;
            if (active) _spinner.Start(); else _spinner.Stop();
        }

        // ── helpers ───────────────────────────────────────────────────────────
        private static Panel Wrap(CardPanel card, int height)
        {
            var w = new Panel { Dock = DockStyle.Top, Height = height, BackColor = Theme.BG, Padding = new Padding(24, 14, 24, 0) };
            card.Dock = DockStyle.Fill;
            w.Controls.Add(card);
            return w;
        }

        private static Label Lbl(string text, Font font, Color fg, int x, int y)
            => new Label { Text = text, Font = font, ForeColor = fg, BackColor = Color.Transparent, Left = x, Top = y, AutoSize = true };

        private static TextBox StyledEntry(int x, int y, int w, string placeholder)
            => new TextBox { Text = placeholder, ForeColor = Theme.SubText, BackColor = Theme.Panel, Font = Theme.FontDefault, BorderStyle = BorderStyle.FixedSingle, Left = x, Top = y, Width = w, Height = 36 };

        private static Button MiniBtn(string text) => new Button
        {
            Text = text, BackColor = Theme.Panel, ForeColor = Theme.Text, FlatStyle = FlatStyle.Flat,
            Font = Theme.FontSm, Height = 32, AutoSize = true, Cursor = Cursors.Hand,
            Padding = new Padding(12, 0, 12, 0), FlatAppearance = { BorderSize = 0, MouseOverBackColor = Theme.Border }
        };

        private static ComboBox StyledCombo(string[] items, int x, int y, int w)
        {
            var cb = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Font = Theme.FontDefault, BackColor = Theme.Panel, ForeColor = Theme.Text, Left = x, Top = y, Width = w, Height = 34 };
            cb.Items.AddRange(items.Cast<object>().ToArray()); cb.SelectedIndex = 0;
            return cb;
        }

        private static Label Badge(string text, Color bg, int x, int y)
            => new Label { Text = text, Font = Theme.FontXs, ForeColor = Color.White, BackColor = bg, Left = x, Top = y, Width = 44, Height = 22, TextAlign = ContentAlignment.MiddleCenter, AutoSize = false };
    }
}
