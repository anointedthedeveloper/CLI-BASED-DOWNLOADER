using System.Drawing;
using System.Windows.Forms;

namespace Animedownloader
{
    public class BrowsePage : Panel
    {
        private readonly AppState _state;
        private TextBox  _urlBox   = null!;
        private Label    _status   = null!;
        private Button   _fetchBtn = null!;
        private Button   _stopBtn  = null!;
        private TextBox  _rangeBox = null!;
        private ComboBox _qualCb   = null!;
        private ComboBox _audioCb  = null!;
        private FlowLayoutPanel _episodeList = null!;
        private Panel    _heroPanel = null!;
        private Panel    _listPanel = null!;
        private Label    _titleLbl  = null!;
        private Label    _metaLbl   = null!;

        public BrowsePage(AppState state)
        {
            _state = state;
            Dock = DockStyle.Fill;
            BackColor = Theme.BG;
            Build();
        }

        private void Build()
        {
            // ── anime header card ──────────────────────────────────────────
            var hdr = MakeCard(80);
            hdr.Dock = DockStyle.Top;
            var icon = new Label { Text = "📺", Font = new Font("Segoe UI", 22), ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 16, Top = 10, Width = 60, Height = 60, TextAlign = ContentAlignment.MiddleCenter };
            _titleLbl = new Label { Text = "AnimePahe Downloader", Font = Theme.FontLg, ForeColor = Theme.Text, BackColor = Theme.Card, Left = 82, Top = 14, AutoSize = true };
            _metaLbl  = new Label { Text = "Paste a URL and click Fetch to load episodes.", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 82, Top = 42, AutoSize = true };
            hdr.Controls.AddRange(new Control[] { icon, _titleLbl, _metaLbl });

            // ── url card ───────────────────────────────────────────────────
            var urlCard = MakeCard(72);
            urlCard.Dock = DockStyle.Top;
            var urlLbl = new Label { Text = "URL", Font = Theme.FontBold, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 16, Top = 22, AutoSize = true };
            _urlBox = new TextBox { Text = "Paste AnimePahe series or episode URL…", ForeColor = Theme.SubText, BackColor = Theme.Panel, Font = Theme.FontDefault, BorderStyle = BorderStyle.FixedSingle, Left = 56, Top = 14, Width = 380, Height = 28 };
            _urlBox.Enter += (s, e) => { if (_urlBox.ForeColor == Theme.SubText) { _urlBox.Text = ""; _urlBox.ForeColor = Theme.Text; } };
            _urlBox.Leave += (s, e) => { if (_urlBox.Text == "") { _urlBox.Text = "Paste AnimePahe series or episode URL…"; _urlBox.ForeColor = Theme.SubText; } };
            _urlBox.TextChanged += (s, e) => _state.Url = _urlBox.ForeColor == Theme.Text ? _urlBox.Text : "";

            var rangeLbl = new Label { Text = "Range", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 446, Top = 22, AutoSize = true };
            _rangeBox = new TextBox { Text = "all", BackColor = Theme.Panel, ForeColor = Theme.Text, Font = Theme.FontDefault, BorderStyle = BorderStyle.FixedSingle, Left = 494, Top = 14, Width = 70, Height = 28 };
            _rangeBox.TextChanged += (s, e) => _state.FetchRange = _rangeBox.Text;

            _fetchBtn = MakeBtn("🔄 Fetch", Theme.Accent, Color.White); _fetchBtn.Left = 574; _fetchBtn.Top = 12;
            _fetchBtn.Click += (s, e) => OnFetch();
            _stopBtn = MakeBtn("✕ Stop", Theme.Danger, Color.White); _stopBtn.Left = 660; _stopBtn.Top = 12; _stopBtn.Enabled = false;
            _stopBtn.Click += (s, e) => OnStop();
            _status = new Label { Text = "", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 56, Top = 48, AutoSize = true };
            urlCard.Controls.AddRange(new Control[] { urlLbl, _urlBox, rangeLbl, _rangeBox, _fetchBtn, _stopBtn, _status });

            // ── episode controls bar ───────────────────────────────────────
            var ctrlBar = MakeCard(46);
            ctrlBar.Dock = DockStyle.Top;
            var epLbl   = new Label { Text = "Episodes", Font = Theme.FontBold, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 14, Top = 14, AutoSize = true };
            var selAll  = MakeBtn("✓ All",  Theme.Panel, Theme.Text, small: true); selAll.Left  = 90;  selAll.Top = 8;
            var selNone = MakeBtn("✗ None", Theme.Panel, Theme.Text, small: true); selNone.Left = 148; selNone.Top = 8;
            selAll.Click  += (s, e) => SetAllChecked(true);
            selNone.Click += (s, e) => SetAllChecked(false);

            var qualLbl = new Label { Text = "Quality", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 240, Top = 14, AutoSize = true };
            _qualCb = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Font = Theme.FontSm, BackColor = Theme.Panel, ForeColor = Theme.Text, Left = 294, Top = 10, Width = 80 };
            _qualCb.Items.AddRange(new object[] { "Max", "Min", "1080", "720", "480", "360" });
            _qualCb.SelectedIndex = 0;
            _qualCb.SelectedIndexChanged += (s, e) => _state.Quality = _qualCb.SelectedItem?.ToString() ?? "Max";

