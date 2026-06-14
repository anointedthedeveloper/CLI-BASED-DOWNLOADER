@echo off
REM ============================================================
REM  AnimePahe Downloader — One-click Windows build
REM  Produces: dist\AnimePaheDownloader\AnimePaheDownloader.exe
REM ============================================================

echo.
echo =====================================================
echo  AnimePahe Downloader - Build Script
echo =====================================================
echo.

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

REM Install / upgrade PyInstaller and dependencies
echo [1/4] Installing build dependencies...
pip install pyinstaller pillow requests cloudscraper plyer --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)

REM Clean previous build artifacts
echo [2/4] Cleaning old build files...
if exist build  rmdir /s /q build
if exist dist   rmdir /s /q dist

REM Run PyInstaller
echo [3/4] Building executable with PyInstaller...
pyinstaller build.spec --noconfirm --clean
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed. See output above.
    pause
    exit /b 1
)

REM Copy curl.exe into the dist folder if available locally
echo [4/4] Checking for curl.exe...
where curl >nul 2>&1
if not errorlevel 1 (
    echo   Found system curl — copying to dist folder...
    copy /y "%SYSTEMROOT%\System32\curl.exe" "dist\AnimePaheDownloader\" >nul 2>&1
    if errorlevel 1 (
        REM Try copying from PATH
        for /f "delims=" %%i in ('where curl') do copy /y "%%i" "dist\AnimePaheDownloader\" >nul 2>&1
    )
    echo   curl.exe copied.
) else (
    echo   [WARN] curl.exe not found. Download curl for Windows and place
    echo          curl.exe in dist\AnimePaheDownloader\ before distributing.
)

REM Copy README for FlareSolverr folder
if exist "fs\README.txt" (
    xcopy /e /i /q "fs" "dist\AnimePaheDownloader\fs" >nul
)

echo.
echo =====================================================
echo  Build complete!
echo  Output: dist\AnimePaheDownloader\AnimePaheDownloader.exe
echo.
echo  IMPORTANT - Before distributing:
echo    1. Copy flaresolverr.exe + internal\ into:
echo       dist\AnimePaheDownloader\fs\
echo.
echo    2. Verify curl.exe is in:
echo       dist\AnimePaheDownloader\
echo =====================================================
echo.
pause
