using System.Drawing;
using System.Windows.Forms;

namespace Animedownloader
{
    public class LogPage : Panel
    {
        private readonly AppState _state;
        private readonly List<(string tag, string ts, string msg)> _entries = new();
        private RichTextBox _logBox     = null!;
        private string      _filter     = "all";
        private Label       _totalLbl   = null!, _successLbl = null!, _errorLbl = null!, _infoLbl = null!;
        private readonly Dictionary<string, AccentButton> _filterBtns = new();

        public LogPage(AppState state)
        {
            _state = state;
            Dock = DockStyle.Fill;
            BackColor = Theme.BG;
            DoubleBuffered = true;
            Build();
        }

        private void Build()
        {
            // ── header card ────────────────────────────────────────────────
            var hdrCard = new CardPanel { Height = 126, Padding = new Padding(18, 10, 18, 8) };
            hdrCard.Dock = DockStyle.Top;

            var titleLbl = new Label { Text = "Activity Log", Font = Theme.FontLg, ForeColor = Theme.Text, BackColor = Color.Transparent, Left = 18, Top = 12, AutoSize = true };
            var subLbl   = new Label { Text = "Full history of fetches, downloads and errors.", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 18, Top = 44, AutoSize = true };

            // stats row
            _totalLbl   = StatLbl("0 Total",   Theme.SubText, 18);
            _successLbl = StatLbl("0 Success", Theme.Success, 110);
            _errorLbl   = StatLbl("0 Errors",  Theme.Danger,  210);
            _infoLbl    = StatLbl("0 Info",    Theme.Accent,  300);
            _totalLbl.Top = _successLbl.Top = _errorLbl.Top = _infoLbl.Top = 68;
            hdrCard.Controls.AddRange(new Control[] { titleLbl, subLbl, _totalLbl, _successLbl, _errorLbl, _infoLbl });

            // filter + action buttons
            (string key, string label)[] filters = { ("all", "All"), ("success", "✓ Success"), ("error", "✗ Errors"), ("info", "ℹ Info") };
            int bx = 18;
            foreach (var (key, label) in filters)
            {
                string k = key;
                var btn = new AccentButton
                {
                    Text = label, Left = bx, Top = 96, Width = 90,
                    BaseColor  = k == "all" ? Theme.Accent : Theme.Panel,
                    HoverColor = k == "all" ? Theme.AccentHv : Theme.Border,
                    ForeColor  = k == "all" ? Color.White : Theme.Text,
                    Font = Theme.FontXs, Height = 28
                };
                btn.Click += (s, e) => SetFilter(k);
                _filterBtns[key] = btn;
                hdrCard.Controls.Add(btn);
                bx += 96;
            }
            bx += 12;
            var exportBtn = new GhostButton { Text = "💾 Export", Left = bx, Top = 96, Width = 96, Font = Theme.FontXs, Height = 28, ForeColor = Theme.Accent };
            exportBtn.Click += (s, e) => Export();
            var clearBtn  = new AccentButton { Text = "🗑 Clear", Left = bx + 102, Top = 96, Width = 86, Font = Theme.FontXs, Height = 28, BaseColor = Color.FromArgb(220, 235, 255), HoverColor = Theme.Danger, ForeColor = Theme.Danger };
            clearBtn.Click += (s, e) => Clear();
            hdrCard.Controls.AddRange(new Control[] { exportBtn, clearBtn });

            var hdrWrap = new Panel { Dock = DockStyle.Top, Height = 140, BackColor = Theme.BG, Padding = new Padding(16, 14, 16, 0) };
            hdrWrap.Controls.Add(hdrCard);
            hdrCard.Dock = DockStyle.Fill;

            // ── log box ────────────────────────────────────────────────────
            var logCard = new CardPanel { CornerRadius = 12 };
            logCard.Dock = DockStyle.Fill;
            _logBox = new RichTextBox { Dock = DockStyle.Fill, BackColor = Theme.Terminal, ForeColor = Theme.TermFg, Font = Theme.FontMono, ReadOnly = true, BorderStyle = BorderStyle.None, ScrollBars = RichTextBoxScrollBars.Vertical, Padding = new Padding(10) };
            logCard.Controls.Add(_logBox);

            var logWrap = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG, Padding = new Padding(16, 8, 16, 16) };
            logWrap.Controls.Add(logCard);

            Controls.Add(logWrap);
            Controls.Add(hdrWrap);
        }

        public void Append(string msg, string tag)
        {
            if (InvokeRequired) { Invoke(() => Append(msg, tag)); return; }
            string ts = DateTime.Now.ToString("HH:mm:ss");
            _entries.Add((tag, ts, msg));
            UpdateStats();
            if (_filter == "all" || _filter == tag) WriteEntry(ts, msg, tag);
        }

        private void WriteEntry(string ts, string msg, string tag)
        {
            Color col = tag switch { "success" => Theme.Success, "error" => Theme.Danger, "info" => Theme.SubText, _ => Theme.TermFg };
            _logBox.SelectionColor = Color.FromArgb(100, 150, 200); _logBox.AppendText($"[{ts}]  ");
            _logBox.SelectionColor = col; _logBox.AppendText(msg + "\n");
            _logBox.ScrollToCaret();
        }

        private void SetFilter(string key)
        {
            _filter = key;
            foreach (var (k, b) in _filterBtns)
            {
                b.BaseColor  = k == key ? Theme.Accent : Theme.Panel;
                b.HoverColor = k == key ? Theme.AccentHv : Theme.Border;
                b.ForeColor  = k == key ? Color.White : Theme.Text;
                b.Invalidate();
            }
            _logBox.Clear();
            foreach (var (tag, ts, msg) in _entries)
                if (_filter == "all" || _filter == tag) WriteEntry(ts, msg, tag);
        }

        private void Clear() { _entries.Clear(); _logBox.Clear(); UpdateStats(); }

        private void UpdateStats()
        {
            int total = _entries.Count, s = 0, err = 0, info = 0;
            foreach (var (tag, _, _) in _entries) { if (tag == "success") s++; else if (tag == "error") err++; else if (tag == "info") info++; }
            _totalLbl.Text = $"{total} Total"; _successLbl.Text = $"{s} Success";
            _errorLbl.Text = $"{err} Errors";  _infoLbl.Text    = $"{info} Info";
        }

        private void Export()
        {
            using var dlg = new SaveFileDialog { Filter = "Text files|*.txt|All files|*.*", FileName = $"animepahe_log_{DateTime.Now:yyyyMMdd_HHmmss}.txt" };
            if (dlg.ShowDialog() != DialogResult.OK) return;
            File.WriteAllLines(dlg.FileName, _entries.Select(e => $"[{e.ts}] [{e.tag.ToUpper(),-7}] {e.msg}"));
        }

        private static Label StatLbl(string text, Color fg, int left) =>
            new Label { Text = text, Font = Theme.FontSm, ForeColor = fg, BackColor = Color.Transparent, Left = left, AutoSize = true };
    }
}
