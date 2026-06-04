using System.Drawing;
using System.Windows.Forms;

namespace Animedownloader
{
    public class DownloadsPage : Panel
    {
        private readonly AppState _state;
        private TextBox    _dirBox     = null!;
        private Button     _browseBtn  = null!;
        private Button     _startBtn   = null!;
        private Button     _stopBtn    = null!;
        private Label      _diskLbl    = null!;
        private ProgressBar _overallBar = null!;
        private ProgressBar _fileBar    = null!;
        private Label      _overallLbl = null!;
        private Label      _fileLbl    = null!;
        private Label      _statusBadge= null!;
        private RichTextBox _logBox    = null!;
        private Panel      _idleBanner = null!;
        private Panel      _logPanel   = null!;
        private bool       _running;

        public DownloadsPage(AppState state)
        {
            _state = state;
            _state.LogCallback = AppendLog;
            Dock = DockStyle.Fill;
            BackColor = Theme.BG;
            Build();
        }

        private void Build()
        {
            // ── controls card ──────────────────────────────────────────────
            var ctrl = MakeCard(72);
            ctrl.Dock = DockStyle.Top;
            var saveLbl = new Label { Text = "Save to", Font = Theme.FontBold, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 16, Top = 22, AutoSize = true };
            _dirBox = new TextBox { Text = _state.SaveDir, BackColor = Theme.Panel, ForeColor = Theme.Text, Font = Theme.FontDefault, BorderStyle = BorderStyle.FixedSingle, Left = 72, Top = 14, Width = 380, Height = 28 };
            _dirBox.TextChanged += (s, e) => _state.SaveDir = _dirBox.Text;

            _browseBtn = MakeBtn("📁 Browse", Theme.Panel, Theme.Text); _browseBtn.Left = 462; _browseBtn.Top = 12;
            _browseBtn.Click += (s, e) => {
                using var dlg = new FolderBrowserDialog { SelectedPath = _state.SaveDir };
                if (dlg.ShowDialog() == DialogResult.OK) { _state.SaveDir = dlg.SelectedPath; _dirBox.Text = dlg.SelectedPath; }
            };

            _startBtn = MakeBtn("⬇  Start Download", Theme.Accent, Color.White, bold: true); _startBtn.Left = 570; _startBtn.Top = 12;
            _startBtn.Click += (s, e) => OnStart();

            _stopBtn = MakeBtn("⬛ Stop", Theme.Danger, Color.White, bold: true); _stopBtn.Left = 710; _stopBtn.Top = 12; _stopBtn.Enabled = false;
            _stopBtn.Click += (s, e) => OnStop();

            _diskLbl = new Label { Text = GetDiskInfo(), Font = Theme.FontXs, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 72, Top = 48, AutoSize = true };
            ctrl.Controls.AddRange(new Control[] { saveLbl, _dirBox, _browseBtn, _startBtn, _stopBtn, _diskLbl });

            // ── progress card ──────────────────────────────────────────────
            var progCard = MakeCard(110);
            progCard.Dock = DockStyle.Top;

            _statusBadge = new Label { Text = "Idle", Font = Theme.FontXs, ForeColor = Theme.SubText, BackColor = Theme.Border, Left = 16, Top = 14, Width = 60, Height = 20, TextAlign = ContentAlignment.MiddleCenter };
            var progTitle = new Label { Text = "Download Progress", Font = Theme.FontBold, ForeColor = Theme.Accent, BackColor = Theme.Card, Left = 82, Top = 14, AutoSize = true };

            var ovLbl = new Label { Text = "Overall", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 16, Top = 42, Width = 60, AutoSize = false };
            _overallBar = new ProgressBar { Left = 82, Top = 42, Width = 500, Height = 16, Style = ProgressBarStyle.Continuous, ForeColor = Theme.Accent };
            _overallLbl = new Label { Text = "", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 590, Top = 42, AutoSize = true };

            var fileLbl = new Label { Text = "File", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 16, Top = 70, Width = 60, AutoSize = false };
            _fileBar = new ProgressBar { Left = 82, Top = 70, Width = 500, Height = 16, Style = ProgressBarStyle.Continuous, ForeColor = Theme.Success };
            _fileLbl = new Label { Text = "", Font = Theme.FontSm, ForeColor = Theme.Success, BackColor = Theme.Card, Left = 590, Top = 70, AutoSize = true };

            progCard.Controls.AddRange(new Control[] { _statusBadge, progTitle, ovLbl, _overallBar, _overallLbl, fileLbl, _fileBar, _fileLbl });

            // ── idle banner ────────────────────────────────────────────────
            _idleBanner = new Panel { Dock = DockStyle.Fill, BackColor = Theme.Card };
            var idleCard = MakeCard(120); idleCard.Width = 420;
            var idleIcon  = new Label { Text = "⬇", Font = new Font("Segoe UI", 32), ForeColor = Theme.Accent, BackColor = Theme.Card, Left = 20, Top = 8, AutoSize = true };
            var idleTitle = new Label { Text = "No active downloads", Font = Theme.FontBold, ForeColor = Theme.Text, BackColor = Theme.Card, Left = 20, Top = 60, AutoSize = true };
            var idleHint  = new Label { Text = "Browse → Fetch episodes → select them → Start Download", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 20, Top = 84, AutoSize = true };
            idleCard.Controls.AddRange(new Control[] { idleIcon, idleTitle, idleHint });
            _idleBanner.Controls.Add(idleCard);
            _idleBanner.Resize += (s, e) => { idleCard.Left = (_idleBanner.Width - idleCard.Width) / 2; idleCard.Top = (_idleBanner.Height - idleCard.Height) / 2; };

            // ── log panel ──────────────────────────────────────────────────
            _logPanel = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG, Visible = false };
            var logHdr = new Panel { Dock = DockStyle.Top, Height = 32, BackColor = Theme.BG };
            var actLbl   = new Label { Text = "Recent Activity", Font = Theme.FontBold, ForeColor = Theme.Accent, BackColor = Theme.BG, Left = 0, Top = 8, AutoSize = true };
            var clearBtn = MakeBtn("Clear", Theme.Panel, Theme.Text, small: true); clearBtn.Left = 200; clearBtn.Top = 4;
            clearBtn.Click += (s, e) => { _logBox.Clear(); };
            logHdr.Controls.AddRange(new Control[] { actLbl, clearBtn });

