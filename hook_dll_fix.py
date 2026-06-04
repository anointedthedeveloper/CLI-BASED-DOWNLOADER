"""
Runtime hook: ensure python314.dll is findable by the bootloader.
PyInstaller 6 places DLLs in _internal/ but the bootloader on some
Windows installs looks beside the .exe first. We add _internal to
the DLL search path explicitly.
"""
import os
import sys

if sys.platform == "win32":
    _base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    # Add _MEIPASS (_internal) to Windows DLL search path
    try:
        import ctypes
        ctypes.windll.kernel32.AddDllDirectory(_base)
    except Exception:
        pass
    os.add_dll_directory(_base)
