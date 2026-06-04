using System.Drawing;
using System.Windows.Forms;

namespace Animedownloader
{
    public class LogPage : Panel
    {
        private readonly AppState _state;
        private readonly List<(string tag, string ts, string msg)> _entries = new();
        private RichTextBox _logBox   = null!;
        private string      _filter   = "all";
        private Label       _totalLbl = null!, _successLbl = null!, _errorLbl = null!, _infoLbl = null!;
        private readonly Dictionary<string, Button> _filterBtns = new();

        public LogPage(AppState state)
        {
            _state = state;
            Dock = DockStyle.Fill;
            BackColor = Theme.BG;
            Build();
        }

        private void Build()
        {
            // ── header card ────────────────────────────────────────────────
            var hdr = new Panel { BackColor = Theme.Card, Height = 110, Dock = DockStyle.Top, Padding = new Padding(18, 12, 18, 8) };
            var titleLbl = new Label { Text = "Activity Log", Font = Theme.FontLg, ForeColor = Theme.Text, BackColor = Theme.Card, Left = 18, Top = 12, AutoSize = true };
            var subLbl   = new Label { Text = "Full history of fetches, downloads and errors.", Font = Theme.FontSm, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 18, Top = 42, AutoSize = true };

            // filter buttons
            string[] filters = { "All", "✓ Success", "✗ Errors", "ℹ Info" };
            string[] keys    = { "all", "success", "error", "info" };
            int bx = 18;
            for (int i = 0; i < filters.Length; i++)
            {
                string key = keys[i];
                var btn = new Button { Text = filters[i], BackColor = key == "all" ? Theme.Accent : Theme.Panel, ForeColor = key == "all" ? Color.White : Theme.Text, FlatStyle = FlatStyle.Flat, Font = Theme.FontXs, Height = 26, AutoSize = true, Left = bx, Top = 68, Padding = new Padding(8, 0, 8, 0), FlatAppearance = { BorderSize = 0 } };
                btn.Click += (s, e) => SetFilter(key);
                _filterBtns[key] = btn;
                hdr.Controls.Add(btn);
                bx += btn.PreferredSize.Width + 6;
            }
            bx += 12;
            var exportBtn = new Button { Text = "💾 Export", BackColor = Theme.Panel, ForeColor = Theme.Text, FlatStyle = FlatStyle.Flat, Font = Theme.FontXs, Height = 26, AutoSize = true, Left = bx, Top = 68, Padding = new Padding(8, 0, 8, 0), FlatAppearance = { BorderSize = 0 } };
            exportBtn.Click += (s, e) => Export();
            var clearBtn  = new Button { Text = "🗑 Clear",  BackColor = Theme.Panel, ForeColor = Theme.Text, FlatStyle = FlatStyle.Flat, Font = Theme.FontXs, Height = 26, AutoSize = true, Left = bx + 90, Top = 68, Padding = new Padding(8, 0, 8, 0), FlatAppearance = { BorderSize = 0 } };
            clearBtn.Click += (s, e) => Clear();
            hdr.Controls.AddRange(new Control[] { titleLbl, subLbl, exportBtn, clearBtn });

            // ── stats bar ──────────────────────────────────────────────────
            var statsBar = new Panel { BackColor = Theme.Card, Height = 38, Dock = DockStyle.Top };
            _totalLbl   = StatLabel("0 Total",   Theme.SubText, 16);
            _successLbl = StatLabel("0 Success", Theme.Success, 100);
            _errorLbl   = StatLabel("0 Errors",  Theme.Danger,  190);
            _infoLbl    = StatLabel("0 Info",    Theme.Accent,  270);
            statsBar.Controls.AddRange(new Control[] { _totalLbl, _successLbl, _errorLbl, _infoLbl });

            // ── log box ────────────────────────────────────────────────────
            _logBox = new RichTextBox { Dock = DockStyle.Fill, BackColor = Theme.Terminal, ForeColor = Theme.TermFg, Font = Theme.FontMono, ReadOnly = true, BorderStyle = BorderStyle.None, ScrollBars = RichTextBoxScrollBars.Vertical };

            Controls.Add(_logBox);
            Controls.Add(statsBar);
            Controls.Add(hdr);
        }

        public void Append(string msg, string tag)
        {
            if (InvokeRequired) { Invoke(() => Append(msg, tag)); return; }
            string ts = DateTime.Now.ToString("HH:mm:ss");
            _entries.Add((tag, ts, msg));
            UpdateStats();
            if (_filter == "all" || _filter == tag)
                WriteEntry(ts, msg, tag);
        }

        private void WriteEntry(string ts, string msg, string tag)
        {
            Color col = tag switch { "success" => Theme.Success, "error" => Theme.Danger, "info" => Theme.SubText, _ => Theme.TermFg };
            _logBox.SelectionColor = Theme.Border; _logBox.AppendText($"[{ts}]  ");
            _logBox.SelectionColor = col;          _logBox.AppendText(msg + "\n");
            _logBox.ScrollToCaret();
        }

        private void SetFilter(string key)
        {
            _filter = key;
            foreach (var (k, b) in _filterBtns) { b.BackColor = k == key ? Theme.Accent : Theme.Panel; b.ForeColor = k == key ? Color.White : Theme.Text; }
            _logBox.Clear();
            foreach (var (tag, ts, msg) in _entries)
                if (_filter == "all" || _filter == tag) WriteEntry(ts, msg, tag);
        }

        private void Clear() { _entries.Clear(); _logBox.Clear(); UpdateStats(); }

        private void UpdateStats()
        {
            int total = _entries.Count, success = 0, error = 0, info = 0;
            foreach (var (tag, _, _) in _entries) { if (tag == "success") success++; else if (tag == "error") error++; else if (tag == "info") info++; }
            _totalLbl.Text   = $"{total} Total";
            _successLbl.Text = $"{success} Success";
            _errorLbl.Text   = $"{error} Errors";
            _infoLbl.Text    = $"{info} Info";
        }

        private void Export()
        {
            using var dlg = new SaveFileDialog { Filter = "Text files|*.txt|All files|*.*", FileName = $"animepahe_log_{DateTime.Now:yyyyMMdd_HHmmss}.txt" };
            if (dlg.ShowDialog() != DialogResult.OK) return;
            File.WriteAllLines(dlg.FileName, _entries.Select(e => $"[{e.ts}] [{e.tag.ToUpper(),-7}] {e.msg}"));
        }

        private static Label StatLabel(string text, Color fg, int left) => new Label { Text = text, Font = Theme.FontSm, ForeColor = fg, BackColor = Theme.Card, Left = left, Top = 10, AutoSize = true };
    }
}
