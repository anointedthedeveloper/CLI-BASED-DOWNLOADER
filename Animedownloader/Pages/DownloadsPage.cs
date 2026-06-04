using System.Drawing;
using System.Windows.Forms;

namespace Animedownloader
{
    public class DownloadsPage : Panel
    {
        private readonly AppState  _state;
        private TextBox            _dirBox     = null!;
        private AccentButton       _startBtn   = null!;
        private AccentButton       _stopBtn    = null!;
        private Label              _diskLbl    = null!;
        private SmoothProgressBar  _overallBar = null!;
        private SmoothProgressBar  _fileBar    = null!;
        private Label              _overallLbl = null!;
        private Label              _fileLbl    = null!;
        private Label              _statusBadge= null!;
        private RichTextBox        _logBox     = null!;
        private Panel              _idleBanner = null!;
        private Panel              _logPanel   = null!;
        private SpinnerControl     _dlSpinner  = null!;

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
            // ── save-to card ───────────────────────────────────────────────
            var ctrlCard = new CardPanel { Height = 90 };
            var saveLbl  = Lbl("Save to", Theme.FontBold, Theme.SubText, 20, 32);
            _dirBox = new TextBox { Text = _state.SaveDir, BackColor = Theme.Panel, ForeColor = Theme.Text, Font = Theme.FontDefault, BorderStyle = BorderStyle.FixedSingle, Left = 88, Top = 22, Width = 500, Height = 36 };
            _dirBox.TextChanged += (s, e) => _state.SaveDir = _dirBox.Text;

            var browseBtn = new GhostButton { Text = "📁  Browse", Left = 600, Top = 20, Width = 120, Height = 40, Font = Theme.FontSm };
            browseBtn.Click += (s, e) =>
            {
                using var dlg = new FolderBrowserDialog { SelectedPath = _state.SaveDir };
                if (dlg.ShowDialog() == DialogResult.OK) { _state.SaveDir = dlg.SelectedPath; _dirBox.Text = dlg.SelectedPath; RefreshDisk(); }
            };
            _startBtn = new AccentButton { Text = "⬇  Start Download", Left = 734, Top = 20, Width = 180, Height = 40 };
            _startBtn.Click += (s, e) => OnStart();
            _stopBtn  = new AccentButton { Text = "⬛  Stop", Left = 924, Top = 20, Width = 110, Height = 40, BaseColor = Theme.Danger, HoverColor = Color.FromArgb(155, 18, 18), Enabled = false };
            _stopBtn.Click += (s, e) => OnStop();
            _diskLbl = Lbl(GetDiskInfo(), Theme.FontXs, Theme.SubText, 88, 66);
            ctrlCard.Controls.AddRange(new Control[] { saveLbl, _dirBox, browseBtn, _startBtn, _stopBtn, _diskLbl });

            // ── progress card ──────────────────────────────────────────────
            var progCard = new CardPanel { Height = 130 };
            _dlSpinner   = new SpinnerControl { Left = 20, Top = 18, Width = 32, Height = 32, Visible = false };
            var progTitle = Lbl("Download Progress", Theme.FontBold, Theme.Accent, 62, 22);
            _statusBadge  = new Label { Text = "  Idle  ", Font = Theme.FontXs, ForeColor = Theme.SubText, BackColor = Theme.Border, Left = 250, Top = 20, AutoSize = false, Width = 100, Height = 26, TextAlign = ContentAlignment.MiddleCenter };

            var ovLbl = Lbl("Overall", Theme.FontSm, Theme.SubText, 20, 68); ovLbl.Width = 62;
            _overallBar = new SmoothProgressBar { Left = 90, Top = 70, Width = 700, Height = 14, BarColor = Theme.Accent };
            _overallLbl = Lbl("", Theme.FontXs, Theme.SubText, 800, 68);

            var fLbl = Lbl("File", Theme.FontSm, Theme.SubText, 20, 98); fLbl.Width = 62;
            _fileBar = new SmoothProgressBar { Left = 90, Top = 100, Width = 700, Height = 14, BarColor = Theme.Success };
            _fileLbl = Lbl("", Theme.FontXs, Theme.Success, 800, 98);

            progCard.Controls.AddRange(new Control[] { _dlSpinner, progTitle, _statusBadge, ovLbl, _overallBar, _overallLbl, fLbl, _fileBar, _fileLbl });

            // ── idle banner ────────────────────────────────────────────────
            _idleBanner = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG };
            var idleCard = new CardPanel { Width = 500, Height = 170, CornerRadius = 18 };
            var idleIcon  = new Label { Text = "⬇", Font = new Font("Segoe UI", 38), ForeColor = Theme.Accent, BackColor = Color.Transparent, Left = 0, Top = 16, Width = 500, TextAlign = ContentAlignment.MiddleCenter };
            var idleTitle = new Label { Text = "No active downloads", Font = new Font("Segoe UI", 14, FontStyle.Bold), ForeColor = Theme.Text, BackColor = Color.Transparent, Left = 20, Top = 82, Width = 460, TextAlign = ContentAlignment.MiddleCenter };
            var idleHint  = new Label { Text = "Browse → Fetch episodes → select them → Start Download", Font = Theme.FontDefault, ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 20, Top = 118, Width = 460, TextAlign = ContentAlignment.MiddleCenter };
            idleCard.Controls.AddRange(new Control[] { idleIcon, idleTitle, idleHint });
            _idleBanner.Controls.Add(idleCard);
            _idleBanner.Resize += (s, e) => { idleCard.Left = (_idleBanner.Width - idleCard.Width) / 2; idleCard.Top = (_idleBanner.Height - idleCard.Height) / 2; };

