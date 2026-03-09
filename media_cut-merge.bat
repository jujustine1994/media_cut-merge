@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Audio/Video Split-Merge Tool
color 0a
cls

cd /d "%~dp0"

echo ========================================================
echo   Audio/Video Split-Merge Tool
echo   Split or merge audio/video files
echo   Created by CTH
echo ========================================================
echo.

:: ==== PRE-CHECKS ====

:: ---- Check Python ----
echo [1/2] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Python not found. Python is required to run this tool.
    echo.
    set /p INSTALL_PY=Install Python now? [Y/n] - Press Enter to agree:
    if "!INSTALL_PY!"=="" set INSTALL_PY=Y
    if /i "!INSTALL_PY!" neq "Y" (
        echo Cancelled. Please install Python and restart.
        pause
        exit /b 1
    )
    winget --version >nul 2>&1
    if !errorlevel! equ 0 (
        echo [INFO] Installing Python via winget, please wait...
        winget install --id Python.Python.3 -e --silent --accept-source-agreements --accept-package-agreements
    ) else (
        echo [ERROR] winget not found. Please install Python manually: https://www.python.org/
        pause
        exit /b 1
    )
    echo.
    echo [INFO] Done! Please close this window and double-click the bat again.
    pause
    exit /b 0
) else (
    for /f "tokens=*" %%v in ('python --version') do echo [OK] %%v is installed.
)

:: ---- Check ffmpeg ----
echo [2/2] Checking ffmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] ffmpeg not found. ffmpeg is required to run this tool.
    echo.
    set /p INSTALL_FF=Install ffmpeg now? [Y/n] - Press Enter to agree:
    if "!INSTALL_FF!"=="" set INSTALL_FF=Y
    if /i "!INSTALL_FF!" neq "Y" (
        echo Cancelled. Please install ffmpeg and restart.
        pause
        exit /b 1
    )
    winget --version >nul 2>&1
    if !errorlevel! equ 0 (
        echo [INFO] Installing ffmpeg via winget, please wait...
        winget install --id Gyan.FFmpeg -e --silent --accept-source-agreements --accept-package-agreements
    ) else (
        echo [ERROR] winget not found. Please install ffmpeg manually: https://ffmpeg.org/download.html
        pause
        exit /b 1
    )
    echo.
    echo [INFO] Done! Please close this window and double-click the bat again.
    pause
    exit /b 0
) else (
    echo [OK] ffmpeg is installed.
)

:: ==== LAUNCH ====

echo.
echo [START] Starting... keep this window open.
echo.

python main.py

:: ==== EXIT HANDLING ====

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Program stopped unexpectedly. Please report the error above.
    pause
)

echo.
echo Closing in 5 seconds...
timeout /t 5
