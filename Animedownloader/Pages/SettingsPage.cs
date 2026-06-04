using System.Drawing;
using System.Windows.Forms;

namespace Animedownloader
{
    public class SettingsPage : Panel
    {
        private readonly AppState _state;

        public SettingsPage(AppState state)
        {
            _state = state;
            Dock = DockStyle.Fill;
            BackColor = Theme.BG;
            DoubleBuffered = true;
            Build();
        }

        private void Build()
        {
            var scroll = new Panel { Dock = DockStyle.Fill, AutoScroll = true, BackColor = Theme.BG };
            var inner  = new FlowLayoutPanel
            {
                FlowDirection = FlowDirection.TopDown, WrapContents = false,
                AutoSize = true, Width = 800,
                BackColor = Theme.BG, Padding = new Padding(32, 20, 32, 32)
            };
            inner.Resize += (s, e) => inner.Width = scroll.ClientSize.Width;

            var titleLbl = new Label { Text = "Settings", Font = Theme.FontXl, ForeColor = Theme.Text, BackColor = Color.Transparent, AutoSize = true, Margin = new Padding(0, 0, 0, 20) };
            inner.Controls.Add(titleLbl);

            // ── CF Bypass ─────────────────────────────────────────────────
            var cfCard = MakeSectionCard("⚡  Cloudflare Bypass", inner.Width - 64);
            string[] bypassOpts = { "curl  (Fast, default)", "undetected-chromedriver  ⭐ (Most reliable)", "FlareSolverr  (External solver service)", "Cloudscraper  (Python library)", "Browser Automation  (Selenium)" };
            string[] bypassVals = { "curl", "uc", "flaresolverr", "cloudscraper", "browser" };
            int ty = 46;
            for (int i = 0; i < bypassOpts.Length; i++)
            {
                string val = bypassVals[i];
                var rb = new RadioButton { Text = bypassOpts[i], Font = Theme.FontDefault, ForeColor = Theme.Text, BackColor = Color.Transparent, Left = 18, Top = ty, AutoSize = true, Checked = _state.BypassMethod == val };
                rb.CheckedChanged += (s, e) => { if (rb.Checked) _state.BypassMethod = val; };
                cfCard.Controls.Add(rb); ty += 28;
            }
            var sep = new Panel { BackColor = Theme.Border, Left = 16, Top = ty, Width = cfCard.Width - 32, Height = 1 }; cfCard.Controls.Add(sep); ty += 10;
            var bwsLbl = new Label { Text = "Browser:", Font = Theme.FontDefault, ForeColor = Theme.Text, BackColor = Color.Transparent, Left = 18, Top = ty + 4, AutoSize = true };
            var bwsCb  = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Font = Theme.FontSm, BackColor = Theme.Panel, ForeColor = Theme.Text, Left = 84, Top = ty, Width = 120 };
            bwsCb.Items.AddRange(new object[] { "chrome", "edge" });
            bwsCb.SelectedItem = _state.BrowserType;
            bwsCb.SelectedIndexChanged += (s, e) => _state.BrowserType = bwsCb.SelectedItem?.ToString() ?? "chrome";
            ty += 34;
            var hlChk = new CheckBox { Text = "Headless mode",  Font = Theme.FontSm, ForeColor = Theme.Text, BackColor = Color.Transparent, Left = 18, Top = ty, Checked = _state.Headless,  AutoSize = true };
            var icChk = new CheckBox { Text = "Incognito mode", Font = Theme.FontSm, ForeColor = Theme.Text, BackColor = Color.Transparent, Left = 160, Top = ty, Checked = _state.Incognito, AutoSize = true };
            hlChk.CheckedChanged += (s, e) => _state.Headless   = hlChk.Checked;
            icChk.CheckedChanged += (s, e) => _state.Incognito  = icChk.Checked;
            ty += 30;
            cfCard.Height = ty + 12;
            cfCard.Controls.AddRange(new Control[] { bwsLbl, bwsCb, hlChk, icChk });
            inner.Controls.Add(cfCard);

            // ── Downloads ─────────────────────────────────────────────────
            var dlCard = MakeSectionCard("⬇  Downloads", inner.Width - 64);
            dlCard.Height = 100;
            var dlLbl  = new Label { Text = "Max concurrent downloads:", Font = Theme.FontDefault, ForeColor = Theme.Text, BackColor = Color.Transparent, Left = 18, Top = 46, AutoSize = true };
            var dlCb   = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Font = Theme.FontDefault, BackColor = Theme.Panel, ForeColor = Theme.Text, Left = 230, Top = 42, Width = 70 };
            dlCb.Items.AddRange(new object[] { "1", "2", "3", "4", "5" });
            dlCb.SelectedItem = _state.MaxWorkers.ToString();
            dlCb.SelectedIndexChanged += (s, e) => { if (int.TryParse(dlCb.SelectedItem?.ToString(), out int v)) _state.MaxWorkers = v; };
            var dlHint = new Label { Text = "More workers = faster batch downloads, but uses more bandwidth.", Font = Theme.FontXs, ForeColor = Theme.SubText, BackColor = Color.Transparent, Left = 18, Top = 72, AutoSize = true };
            dlCard.Controls.AddRange(new Control[] { dlLbl, dlCb, dlHint });
            inner.Controls.Add(dlCard);

            // ── About ─────────────────────────────────────────────────────
            var aboutCard = MakeSectionCard("ℹ  About", inner.Width - 64);
            string[] lines =
            {
                "AnimePahe Downloader  —  C# Edition",
                "Version 1.0  ·  White & Blue Theme",
                "",
                "Download anime from AnimePahe easily.",
                "  1. Browse page → paste URL → Fetch episodes",
                "  2. Select episodes, choose quality & audio",
                "  3. Downloads page → set save folder → Start Download",
                "",
                "If Cloudflare blocks you:",
                "  • Use undetected-chromedriver (best success rate)",
                "  • Or run FlareSolverr and click Solve CF on Downloads page",
            };
            int ay = 44;
            foreach (var line in lines)
            {
                bool isSub = line.StartsWith("  ") || line == "";
                var l = new Label { Text = line, Font = isSub ? Theme.FontXs : Theme.FontSm, ForeColor = isSub ? Theme.SubText : Theme.Text, BackColor = Color.Transparent, Left = 18, Top = ay, AutoSize = true };
                aboutCard.Controls.Add(l);
                ay += string.IsNullOrEmpty(line) ? 8 : 20;
            }
            aboutCard.Height = ay + 14;
            inner.Controls.Add(aboutCard);

            scroll.Controls.Add(inner);
            Controls.Add(scroll);
        }

        private static CardPanel MakeSectionCard(string title, int width)
        {
            var card = new CardPanel { Width = width, Height = 120, CornerRadius = 12, Margin = new Padding(0, 0, 0, 16) };
            var lbl  = new Label { Text = title, Font = Theme.FontBold, ForeColor = Theme.Accent, BackColor = Color.Transparent, Left = 18, Top = 14, AutoSize = true };
            var sep  = new Panel { BackColor = Theme.Border, Left = 16, Top = 36, Width = width - 32, Height = 1 };
            card.Controls.AddRange(new Control[] { lbl, sep });
            return card;
        }
    }
}
