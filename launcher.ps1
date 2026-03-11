# Audio/Video Split-Merge Tool 啟動器

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$host.UI.RawUI.WindowTitle = "Audio/Video Split-Merge Tool"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Clear-Host
Write-Host "[INFO] Starting Audio/Video Split-Merge Tool..." -ForegroundColor Green
Write-Host ""

# ======================================
# [1/2] 檢查 Python
# ======================================
Write-Host "[1/2] 檢查 Python 環境..." -ForegroundColor Cyan
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[WARNING] 未偵測到 Python，本程式需要 Python 才能執行。" -ForegroundColor Yellow
    $ans = Read-Host "是否要立即安裝 Python？[Y/n] - 直接按 Enter 代表同意"
    if ($ans -eq "" -or $ans -ieq "Y") {
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            Write-Host "[INFO] 透過 winget 安裝 Python，請稍候..." -ForegroundColor Gray
            winget install --id Python.Python.3 -e --silent --accept-source-agreements --accept-package-agreements
        } else {
            Write-Host "[ERROR] 找不到 winget，請手動至 https://www.python.org/ 下載安裝後重新執行。" -ForegroundColor Red
            Read-Host "按 Enter 關閉"; exit 1
        }
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
        if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
            Write-Host "[INFO] 安裝完成，請關閉視窗後重新點兩下啟動檔。" -ForegroundColor Yellow
            Read-Host "按 Enter 關閉"; exit 0
        }
        Write-Host "[OK] Python 安裝完成。" -ForegroundColor Green
    } else {
        Write-Host "已取消。" -ForegroundColor Gray; Read-Host "按 Enter 關閉"; exit 1
    }
} else {
    $pyVer = python --version 2>&1
    Write-Host "[OK] $pyVer 已安裝。" -ForegroundColor Green
}

# ======================================
# [2/2] 檢查 ffmpeg
# ======================================
Write-Host "[2/2] 檢查 ffmpeg..." -ForegroundColor Cyan
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "[WARNING] 未偵測到 ffmpeg，本程式需要 ffmpeg 才能處理音影片。" -ForegroundColor Yellow
    $ans = Read-Host "是否要立即安裝 ffmpeg？[Y/n] - 直接按 Enter 代表同意"
    if ($ans -eq "" -or $ans -ieq "Y") {
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            Write-Host "[INFO] 透過 winget 安裝 ffmpeg，請稍候..." -ForegroundColor Gray
            winget install --id Gyan.FFmpeg -e --silent --accept-source-agreements --accept-package-agreements
        } else {
            Write-Host "[ERROR] 找不到 winget，請手動至 https://ffmpeg.org/download.html 下載安裝後重新執行。" -ForegroundColor Red
            Read-Host "按 Enter 關閉"; exit 1
        }
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
        if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
            Write-Host "[INFO] 安裝完成，請關閉視窗後重新點兩下啟動檔。" -ForegroundColor Yellow
            Read-Host "按 Enter 關閉"; exit 0
        }
        Write-Host "[OK] ffmpeg 安裝完成。" -ForegroundColor Green
    } else {
        Write-Host "已取消。" -ForegroundColor Gray; Read-Host "按 Enter 關閉"; exit 1
    }
} else {
    Write-Host "[OK] ffmpeg 已安裝。" -ForegroundColor Green
}

Write-Host ""
Write-Host "[START] 啟動中，請保持此視窗開啟..." -ForegroundColor Green
Write-Host ""

python main.py
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] 程式意外停止，請回報上方錯誤訊息。" -ForegroundColor Red
    Read-Host "按 Enter 關閉"
} else {
    Write-Host ""
    Write-Host "5 秒後自動關閉..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
}
