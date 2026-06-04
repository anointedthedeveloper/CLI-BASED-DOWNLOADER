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
            var hdrCard = new CardPanel { Height = 148 };

            var titleLbl = new Label { Text = "Activity Log", Font = new Font("Segoe UI", 15, FontStyle.Bold), ForeColor = Theme.Text, BackColor = Color.Transparent, Left = 24, Top = 20, AutoSize = true };
            var subLbl   = Lbl("Full history of fetches, downloads and errors.", Theme.FontDefault, Theme.SubText, 24, 56);

            // stats
            _totalLbl   = StatLbl("0 Total",   Theme.SubText, 24);
            _successLbl = StatLbl("0 Success", Theme.Success, 130);
            _errorLbl   = StatLbl("0 Errors",  Theme.Danger,  250);
            _infoLbl    = StatLbl("0 Info",    Theme.Accent,  360);
            foreach (var l in new[] { _totalLbl, _successLbl, _errorLbl, _infoLbl }) l.Top = 84;
            hdrCard.Controls.AddRange(new Control[] { titleLbl, subLbl, _totalLbl, _successLbl, _errorLbl, _infoLbl });

            // filter buttons
            (string key, string label)[] filters = { ("all", "All"), ("success", "✓ Success"), ("error", "✗ Errors"), ("info", "ℹ Info") };
            int bx = 24;
            foreach (var (key, label) in filters)
            {
                string k = key;
                var btn = new AccentButton
                {
                    Text = label, Left = bx, Top = 108, Width = 108, Height = 34,
                    BaseColor = k == "all" ? Theme.Accent : Theme.Panel,
                    HoverColor = k == "all" ? Theme.AccentHv : Theme.Border,
                    ForeColor = k == "all" ? Color.White : Theme.Text,
                    Font = Theme.FontSm
                };
                btn.Click += (s, e) => SetFilter(k);
                _filterBtns[key] = btn;
                hdrCard.Controls.Add(btn);
                bx += 114;
            }
            bx += 16;
            var exportBtn = new GhostButton { Text = "💾 Export", Left = bx,       Top = 108, Width = 112, Height = 34, Font = Theme.FontSm, ForeColor = Theme.Accent };
            var clearBtn  = new AccentButton { Text = "🗑 Clear",  Left = bx + 118, Top = 108, Width = 100, Height = 34, Font = Theme.FontSm, BaseColor = Color.FromArgb(220, 232, 255), HoverColor = Theme.Danger, ForeColor = Theme.Danger };
            exportBtn.Click += (s, e) => Export();
            clearBtn.Click  += (s, e) => Clear();
            hdrCard.Controls.AddRange(new Control[] { exportBtn, clearBtn });

            // ── log box ────────────────────────────────────────────────────
            var logCard = new CardPanel { Dock = DockStyle.Fill, CornerRadius = 12 };
            _logBox = new RichTextBox { Dock = DockStyle.Fill, BackColor = Theme.Terminal, ForeColor = Theme.TermFg, Font = Theme.FontMono, ReadOnly = true, BorderStyle = BorderStyle.None, ScrollBars = RichTextBoxScrollBars.Vertical, Padding = new Padding(14) };
            logCard.Controls.Add(_logBox);

            var logWrap = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG, Padding = new Padding(24, 10, 24, 24) };
            logWrap.Controls.Add(logCard);

            Controls.Add(logWrap);
            Controls.Add(Wrap(hdrCard, 164));
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
            _logBox.SelectionColor = Color.FromArgb(90, 140, 200); _logBox.AppendText($"[{ts}]  ");
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

        private static Panel Wrap(CardPanel card, int h)
        {
            var w = new Panel { Dock = DockStyle.Top, Height = h, BackColor = Theme.BG, Padding = new Padding(24, 14, 24, 0) };
            card.Dock = DockStyle.Fill; w.Controls.Add(card); return w;
        }
        private static Label Lbl(string t, Font f, Color fg, int x, int y) => new Label { Text = t, Font = f, ForeColor = fg, BackColor = Color.Transparent, Left = x, Top = y, AutoSize = true };
        private static Label StatLbl(string text, Color fg, int left) => new Label { Text = text, Font = Theme.FontDefault, ForeColor = fg, BackColor = Color.Transparent, Left = left, AutoSize = true };
    }
}