            // ── log panel ──────────────────────────────────────────────────
            _logPanel = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG, Visible = false };
            var logHdr  = new Panel { Dock = DockStyle.Top, Height = 40, BackColor = Theme.BG };
            var actLbl  = Lbl("Recent Activity", Theme.FontBold, Theme.Accent, 0, 10);
            var clearBtn = MiniBtn("Clear"); clearBtn.Left = 180; clearBtn.Top = 6;
            clearBtn.Click += (s, e) => _logBox.Clear();
            logHdr.Controls.AddRange(new Control[] { actLbl, clearBtn });

            var logCard = new CardPanel { Dock = DockStyle.Fill, CornerRadius = 10 };
            _logBox = new RichTextBox { Dock = DockStyle.Fill, BackColor = Theme.Terminal, ForeColor = Theme.TermFg, Font = Theme.FontMono, ReadOnly = true, BorderStyle = BorderStyle.None, ScrollBars = RichTextBoxScrollBars.Vertical, Padding = new Padding(12) };
            logCard.Controls.Add(_logBox);
            _logPanel.Controls.Add(logCard);
            _logPanel.Controls.Add(logHdr);

            var fillArea = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG, Padding = new Padding(24, 10, 24, 24) };
            fillArea.Controls.Add(_logPanel);
            fillArea.Controls.Add(_idleBanner);

            Controls.Add(fillArea);
            Controls.Add(Wrap(progCard, 146));
            Controls.Add(Wrap(ctrlCard, 106));
        }

        private void OnStart()
        {
            if (_state.Episodes.Count == 0) { MessageBox.Show("Go to Browse and fetch episodes first.", "No Episodes", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
            SetRunning(true);
            _state.Log($"Starting: {_state.SeriesTitle}", "info");
            _state.Log($"Save to:  {_state.SaveDir}", "info");
            _state.Log("(Stub) — wire up real download logic here.", "info");
            Task.Run(async () =>
            {
                for (int i = 0; i <= 100; i += 2)
                {
                    await Task.Delay(60);
                    int v = i;
                    BeginInvoke(() =>
                    {
                        SetOverall(v, $"{v}%  ·  {v / 4 + 1} / 24 episodes");
                        SetFile(v, $"{v * 0.44:F1} MB / 44.0 MB   {3.2:F1} MB/s");
                    });
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

        private void SetRunning(bool on)
        {
            if (InvokeRequired) { Invoke(() => SetRunning(on)); return; }
            _startBtn.Enabled = !on; _stopBtn.Enabled = on;
            _statusBadge.Text      = on ? "  Downloading…  " : "  Idle  ";
            _statusBadge.ForeColor = on ? Theme.Success : Theme.SubText;
            _statusBadge.BackColor = on ? Color.FromArgb(30, 27, 153, 85) : Theme.Border;
            if (on) { _dlSpinner.Visible = true; _dlSpinner.Start(); } else { _dlSpinner.Stop(); }
            if (!on) { _idleBanner.Visible = true; _logPanel.Visible = false; }
        }

        private void RefreshDisk() => _diskLbl.Text = GetDiskInfo();
        private string GetDiskInfo()
        {
            try { var d = new DriveInfo(Path.GetPathRoot(_state.SaveDir) ?? "C:\\"); return $"💾  {d.AvailableFreeSpace / 1e9:F1} GB free of {d.TotalSize / 1e9:F1} GB"; }
            catch { return "Disk info unavailable"; }
        }

        private static Panel Wrap(CardPanel card, int height)
        {
            var w = new Panel { Dock = DockStyle.Top, Height = height, BackColor = Theme.BG, Padding = new Padding(24, 14, 24, 0) };
            card.Dock = DockStyle.Fill; w.Controls.Add(card); return w;
        }
        private static Label Lbl(string t, Font f, Color fg, int x, int y) => new Label { Text = t, Font = f, ForeColor = fg, BackColor = Color.Transparent, Left = x, Top = y, AutoSize = true };
        private static Button MiniBtn(string text) => new Button { Text = text, BackColor = Theme.Panel, ForeColor = Theme.SubText, FlatStyle = FlatStyle.Flat, Font = Theme.FontXs, Height = 28, AutoSize = true, Cursor = Cursors.Hand, Padding = new Padding(10, 0, 10, 0), FlatAppearance = { BorderSize = 0, MouseOverBackColor = Theme.Border } };
    }
}
