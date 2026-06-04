using System.Diagnostics;
using System.Net.Http;
using System.Text;
using System.Text.Json;

namespace Animedownloader
{
    public static class FlareSolverrManager
    {
        private const string ApiUrl    = "http://localhost:8191/v1";
        private const string HealthUrl = "http://localhost:8191/";
        private static Process? _proc;
        private static readonly HttpClient _http = new() { Timeout = TimeSpan.FromMinutes(4) };

        // cached cookies + UA from last solve
        public static Dictionary<string, string> CachedCookies { get; private set; } = new();
        public static string CachedUserAgent { get; private set; } = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138.0.0.0 Safari/537.36";
        public static DateTime CookieExpiry { get; private set; } = DateTime.MinValue;
        public static bool CookiesValid => CachedCookies.ContainsKey("cf_clearance") && DateTime.UtcNow < CookieExpiry;

        // ── start bundled exe ─────────────────────────────────────────────────
        public static async Task<bool> StartBundledAsync(Action<string> log)
        {
            if (await IsRunningAsync()) { log("[INFO] FlareSolverr already running on :8191"); return true; }

            string exe = GetExePath();
            if (!File.Exists(exe)) { log($"[WARN] flaresolverr.exe not found at: {exe}"); return false; }

            log("[INFO] Starting bundled FlareSolverr…");
            try
            {
                var si = new ProcessStartInfo(exe, "--max-timeout 180000")
                {
                    UseShellExecute  = false,
                    CreateNoWindow   = true,
                    WorkingDirectory = Path.GetDirectoryName(exe)!
                };
                _proc = Process.Start(si);
                for (int i = 0; i < 40; i++)
                {
                    await Task.Delay(500);
                    if (await IsRunningAsync()) { log($"[OK] FlareSolverr started (PID {_proc?.Id})"); return true; }
                    if (_proc?.HasExited == true) { log("[ERROR] FlareSolverr process exited early."); return false; }
                }
                log("[WARN] FlareSolverr did not respond within 20s.");
                return false;
            }
            catch (Exception ex) { log($"[ERROR] Failed to start FlareSolverr: {ex.Message}"); return false; }
        }

        public static void StopBundled()
        {
            try { if (_proc is { HasExited: false }) { _proc.Kill(); _proc = null; } } catch { }
        }

        public static async Task<bool> IsRunningAsync()
        {
            try
            {
                using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(2));
                var r = await _http.GetAsync(HealthUrl, cts.Token);
                return r.IsSuccessStatusCode;
            }
            catch { return false; }
        }

        // ── solve CF and cache cookies ────────────────────────────────────────
        public static async Task<bool> SolveAsync(string url, Action<string> log)
        {
            if (!await IsRunningAsync()) { log("[WARN] FlareSolverr not running — cannot solve CF."); return false; }
            try
            {
                log($"[INFO] FlareSolverr solving: {url} (may take 60-90s)…");
                var payload = JsonSerializer.Serialize(new { cmd = "request.get", url, maxTimeout = 180000 });
                var req = new HttpRequestMessage(HttpMethod.Post, ApiUrl)
                {
                    Content = new StringContent(payload, Encoding.UTF8, "application/json")
                };
                var resp = await _http.SendAsync(req);
                var body = await resp.Content.ReadAsStringAsync();
                var doc  = JsonDocument.Parse(body);
                var root = doc.RootElement;

                if (root.GetProperty("status").GetString() != "ok")
                {
                    log($"[ERROR] FlareSolverr: {root.GetProperty("message").GetString()}");
                    return false;
                }

                var sol = root.GetProperty("solution");
                var cookies = new Dictionary<string, string>();
                foreach (var c in sol.GetProperty("cookies").EnumerateArray())
                    cookies[c.GetProperty("name").GetString()!] = c.GetProperty("value").GetString()!;

                if (sol.TryGetProperty("userAgent", out var uaProp) && !string.IsNullOrEmpty(uaProp.GetString()))
                    CachedUserAgent = uaProp.GetString()!;

                CachedCookies = cookies;
                CookieExpiry  = DateTime.UtcNow.AddHours(2);
                log($"[OK] CF solved — {cookies.Count} cookies cached for 2h. Keys: {string.Join(", ", cookies.Keys)}");
                return true;
            }
            catch (Exception ex) { log($"[ERROR] FlareSolverr error: {ex.Message}"); return false; }
        }

        public static string BuildCookieHeader()
        {
            return string.Join("; ", CachedCookies.Select(kv => $"{kv.Key}={kv.Value}"));
        }

        private static string GetExePath()
        {
            string[] candidates = {
                Path.Combine(AppContext.BaseDirectory, "flaresolverr_bin", "flaresolverr.exe"),
                Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "flaresolverr_bin", "flaresolverr.exe"),
            };
            foreach (var c in candidates) if (File.Exists(Path.GetFullPath(c))) return Path.GetFullPath(c);
            return candidates[0];
        }
    }
}
