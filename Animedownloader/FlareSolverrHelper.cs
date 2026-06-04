using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Threading;
using System.Threading.Tasks;

namespace Animedownloader
{
    public class FlareSolverrHelper
    {
        private readonly string _pythonScriptsDir;
        private readonly string _rootDir;
        private static Process? _flareSolverrProcess;
        private static readonly object _lock = new object();
        private const string FLARESOLVERR_URL = "http://localhost:8191/";
        private static readonly HttpClient _httpClient = new HttpClient { Timeout = TimeSpan.FromSeconds(5) };

        public FlareSolverrHelper(string rootDir)
        {
            _rootDir = rootDir;
            _pythonScriptsDir = Path.Combine(rootDir, "Animedownloader", "python_scripts");
        }

        public bool IsRunning()
        {
            try
            {
                var response = _httpClient.GetAsync(FLARESOLVERR_URL).Result;
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        public bool Start()
        {
            lock (_lock)
            {
                if (IsRunning())
                {
                    Debug.WriteLine("FlareSolverr already running on port 8191.");
                    return true;
                }

                if (_flareSolverrProcess != null && !_flareSolverrProcess.HasExited)
                {
                    Debug.WriteLine("FlareSolverr is already starting or running.");
                    return true;
                }

                try
                {
                    var exe = GetBundledExecutable();
                    if (!File.Exists(exe))
                    {
                        Debug.WriteLine($"Bundled flaresolverr.exe not found: {exe}");
                        return false;
                    }

                    Debug.WriteLine("Starting bundled FlareSolverr...");
                    _flareSolverrProcess = new Process
                    {
                        StartInfo = new ProcessStartInfo
                        {
                            FileName = exe,
                            Arguments = "--max-timeout 180000",
                            UseShellExecute = false,
                            CreateNoWindow = true,
                            RedirectStandardOutput = true,
                            RedirectStandardError = true,
                            WorkingDirectory = Path.GetDirectoryName(exe),
                        }
                    };

                    _flareSolverrProcess.Start();

                    // Wait up to 15s for it to come up
                    for (int i = 0; i < 30; i++)
                    {
                        Thread.Sleep(500);
                        if (IsRunning())
                        {
                            Debug.WriteLine($"FlareSolverr started (PID {_flareSolverrProcess.Id})");
                            return true;
                        }

                        if (_flareSolverrProcess.HasExited)
                        {
                            Debug.WriteLine($"FlareSolverr process exited early with code {_flareSolverrProcess.ExitCode}.");
                            return false;
                        }
                    }

                    Debug.WriteLine("FlareSolverr did not respond in time.");
                    return false;
                }
                catch (Exception ex)
                {
                    Debug.WriteLine($"Failed to start FlareSolverr: {ex.Message}");
                    return false;
                }
            }
        }

        public void Stop()
        {
            lock (_lock)
            {
                if (_flareSolverrProcess != null && !_flareSolverrProcess.HasExited)
                {
                    _flareSolverrProcess.Kill();
                    _flareSolverrProcess = null;
                    Debug.WriteLine("FlareSolverr stopped.");
                }
            }
        }

        private string GetBundledExecutable()
        {
            var basePath = AppDomain.CurrentDomain.BaseDirectory;
            var candidates = new[]
            {
                Path.Combine(basePath, "flaresolverr_bin", "flaresolverr.exe"),
                Path.Combine(basePath, "..", "flaresolverr_bin", "flaresolverr.exe"),
            };

            foreach (var candidate in candidates)
            {
                if (File.Exists(candidate))
                {
                    return candidate;
                }
            }

            return candidates[0];
        }
    }
}
