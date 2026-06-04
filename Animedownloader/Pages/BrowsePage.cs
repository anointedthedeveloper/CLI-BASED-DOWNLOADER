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

        // hero slideshow
        private Label  _slideIcon  = null!;
        private Label  _slideTitle = null!;
        private Label  _slideBody  = null!;
        private Panel  _dotsPanel  = null!;
        private int    _slideIdx;
        private System.Windows.Forms.Timer? _slideTimer;
        private readonly (string icon, string title, string body)[] _slides =
        {
            ("🎌", "Welcome to AnimePahe Downloader",  "Paste a series URL above and click Fetch.\nYour episode list will appear here with details."),
            ("🔍", "Search while you type",             "Type an anime name in the search bar above\nand auto-complete suggestions appear instantly."),
            ("⬇", "Flexible quality & language",       "Choose Max / Min or a specific resolution.\nSelect Japanese, English dub, or Chinese audio."),
            ("🛡", "Cloudflare bypass built-in",        "If the site is blocked, head to Settings\nand choose the bypass method that works for you."),
            ("📦", "Batch downloads",                   "Select episodes with checkboxes, then hit\nStart Download — up to 5 concurrent workers."),
        };

        public BrowsePage(AppState state)
        {
            _state = state;
            Dock   = DockStyle.Fill;
            BackColor = Theme.BG;
            DoubleBuffered = true;
            Build();
            StartSlideshow();
        }

        private void Build()
        {
            // ── anime header card ──────────────────────────────────────────
            var hdrCard = new CardPanel { Dock = DockStyle.Top, Height = 86, Margin = new Padding(16, 14, 16, 0), Padding = new Padding(16, 0, 16, 0) };
            hdrCard.Paint += (s, e) => { };

            var icon = new Label { Text = "📺", Font = new Font("Segoe UI", 24), ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 14, Top = 14, Width = 56, Height = 56, TextAlign = ContentAlignment.MiddleCenter };
            _titleLbl = new Label { Text = "AnimePahe Downloader", Font = Theme.FontLg, ForeColor = Theme.Text, BackColor = Color.Transparent, Left = 78, Top = 16, AutoSize = true };
            _metaLbl  = new Label { Text = "Paste a URL and click Fetch to load episodes.", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 78, Top = 46, AutoSize = true };
            _spinner  = new SpinnerControl { Left = 0, Top = 18, Width = 46, Height = 46, SpinColor = Theme.Accent, Visible = false };

            hdrCard.Controls.AddRange(new Control[] { icon, _titleLbl, _metaLbl, _spinner });

            var hdrWrap = new Panel { Dock = DockStyle.Top, Height = 100, BackColor = Theme.BG, Padding = new Padding(16, 14, 16, 0) };
            hdrWrap.Controls.Add(hdrCard);
            hdrCard.Dock = DockStyle.Fill;

            // ── url card ───────────────────────────────────────────────────
            var urlCard = new CardPanel { Height = 78, Padding = new Padding(16, 8, 16, 8) };
            urlCard.Dock = DockStyle.Top;

            var urlLbl = StyledLabel("URL", Theme.SubText, Theme.FontBold); urlLbl.Left = 16; urlLbl.Top = 24;

            _urlBox = new TextBox
            {
                Text = "Paste AnimePahe series or episode URL…", ForeColor = Theme.SubText,
                BackColor = Theme.Panel, Font = Theme.FontDefault, BorderStyle = BorderStyle.FixedSingle,
                Left = 58, Top = 16, Width = 420, Height = 30
            };
            StyleTextBox(_urlBox);
            _urlBox.Enter += (s, e) => { if (_urlBox.ForeColor == Theme.SubText) { _urlBox.Text = ""; _urlBox.ForeColor = Theme.Text; } };
            _urlBox.Leave += (s, e) => { if (_urlBox.Text == "") { _urlBox.Text = "Paste AnimePahe series or episode URL…"; _urlBox.ForeColor = Theme.SubText; } };
            _urlBox.TextChanged += (s, e) => _state.Url = _urlBox.ForeColor == Theme.Text ? _urlBox.Text : "";

            var rangeLbl = StyledLabel("Range", Theme.SubText, Theme.FontSm); rangeLbl.Left = 490; rangeLbl.Top = 22;
            _rangeBox = new TextBox { Text = "all", BackColor = Theme.Panel, ForeColor = Theme.Text, Font = Theme.FontDefault, BorderStyle = BorderStyle.FixedSingle, Left = 538, Top = 16, Width = 70, Height = 30 };
            StyleTextBox(_rangeBox);
            _rangeBox.TextChanged += (s, e) => _state.FetchRange = _rangeBox.Text;

            _fetchBtn = new AccentButton { Text = "🔄  Fetch", Left = 620, Top = 14, Width = 110 };
            _fetchBtn.Click += (s, e) => OnFetch();
            _stopBtn = new AccentButton { Text = "✕  Stop", Left = 738, Top = 14, Width = 90, BaseColor = Theme.Danger, HoverColor = Color.FromArgb(160, 20, 20), Enabled = false };
            _stopBtn.Click += (s, e) => OnStop();

            _status = new Label { Text = "", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 58, Top = 52, AutoSize = true };
            urlCard.Controls.AddRange(new Control[] { urlLbl, _urlBox, rangeLbl, _rangeBox, _fetchBtn, _stopBtn, _status });

            var urlWrap = new Panel { Dock = DockStyle.Top, Height = 88, BackColor = Theme.BG, Padding = new Padding(16, 0, 16, 0) };
            urlWrap.Controls.Add(urlCard);
            urlCard.Dock = DockStyle.Fill;

            // ── episode controls bar ───────────────────────────────────────
            var ctrlCard = new CardPanel { Height = 52, Padding = new Padding(14, 0, 14, 0) };
            ctrlCard.Dock = DockStyle.Top;

            var epLbl  = StyledLabel("Episodes", Theme.SubText, Theme.FontBold); epLbl.Left = 14; epLbl.Top = 16;
            var selAll  = SmallBtn("✓ All",  Theme.Panel, Theme.Text); selAll.Left  = 94;  selAll.Top = 10;
            var selNone = SmallBtn("✗ None", Theme.Panel, Theme.Text); selNone.Left = 150; selNone.Top = 10;
            selAll.Click  += (s, e) => SetAllChecked(true);
            selNone.Click += (s, e) => SetAllChecked(false);

            var qualLbl = StyledLabel("Quality", Theme.SubText, Theme.FontSm); qualLbl.Left = 260; qualLbl.Top = 16;
            _qualCb = StyledCombo(new[] { "Max", "Min", "1080", "720", "480", "360" }, 310, 10, 88);
            _qualCb.SelectedIndexChanged += (s, e) => _state.Quality = _qualCb.SelectedItem?.ToString() ?? "Max";

            var audLbl = StyledLabel("Audio", Theme.SubText, Theme.FontSm); audLbl.Left = 410; audLbl.Top = 16;
            _audioCb = StyledCombo(new[] { "jp (Japanese)", "en (English)", "zh (Chinese)" }, 452, 10, 138);
            _audioCb.SelectedIndexChanged += (s, e) => _state.Audio = _audioCb.SelectedItem?.ToString() ?? "jp (Japanese)";

            ctrlCard.Controls.AddRange(new Control[] { epLbl, selAll, selNone, qualLbl, _qualCb, audLbl, _audioCb });

            var ctrlWrap = new Panel { Dock = DockStyle.Top, Height = 62, BackColor = Theme.BG, Padding = new Padding(16, 0, 16, 0) };
            ctrlWrap.Controls.Add(ctrlCard);
            ctrlCard.Dock = DockStyle.Fill;

            // ── hero panel ─────────────────────────────────────────────────
            _heroPanel = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG };
            var heroCard = new CardPanel { Width = 500, Height = 240, CornerRadius = 16 };
            _slideIcon  = new Label { Text = _slides[0].icon, Font = new Font("Segoe UI", 42), ForeColor = Theme.Accent, BackColor = Color.Transparent, Left = 0, Top = 14, Width = 500, TextAlign = ContentAlignment.MiddleCenter };
            _slideTitle = new Label { Text = _slides[0].title, Font = Theme.FontLg, ForeColor = Theme.Text, BackColor = Color.Transparent, Left = 20, Top = 80, Width = 460, TextAlign = ContentAlignment.MiddleCenter };
            _slideBody  = new Label { Text = _slides[0].body,  Font = Theme.FontHero, ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 20, Top = 118, Width = 460, Height = 50, TextAlign = ContentAlignment.TopCenter };

            _dotsPanel = new Panel { Left = 0, Top = 196, Width = 500, Height = 20, BackColor = Color.Transparent };
            RebuildDots();

            heroCard.Controls.AddRange(new Control[] { _slideIcon, _slideTitle, _slideBody, _dotsPanel });
            _heroPanel.Controls.Add(heroCard);
            _heroPanel.Resize += (s, e) => { heroCard.Left = (_heroPanel.Width - heroCard.Width) / 2; heroCard.Top = (_heroPanel.Height - heroCard.Height) / 2; };

            // ── episode list panel ─────────────────────────────────────────
            _listPanel = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG, Visible = false };
            _epList = new FlowLayoutPanel { Dock = DockStyle.Fill, BackColor = Theme.BG, FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoScroll = true, Padding = new Padding(16, 4, 16, 16) };
            _listPanel.Controls.Add(_epList);

            var fillArea = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG };
            fillArea.Controls.Add(_listPanel);
            fillArea.Controls.Add(_heroPanel);

            Controls.Add(fillArea);
            Controls.Add(ctrlWrap);
            Controls.Add(urlWrap);
            Controls.Add(hdrWrap);
        }

        // ── slideshow ─────────────────────────────────────────────────────────
        private void StartSlideshow()
        {
            _slideTimer = new System.Windows.Forms.Timer { Interval = 4000 };
            _slideTimer.Tick += (s, e) => NextSlide();
            _slideTimer.Start();
        }

        private void NextSlide()
        {
            _slideIdx = (_slideIdx + 1) % _slides.Length;
            AnimateSlide();
        }

        private void AnimateSlide()
        {
            var slide = _slides[_slideIdx];
            float a = 0f;
            var t = new System.Windows.Forms.Timer { Interval = 16 };
            t.Tick += (s, e) =>
            {
                a = Math.Min(1f, a + 0.08f);
                int alpha = (int)(255 * a);
                _slideIcon.ForeColor  = Color.FromArgb(alpha, Theme.Accent);
                _slideTitle.ForeColor = Color.FromArgb(alpha, Theme.Text);
                _slideBody.ForeColor  = Color.FromArgb(alpha, Theme.SubText);
                if (a >= 1f) { t.Stop(); t.Dispose(); }
            };
            _slideIcon.ForeColor = Color.Transparent; _slideTitle.ForeColor = Color.Transparent; _slideBody.ForeColor = Color.Transparent;
            _slideIcon.Text  = slide.icon;
            _slideTitle.Text = slide.title;
            _slideBody.Text  = slide.body;
            RebuildDots();
            t.Start();
        }

        private void RebuildDots()
        {
            _dotsPanel.Controls.Clear();
            int x = (_dotsPanel.Width - _slides.Length * 16) / 2;
            for (int i = 0; i < _slides.Length; i++)
            {
                int idx = i;
                var dot = new Button
                {
                    Left = x, Top = 2, Width = 12, Height = 12,
                    BackColor = idx == _slideIdx ? Theme.Accent : Theme.Border,
                    FlatStyle = FlatStyle.Flat, FlatAppearance = { BorderSize = 0 },
                    Cursor = Cursors.Hand, Tag = idx
                };
                int r = idx == _slideIdx ? 6 : 5;
                dot.Region = new Region(Theme.RoundedPath(new Rectangle(0, 0, dot.Width, dot.Height), r));
                dot.Click += (s, e) => { _slideIdx = idx; AnimateSlide(); _slideTimer?.Stop(); StartSlideshow(); };
                _dotsPanel.Controls.Add(dot);
                x += 16;
            }
        }

        // ── fetch ─────────────────────────────────────────────────────────────
        private void OnFetch()
        {
            string url = _urlBox.ForeColor == Theme.Text ? _urlBox.Text.Trim() : "";
            if (string.IsNullOrEmpty(url)) { SetStatus("⚠  Paste a URL first.", Theme.Warning); return; }
            _state.Url = url;
            SetStatus("Fetching episodes… (stub)", Theme.SubText);
            SetFetching(true);

            Task.Run(async () =>
            {
                await Task.Delay(1400);
                var eps = Enumerable.Range(1, 24).Select(i => new EpisodeItem
                {
                    Number   = i,
                    Title    = $"Episode {i} — The Journey Continues",
                    Audio    = i % 5 == 0 ? "eng" : "jpn",
                    IsFiller = i % 7 == 0,
                    PlayUrl  = $"https://animepahe.pw/play/demo/{i}",
                    Selected = true
                }).ToList();
                _state.Episodes    = eps;
                _state.SeriesTitle = "Demo Anime Series";
                BeginInvoke(() =>
                {
                    _titleLbl.Text = "Demo Anime Series";
                    _metaLbl.Text  = "TV · 24 eps  ·  HD";
                    SetStatus("✓  Loaded 24 episodes", Theme.Success);
                    SetFetching(false);
                    PopulateEpisodes(eps);
                });
            });
        }

        private void OnStop() { SetFetching(false); SetStatus("Fetch stopped.", Theme.SubText); }

        public void PopulateEpisodes(List<EpisodeItem> eps)
        {
            _slideTimer?.Stop();
            _epList.SuspendLayout();
            _epList.Controls.Clear();

            // column header
            var hdrRow = new CardPanel { Width = _epList.Width - 40, Height = 32, CornerRadius = 6, ShowShadow = false };
            hdrRow.BackColor = Theme.Panel;
            hdrRow.Margin = new Padding(0, 0, 0, 4);
            var h1 = HdrLbl("",        14);  h1.Left = 10;
            var h2 = HdrLbl("Ep #",    40);  h2.Left = 34;
            var h3 = HdrLbl("Title",    0);  h3.Left = 86; h3.Width = 300;
            var h4 = HdrLbl("Audio",   50);  h4.Left = 398;
            var h5 = HdrLbl("Tag",     50);  h5.Left = 454;
            hdrRow.Controls.AddRange(new Control[] { h1, h2, h3, h4, h5 });
            _epList.Controls.Add(hdrRow);

            // select all / none
            var selRow = new Panel { Width = _epList.Width - 40, Height = 32, BackColor = Theme.BG, Margin = new Padding(0, 0, 0, 6) };
            var saBtn = SmallBtn("✓ All",  Theme.Panel, Theme.Text); saBtn.Left = 0; saBtn.Top = 4;
            var snBtn = SmallBtn("✗ None", Theme.Panel, Theme.Text); snBtn.Left = 60; snBtn.Top = 4;
            var countLbl = new Label { Text = $"{eps.Count} episodes", Font = Theme.FontXs, ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 130, Top = 10, AutoSize = true };
            saBtn.Click += (s, e) => SetAllChecked(true);
            snBtn.Click += (s, e) => SetAllChecked(false);
            selRow.Controls.AddRange(new Control[] { saBtn, snBtn, countLbl });
            _epList.Controls.Add(selRow);

            bool alt = false;
            foreach (var ep in eps)
            {
                var ep2 = ep;
                var row = new CardPanel
                {
                    Width = _epList.Width - 40, Height = 50,
                    BackColor = alt ? Theme.RowAlt : Theme.Card,
                    CornerRadius = 8, ShowShadow = false,
                    Margin = new Padding(0, 0, 0, 3)
                };
                alt = !alt;

                // hover effect
                row.MouseEnter += (s, e) => { row.BackColor = Theme.CardHover; row.Invalidate(); };
                row.MouseLeave += (s, e) => { row.BackColor = alt ? Theme.RowAlt : Theme.Card; row.Invalidate(); };

                var chk = new CheckBox { Checked = ep2.Selected, Left = 10, Top = 16, Width = 20, BackColor = Color.Transparent };
                chk.CheckedChanged += (s, e) => ep2.Selected = chk.Checked;

                var numLbl   = new Label { Text = $"Ep {ep2.Number,2}", Font = Theme.FontBold, ForeColor = Theme.Accent,   BackColor = Color.Transparent, Left = 36, Top = 8,  Width = 48, AutoSize = false };
                var titleLbl = new Label { Text = ep2.Title,           Font = Theme.FontSm,   ForeColor = Theme.Text,     BackColor = Color.Transparent, Left = 88, Top = 8,  Width = 298, AutoSize = false };
                var subLbl   = new Label { Text = ep2.PlayUrl,         Font = Theme.FontXs,   ForeColor = Theme.SubText,  BackColor = Color.Transparent, Left = 88, Top = 28, Width = 298, AutoSize = false };

                string audioTag = ep2.Audio.Contains("eng") ? "ENG" : "JPN";
                Color  audioCol = ep2.Audio.Contains("eng") ? Theme.Success : Theme.Accent;
                var audioLbl = MakeBadge(audioTag, audioCol, 398, 14);

                row.Controls.AddRange(new Control[] { chk, numLbl, titleLbl, subLbl, audioLbl });

                if (ep2.IsFiller)
                    row.Controls.Add(MakeBadge("Filler", Theme.Warning, 454, 14));

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
            _fetchBtn.Enabled = !active;
            _fetchBtn.Text    = active ? "⏳  Fetching…" : "🔄  Fetch";
            _stopBtn.Enabled  = active;
            _spinner.Visible  = active;
            if (active) _spinner.Start(); else _spinner.Stop();
        }

        // ── small helpers ─────────────────────────────────────────────────────
        private static Label StyledLabel(string t, Color fg, Font f) =>
            new Label { Text = t, Font = f, ForeColor = fg, BackColor = Color.Transparent, AutoSize = true };

        private static void StyleTextBox(TextBox tb)
        {
            tb.BackColor = Theme.Panel;
        }

        private static Button SmallBtn(string text, Color bg, Color fg) => new Button
        {
            Text = text, BackColor = bg, ForeColor = fg, FlatStyle = FlatStyle.Flat,
            Font = Theme.FontXs, Height = 26, AutoSize = true, Cursor = Cursors.Hand,
            Padding = new Padding(8, 0, 8, 0), FlatAppearance = { BorderSize = 0, MouseOverBackColor = Theme.Border }
        };

        private static ComboBox StyledCombo(string[] items, int x, int y, int w)
        {
            var cb = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Font = Theme.FontSm, BackColor = Theme.Panel, ForeColor = Theme.Text, Left = x, Top = y, Width = w };
            cb.Items.AddRange(items.Cast<object>().ToArray());
            cb.SelectedIndex = 0;
            return cb;
        }

        private static Label MakeBadge(string text, Color bg, int left, int top) => new Label
        {
            Text = text, Font = Theme.FontXs, ForeColor = Color.White, BackColor = bg,
            Left = left, Top = top, Width = 40, Height = 20, TextAlign = ContentAlignment.MiddleCenter,
            AutoSize = false
        };

        private static Label HdrLbl(string text, int w) => new Label
        {
            Text = text, Font = Theme.FontXs, ForeColor = Theme.SubText, BackColor = Color.Transparent,
            Top = 8, Width = w, AutoSize = w == 0
        };
    }
}
