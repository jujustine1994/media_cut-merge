# Audio/Video Split-Merge Tool 啟動器

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$host.UI.RawUI.WindowTitle = "Audio/Video Split-Merge Tool"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# ======================================
# 執行紀錄（必加，須放在 trap 之前，閃退才記得到）
# 完整規則見 windows-tool.md「執行紀錄」；範本說明見 windows-tool-templates.md「執行紀錄範本」
# ======================================
$LogFile = Join-Path $ScriptDir "logs\app.log"
New-Item -ItemType Directory -Force (Split-Path $LogFile) | Out-Null
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)   # 不可用 Add-Content -Encoding UTF8，會寫 BOM（地雷十一）

function Write-Log {
    param([string]$Msg, [string]$Level = "INFO")
    $line = "[{0}] [{1,-5}] {2}`r`n" -f (Get-Date -Format "HH:mm:ss"), $Level, $Msg
    try { [System.IO.File]::AppendAllText($LogFile, $line, $Utf8NoBom) } catch {}   # 不持有 handle（地雷十）
}

function Write-LogHeader {
    param([string]$Msg)
    $line = "=== {0} {1} ===`r`n" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Msg
    try { [System.IO.File]::AppendAllText($LogFile, $line, $Utf8NoBom) } catch {}
}

Write-LogHeader "啟動"

# 攔截所有未預期例外，防止視窗直接閃退
trap {
    Write-Log "[CRASH] $($_.Exception.Message) @ 第 $($_.InvocationInfo.ScriptLineNumber) 行" "FATAL"
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Red
    Write-Host "[CRASH] 意外錯誤，程式無法繼續執行" -ForegroundColor Red
    Write-Host ""
    Write-Host "  錯誤訊息：$($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "  發生位置：$($_.InvocationInfo.ScriptLineNumber) 行" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  已記錄至 logs\app.log，請連同此畫面回報給開發者。" -ForegroundColor White
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Red
    Read-Host "按 Enter 關閉"
    exit 1
}

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
            # 不帶次版號的 Python.Python.3 已被上游下架（地雷十二），版號一定要寫
            winget install --id Python.Python.3.13 -e --silent --accept-source-agreements --accept-package-agreements --override "/quiet PrependPath=1 Include_pip=1"
            if ($LASTEXITCODE -ne 0) {
                Write-Log "winget install Python.Python.3.13 失敗（exit $LASTEXITCODE）" "ERROR"
                Write-Host "[ERROR] Python 安裝失敗（winget exit $LASTEXITCODE），請確認網路連線後重新執行。" -ForegroundColor Red
                Read-Host "按 Enter 關閉"; exit 1
            }
        } else {
            Write-Log "找不到 winget，無法自動安裝 Python" "ERROR"
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
if (-not $pyVer) { $pyVer = python --version 2>&1 }

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
            Write-Log "找不到 winget，無法自動安裝 ffmpeg" "ERROR"
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

Write-Log "環境就緒 | $pyVer"

Write-Host ""
Write-Host "[START] 啟動中，請保持此視窗開啟..." -ForegroundColor Green
Write-Host ""

python main.py
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Log "主程式異常結束（exit code $exitCode）" "ERROR"
    Write-Host ""
    Write-Host "[ERROR] 程式意外停止，請回報上方錯誤訊息。" -ForegroundColor Red
    Read-Host "按 Enter 關閉"
} else {
    Write-Host ""
    Write-Host "5 秒後自動關閉..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
}
