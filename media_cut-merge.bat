@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title 音影片分割合併工具
color 0a
cls

cd /d "%~dp0"

echo ========================================================
echo   音影片分割合併工具
echo   分割或合併音訊 / 影像檔案，輸出至原始目錄
echo   Created by CTH
echo ========================================================
echo.

:: ==== 前置檢查 ====

:: ---- 檢查 Python ----
echo [1/2] 檢查 Python 環境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] 未偵測到 Python，本程式需要 Python 才能執行。
    echo.
    set /p INSTALL_PY=是否要立即安裝 Python？[Y/n]（直接按 Enter 代表同意）：
    if "!INSTALL_PY!"=="" set INSTALL_PY=Y
    if /i "!INSTALL_PY!" neq "Y" (
        echo 已取消。請安裝 Python 後重新啟動。
        pause
        exit /b 1
    )
    echo.
    :: 優先用 winget 安裝
    winget --version >nul 2>&1
    if !errorlevel! equ 0 (
        echo [INFO] 使用 winget 安裝 Python，請稍候...
        winget install --id Python.Python.3 -e --silent --accept-source-agreements --accept-package-agreements
    ) else (
        :: winget 不存在，改用 PowerShell 下載安裝程式靜默執行
        echo [INFO] 正在下載 Python 安裝程式，請稍候...
        powershell -NoProfile -Command ^
            "$out = \"$env:TEMP\python_installer.exe\";" ^
            "Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe' -OutFile $out;" ^
            "Write-Host '[INFO] 安裝中...';" ^
            "Start-Process $out -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait;" ^
            "Remove-Item $out -Force -EA SilentlyContinue"
    )
    :: 嘗試刷新 PATH，避免需要重開視窗
    for /f "tokens=*" %%i in ('powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable(\"PATH\",\"Machine\")"') do set "PATH=%%i;%PATH%"
    python --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo.
        echo [INFO] 安裝完成！
        echo.
        echo   請關閉此視窗，然後再次點兩下 bat 檔重新啟動。
        pause
        exit /b 0
    )
    echo [OK] Python 安裝完成。
) else (
    for /f "tokens=*" %%v in ('python --version') do echo [OK] %%v 已安裝。
)

:: ---- 檢查 ffmpeg ----
echo [2/2] 檢查 ffmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] 未偵測到 ffmpeg，本程式需要 ffmpeg 才能執行。
    echo.
    set /p INSTALL_FF=是否要立即安裝 ffmpeg？[Y/n]（直接按 Enter 代表同意）：
    if "!INSTALL_FF!"=="" set INSTALL_FF=Y
    if /i "!INSTALL_FF!" neq "Y" (
        echo 已取消。請安裝 ffmpeg 後重新啟動。
        pause
        exit /b 1
    )
    echo.
    :: 優先用 winget 安裝
    winget --version >nul 2>&1
    if !errorlevel! equ 0 (
        echo [INFO] 使用 winget 安裝 ffmpeg，請稍候...
        winget install --id Gyan.FFmpeg -e --silent --accept-source-agreements --accept-package-agreements
    ) else (
        :: winget 不存在，用 PowerShell 下載 zip 並解壓縮至 C:\ffmpeg
        echo [INFO] 正在下載 ffmpeg，請稍候（檔案較大，約需數分鐘）...
        powershell -NoProfile -Command ^
            "$zip = \"$env:TEMP\ffmpeg.zip\";" ^
            "$dest = 'C:\ffmpeg';" ^
            "Invoke-WebRequest 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile $zip;" ^
            "Write-Host '[INFO] 解壓縮中...';" ^
            "Expand-Archive $zip $dest -Force;" ^
            "$bin = (Get-ChildItem $dest -Recurse -Filter 'ffmpeg.exe' | Select-Object -First 1).DirectoryName;" ^
            "$cur = [System.Environment]::GetEnvironmentVariable('PATH','Machine');" ^
            "if ($cur -notlike \"*$bin*\") {" ^
            "    [System.Environment]::SetEnvironmentVariable('PATH', \"$cur;$bin\", 'Machine');" ^
            "    Write-Host '[OK] 已將 ffmpeg 路徑加入系統 PATH'" ^
            "};" ^
            "Remove-Item $zip -Force -EA SilentlyContinue"
    )
    :: 嘗試刷新 PATH，避免需要重開視窗
    for /f "tokens=*" %%i in ('powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable(\"PATH\",\"Machine\")"') do set "PATH=%%i;%PATH%"
    ffmpeg -version >nul 2>&1
    if !errorlevel! neq 0 (
        echo.
        echo [INFO] 安裝完成！
        echo.
        echo   請關閉此視窗，然後再次點兩下 bat 檔重新啟動。
        pause
        exit /b 0
    )
    echo [OK] ffmpeg 安裝完成。
) else (
    :: 只取第一行版本資訊，避免輸出過長
    for /f "tokens=*" %%v in ('ffmpeg -version 2^>^&1 ^| findstr "ffmpeg version"') do echo [OK] %%v
)

:: ==== 啟動 ====

echo.
echo [START] 啟動中，請保持此視窗開啟...
echo.

python main.py

:: ==== 結尾處理 ====

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 程式意外停止，請回報上方錯誤訊息
    pause
)

echo.
echo 5 秒後自動關閉...
timeout /t 5
