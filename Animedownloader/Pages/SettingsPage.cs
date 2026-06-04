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
            Build();
        }

        private void Build()
        {
            var scroll = new Panel { Dock = DockStyle.Fill, BackColor = Theme.BG, AutoScroll = true };

            var inner = new FlowLayoutPanel { FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoSize = true, Dock = DockStyle.Top, BackColor = Theme.BG, Padding = new Padding(32, 20, 32, 20) };

            var titleLbl = new Label { Text = "Settings", Font = Theme.FontLg, ForeColor = Theme.Text, BackColor = Theme.BG, AutoSize = true, Margin = new Padding(0, 0, 0, 18) };
            inner.Controls.Add(titleLbl);

            // ── CF Bypass ─────────────────────────────────────────────────
            var cfCard = MakeSectionCard("⚡  Cloudflare Bypass", 200);
            string[] bypassOpts = { "curl  (Fast, default)", "undetected-chromedriver  ⭐ (Most reliable)", "FlareSolverr  (External solver)", "Cloudscraper  (Python library)", "Browser Automation  (Selenium)" };
            string[] bypassVals = { "curl", "uc", "flaresolverr", "cloudscraper", "browser" };
            for (int i = 0; i < bypassOpts.Length; i++)
            {
                string val = bypassVals[i];
                var rb = new RadioButton { Text = bypassOpts[i], Font = Theme.FontDefault, ForeColor = Theme.Text, BackColor = Theme.Card, Left = 16, Top = 46 + i * 26, AutoSize = true, Checked = _state.BypassMethod == val };
                rb.CheckedChanged += (s, e) => { if (rb.Checked) _state.BypassMethod = val; };
                cfCard.Controls.Add(rb);
            }
            var browserLbl = new Label { Text = "Browser:", Font = Theme.FontDefault, ForeColor = Theme.Text, BackColor = Theme.Card, Left = 16, Top = 186, AutoSize = true };
            var browserCb  = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Font = Theme.FontSm, BackColor = Theme.Panel, ForeColor = Theme.Text, Left = 82, Top = 182, Width = 110 };
            browserCb.Items.AddRange(new object[] { "chrome", "edge" });
            browserCb.SelectedItem = _state.BrowserType;
            browserCb.SelectedIndexChanged += (s, e) => _state.BrowserType = browserCb.SelectedItem?.ToString() ?? "chrome";
            var headlessChk = new CheckBox { Text = "Headless mode", Font = Theme.FontSm, ForeColor = Theme.Text, BackColor = Theme.Card, Left = 16, Top = 212, Checked = _state.Headless, AutoSize = true };
            headlessChk.CheckedChanged += (s, e) => _state.Headless = headlessChk.Checked;
            var incognitoChk = new CheckBox { Text = "Incognito mode", Font = Theme.FontSm, ForeColor = Theme.Text, BackColor = Theme.Card, Left = 160, Top = 212, Checked = _state.Incognito, AutoSize = true };
            incognitoChk.CheckedChanged += (s, e) => _state.Incognito = incognitoChk.Checked;
            cfCard.Height = 246;
            cfCard.Controls.AddRange(new Control[] { browserLbl, browserCb, headlessChk, incognitoChk });
            inner.Controls.Add(cfCard);

            // ── Downloads ─────────────────────────────────────────────────
            var dlCard = MakeSectionCard("⬇  Downloads", 90);
            var dlLbl  = new Label { Text = "Max concurrent downloads:", Font = Theme.FontDefault, ForeColor = Theme.Text, BackColor = Theme.Card, Left = 16, Top = 46, AutoSize = true };
            var dlCb   = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Font = Theme.FontDefault, BackColor = Theme.Panel, ForeColor = Theme.Text, Left = 218, Top = 42, Width = 70 };
            dlCb.Items.AddRange(new object[] { "1", "2", "3", "4", "5" });
            dlCb.SelectedItem = _state.MaxWorkers.ToString();
            dlCb.SelectedIndexChanged += (s, e) => { if (int.TryParse(dlCb.SelectedItem?.ToString(), out int v)) _state.MaxWorkers = v; };
            var dlHint = new Label { Text = "More workers = faster batch downloads, but uses more bandwidth.", Font = Theme.FontXs, ForeColor = Theme.SubText, BackColor = Theme.Card, Left = 16, Top = 70, AutoSize = true };
            dlCard.Controls.AddRange(new Control[] { dlLbl, dlCb, dlHint });
            inner.Controls.Add(dlCard);

            // ── About ─────────────────────────────────────────────────────
            var aboutCard = MakeSectionCard("ℹ  About", 190);
            string[] lines = {
                "AnimePahe Downloader  —  C# Edition",
                "Version 1.0",
                "",
                "Download anime from AnimePahe easily.",
                "  1. Browse page → paste URL → Fetch episodes",
                "  2. Select episodes, choose quality & audio",
                "  3. Downloads page → set save folder → Start Download",
                "",
                "If Cloudflare blocks you:",
                "  • Use undetected-chromedriver (best success rate)",
                "  • Or run FlareSolverr and use the Solve CF button",
            };
            int ty = 44;
            foreach (var line in lines)
            {
                var l = new Label { Text = line, Font = line.StartsWith(" ") || line == "" ? Theme.FontXs : Theme.FontSm, ForeColor = line.StartsWith(" ") || line == "" ? Theme.SubText : Theme.Text, BackColor = Theme.Card, Left = 16, Top = ty, AutoSize = true };
                aboutCard.Controls.Add(l);
                ty += string.IsNullOrEmpty(line) ? 8 : 18;
            }
            aboutCard.Height = ty + 16;
            inner.Controls.Add(aboutCard);

            scroll.Controls.Add(inner);
            Controls.Add(scroll);
        }

        private static Panel MakeSectionCard(string title, int height)
        {
            var wrap = new Panel { BackColor = Theme.BG, Width = 700, Height = height + 4, Margin = new Padding(0, 0, 0, 14) };
            var card = new Panel { BackColor = Theme.Card, Left = 0, Top = 2, Width = 700, Height = height };
            var titleLbl = new Label { Text = title, Font = Theme.FontBold, ForeColor = Theme.Accent, BackColor = Theme.Card, Left = 16, Top = 14, AutoSize = true };
            card.Controls.Add(titleLbl);
            wrap.Controls.Add(card);
            return card;
        }
    }
}
