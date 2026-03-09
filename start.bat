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

echo [1/2] 檢查 Python 環境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 找不到 Python，請至 https://www.python.org/ 下載安裝後重新執行
    pause
    exit
)

echo [2/2] 檢查 ffmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 找不到 ffmpeg，請依照以下步驟安裝：
    echo.
    echo   1. 前往 https://ffmpeg.org/download.html 下載 Windows 版本
    echo   2. 解壓縮後，將 bin 資料夾路徑加入系統環境變數 PATH
    echo   3. 重新開啟此視窗再執行
    echo.
    pause
    exit
)

echo.
echo [START] 啟動中，請保持此視窗開啟...
echo.

python main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 程式意外停止，請回報上方錯誤訊息
    pause
)

echo.
echo 5 秒後自動關閉...
timeout /t 5
