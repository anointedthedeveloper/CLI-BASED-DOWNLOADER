using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Shapes;
using System.IO;
using System.Diagnostics;
using System.Windows.Forms;

namespace Animedownloader
{
    public partial class MainWindow : Window
    {
        private SearchHelper _searchHelper = null!;
        private DownloadHelper _downloadHelper = null!;
        private FlareSolverrHelper _flareSolverrHelper = null!;

        private List<string> _animeCatalog = new List<string>
        {
            "Naruto", "One Piece", "Bleach", "Attack on Titan",
            "Demon Slayer", "Jujutsu Kaisen", "My Hero Academia",
            "Spy x Family", "Tokyo Revengers", "Hunter x Hunter",
        };

        private string _selectedAnimeTitle = "";
        private string _selectedResolution = "1080p";
        private List<string> _recentSearches = new List<string>();

        public MainWindow()
        {
            InitializeComponent();

            var rootDir = AppDomain.CurrentDomain.BaseDirectory;
            _searchHelper = new SearchHelper(rootDir);
            _downloadHelper = new DownloadHelper(rootDir);
            _flareSolverrHelper = new FlareSolverrHelper(rootDir);

            InitializeUI();
        }

        private void InitializeUI()
        {
            SearchTextBox.Foreground = (Brush)FindResource("TextBrush");
            SearchTextBox.CaretBrush = (Brush)FindResource("TextBrush");

            var placeholder = new TextBlock 
            { 
                Text = "🔍 Search for anime...", 
                Foreground = (Brush)FindResource("TextSecondaryBrush"),
                Margin = new Thickness(16, 12, 0, 0)
            };

            UpdateFlareSolverrStatus();
        }

        private void NavButton_Click(object sender, RoutedEventArgs e)
        {
            var button = sender as Button;
            if (button?.Tag is string page)
            {
                ShowPage(page);
            }
        }

        private void ShowPage(string pageName)
        {
            HomePage.Visibility = pageName == "Home" ? Visibility.Visible : Visibility.Collapsed;
            DownloadsPage.Visibility = pageName == "Downloads" ? Visibility.Visible : Visibility.Collapsed;
            LibraryPage.Visibility = pageName == "Library" ? Visibility.Visible : Visibility.Collapsed;
            HistoryPage.Visibility = pageName == "History" ? Visibility.Visible : Visibility.Collapsed;
            SettingsPage.Visibility = pageName == "Settings" ? Visibility.Visible : Visibility.Collapsed;

            UpdateNavButtonStates(pageName);
        }

        private void UpdateNavButtonStates(string activePage)
        {
            ResetNavButton(HomeBtn);
            ResetNavButton(DownloadsBtn);
            ResetNavButton(LibraryBtn);
            ResetNavButton(HistoryBtn);
            ResetNavButton(SettingsBtn);

            Button? activeBtn = activePage switch
            {
                "Home" => HomeBtn,
                "Downloads" => DownloadsBtn,
                "Library" => LibraryBtn,
                "History" => HistoryBtn,
                "Settings" => SettingsBtn,
                _ => null
            };

            if (activeBtn != null)
            {
                activeBtn.Background = (Brush)FindResource("AccentBrush");
                activeBtn.Foreground = (Brush)FindResource("TextBrush");
            }
        }

        private void ResetNavButton(Button btn)
        {
            btn.Background = (Brush)FindResource("SurfaceBrush");
            btn.Foreground = (Brush)FindResource("TextSecondaryBrush");
        }

        private void SearchButton_Click(object sender, RoutedEventArgs e)
        {
            var query = SearchTextBox.Text.Trim();
            if (!string.IsNullOrWhiteSpace(query))
            {
                if (!_recentSearches.Contains(query))
                {
                    _recentSearches.Insert(0, query);
                    if (_recentSearches.Count > 10)
                        _recentSearches.RemoveAt(_recentSearches.Count - 1);
                }

                PopulateSearchResults(query);
            }
        }

        private void PopulateSearchResults(string query)
        {
            SearchResultsGrid.Items.Clear();
            RecentSearchesPanel.Children.Clear();

            // Populate recent searches as chips
            foreach (var search in _recentSearches)
            {
                var chip = CreateChip(search);
                RecentSearchesPanel.Children.Add(chip);
            }

            // Filter catalog
            var results = new List<string>();
            foreach (var anime in _animeCatalog)
            {
                if (anime.Contains(query, StringComparison.OrdinalIgnoreCase))
                {
                    results.Add(anime);
                }
            }

            // Create anime cards
            foreach (var anime in results)
            {
                var card = CreateAnimeCard(anime);
                SearchResultsGrid.Items.Add(card);
            }
        }

