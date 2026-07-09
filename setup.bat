@echo off
setlocal

echo ============================================
echo   ShotSweep Setup
echo ============================================
echo.

REM --- Check Python is installed ---
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on this computer.
    echo Please install Python from https://www.python.org/downloads/
    echo During install, make sure to check "Add python.exe to PATH".
    pause
    exit /b 1
)

echo [1/3] Installing required packages...
python -m pip install --quiet -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies. Check your internet connection.
    pause
    exit /b 1
)

echo [2/3] Enabling auto-start when Windows logs in...
set "STARTUP_VBS=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\start_shotsweep.vbs"
(
echo Set objShell = CreateObject("WScript.Shell"^)
echo objShell.Run "pythonw ""%~dp0ShotSweep.py""", 0, False
) > "%STARTUP_VBS%"

echo [3/3] Starting ShotSweep now...
wscript "%~dp0start_shotsweep.vbs"

echo.
echo ============================================
echo   Done! ShotSweep is running in the background.
echo.
echo   Ctrl+Shift+S   full screen shot (expires)
echo   Ctrl+Shift+K   full screen shot (keeper)
echo   Ctrl+Shift+A   select an area (expires)
echo   Ctrl+Shift+D   select an area (keeper)
echo   Ctrl+Shift+Q   quit
echo.
echo   It will also start automatically next time
echo   you log into Windows.
echo ============================================
pause