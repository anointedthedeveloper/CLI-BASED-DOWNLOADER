namespace Animedownloader
{
    public class AppState
    {
        public string Url          { get; set; } = "";
        public string FetchRange   { get; set; } = "all";
        public string Quality      { get; set; } = "Max";
        public string Audio        { get; set; } = "jp (Japanese)";
        public string SaveDir      { get; set; } = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile) + "\\Downloads";
        public string BypassMethod { get; set; } = "flaresolverr";
        public string BrowserType  { get; set; } = "chrome";
        public bool   Headless     { get; set; } = true;
        public bool   Incognito    { get; set; } = false;
        public int    MaxWorkers   { get; set; } = 3;
        public string SeriesTitle  { get; set; } = "";

        public List<EpisodeItem> Episodes { get; set; } = new();
        public Action<string, string>? LogCallback { get; set; }
        public void Log(string msg, string tag = "info") => LogCallback?.Invoke(msg, tag);
    }

    public class EpisodeItem
    {
        public bool   Selected { get; set; } = true;
        public int    Number   { get; set; }
        public string Title    { get; set; } = "";
        public string Audio    { get; set; } = "jpn";
        public bool   IsFiller { get; set; }
        public string PlayUrl  { get; set; } = "";
        public string SnapUrl  { get; set; } = "";
    }
}