            _logBox = new RichTextBox { Dock = DockStyle.Fill, BackColor = Theme.Terminal, ForeColor = Theme.TermFg, Font = Theme.FontMono, ReadOnly = true, BorderStyle = BorderStyle.None, ScrollBars = RichTextBoxScrollBars.Vertical };
            _logPanel.Controls.Add(_logBox);
            _logPanel.Controls.Add(logHdr);

            var fillArea = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG };
            fillArea.Controls.Add(_logPanel);
            fillArea.Controls.Add(_idleBanner);

            Controls.Add(fillArea);
            Controls.Add(progCard);
            Controls.Add(ctrl);
        }

        private void OnStart()
        {
            if (_state.Episodes.Count == 0) { MessageBox.Show("Go to Browse, fetch episodes first.", "No Episodes", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
            SetRunning(true);
            _state.Log($"Starting download: {_state.SeriesTitle}", "info");
            _state.Log($"Save to: {_state.SaveDir}", "info");
            _state.Log("(Stub) — wire up real download logic here.", "info");
            // Demo progress animation
            Task.Run(async () =>
            {
                for (int i = 0; i <= 100; i += 5)
                {
                    await Task.Delay(120);
                    int val = i;
                    BeginInvoke(() => { SetOverall(val, $"{val}%"); SetFile(val, $"{val / 10.0:F1} MB / 45.0 MB"); });
                }
                BeginInvoke(() => { _state.Log("All done! ✓", "success"); SetRunning(false); });
            });
        }

        private void OnStop()
        {
            _state.Log("Stop requested.", "info");
            SetRunning(false);
        }

        public void AppendLog(string msg, string tag)
        {
            if (InvokeRequired) { Invoke(() => AppendLog(msg, tag)); return; }
            _idleBanner.Visible = false;
            _logPanel.Visible   = true;
            Color col = tag switch { "success" => Theme.Success, "error" => Theme.Danger, "info" => Theme.SubText, _ => Theme.TermFg };
            _logBox.SelectionStart  = _logBox.TextLength;
            _logBox.SelectionLength = 0;
            _logBox.SelectionColor  = col;
            _logBox.AppendText(msg + "\n");
            _logBox.ScrollToCaret();
        }

        public void SetOverall(int pct, string label)
        {
            if (InvokeRequired) { Invoke(() => SetOverall(pct, label)); return; }
            _overallBar.Value = Math.Clamp(pct, 0, 100);
            _overallLbl.Text  = label;
        }

        public void SetFile(int pct, string label)
        {
            if (InvokeRequired) { Invoke(() => SetFile(pct, label)); return; }
            _fileBar.Value = Math.Clamp(pct, 0, 100);
            _fileLbl.Text  = label;
        }

        private void SetRunning(bool running)
        {
            if (InvokeRequired) { Invoke(() => SetRunning(running)); return; }
            _running = running;
            _startBtn.Enabled = !running; _startBtn.BackColor = running ? Theme.Border : Theme.Accent;
            _stopBtn.Enabled  = running;
            _statusBadge.Text = running ? "Downloading…" : "Idle";
            _statusBadge.ForeColor = running ? Theme.Success : Theme.SubText;
            if (!running) { _idleBanner.Visible = true; _logPanel.Visible = false; }
        }

        private string GetDiskInfo()
        {
            try
            {
                var drive = new DriveInfo(Path.GetPathRoot(_state.SaveDir) ?? "C:\\");
                double free  = drive.AvailableFreeSpace / 1e9;
                double total = drive.TotalSize / 1e9;
                return $"💾  {free:F1} GB free of {total:F1} GB";
            }
            catch { return "Disk info unavailable"; }
        }

        private static Panel MakeCard(int height) => new Panel { BackColor = Theme.Card, Height = height };
        private static Button MakeBtn(string text, Color bg, Color fg, bool small = false, bool bold = false) => new Button
        {
            Text = text, BackColor = bg, ForeColor = fg, FlatStyle = FlatStyle.Flat,
            Font = bold ? Theme.FontBold : (small ? Theme.FontXs : Theme.FontSm),
            Height = small ? 26 : 30, AutoSize = true, Padding = new Padding(10, 0, 10, 0),
            FlatAppearance = { BorderSize = 0 }
        };
    }
}
