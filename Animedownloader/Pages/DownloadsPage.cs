using System.Drawing;
using System.Windows.Forms;

namespace Animedownloader
{
    public class DownloadsPage : Panel
    {
        private readonly AppState    _state;
        private TextBox              _dirBox     = null!;
        private AccentButton         _startBtn   = null!;
        private AccentButton         _stopBtn    = null!;
        private Label                _diskLbl    = null!;
        private SmoothProgressBar    _overallBar = null!;
        private SmoothProgressBar    _fileBar    = null!;
        private Label                _overallLbl = null!;
        private Label                _fileLbl    = null!;
        private Label                _statusBadge= null!;
        private RichTextBox          _logBox     = null!;
        private Panel                _idleBanner = null!;
        private Panel                _logPanel   = null!;
        private SpinnerControl       _dlSpinner  = null!;

        public DownloadsPage(AppState state)
        {
            _state = state;
            _state.LogCallback = AppendLog;
            Dock = DockStyle.Fill;
            BackColor = Theme.BG;
            DoubleBuffered = true;
            Build();
        }

        private void Build()
        {
            // ── controls card ──────────────────────────────────────────────
            var ctrlCard = new CardPanel { Height = 80 };
            ctrlCard.Dock = DockStyle.Top;

            var saveLbl = new Label { Text = "Save to", Font = Theme.FontBold, ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 16, Top = 26, AutoSize = true };
            _dirBox = new TextBox { Text = _state.SaveDir, BackColor = Theme.Panel, ForeColor = Theme.Text, Font = Theme.FontDefault, BorderStyle = BorderStyle.FixedSingle, Left = 78, Top = 18, Width = 400, Height = 30 };
            _dirBox.TextChanged += (s, e) => _state.SaveDir = _dirBox.Text;

            var browseBtn = new GhostButton { Text = "📁  Browse", Left = 488, Top = 16, Width = 100, Font = Theme.FontSm, ForeColor = Theme.Accent };
            browseBtn.Click += (s, e) =>
            {
                using var dlg = new FolderBrowserDialog { SelectedPath = _state.SaveDir };
                if (dlg.ShowDialog() == DialogResult.OK) { _state.SaveDir = dlg.SelectedPath; _dirBox.Text = dlg.SelectedPath; RefreshDisk(); }
            };

            _startBtn = new AccentButton { Text = "⬇  Start Download", Left = 600, Top = 16, Width = 160, BaseColor = Theme.Accent };
            _startBtn.Click += (s, e) => OnStart();

            _stopBtn = new AccentButton { Text = "⬛  Stop", Left = 770, Top = 16, Width = 90, BaseColor = Theme.Danger, HoverColor = Color.FromArgb(160, 20, 20), Enabled = false };
            _stopBtn.Click += (s, e) => OnStop();

            _diskLbl = new Label { Text = GetDiskInfo(), Font = Theme.FontXs, ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 78, Top = 54, AutoSize = true };
            ctrlCard.Controls.AddRange(new Control[] { saveLbl, _dirBox, browseBtn, _startBtn, _stopBtn, _diskLbl });

            var ctrlWrap = new Panel { Dock = DockStyle.Top, Height = 96, BackColor = Theme.BG, Padding = new Padding(16, 14, 16, 0) };
            ctrlWrap.Controls.Add(ctrlCard);
            ctrlCard.Dock = DockStyle.Fill;

            // ── progress card ──────────────────────────────────────────────
            var progCard = new CardPanel { Height = 120 };
            progCard.Dock = DockStyle.Top;

            _dlSpinner = new SpinnerControl { Left = 16, Top = 14, Width = 28, Height = 28, Visible = false };
            var progTitle = new Label { Text = "Download Progress", Font = Theme.FontBold, ForeColor = Theme.Accent, BackColor = Color.Transparent, Left = 52, Top = 16, AutoSize = true };
            _statusBadge  = MakeBadge("Idle", Theme.Border, Theme.SubText); _statusBadge.Left = 240; _statusBadge.Top = 14;

            var ovLbl = new Label { Text = "Overall", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 16, Top = 52, Width = 60, AutoSize = false };
            _overallBar = new SmoothProgressBar { Left = 82, Top = 54, Width = 520, Height = 12, BarColor = Theme.Accent };
            _overallLbl = new Label { Text = "", Font = Theme.FontXs, ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 612, Top = 51, AutoSize = true };

            var fileLbl = new Label { Text = "File", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 16, Top = 82, Width = 60, AutoSize = false };
            _fileBar    = new SmoothProgressBar { Left = 82, Top = 84, Width = 520, Height = 12, BarColor = Theme.Success };
            _fileLbl    = new Label { Text = "", Font = Theme.FontXs, ForeColor = Theme.Success, BackColor = Color.Transparent, Left = 612, Top = 81, AutoSize = true };

            progCard.Controls.AddRange(new Control[] { _dlSpinner, progTitle, _statusBadge, ovLbl, _overallBar, _overallLbl, fileLbl, _fileBar, _fileLbl });

            var progWrap = new Panel { Dock = DockStyle.Top, Height = 134, BackColor = Theme.BG, Padding = new Padding(16, 0, 16, 0) };
            progWrap.Controls.Add(progCard);
            progCard.Dock = DockStyle.Fill;

            // ── idle banner ────────────────────────────────────────────────
            _idleBanner = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG };
            var idleCard = new CardPanel { Width = 440, Height = 150, CornerRadius = 16 };
            var idleIcon  = new Label { Text = "⬇", Font = new Font("Segoe UI", 36), ForeColor = Theme.Accent, BackColor = Color.Transparent, Left = 0, Top = 14, Width = 440, TextAlign = ContentAlignment.MiddleCenter };
            var idleTitle = new Label { Text = "No active downloads", Font = Theme.FontLg, ForeColor = Theme.Text, BackColor = Color.Transparent, Left = 20, Top = 72, Width = 400, TextAlign = ContentAlignment.MiddleCenter };
            var idleHint  = new Label { Text = "Browse → Fetch episodes → select → Start Download", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 20, Top = 108, Width = 400, TextAlign = ContentAlignment.MiddleCenter };
            idleCard.Controls.AddRange(new Control[] { idleIcon, idleTitle, idleHint });
            _idleBanner.Controls.Add(idleCard);
            _idleBanner.Resize += (s, e) => { idleCard.Left = (_idleBanner.Width - idleCard.Width) / 2; idleCard.Top = (_idleBanner.Height - idleCard.Height) / 2; };

