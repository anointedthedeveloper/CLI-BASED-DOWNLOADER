# -*- mode: python ; coding: utf-8 -*-
"""
build.spec — PyInstaller spec for AnimePahe Downloader standalone exe.

Usage:
    pyinstaller build.spec

Or run build.bat for a one-click Windows build.
"""

import sys
import os

block_cipher = None

# ── data files bundled into the exe ──────────────────────────────────────────
# (source_path, dest_folder_in_bundle)
added_data = [
    ("appico.ico",  "."),
    ("logo.ico",    "."),
    ("ui",          "ui"),
    ("pages",       "pages"),
    ("fs",          "fs"),          # FlareSolverr folder (user places exe here)
]

# ── hidden imports that PyInstaller may miss ──────────────────────────────────
hidden_imports = [
    # Tkinter
    "tkinter",
    "tkinter.ttk",
    "tkinter.messagebox",
    "tkinter.filedialog",
    # PIL
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
    "PIL.ImageDraw",
    "PIL.ImageFont",
    # Requests / network
    "requests",
    "requests.adapters",
    "cloudscraper",
    "urllib3",
    "urllib3.util",
    "certifi",
    "charset_normalizer",
    # Selenium (optional)
    "selenium",
    "selenium.webdriver",
    # Notifications (optional)
    "plyer",
    "plyer.platforms",
    "plyer.platforms.win.notification",
    # Project modules
    "animepahe",
    "kwik",
    "downloader",
    "session",
    "flaresolverr",
    "fs_launcher",
    "notifications",
    "queue_manager",
    "browser",
    "pages.browse",
    "pages.downloads",
    "pages.log",
    "pages.settings",
    "pages.queue",
    "ui.theme",
    "ui.widgets",
    "ui.logo",
]

a = Analysis(
    ["app.py"],
    pathex=["."],
    binaries=[],
    datas=added_data,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "numpy", "scipy", "pytest", "IPython"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AnimePaheDownloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,          # no console window
    icon="appico.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AnimePaheDownloader",
)
