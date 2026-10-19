# Audio/Video Split-Merge Tool 啟動器

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$host.UI.RawUI.WindowTitle = "Audio/Video Split-Merge Tool"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# venv 建在專案外，避開 Google Drive 同步（見 windows-tool.md「venv 位置」）
$VenvPath   = Join-Path $env:USERPROFILE "venvs\Video-Combiner"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"

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

Write-LogHeader "App start"

# 攔截所有未預期例外，防止視窗直接閃退
trap {
    Write-Log "[CRASH] $($_.Exception.Message) @ line $($_.InvocationInfo.ScriptLineNumber)" "FATAL"
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
# [1/3] 檢查 uv
#
# ⚠ 只檢查 uv，不檢查系統 Python——uv 自己就會下載 Python（地雷十二）。
# ======================================
Write-Host "[1/3] 檢查 uv 套件管理工具..." -ForegroundColor Cyan
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Log "uv not found, installing" "WARN"
    Write-Host "[INFO] 找不到 uv，開始下載安裝程式（astral.sh）..." -ForegroundColor Yellow
    # 較舊的 Win10 上 PowerShell 5.1 可能仍預設 TLS 1.0/1.1，astral.sh 只收 1.2 以上
    try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}
    try {
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    } catch {
        Write-Log "uv download failed -> $($_.Exception.GetType().Name)" "ERROR"
    }
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "User") + ";" + $env:PATH
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Log "uv install failed" "ERROR"
        Write-Host "[ERROR] uv 安裝失敗，多半是連不上網路。請確認網路連線後關閉視窗，" -ForegroundColor Red
        Write-Host "        重新點兩下啟動檔再試一次。" -ForegroundColor Red
        Read-Host "按 Enter 關閉"; exit 1
    }
}
$uvVer = uv --version
Write-Host "[OK] $uvVer 就緒。" -ForegroundColor Green

# ======================================
# [2/3] 檢查虛擬環境
#
# 目前只用 tkinter + 標準函式庫，requirements.txt 沒有實際套件；
# 空檔丟給 uv 會每次印一行 warning，所以有套件才跑 install。
# ======================================
Write-Host "[2/3] 檢查虛擬環境..." -ForegroundColor Cyan
$hasDeps = [bool](Get-Content "requirements.txt" -ErrorAction SilentlyContinue | Where-Object { $_ -match '^\s*[^#\s]' })
if (-not (Test-Path $VenvPython)) {
    Write-Host ""
    Write-Host "  ============================================" -ForegroundColor Cyan
    Write-Host "    Audio/Video Split-Merge Tool - 首次安裝說明" -ForegroundColor Cyan
    Write-Host "  ============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  接下來程式會自動幫你安裝以下東西：" -ForegroundColor White
    Write-Host ""
    Write-Host "    1. Python 本體與虛擬環境（venv）" -ForegroundColor Yellow
    Write-Host "       電腦沒裝過 Python 也沒關係，會自動下載（約 20MB）" -ForegroundColor Gray
    Write-Host "       虛擬環境讓這個工具有獨立乾淨的執行空間，不影響電腦其他程式" -ForegroundColor Gray
    Write-Host ""
    Write-Host "    2. ffmpeg（若電腦還沒有）" -ForegroundColor Yellow
    Write-Host "       實際處理影音分割、合併、轉檔的工具，下一步會再問一次" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  全程只需要一直按 Enter 同意即可。" -ForegroundColor Green
    Write-Host "  如果有任何疑問，可以把這段說明貼給 AI 詢問。" -ForegroundColor Green
    Write-Host ""
    Write-Host "  ============================================" -ForegroundColor Cyan
    Write-Host ""
    $ans = Read-Host "[WARNING] 找不到虛擬環境，現在建立？[Y/n] - 直接按 Enter 代表同意"
    if ($ans -eq "" -or $ans -ieq "Y") {
        Write-Host "[INFO] 下載/建立 Python 虛擬環境中..." -ForegroundColor Gray
        # ⚠ 版號一定要寫，不寫 uv 只找現成直譯器、不會下載
        New-Item -ItemType Directory -Force (Split-Path $VenvPath) | Out-Null
        uv venv "$VenvPath" --python 3.13
        if ($LASTEXITCODE -ne 0) {
            Write-Log "venv creation failed (uv venv exit $LASTEXITCODE)" "ERROR"
            Write-Host "[ERROR] 建立虛擬環境失敗，多半是下載 Python 時連不上網路。" -ForegroundColor Red
            Write-Host "        請確認網路連線後關閉視窗，重新點兩下啟動檔再試一次。" -ForegroundColor Red
            Read-Host "按 Enter 關閉"; exit 1
        }
        if ($hasDeps) {
            uv pip install -r requirements.txt --python "$VenvPython"
            if ($LASTEXITCODE -ne 0) {
                Write-Log "package install failed (uv pip install exit $LASTEXITCODE)" "ERROR"
                Write-Host "[ERROR] 套件安裝失敗，請確認網路連線後重新執行。" -ForegroundColor Red
                Read-Host "按 Enter 關閉"; exit 1
            }
        }
        Write-Host "[OK] 虛擬環境建立完成。" -ForegroundColor Green
    } else {
        Write-Host "已取消。" -ForegroundColor Gray; Read-Host "按 Enter 關閉"; exit 1
    }
} else {
    if ($hasDeps) { uv pip install -r requirements.txt --python "$VenvPython" }
    Write-Host "[OK] 虛擬環境已就緒。" -ForegroundColor Green
}
# 版本問 venv 自己，不問系統 python
$pyVer = (& "$VenvPython" --version 2>&1 | Out-String).Trim()

# ======================================
# [3/3] 檢查 ffmpeg
# ======================================
Write-Host "[3/3] 檢查 ffmpeg..." -ForegroundColor Cyan
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "[WARNING] 未偵測到 ffmpeg，本程式需要 ffmpeg 才能處理音影片。" -ForegroundColor Yellow
    $ans = Read-Host "是否要立即安裝 ffmpeg？[Y/n] - 直接按 Enter 代表同意"
    if ($ans -eq "" -or $ans -ieq "Y") {
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            Write-Host "[INFO] 透過 winget 安裝 ffmpeg，請稍候..." -ForegroundColor Gray
            winget install --id Gyan.FFmpeg -e --silent --accept-source-agreements --accept-package-agreements
        } else {
            Write-Log "winget not found, cannot install ffmpeg" "ERROR"
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

Write-Log "Environment ready | $pyVer | $uvVer"

Write-Host ""
Write-Host "[START] 啟動中，請保持此視窗開啟..." -ForegroundColor Green
Write-Host ""

& "$VenvPython" src\main.py
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Log "app exited abnormally (exit code $exitCode)" "ERROR"
    Write-Host ""
    Write-Host "[ERROR] 程式意外停止，請回報上方錯誤訊息。" -ForegroundColor Red
    Read-Host "按 Enter 關閉"
} else {
    Write-Host ""
    Write-Host "5 秒後自動關閉..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
}
