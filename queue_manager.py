"""
queue_manager.py — Download queue data model for AnimePahe Downloader.
"""
import threading
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class QueueItem:
    title: str
    play_urls: list                    # list of play-page URLs
    quality: int                       # 0=max, -1=min, or specific int like 720/1080
    audio: str                         # "jp" / "en"
    save_dir: str
    id: str           = field(default_factory=lambda: uuid.uuid4().hex[:8])
    status: str       = "pending"      # pending / active / done / error / cancelled
    progress: float   = 0.0            # 0–100
    current_ep: int   = 0              # 1-based index of episode being downloaded
    error: str        = ""
    added_at: float   = field(default_factory=time.time)

    @property
    def ep_count(self) -> int:
        return len(self.play_urls)

    @property
    def quality_label(self) -> str:
        if self.quality == 0:   return "Max"
        if self.quality == -1:  return "Min"
        return f"{self.quality}p"

    @property
    def audio_label(self) -> str:
        return "EN" if self.audio.lower() in ("en", "eng") else "JP"


class DownloadQueue:
    """Thread-safe download queue. Processes items sequentially."""

    def __init__(self):
        self.items: list[QueueItem] = []
        self._lock    = threading.RLock()
        self._active  = False
        self._stop_ev = threading.Event()
        self.on_update = None   # () → None  called on every state change

    # ── public API ────────────────────────────────────────────────────────────

    def add(self, item: QueueItem) -> QueueItem:
        with self._lock:
            self.items.append(item)
        self._notify()
        return item

    def remove(self, item_id: str):
        with self._lock:
            self.items = [i for i in self.items if i.id != item_id]
        self._notify()

    def clear_done(self):
        with self._lock:
            self.items = [i for i in self.items
                          if i.status not in ("done", "error", "cancelled")]
        self._notify()

    def pending_count(self) -> int:
        with self._lock:
            return sum(1 for i in self.items if i.status == "pending")

    def is_active(self) -> bool:
        return self._active

    def start(self, download_fn):
        """
        Start processing pending items.
        download_fn(item: QueueItem, stop_ev: threading.Event) → None
        Runs until the queue is empty or stop() is called.
        """
        if self._active:
            return
        self._stop_ev.clear()
        self._active = True
        threading.Thread(target=self._worker, args=(download_fn,),
                         daemon=True).start()

    def stop(self):
        """Signal the queue runner to stop after the current episode."""
        self._stop_ev.set()

    # ── internals ─────────────────────────────────────────────────────────────

    def _worker(self, download_fn):
        try:
            while not self._stop_ev.is_set():
                item = self._next_pending()
                if item is None:
                    break
                item.status   = "active"
                item.progress = 0.0
                item.error    = ""
                self._notify()
                try:
                    download_fn(item, self._stop_ev)
                    if self._stop_ev.is_set():
                        item.status   = "cancelled"
                        item.progress = 0.0
                    else:
                        item.status   = "done"
                        item.progress = 100.0
                except InterruptedError:
                    item.status   = "cancelled"
                    item.progress = 0.0
                except Exception as exc:
                    item.status = "error"
                    item.error  = str(exc)
                self._notify()
        finally:
            self._active = False
            self._notify()

    def _next_pending(self) -> QueueItem | None:
        with self._lock:
            for item in self.items:
                if item.status == "pending":
                    return item
        return None

    def _notify(self):
        cb = self.on_update
        if cb:
            try:
                cb()
            except Exception:
                pass