            var audLbl = new Label { Text = "Audio", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 384, Top = 14, AutoSize = true };
            _audioCb = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Font = Theme.FontSm, BackColor = Theme.Panel, ForeColor = Theme.Text, Left = 426, Top = 10, Width = 130 };
            _audioCb.Items.AddRange(new object[] { "jp (Japanese)", "en (English)", "zh (Chinese)" });
            _audioCb.SelectedIndex = 0;
            _audioCb.SelectedIndexChanged += (s, e) => _state.Audio = _audioCb.SelectedItem?.ToString() ?? "jp (Japanese)";
            ctrlBar.Controls.AddRange(new Control[] { epLbl, selAll, selNone, qualLbl, _qualCb, audLbl, _audioCb });

            // ── hero panel ─────────────────────────────────────────────────
            _heroPanel = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG };
            var heroCard = MakeCard(180); heroCard.Width = 480;
            var heroIcon  = new Label { Text = "🎌", Font = new Font("Segoe UI", 36), ForeColor = Theme.Accent, BackColor = Theme.Card, Left = 20, Top = 10, AutoSize = true };
            var heroTitle = new Label { Text = "Welcome to AnimePahe Downloader", Font = Theme.FontLg, ForeColor = Theme.Text, BackColor = Theme.Card, Left = 20, Top = 64, AutoSize = true };
            var heroBody  = new Label { Text = "Paste a series or episode URL above, then click Fetch.\nYour episode list will appear here.", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 20, Top = 96, AutoSize = true };
            heroCard.Controls.AddRange(new Control[] { heroIcon, heroTitle, heroBody });
            _heroPanel.Controls.Add(heroCard);
            _heroPanel.Resize += (s, e) => { heroCard.Left = (_heroPanel.Width - heroCard.Width) / 2; heroCard.Top = (_heroPanel.Height - heroCard.Height) / 2; };

            // ── episode list panel ─────────────────────────────────────────
            _listPanel = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG, Visible = false };
            _episodeList = new FlowLayoutPanel { Dock = DockStyle.Fill, BackColor = Theme.BG, FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoScroll = true, Padding = new Padding(4) };
            _listPanel.Controls.Add(_episodeList);

            var fillArea = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG };
            fillArea.Controls.Add(_listPanel);
            fillArea.Controls.Add(_heroPanel);

            Controls.Add(fillArea);
            Controls.Add(ctrlBar);
            Controls.Add(urlCard);
            Controls.Add(hdr);
        }

        private void OnFetch()
        {
            string url = _urlBox.ForeColor == Theme.Text ? _urlBox.Text.Trim() : "";
            if (string.IsNullOrEmpty(url)) { SetStatus("Paste a URL first.", Theme.Danger); return; }
            _state.Url = url;
            SetStatus("Fetching episodes… (stub)", Theme.SubText);
            SetFetching(true);
            Task.Run(async () =>
            {
                await Task.Delay(1200);
                var eps = Enumerable.Range(1, 12).Select(i => new EpisodeItem
                {
                    Number = i, Title = $"Episode {i}", Audio = i % 4 == 0 ? "eng" : "jpn",
                    IsFiller = i == 5, PlayUrl = $"https://animepahe.pw/play/demo/{i}", Selected = true
                }).ToList();
                _state.Episodes = eps;
                _state.SeriesTitle = "Demo Anime";
                BeginInvoke(() =>
                {
                    _titleLbl.Text = "Demo Anime"; _metaLbl.Text = "TV · 12 eps";
                    SetStatus("✓ Loaded 12 episodes", Theme.Success);
                    SetFetching(false);
                    PopulateEpisodes(eps);
                });
            });
        }

        private void OnStop() { SetFetching(false); SetStatus("Fetch stopped.", Theme.SubText); }

        public void PopulateEpisodes(List<EpisodeItem> eps)
        {
            _episodeList.SuspendLayout();
            _episodeList.Controls.Clear();
            bool alt = false;
            foreach (var ep in eps)
            {
                var ep2 = ep;
                var row = new Panel { Width = 700, Height = 44, BackColor = alt ? Theme.RowAlt : Theme.Card, Margin = new Padding(0, 0, 0, 1) };
                alt = !alt;
                var chk = new CheckBox { Checked = ep2.Selected, Left = 8, Top = 12, Width = 20, BackColor = row.BackColor };
                chk.CheckedChanged += (s, e) => ep2.Selected = chk.Checked;
                var numLbl   = new Label { Text = $"Ep {ep2.Number}", Font = Theme.FontBold, ForeColor = Theme.Accent, BackColor = row.BackColor, Left = 34, Top = 6,  Width = 52,  AutoSize = false };
                var titleLbl = new Label { Text = ep2.Title,          Font = Theme.FontSm,   ForeColor = Theme.Text,   BackColor = row.BackColor, Left = 34, Top = 24, Width = 260, AutoSize = false };
                string audioTag = ep2.Audio.Contains("eng") ? "ENG" : "JPN";
                Color  audioCol = ep2.Audio.Contains("eng") ? Theme.Success : Theme.Accent;
                var audioLbl = new Label { Text = audioTag, Font = Theme.FontXs, ForeColor = Color.White, BackColor = audioCol, Left = 304, Top = 12, Width = 36, Height = 20, TextAlign = ContentAlignment.MiddleCenter };
                row.Controls.AddRange(new Control[] { chk, numLbl, titleLbl, audioLbl });
                if (ep2.IsFiller)
                {
                    var fLbl = new Label { Text = "Filler", Font = Theme.FontXs, ForeColor = Color.White, BackColor = Color.FromArgb(249, 115, 22), Left = 346, Top = 12, Width = 42, Height = 20, TextAlign = ContentAlignment.MiddleCenter };
                    row.Controls.Add(fLbl);
                }
                _episodeList.Controls.Add(row);
            }
            _episodeList.ResumeLayout();
            _heroPanel.Visible = false;
            _listPanel.Visible = true;
        }

        private void SetAllChecked(bool val)
        {
            foreach (var ep in _state.Episodes) ep.Selected = val;
            foreach (Control c in _episodeList.Controls)
                foreach (Control ch in c.Controls)
                    if (ch is CheckBox cb) cb.Checked = val;
        }

        public void SetStatus(string msg, Color color)
        {
            if (InvokeRequired) { Invoke(() => SetStatus(msg, color)); return; }
            _status.Text = msg; _status.ForeColor = color;
        }

        public void SetFetching(bool active)
        {
            if (InvokeRequired) { Invoke(() => SetFetching(active)); return; }
            _fetchBtn.Enabled = !active; _fetchBtn.Text = active ? "⏳ Fetching…" : "🔄 Fetch";
            _stopBtn.Enabled = active;
        }

        private static Panel MakeCard(int height) => new Panel { BackColor = Theme.Card, Height = height };
        private static Button MakeBtn(string text, Color bg, Color fg, bool small = false) => new Button
        {
            Text = text, BackColor = bg, ForeColor = fg, FlatStyle = FlatStyle.Flat,
            Font = small ? Theme.FontXs : Theme.FontSm, Height = small ? 26 : 30, AutoSize = true,
            Padding = new Padding(10, 0, 10, 0), FlatAppearance = { BorderSize = 0 }
        };
    }
}