            // ── log panel ──────────────────────────────────────────────────
            _logPanel = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG, Visible = false };
            var logHdrRow = new Panel { Dock = DockStyle.Top, Height = 34, BackColor = Theme.BG };
            var actLbl  = new Label { Text = "Recent Activity", Font = Theme.FontBold, ForeColor = Theme.Accent, BackColor = Color.Transparent, Left = 0, Top = 8, AutoSize = true };
            var clearBtn = SmallBtn("Clear", Theme.Panel, Theme.SubText); clearBtn.Left = 160; clearBtn.Top = 4;
            clearBtn.Click += (s, e) => _logBox.Clear();
            logHdrRow.Controls.AddRange(new Control[] { actLbl, clearBtn });

            _logBox = new RichTextBox { Dock = DockStyle.Fill, BackColor = Theme.Terminal, ForeColor = Theme.TermFg, Font = Theme.FontMono, ReadOnly = true, BorderStyle = BorderStyle.None, ScrollBars = RichTextBoxScrollBars.Vertical, Padding = new Padding(8) };
            _logPanel.Controls.Add(_logBox);
            _logPanel.Controls.Add(logHdrRow);

            var fillArea = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG, Padding = new Padding(16, 0, 16, 16) };
            fillArea.Controls.Add(_logPanel);
            fillArea.Controls.Add(_idleBanner);

            Controls.Add(fillArea);
            Controls.Add(progWrap);
            Controls.Add(ctrlWrap);
        }

        private void OnStart()
        {
            if (_state.Episodes.Count == 0)
            {
                MessageBox.Show("Go to Browse, fetch episodes first.", "No Episodes", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            SetRunning(true);
            _state.Log($"Starting: {_state.SeriesTitle}", "info");
            _state.Log($"Save to: {_state.SaveDir}", "info");
            _state.Log("(Stub) — wire up real download logic here.", "info");

            Task.Run(async () =>
            {
                for (int i = 0; i <= 100; i += 2)
                {
                    await Task.Delay(60);
                    int v = i;
                    BeginInvoke(() => { SetOverall(v, $"{v}%  ·  {v / 4 + 1} / 24 episodes"); SetFile(v, $"{v * 0.42:F1} MB / 42.0 MB  ·  {3.2:F1} MB/s"); });
                }
                BeginInvoke(() => { _state.Log("All done! ✓", "success"); SetRunning(false); });
            });
        }

        private void OnStop() { _state.Log("Stop requested.", "info"); SetRunning(false); }

        public void AppendLog(string msg, string tag)
        {
            if (InvokeRequired) { Invoke(() => AppendLog(msg, tag)); return; }
            _idleBanner.Visible = false; _logPanel.Visible = true;
            Color col = tag switch { "success" => Theme.Success, "error" => Theme.Danger, "info" => Theme.SubText, _ => Theme.TermFg };
            _logBox.SelectionStart = _logBox.TextLength; _logBox.SelectionLength = 0;
            _logBox.SelectionColor = col;
            _logBox.AppendText(msg + "\n");
            _logBox.ScrollToCaret();
        }

        public void SetOverall(int pct, string label)
        {
            if (InvokeRequired) { Invoke(() => SetOverall(pct, label)); return; }
            _overallBar.Value = pct; _overallLbl.Text = label;
        }

        public void SetFile(int pct, string label)
        {
            if (InvokeRequired) { Invoke(() => SetFile(pct, label)); return; }
            _fileBar.Value = pct; _fileLbl.Text = label;
        }

        private void SetRunning(bool running)
        {
            if (InvokeRequired) { Invoke(() => SetRunning(running)); return; }
            _startBtn.Enabled   = !running;
            _stopBtn.Enabled    = running;
            _statusBadge.Text   = running ? " Downloading… " : "  Idle  ";
            _statusBadge.BackColor = running ? Color.FromArgb(30, 27, 153, 85) : Theme.Border;
            _statusBadge.ForeColor = running ? Theme.Success : Theme.SubText;
            if (running) { _dlSpinner.Visible = true; _dlSpinner.Start(); }
            else         { _dlSpinner.Stop(); }
            if (!running) { _idleBanner.Visible = true; _logPanel.Visible = false; }
        }

        private void RefreshDisk() => _diskLbl.Text = GetDiskInfo();

        private string GetDiskInfo()
        {
            try
            {
                var d = new DriveInfo(Path.GetPathRoot(_state.SaveDir) ?? "C:\\");
                return $"💾  {d.AvailableFreeSpace / 1e9:F1} GB free of {d.TotalSize / 1e9:F1} GB";
            }
            catch { return "Disk info unavailable"; }
        }

        private static Label MakeBadge(string text, Color bg, Color fg) => new Label
        {
            Text = text, Font = Theme.FontXs, BackColor = bg, ForeColor = fg,
            AutoSize = false, Width = 110, Height = 22, TextAlign = ContentAlignment.MiddleCenter
        };

        private static Button SmallBtn(string text, Color bg, Color fg) => new Button
        {
            Text = text, BackColor = bg, ForeColor = fg, FlatStyle = FlatStyle.Flat,
            Font = Theme.FontXs, Height = 26, AutoSize = true, Cursor = Cursors.Hand,
            Padding = new Padding(8, 0, 8, 0), FlatAppearance = { BorderSize = 0, MouseOverBackColor = Theme.Border }
        };
    }
}
