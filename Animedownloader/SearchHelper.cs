using System;
using System.Diagnostics;
using System.Text.Json;
using System.Collections.Generic;

namespace Animedownloader
{
    public class SearchHelper
    {
        private readonly string _pythonScriptsDir;
        private readonly string _rootDir;

        public SearchHelper(string rootDir)
        {
            _rootDir = rootDir;
            _pythonScriptsDir = System.IO.Path.Combine(rootDir, "Animedownloader", "python_scripts");
        }

        public List<Dictionary<string, object>> Search(string query)
        {
            if (string.IsNullOrWhiteSpace(query))
            {
                return new List<Dictionary<string, object>>();
            }

            try
            {
                var searchScriptPath = System.IO.Path.Combine(_pythonScriptsDir, "search.py");
                if (!System.IO.File.Exists(searchScriptPath))
                {
                    throw new System.IO.FileNotFoundException($"search.py not found at {searchScriptPath}");
                }

                var proc = new Process
                {
                    StartInfo = new ProcessStartInfo
                    {
                        FileName = "python",
                        Arguments = $"\"{searchScriptPath}\" \"{query}\"",
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        UseShellExecute = false,
                        CreateNoWindow = true,
                        WorkingDirectory = _rootDir,
                    }
                };

                proc.Start();
                var output = proc.StandardOutput.ReadToEnd();
                var error = proc.StandardError.ReadToEnd();
                proc.WaitForExit();

                if (proc.ExitCode != 0)
                {
                    throw new Exception($"search.py exited with code {proc.ExitCode}: {error}");
                }

                if (string.IsNullOrWhiteSpace(output))
                {
                    return new List<Dictionary<string, object>>();
                }

                var results = JsonSerializer.Deserialize<List<Dictionary<string, object>>>(output);
                return results ?? new List<Dictionary<string, object>>();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Search error: {ex.Message}");
                return new List<Dictionary<string, object>>();
            }
        }
    }
}
