using System;
using System.Diagnostics;

namespace Animedownloader
{
    public class DownloadHelper
    {
        private readonly string _pythonScriptsDir;
        private readonly string _rootDir;

        public DownloadHelper(string rootDir)
        {
            _rootDir = rootDir;
            _pythonScriptsDir = System.IO.Path.Combine(rootDir, "Animedownloader", "python_scripts");
        }

        public bool Download(string url, string referer, string destDir, string? filename = null, Action<string>? onProgress = null)
        {
            if (string.IsNullOrWhiteSpace(url) || string.IsNullOrWhiteSpace(destDir))
            {
                throw new ArgumentException("URL and destination directory are required.");
            }

            try
            {
                var downloadScriptPath = System.IO.Path.Combine(_pythonScriptsDir, "download.py");
                if (!System.IO.File.Exists(downloadScriptPath))
                {
                    throw new System.IO.FileNotFoundException($"download.py not found at {downloadScriptPath}");
                }

                System.IO.Directory.CreateDirectory(destDir);

                var args = $"\"{downloadScriptPath}\" \"{url}\" \"{referer}\" \"{destDir}\"";
                if (!string.IsNullOrWhiteSpace(filename))
                {
                    args += $" \"{filename}\"";
                }

                var proc = new Process
                {
                    StartInfo = new ProcessStartInfo
                    {
                        FileName = "python",
                        Arguments = args,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        UseShellExecute = false,
                        CreateNoWindow = true,
                        WorkingDirectory = _rootDir,
                    }
                };

                proc.Start();

                while (!proc.StandardOutput.EndOfStream)
                {
                    var line = proc.StandardOutput.ReadLine();
                    if (!string.IsNullOrWhiteSpace(line))
                    {
                        onProgress?.Invoke(line);
                    }
                }

                var error = proc.StandardError.ReadToEnd();
                proc.WaitForExit();

                if (proc.ExitCode != 0)
                {
                    throw new Exception($"download.py exited with code {proc.ExitCode}: {error}");
                }

                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Download error: {ex.Message}");
                throw;
            }
        }
    }
}