        private Border CreateChip(string text)
        {
            var chip = new Border
            {
                Background = (Brush)FindResource("SurfaceLightBrush"),
                CornerRadius = new CornerRadius(16),
                Padding = new Thickness(12, 6),
                Margin = new Thickness(0, 0, 8, 0),
            };

            var stackPanel = new StackPanel { Orientation = Orientation.Horizontal };
            var textBlock = new TextBlock 
            { 
                Text = text, 
                Foreground = (Brush)FindResource("TextBrush"),
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(0, 0, 8, 0)
            };
            var closeBtn = new Button
            {
                Content = "✕",
                Background = "Transparent",
                Foreground = (Brush)FindResource("TextSecondaryBrush"),
                BorderThickness = new Thickness(0),
                Padding = new Thickness(0),
                Width = 16,
                Height = 16,
                FontSize = 12,
                VerticalAlignment = VerticalAlignment.Center
            };
            closeBtn.Click += (s, e) => RecentSearchesPanel.Children.Remove(chip);

            stackPanel.Children.Add(textBlock);
            stackPanel.Children.Add(closeBtn);
            chip.Child = stackPanel;

            return chip;
        }

        private Border CreateAnimeCard(string animeTitle)
        {
            var card = new Border
            {
                Background = (Brush)FindResource("SurfaceLightBrush"),
                CornerRadius = new CornerRadius(8),
                Margin = new Thickness(8),
                Width = 140,
                Height = 180,
                Cursor = System.Windows.Input.Cursors.Hand
            };

            var stackPanel = new StackPanel 
            { 
                Orientation = Orientation.Vertical,
                Margin = new Thickness(8),
                VerticalAlignment = VerticalAlignment.Center
            };

            // Placeholder poster
            var posterBg = new Rectangle 
            { 
                Fill = (Brush)FindResource("SurfaceBrush"),
                Height = 120,
                RadiusX = 4,
                RadiusY = 4,
                Margin = new Thickness(0, 0, 0, 8),
                Width = 124
            };

            var textBlock = new TextBlock
            {
                Text = animeTitle,
                Foreground = (Brush)FindResource("TextBrush"),
                TextAlignment = TextAlignment.Center,
                TextWrapping = TextWrapping.Wrap,
                FontWeight = FontWeights.SemiBold,
                FontSize = 12,
                Height = 40
            };

            stackPanel.Children.Add(posterBg);
            stackPanel.Children.Add(textBlock);
            card.Child = stackPanel;

            // Click to select anime
            card.MouseDown += (s, e) =>
            {
                _selectedAnimeTitle = animeTitle;
                ShowDetailsPage(animeTitle);
            };

            return card;
        }

        private void ShowDetailsPage(string animeTitle)
        {
            SearchTextBox.Text = animeTitle;
            HistoryLog.AppendText($"{DateTime.Now:T} Selected: {animeTitle}{Environment.NewLine}");
        }

        private void BrowseFolder_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new FolderBrowserDialog();
            if (dialog.ShowDialog() == DialogResult.OK)
            {
                DownloadFolderTextBox.Text = dialog.SelectedPath;
            }
        }

        private void StartFlareSolverr_Click(object sender, RoutedEventArgs e)
        {
            HistoryLog.AppendText($"{DateTime.Now:T} Starting FlareSolverr...{Environment.NewLine}");
            if (_flareSolverrHelper.Start())
            {
                HistoryLog.AppendText($"{DateTime.Now:T} FlareSolverr started successfully!{Environment.NewLine}");
                UpdateFlareSolverrStatus();
            }
            else
            {
                HistoryLog.AppendText($"{DateTime.Now:T} Failed to start FlareSolverr.{Environment.NewLine}");
            }
        }

        private void UpdateFlareSolverrStatus()
        {
            var status = _flareSolverrHelper.IsRunning() ? "✓ Running on port 8191" : "✗ Not Running";
            FlareSolverrStatus.Text = status;
        }

        protected override void OnClosed(EventArgs e)
        {
            _flareSolverrHelper.Stop();
            base.OnClosed(e);
        }
    }
}
