using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Windows.Forms;

namespace Animedownloader
{
    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }

    public class MainForm : Form
    {
        private Panel _sidebarPanel = null!;
        private Panel _contentPanel = null!;
        private Button _homeButton = null!;
        private Button _downloadsButton = null!;
        private Button _libraryButton = null!;
        private Button _historyButton = null!;
        private Button _settingsButton = null!;

        private Panel _homePage = null!;
        private Panel _detailsPage = null!;
        private Panel _downloadsPage = null!;
        private Panel _libraryPage = null!;
        private Panel _historyPage = null!;
        private Panel _settingsPage = null!;

        private readonly List<string> _animeCatalog = new()
        {
            "Naruto", "One Piece", "Bleach", "Attack on Titan",
            "Demon Slayer", "Jujutsu Kaisen", "My Hero Academia",
            "Spy x Family", "Tokyo Revengers", "Hunter x Hunter",
        };

        private ListBox _recentSearches = null!;
        private ListBox _searchResults = null!;
        private TextBox _searchTextBox = null!;
        private TextBox _urlTextBox = null!;
        private FlowLayoutPanel _downloadQueuePanel = null!;
        private TreeView _libraryTree = null!;
        private TextBox _historyLog = null!;
        private TextBox _downloadFolderTextBox = null!;
        private RadioButton _quality720p = null!;
        private RadioButton _quality1080p = null!;
        private NumericUpDown _concurrentDownloads = null!;
        private ComboBox _themeComboBox = null!;
        private Label _detailsTitle = null!;
        private Label _detailsEpisodeCount = null!;
        private FlowLayoutPanel _detailsResolutions = null!;
        private FlowLayoutPanel _detailsEpisodeList = null!;
        private TextBox _detailsDescription = null!;
        private PictureBox _detailsPoster = null!;
        private string _selectedAnimeTitle = "";
        private string _selectedResolution = "1080p";
        private int _currentEpisodeCount = 12;
        private Label _flareSolverInfoLabel = null!;

        private SearchHelper _searchHelper = null!;
        private DownloadHelper _downloadHelper = null!;
        private FlareSolverrHelper _flareSolverrHelper = null!;

        public MainForm()
        {
            Text = "AnimeDownloader";
            Size = new Size(1020, 680);
            MinimumSize = new Size(900, 620);
            StartPosition = FormStartPosition.CenterScreen;
            BackColor = Color.White;

            var rootDir = AppDomain.CurrentDomain.BaseDirectory;
            _searchHelper = new SearchHelper(rootDir);
            _downloadHelper = new DownloadHelper(rootDir);
            _flareSolverrHelper = new FlareSolverrHelper(rootDir);

            _sidebarPanel = new Panel
            {
                Dock = DockStyle.Left,
                Width = 180,
                BackColor = Color.FromArgb(240, 249, 255),
            };

            _contentPanel = new Panel
            {
                Dock = DockStyle.Fill,
                BackColor = Color.White,
            };

            var logo = new Label
            {
                Text = "AnimeDownloader",
                Font = new Font("Segoe UI Semibold", 14F, FontStyle.Bold, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(10, 84, 153),
                AutoSize = false,
                TextAlign = ContentAlignment.MiddleCenter,
                Dock = DockStyle.Top,
                Height = 80,
                Padding = new Padding(12, 15, 12, 0),
            };

            _homeButton = CreateSidebarButton("Home", 0);
            _downloadsButton = CreateSidebarButton("Downloads", 1);
            _libraryButton = CreateSidebarButton("Library", 2);
            _historyButton = CreateSidebarButton("History", 3);
            _settingsButton = CreateSidebarButton("Settings", 4);

            _sidebarPanel.Controls.AddRange(new Control[]
            {
                _settingsButton,
                _historyButton,
                _libraryButton,
                _downloadsButton,
                _homeButton,
                logo,
            });

            _homePage = CreatePagePanel();
            _detailsPage = CreatePagePanel();
            _downloadsPage = CreatePagePanel();
            _libraryPage = CreatePagePanel();
            _historyPage = CreatePagePanel();
            _settingsPage = CreatePagePanel();

            InitializeHomePage();
            InitializeDetailsPage();
            InitializeDownloadsPage();
            InitializeLibraryPage();
            InitializeHistoryPage();
            InitializeSettingsPage();

            _contentPanel.Controls.AddRange(new Control[]
            {
                _homePage,
                _detailsPage,
                _downloadsPage,
                _libraryPage,
                _historyPage,
                _settingsPage,
            });

            Controls.Add(_contentPanel);
            Controls.Add(_sidebarPanel);

            ShowPage(_homePage);
        }

        private Button CreateSidebarButton(string text, int topIndex)
        {
            var btn = new Button
            {
                Text = text,
                Font = new Font("Segoe UI", 10F, FontStyle.Regular, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(10, 84, 153),
                BackColor = Color.FromArgb(240, 249, 255),
                FlatStyle = FlatStyle.Flat,
                TextAlign = ContentAlignment.MiddleLeft,
                Size = new Size(180, 50),
                Location = new Point(0, 80 + topIndex * 52),
                Cursor = Cursors.Hand,
            };
            btn.FlatAppearance.BorderSize = 0;
            btn.Click += (sender, args) => OnNavigationClicked(text);
            return btn;
        }

        private void InitializeHomePage()
        {
            var header = CreatePageHeader("Home");
            _homePage.Controls.Add(header);

            _searchTextBox = new TextBox
            {
                PlaceholderText = "Search anime by name...",
                Font = new Font("Segoe UI", 11F, FontStyle.Regular, GraphicsUnit.Point),
                Size = new Size(420, 36),
                Location = new Point(28, 96),
                BorderStyle = BorderStyle.FixedSingle,
                BackColor = Color.FromArgb(247, 249, 255),
            };

            var searchButton = new Button
            {
                Text = "Search",
                Font = new Font("Segoe UI", 10F, FontStyle.Bold, GraphicsUnit.Point),
                BackColor = Color.FromArgb(10, 84, 153),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Size = new Size(120, 36),
                Location = new Point(462, 96),
                Cursor = Cursors.Hand,
            };
            searchButton.FlatAppearance.BorderSize = 0;
            searchButton.Click += (sender, args) => SearchAnime();

            _urlTextBox = new TextBox
            {
                PlaceholderText = "Or paste anime URL...",
                Font = new Font("Segoe UI", 11F, FontStyle.Regular, GraphicsUnit.Point),
                Size = new Size(420, 36),
                Location = new Point(28, 148),
                BorderStyle = BorderStyle.FixedSingle,
                BackColor = Color.FromArgb(247, 249, 255),
            };

            var urlButton = new Button
            {
                Text = "Open",
                Font = new Font("Segoe UI", 10F, FontStyle.Bold, GraphicsUnit.Point),
                BackColor = Color.FromArgb(10, 84, 153),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Size = new Size(120, 36),
                Location = new Point(462, 148),
                Cursor = Cursors.Hand,
            };
            urlButton.FlatAppearance.BorderSize = 0;
            urlButton.Click += (sender, args) => OpenAnimeUrl();

            var resultLabel = new Label
            {
                Text = "Search Results",
                Font = new Font("Segoe UI Semibold", 12F, FontStyle.Bold, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(24, 43, 80),
                Location = new Point(28, 196),
                AutoSize = true,
            };

            _searchResults = new ListBox
            {
                Font = new Font("Segoe UI", 10F, FontStyle.Regular, GraphicsUnit.Point),
                ItemHeight = 18,
                Location = new Point(28, 226),
                Size = new Size(554, 160),
                BorderStyle = BorderStyle.FixedSingle,
            };
            _searchResults.DoubleClick += (sender, args) => OpenSelectedSearch();

            _searchTextBox.TextChanged += (sender, args) => PopulateSearchResults(_searchTextBox.Text);

            var recentLabel = new Label
            {
                Text = "Recent Searches",
                Font = new Font("Segoe UI Semibold", 12F, FontStyle.Bold, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(24, 43, 80),
                Location = new Point(28, 396),
                AutoSize = true,
            };

            _recentSearches = new ListBox
            {
                Font = new Font("Segoe UI", 10F, FontStyle.Regular, GraphicsUnit.Point),
                ItemHeight = 18,
                Location = new Point(28, 426),
                Size = new Size(554, 160),
                BorderStyle = BorderStyle.FixedSingle,
            };
            _recentSearches.Items.AddRange(new object[] { "Naruto", "One Piece", "Bleach" });
            _recentSearches.DoubleClick += (sender, args) => OpenSelectedRecent();

            _homePage.Controls.Add(_searchTextBox);
            _homePage.Controls.Add(searchButton);
            _homePage.Controls.Add(_urlTextBox);
            _homePage.Controls.Add(urlButton);
            _homePage.Controls.Add(resultLabel);
            _homePage.Controls.Add(_searchResults);
            _homePage.Controls.Add(recentLabel);
            _homePage.Controls.Add(_recentSearches);
            PopulateSearchResults(string.Empty);
        }

        private void InitializeDetailsPage()
        {
            var header = CreatePageHeader("Anime Details");
            _detailsPage.Controls.Add(header);

            var backButton = new Button
            {
                Text = "← Back",
                Font = new Font("Segoe UI", 9F, FontStyle.Regular, GraphicsUnit.Point),
                BackColor = Color.FromArgb(235, 241, 248),
                ForeColor = Color.FromArgb(10, 84, 153),
                FlatStyle = FlatStyle.Flat,
                Size = new Size(80, 30),
                Location = new Point(28, 96),
                Cursor = Cursors.Hand,
            };
            backButton.FlatAppearance.BorderSize = 0;
            backButton.Click += (sender, args) => ShowPage(_homePage);

            _detailsPoster = new PictureBox
            {
                Size = new Size(210, 300),
                Location = new Point(28, 144),
                BackColor = Color.FromArgb(237, 245, 255),
                BorderStyle = BorderStyle.FixedSingle,
                SizeMode = PictureBoxSizeMode.CenterImage,
            };

            _detailsTitle = new Label
            {
                Text = "Anime Title",
                Font = new Font("Segoe UI Semibold", 18F, FontStyle.Bold, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(10, 84, 153),
                Location = new Point(256, 148),
                AutoSize = true,
            };

            _detailsEpisodeCount = new Label
            {
                Text = "220 Episodes",
                Font = new Font("Segoe UI", 10F, FontStyle.Regular, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(90, 105, 130),
                Location = new Point(256, 190),
                AutoSize = true,
            };

            _detailsResolutions = new FlowLayoutPanel
            {
                Location = new Point(256, 220),
                Size = new Size(520, 48),
                AutoSize = true,
            };
            _detailsResolutions.Controls.Add(CreateResolutionButton("480p"));
            _detailsResolutions.Controls.Add(CreateResolutionButton("720p"));
            _detailsResolutions.Controls.Add(CreateResolutionButton("1080p"));

            _detailsDescription = new TextBox
            {
                Text = "Description will appear here after selecting an anime. It includes series summary, genres, and release info.",
                Font = new Font("Segoe UI", 10F, FontStyle.Regular, GraphicsUnit.Point),
                Location = new Point(256, 280),
                Size = new Size(520, 100),
                Multiline = true,
                ReadOnly = true,
                BackColor = Color.FromArgb(248, 249, 255),
                BorderStyle = BorderStyle.FixedSingle,
            };

            var episodesLabel = new Label
            {
                Text = "Episodes",
                Font = new Font("Segoe UI Semibold", 12F, FontStyle.Bold, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(24, 43, 80),
                Location = new Point(256, 398),
                AutoSize = true,
            };

            _detailsEpisodeList = new FlowLayoutPanel
            {
                Location = new Point(256, 430),
                Size = new Size(520, 210),
                AutoScroll = true,
                FlowDirection = FlowDirection.TopDown,
                WrapContents = false,
            };

            BuildEpisodeList(_currentEpisodeCount);

            _detailsPage.Controls.Add(header);
            _detailsPage.Controls.Add(backButton);
            _detailsPage.Controls.Add(_detailsPoster);
            _detailsPage.Controls.Add(_detailsTitle);
            _detailsPage.Controls.Add(_detailsEpisodeCount);
            _detailsPage.Controls.Add(_detailsResolutions);
            _detailsPage.Controls.Add(_detailsDescription);
            _detailsPage.Controls.Add(episodesLabel);
            _detailsPage.Controls.Add(_detailsEpisodeList);
        }

        private void InitializeDownloadsPage()
        {
            var header = CreatePageHeader("Downloads");
            _downloadsPage.Controls.Add(header);

            var infoLabel = new Label
            {
                Text = "Current Downloads",
                Font = new Font("Segoe UI Semibold", 12F, FontStyle.Bold, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(24, 43, 80),
                Location = new Point(28, 96),
                AutoSize = true,
            };

            _downloadQueuePanel = new FlowLayoutPanel
            {
                Location = new Point(28, 132),
                Size = new Size(760, 510),
                AutoScroll = true,
                FlowDirection = FlowDirection.TopDown,
                WrapContents = false,
            };

            _downloadQueuePanel.Controls.Add(CreateDownloadCard("Naruto EP 20", 70, Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "videos", "anime", "Naruto", "Episode 20")));
            _downloadQueuePanel.Controls.Add(CreateDownloadCard("One Piece EP 10", 40, Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "videos", "anime", "One Piece", "Episode 10")));

            _downloadsPage.Controls.Add(header);
            _downloadsPage.Controls.Add(infoLabel);
            _downloadsPage.Controls.Add(_downloadQueuePanel);
        }

        private void InitializeLibraryPage()
        {
            var header = CreatePageHeader("Library");
            _libraryPage.Controls.Add(header);

            _libraryTree = new TreeView
            {
                Font = new Font("Segoe UI", 10F, FontStyle.Regular, GraphicsUnit.Point),
                Location = new Point(28, 96),
                Size = new Size(760, 540),
                BackColor = Color.FromArgb(248, 249, 255),
                BorderStyle = BorderStyle.FixedSingle,
            };

            var narutoNode = new TreeNode("Naruto")
            {
                Nodes =
                {
                    new TreeNode("Episode 1"),
                    new TreeNode("Episode 2"),
                }
            };
            var bleachNode = new TreeNode("Bleach")
            {
                Nodes =
                {
                    new TreeNode("Episode 1"),
                }
            };
            _libraryTree.Nodes.AddRange(new[] { narutoNode, bleachNode });
            _libraryTree.ExpandAll();

            _libraryPage.Controls.Add(header);
            _libraryPage.Controls.Add(_libraryTree);
        }

        private void InitializeHistoryPage()
        {
            var header = CreatePageHeader("History");
            _historyPage.Controls.Add(header);

            _historyLog = new TextBox
            {
                Font = new Font("Segoe UI", 10F, FontStyle.Regular, GraphicsUnit.Point),
                Location = new Point(28, 96),
                Size = new Size(760, 540),
                Multiline = true,
                ReadOnly = true,
                ScrollBars = ScrollBars.Vertical,
                BackColor = Color.FromArgb(248, 249, 255),
                BorderStyle = BorderStyle.FixedSingle,
                Text = "12:30 PM\r\nNaruto EP 12 Downloaded\r\n\r\n12:40 PM\r\nBleach EP 8 Failed\r\nNetwork Error\r\n",
            };

            _historyPage.Controls.Add(header);
            _historyPage.Controls.Add(_historyLog);
        }

        private void InitializeSettingsPage()
        {
            var header = CreatePageHeader("Settings");
            _settingsPage.Controls.Add(header);

            var folderLabel = new Label
            {
                Text = "Download Folder",
                Font = new Font("Segoe UI Semibold", 11F, FontStyle.Bold, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(24, 43, 80),
                Location = new Point(28, 96),
                AutoSize = true,
            };
            _downloadFolderTextBox = new TextBox
            {
                Font = new Font("Segoe UI", 10F, FontStyle.Regular, GraphicsUnit.Point),
                Location = new Point(28, 126),
                Size = new Size(560, 30),
                BackColor = Color.FromArgb(247, 249, 255),
                BorderStyle = BorderStyle.FixedSingle,
                Text = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "videos", "anime"),
            };
            var folderButton = new Button
            {
                Text = "Browse",
                Font = new Font("Segoe UI", 9F, FontStyle.Regular, GraphicsUnit.Point),
                BackColor = Color.FromArgb(10, 84, 153),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Size = new Size(100, 30),
                Location = new Point(602, 126),
                Cursor = Cursors.Hand,
            };
            folderButton.FlatAppearance.BorderSize = 0;
            folderButton.Click += (sender, args) => BrowseDownloadFolder();

            _flareSolverInfoLabel = new Label
            {
                Text = GetFlareSolverrStatusText(),
                Font = new Font("Segoe UI", 9F, FontStyle.Regular, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(90, 105, 130),
                Location = new Point(28, 160),
                AutoSize = true,
            };

            var openFlareButton = new Button
            {
                Text = "Open FlareSolverr Folder",
                Font = new Font("Segoe UI", 9F, FontStyle.Regular, GraphicsUnit.Point),
                BackColor = Color.FromArgb(10, 84, 153),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Size = new Size(180, 30),
                Location = new Point(602, 162),
                Cursor = Cursors.Hand,
            };
            openFlareButton.FlatAppearance.BorderSize = 0;
            openFlareButton.Click += (sender, args) => OpenFlareSolverrFolder();

            var qualityLabel = new Label
            {
                Text = "Default Quality",
                Font = new Font("Segoe UI Semibold", 11F, FontStyle.Bold, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(24, 43, 80),
                Location = new Point(28, 180),
                AutoSize = true,
            };

            _quality720p = new RadioButton
            {
                Text = "720p",
                Font = new Font("Segoe UI", 10F, FontStyle.Regular, GraphicsUnit.Point),
                Location = new Point(28, 210),
                AutoSize = true,
                Checked = false,
            };
            _quality1080p = new RadioButton
            {
                Text = "1080p",
                Font = new Font("Segoe UI", 10F, FontStyle.Regular, GraphicsUnit.Point),
                Location = new Point(120, 210),
                AutoSize = true,
                Checked = true,
            };

            var concurrentLabel = new Label
            {
                Text = "Concurrent Downloads",
                Font = new Font("Segoe UI Semibold", 11F, FontStyle.Bold, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(24, 43, 80),
                Location = new Point(28, 256),
                AutoSize = true,
            };
            _concurrentDownloads = new NumericUpDown
            {
                Font = new Font("Segoe UI", 10F, FontStyle.Regular, GraphicsUnit.Point),
                Location = new Point(28, 286),
                Size = new Size(80, 30),
                Minimum = 1,
                Maximum = 10,
                Value = 3,
                BackColor = Color.FromArgb(247, 249, 255),
            };

            var themeLabel = new Label
            {
                Text = "Theme",
                Font = new Font("Segoe UI Semibold", 11F, FontStyle.Bold, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(24, 43, 80),
                Location = new Point(28, 340),
                AutoSize = true,
            };
            _themeComboBox = new ComboBox
            {
                Font = new Font("Segoe UI", 10F, FontStyle.Regular, GraphicsUnit.Point),
                Location = new Point(28, 370),
                Size = new Size(160, 28),
                DropDownStyle = ComboBoxStyle.DropDownList,
                BackColor = Color.FromArgb(247, 249, 255),
            };
            _themeComboBox.Items.AddRange(new object[] { "Light", "Dark" });
            _themeComboBox.SelectedIndex = 0;

            _settingsPage.Controls.Add(header);
            _settingsPage.Controls.Add(folderLabel);
            _settingsPage.Controls.Add(_downloadFolderTextBox);
            _settingsPage.Controls.Add(folderButton);
            _settingsPage.Controls.Add(_flareSolverInfoLabel);
            _settingsPage.Controls.Add(openFlareButton);
            _settingsPage.Controls.Add(qualityLabel);
            _settingsPage.Controls.Add(_quality720p);
            _settingsPage.Controls.Add(_quality1080p);
            _settingsPage.Controls.Add(concurrentLabel);
            _settingsPage.Controls.Add(_concurrentDownloads);
            _settingsPage.Controls.Add(themeLabel);
            _settingsPage.Controls.Add(_themeComboBox);
        }

        private Panel CreatePagePanel()
        {
            return new Panel
            {
                Dock = DockStyle.Fill,
                BackColor = Color.White,
                Visible = false,
            };
        }

        private Label CreatePageHeader(string text)
        {
            return new Label
            {
                Text = text,
                Font = new Font("Segoe UI Semibold", 18F, FontStyle.Bold, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(10, 84, 153),
                Location = new Point(28, 24),
                AutoSize = true,
            };
        }

        private Button CreateResolutionButton(string text)
        {
            var btn = new Button
            {
                Text = text,
                Font = new Font("Segoe UI", 9F, FontStyle.Bold, GraphicsUnit.Point),
                BackColor = text == _selectedResolution ? Color.FromArgb(10, 84, 153) : Color.FromArgb(235, 241, 248),
                ForeColor = text == _selectedResolution ? Color.White : Color.FromArgb(10, 84, 153),
                FlatStyle = FlatStyle.Flat,
                Size = new Size(90, 34),
                Cursor = Cursors.Hand,
                Margin = new Padding(0, 0, 8, 0),
            };
            btn.FlatAppearance.BorderSize = 0;
            btn.Click += (sender, args) =>
            {
                _selectedResolution = text;
                UpdateResolutionSelection();
            };
            return btn;
        }

        private void UpdateResolutionSelection()
        {
            foreach (Control control in _detailsResolutions.Controls)
            {
                if (control is Button button)
                {
                    if (button.Text == _selectedResolution)
                    {
                        button.BackColor = Color.FromArgb(10, 84, 153);
                        button.ForeColor = Color.White;
                    }
                    else
                    {
                        button.BackColor = Color.FromArgb(235, 241, 248);
                        button.ForeColor = Color.FromArgb(10, 84, 153);
                    }
                }
            }
        }

        private Panel CreateEpisodeCard(int episodeNumber)
        {
            var card = new Panel
            {
                Size = new Size(500, 42),
                BackColor = Color.FromArgb(247, 249, 255),
                BorderStyle = BorderStyle.FixedSingle,
                Margin = new Padding(0, 0, 0, 8),
            };

            var label = new Label
            {
                Text = $"Episode {episodeNumber}",
                Font = new Font("Segoe UI", 10F, FontStyle.Regular, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(24, 43, 80),
                Location = new Point(12, 10),
                AutoSize = true,
            };

            var downloadButton = new Button
            {
                Text = "Download",
                Font = new Font("Segoe UI", 9F, FontStyle.Bold, GraphicsUnit.Point),
                BackColor = Color.FromArgb(10, 84, 153),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Size = new Size(100, 26),
                Location = new Point(380, 8),
                Cursor = Cursors.Hand,
            };
            downloadButton.FlatAppearance.BorderSize = 0;
            downloadButton.Click += (sender, args) => QueueDownload(episodeNumber);

            card.Controls.Add(label);
            card.Controls.Add(downloadButton);
            return card;
        }

        private Panel CreateDownloadCard(string title, int percent, string folderPath)
        {
            var card = new Panel
            {
                Size = new Size(720, 110),
                BackColor = Color.FromArgb(247, 249, 255),
                BorderStyle = BorderStyle.FixedSingle,
                Margin = new Padding(0, 0, 0, 12),
            };

            var titleLabel = new Label
            {
                Text = title,
                Font = new Font("Segoe UI Semibold", 11F, FontStyle.Bold, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(24, 43, 80),
                Location = new Point(12, 12),
                AutoSize = true,
            };

            var progress = new ProgressBar
            {
                Location = new Point(16, 44),
                Size = new Size(560, 22),
                Value = percent,
            };

            var badge = new Label
            {
                Text = $"{percent}%",
                Font = new Font("Segoe UI", 9F, FontStyle.Regular, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(10, 84, 153),
                Location = new Point(590, 48),
                AutoSize = true,
            };

            var pathLabel = new Label
            {
                Text = folderPath,
                Font = new Font("Segoe UI", 8.5F, FontStyle.Regular, GraphicsUnit.Point),
                ForeColor = Color.FromArgb(100, 110, 130),
                Location = new Point(16, 72),
                AutoSize = true,
            };

            card.Controls.Add(titleLabel);
            card.Controls.Add(progress);
            card.Controls.Add(badge);
            card.Controls.Add(pathLabel);
            return card;
        }

        private void ShowPage(Panel page)
        {
            foreach (Control panel in _contentPanel.Controls)
            {
                panel.Visible = false;
            }
            page.Visible = true;
            UpdateSidebarSelection();
        }

        private void ShowDetailsPage(string animeTitle)
        {
            _selectedAnimeTitle = animeTitle;
            _currentEpisodeCount = 12;
            _detailsTitle.Text = animeTitle;
            _detailsEpisodeCount.Text = $"{_currentEpisodeCount} Episodes";
            _detailsDescription.Text = $"{animeTitle} is a popular anime series. Choose the resolution and download episodes from the list below.";
            _detailsPoster.Image = null;
            BuildEpisodeList(_currentEpisodeCount);
            UpdateResolutionSelection();
            ShowPage(_detailsPage);
        }

        private void BuildEpisodeList(int count)
        {
            _detailsEpisodeList.Controls.Clear();
            for (var i = 1; i <= count; i++)
            {
                _detailsEpisodeList.Controls.Add(CreateEpisodeCard(i));
            }
        }

        private void OnNavigationClicked(string page)
        {
            switch (page)
            {
                case "Home":
                    ShowPage(_homePage);
                    break;
                case "Downloads":
                    ShowPage(_downloadsPage);
                    break;
                case "Library":
                    ShowPage(_libraryPage);
                    break;
                case "History":
                    ShowPage(_historyPage);
                    break;
                case "Settings":
                    ShowPage(_settingsPage);
                    break;
            }
        }

        private void SearchAnime()
        {
            var query = _searchTextBox.Text.Trim();
            if (string.IsNullOrWhiteSpace(query))
            {
                MessageBox.Show("Please enter an anime name to search.", "Search", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            if (!_recentSearches.Items.Contains(query))
            {
                _recentSearches.Items.Insert(0, query);
            }

            _selectedAnimeTitle = query;
            _currentEpisodeCount = 12;
            ShowDetailsPage(query);
            PopulateSearchResults(query);
        }

        private void PopulateSearchResults(string query)
        {
            _searchResults.Items.Clear();
            if (string.IsNullOrWhiteSpace(query))
            {
                foreach (var title in _animeCatalog)
                {
                    _searchResults.Items.Add(title);
                }
                return;
            }

            foreach (var title in _animeCatalog)
            {
                if (title.Contains(query, StringComparison.OrdinalIgnoreCase))
                {
                    _searchResults.Items.Add(title);
                }
            }

            if (_searchResults.Items.Count == 0)
            {
                _searchResults.Items.Add("No results found");
            }
        }

        private void OpenSelectedSearch()
        {
            if (_searchResults.SelectedItem is string selected && selected != "No results found")
            {
                _searchTextBox.Text = selected;
                if (!_recentSearches.Items.Contains(selected))
                {
                    _recentSearches.Items.Insert(0, selected);
                }
                _selectedAnimeTitle = selected;
                _currentEpisodeCount = 12;
                ShowDetailsPage(selected);
            }
        }

        private void OpenAnimeUrl()
        {
            var url = _urlTextBox.Text.Trim();
            if (string.IsNullOrWhiteSpace(url))
            {
                MessageBox.Show("Please paste an anime URL.", "Open URL", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            var animeTitle = "Selected Anime";
            if (!_recentSearches.Items.Contains(animeTitle))
            {
                _recentSearches.Items.Insert(0, animeTitle);
            }
            _selectedAnimeTitle = animeTitle;
            _currentEpisodeCount = 12;
            ShowDetailsPage(animeTitle);
        }

        private void OpenSelectedRecent()
        {
            if (_recentSearches.SelectedItem is string selected)
            {
                _selectedAnimeTitle = selected;
                _currentEpisodeCount = 12;
                ShowDetailsPage(selected);
            }
        }

        private void QueueDownload(int episodeNumber)
        {
            if (string.IsNullOrWhiteSpace(_selectedAnimeTitle))
            {
                MessageBox.Show("Please select an anime before downloading an episode.", "Download", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            var folder = GetDefaultDownloadFolder(_selectedAnimeTitle, episodeNumber);
            var downloadCard = CreateDownloadCard($"{_selectedAnimeTitle} EP {episodeNumber}", 0, folder);
            _downloadQueuePanel.Controls.Add(downloadCard);
            _downloadQueuePanel.ScrollControlIntoView(_downloadQueuePanel.Controls[_downloadQueuePanel.Controls.Count - 1]);
            _historyLog.AppendText($"{DateTime.Now:T} Queued {_selectedAnimeTitle} Episode {episodeNumber} → {folder}{Environment.NewLine}");

            // Simulate download progress (in real implementation, integrate with actual downloader)
            var progressBar = downloadCard.Controls[1] as ProgressBar;
            if (progressBar != null)
            {
                var timer = new System.Windows.Forms.Timer();
                var progress = 0;
                timer.Interval = 100;
                timer.Tick += (s, e) =>
                {
                    progress += new Random().Next(1, 5);
                    if (progress >= 100)
                    {
                        progress = 100;
                        timer.Stop();
                        _historyLog.AppendText($"{DateTime.Now:T} Downloaded {_selectedAnimeTitle} Episode {episodeNumber}{Environment.NewLine}");
                    }
                    progressBar.Value = Math.Min(progress, 100);
                    downloadCard.Invalidate();
                };
                timer.Start();
            }
        }

        private string GetDefaultDownloadFolder(string animeTitle, int episodeNumber)
        {
            var baseFolder = _downloadFolderTextBox.Text;
            if (string.IsNullOrWhiteSpace(baseFolder))
            {
                baseFolder = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "videos", "anime");
            }

            return Path.Combine(baseFolder, animeTitle, $"Episode {episodeNumber}");
        }

        private void BrowseDownloadFolder()
        {
            using var dialog = new FolderBrowserDialog
            {
                Description = "Select the base download folder for anime episodes",
                SelectedPath = _downloadFolderTextBox.Text,
                ShowNewFolderButton = true,
            };

            if (dialog.ShowDialog() == DialogResult.OK)
            {
                _downloadFolderTextBox.Text = dialog.SelectedPath;
                _flareSolverInfoLabel.Text = GetFlareSolverrStatusText();
            }
        }

        private string GetFlareSolverrStatusText()
        {
            var basePath = AppDomain.CurrentDomain.BaseDirectory;
            var localPath = Path.Combine(basePath, "flaresolverr_bin", "flaresolverr.exe");
            var siblingPath = Path.GetFullPath(Path.Combine(basePath, "..", "flaresolverr_bin", "flaresolverr.exe"));
            if (File.Exists(localPath))
            {
                return $"FlareSolverr found: {localPath}";
            }
            if (File.Exists(siblingPath))
            {
                return $"FlareSolverr found: {siblingPath}";
            }
            return "FlareSolverr not found. Place flaresolverr.exe into Animedownloader\\flaresolverr_bin or ..\\flaresolverr_bin.";
        }

        private void OpenFlareSolverrFolder()
        {
            var basePath = AppDomain.CurrentDomain.BaseDirectory;
            var localDirectory = Path.Combine(basePath, "flaresolverr_bin");
            var siblingDirectory = Path.GetFullPath(Path.Combine(basePath, "..", "flaresolverr_bin"));
            var target = Directory.Exists(localDirectory) ? localDirectory : Directory.Exists(siblingDirectory) ? siblingDirectory : localDirectory;

            try
            {
                _historyLog.AppendText($"{DateTime.Now:T} Attempting to start FlareSolverr...{Environment.NewLine}");
                if (_flareSolverrHelper.Start())
                {
                    _historyLog.AppendText($"{DateTime.Now:T} FlareSolverr started successfully!{Environment.NewLine}");
                    MessageBox.Show("FlareSolverr started successfully on port 8191.", "FlareSolverr", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    _flareSolverInfoLabel.Text = "✓ FlareSolverr Running on port 8191";
                }
                else
                {
                    _historyLog.AppendText($"{DateTime.Now:T} Failed to start FlareSolverr.{Environment.NewLine}");
                    MessageBox.Show("Could not start FlareSolverr. Check the flaresolverr_bin folder.", "FlareSolverr", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }
            }
            catch (Exception ex)
            {
                _historyLog.AppendText($"{DateTime.Now:T} Error: {ex.Message}{Environment.NewLine}");
                MessageBox.Show($"Error starting FlareSolverr: {ex.Message}", "FlareSolverr", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void UpdateSidebarSelection()
        {
            var defaultColor = Color.FromArgb(240, 249, 255);
            foreach (Button button in new[] { _homeButton, _downloadsButton, _libraryButton, _historyButton, _settingsButton })
            {
                button.BackColor = defaultColor;
            }

            if (_homePage.Visible) _homeButton.BackColor = Color.FromArgb(220, 235, 250);
            if (_downloadsPage.Visible) _downloadsButton.BackColor = Color.FromArgb(220, 235, 250);
            if (_libraryPage.Visible) _libraryButton.BackColor = Color.FromArgb(220, 235, 250);
            if (_historyPage.Visible) _historyButton.BackColor = Color.FromArgb(220, 235, 250);
            if (_settingsPage.Visible) _settingsButton.BackColor = Color.FromArgb(220, 235, 250);
        }
    }
}
