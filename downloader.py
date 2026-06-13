import os
import re
import time
import subprocess
import threading
import session as _sess

CHUNK       = 1024 * 64   # not used for writing, kept for compat
MAX_RETRIES = 10
BACKOFF     = [1, 2, 4, 8, 16, 16, 16, 16, 16, 16]

# Speed / stall thresholds
LOW_SPEED_THRESHOLD = 100 * 1024   # bytes/s — below this is considered "slow"
LOW_SPEED_GRACE     = 20           # seconds at low speed before we restart
STALL_TIMEOUT       = 30           # seconds with zero new bytes before restart
SPEED_WINDOW        = 5.0          # rolling-average window in seconds

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)


def _filename_from_url(url: str, fallback: str) -> str:
    from urllib.parse import urlparse, parse_qs
    qs = parse_qs(urlparse(url).query)
    if "file" in qs:
        return qs["file"][0]
    seg = urlparse(url).path.rstrip("/").split("/")[-1]
    if seg and "." in seg:
        return seg
    return fallback


class _SpeedTracker:
    """Rolling-window speed tracker."""

    def __init__(self, window: float = SPEED_WINDOW):
        self._window  = window
        self._samples = []   # list of (timestamp, bytes_total)
        self._lock    = threading.Lock()

    def update(self, bytes_total: int):
        now = time.monotonic()
        with self._lock:
            self._samples.append((now, bytes_total))
            cutoff = now - self._window
            self._samples = [(t, b) for t, b in self._samples if t >= cutoff]

    def speed(self) -> float:
        """Return bytes/s over the last window, or 0 if not enough data."""
        with self._lock:
            if len(self._samples) < 2:
                return 0.0
            oldest_t, oldest_b = self._samples[0]
            newest_t, newest_b = self._samples[-1]
            dt = newest_t - oldest_t
            if dt <= 0:
                return 0.0
            return max(0.0, (newest_b - oldest_b) / dt)


def download(
    url: str,
    referer: str,
    dest_dir: str,
    filename: str = "",
    on_progress=None,   # callable(downloaded_bytes, total_bytes, speed_bps, eta_s)
    stop_flag=None,     # threading.Event or callable() → bool
) -> str:
    """
    Downloads url into dest_dir/filename using curl streamed directly to disk.
    Supports resume via Range header.  Returns the final file path.

    Automatically restarts on:
      - Network disconnect / curl error
      - No bytes received for STALL_TIMEOUT seconds
      - Speed below LOW_SPEED_THRESHOLD for LOW_SPEED_GRACE seconds
    """
    def _stopped():
        if stop_flag is None:
            return False
        if callable(stop_flag) and not isinstance(stop_flag, threading.Event):
            return stop_flag()
        return stop_flag.is_set()

    os.makedirs(dest_dir, exist_ok=True)

    if not filename:
        filename = _filename_from_url(url, f"download_{int(time.time())}.mp4")

    filepath = os.path.join(dest_dir, filename)
    tmp_path = filepath + ".part"

    for attempt in range(MAX_RETRIES):
        if _stopped():
            raise InterruptedError("Download cancelled")

        existing = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0

        cookie_str = _sess._cookie_str_for(url)

        # ── get Content-Length via HEAD ───────────────────────────────────────
        total = 0
        try:
            head_cmd = [
                "curl", "-sI",
                "-L", "--max-redirs", "5",
                "--connect-timeout", "15",
                "-A", UA,
                "-H", f"Referer: {referer}",
                "-H", f"Cookie: {cookie_str}",
                url,
            ]
            h_res = subprocess.run(head_cmd, capture_output=True, timeout=20)
            h_out = h_res.stdout.decode("utf-8", errors="replace").lower()
            m_cl  = re.search(r"content-length:\s*(\d+)", h_out)
            if m_cl:
                total = int(m_cl.group(1))
        except Exception:
            pass

        # ── build curl command ────────────────────────────────────────────────
        cmd = [
            "curl", "-S", "--fail-with-body",
            "--max-time",       "0",    # no hard time limit; we police speed ourselves
            "--connect-timeout", "20",
            "--retry",          "0",    # we handle retries ourselves
            "-L", "--max-redirs", "5",
            "-A", UA,
            "-H", f"Referer: {referer}",
            "-H", f"Cookie: {cookie_str}",
            "-H", "Accept: */*",
            "-H", "Accept-Language: en-US,en;q=0.9",
            "-o", tmp_path,
        ]

        if existing > 0:
            cmd += ["-C", str(existing)]

        cmd.append(url)

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            raise RuntimeError("curl not found — please install curl and add it to PATH")

        # ── poll loop ─────────────────────────────────────────────────────────
        tracker          = _SpeedTracker()
        last_advance_t   = time.monotonic()   # last time file grew
        low_speed_since  = None               # when slow speed started
        restart_reason   = None               # set to trigger a retry

        while proc.poll() is None:
            if _stopped():
                proc.terminate()
                proc.wait()
                raise InterruptedError("Download cancelled")

            time.sleep(0.5)

            try:
                current = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
            except OSError:
                current = existing

            now = time.monotonic()

            # track progress
            if current > existing:
                tracker.update(current)
                last_advance_t = now

            speed = tracker.speed()
            total_for_cb = total if total > 0 else current

            if on_progress and current > 0:
                eta = ((total_for_cb - current) / speed
                       if speed > 0 and total_for_cb > current else 0)
                on_progress(current, total_for_cb, speed, eta)

            # ── stall detection (no new bytes) ────────────────────────────────
            if now - last_advance_t > STALL_TIMEOUT and current == existing:
                restart_reason = "stall"
                break

            # ── slow-speed detection (rolling average) ────────────────────────
            if speed > 0:
                if speed < LOW_SPEED_THRESHOLD:
                    if low_speed_since is None:
                        low_speed_since = now
                    elif now - low_speed_since > LOW_SPEED_GRACE:
                        restart_reason = "slow"
                        break
                else:
                    low_speed_since = None

        if restart_reason:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            if attempt < MAX_RETRIES - 1:
                wait = BACKOFF[min(attempt, len(BACKOFF) - 1)]
                time.sleep(wait)
                continue
            raise RuntimeError(
                f"Download aborted ({restart_reason}) after {MAX_RETRIES} attempts"
            )

        # ── curl finished normally ────────────────────────────────────────────
        returncode = proc.wait()
        stderr_out = proc.stderr.read().decode("utf-8", errors="replace")

        if _stopped():
            raise InterruptedError("Download cancelled")

        # exit 33 = range not satisfiable → file already complete
        if returncode == 33:
            if os.path.exists(tmp_path):
                os.replace(tmp_path, filepath)
            return filepath

        if returncode != 0:
            # curl error codes that indicate network problems — always retry
            network_errors = {6, 7, 28, 35, 52, 55, 56}
            if attempt < MAX_RETRIES - 1:
                wait = BACKOFF[min(attempt, len(BACKOFF) - 1)]
                time.sleep(wait)
                continue
            raise RuntimeError(
                f"curl failed (exit {returncode}) after {MAX_RETRIES} attempts.\n"
                f"{stderr_out.strip()}"
            )

        # ── success ───────────────────────────────────────────────────────────
        final_size = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
        if on_progress and final_size > 0:
            on_progress(final_size, final_size, 0, 0)

        os.replace(tmp_path, filepath)
        return filepath

    raise RuntimeError("Download failed after all retries")
