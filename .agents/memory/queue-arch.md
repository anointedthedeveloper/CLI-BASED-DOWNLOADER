---
name: Download queue architecture
description: How the queue system is structured across queue_manager, pages/queue, and app.py.
---

## Architecture

- **`queue_manager.py`** — data only: `QueueItem` dataclass + `DownloadQueue` runner. No UI imports.
- **`pages/queue.py`** — `QueuePage(tk.Frame)` — renders the queue list; calls `app._queue` for data.
- **`app.py`** — owns `self._queue = DownloadQueue()`; provides `add_to_queue()`, `_queue_download_fn(item, stop_ev)`.

## Key data shape
`QueueItem.play_urls` — list of AnimePahe play-page URLs (same format as used by `_run_downloads`). Quality is `int` (0=max, -1=min, 720/1080/etc).

## Why sequential (not parallel)
Queue runner processes items one at a time to avoid overloading the connection and triggering extra CF challenges.

## episode_vars format
`app.episode_vars` is a list of `(BooleanVar, _, play_url)` 3-tuples. `add_to_queue` extracts `[u for var, _, u in episode_vars if var.get()]`.

## Sleep prevention
`downloader.prevent_sleep()` / `downloader.allow_sleep()` are called in both `_run_downloads` and `_queue_download_fn` (try/finally). Uses `SetThreadExecutionState` on Windows.
