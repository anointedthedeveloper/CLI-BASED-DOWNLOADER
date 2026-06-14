"""
notifications.py — Desktop notifications for AnimePahe Downloader.
No mandatory external dependency — falls back gracefully on every platform.
"""
import sys
import threading

_lock = threading.Lock()


def notify(title: str, message: str, timeout: int = 5):
    """Show a desktop notification (non-blocking, best-effort)."""
    threading.Thread(target=_show, args=(title, message, timeout),
                     daemon=True).start()


def _show(title: str, message: str, timeout: int):
    with _lock:
        try:
            if sys.platform == "win32":
                _notify_win(title, message, timeout)
            elif sys.platform == "darwin":
                _notify_mac(title, message)
            else:
                _notify_linux(title, message)
        except Exception:
            pass


def _notify_win(title: str, message: str, timeout: int):
    # 1. Try plyer (cross-platform, bundles with PyInstaller)
    try:
        from plyer import notification
        notification.notify(title=title, message=message,
                            app_name="AnimePahe Downloader",
                            timeout=timeout)
        return
    except Exception:
        pass

    # 2. Try winotify (modern Windows toast, no tray icon needed)
    try:
        from winotify import Notification
        t = Notification(app_id="AnimePahe Downloader",
                         title=title, msg=message,
                         duration="short")
        t.show()
        return
    except Exception:
        pass

    # 3. Windows balloon tip via ctypes (legacy — needs systray, best-effort)
    try:
        import ctypes, ctypes.wintypes
        NIF_MESSAGE  = 0x01
        NIF_ICON     = 0x02
        NIF_TIP      = 0x04
        NIM_ADD      = 0x00
        NIM_MODIFY   = 0x01
        NIM_DELETE   = 0x02
        NIF_INFO     = 0x10
        NIIF_INFO    = 0x01
        WM_USER      = 0x0400

        class NOTIFYICONDATA(ctypes.Structure):
            _fields_ = [
                ("cbSize",           ctypes.wintypes.DWORD),
                ("hWnd",             ctypes.wintypes.HWND),
                ("uID",              ctypes.wintypes.UINT),
                ("uFlags",           ctypes.wintypes.UINT),
                ("uCallbackMessage", ctypes.wintypes.UINT),
                ("hIcon",            ctypes.wintypes.HICON),
                ("szTip",            ctypes.c_wchar * 128),
                ("dwState",          ctypes.wintypes.DWORD),
                ("dwStateMask",      ctypes.wintypes.DWORD),
                ("szInfo",           ctypes.c_wchar * 256),
                ("uTimeout_uVersion", ctypes.wintypes.UINT),
                ("szInfoTitle",      ctypes.c_wchar * 64),
                ("dwInfoFlags",      ctypes.wintypes.DWORD),
            ]

        shell32 = ctypes.windll.shell32
        nid = NOTIFYICONDATA()
        nid.cbSize     = ctypes.sizeof(nid)
        nid.uFlags     = NIF_ICON | NIF_INFO | NIF_TIP
        nid.szTip      = "AnimePahe Downloader"
        nid.szInfo     = message[:255]
        nid.szInfoTitle = title[:63]
        nid.dwInfoFlags = NIIF_INFO
        nid.uTimeout_uVersion = timeout * 1000
        shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
        import time; time.sleep(timeout)
        shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
    except Exception:
        pass


def _notify_mac(title: str, message: str):
    import subprocess
    script = (f'display notification "{message.replace(chr(34), "")}" '
              f'with title "{title.replace(chr(34), "")}"')
    subprocess.run(["osascript", "-e", script],
                   capture_output=True, timeout=5)


def _notify_linux(title: str, message: str):
    import subprocess
    try:
        subprocess.run(["notify-send", "--app-name=AnimePahe Downloader",
                        title, message],
                       capture_output=True, timeout=5)
    except Exception:
        pass
