# ARCHITECTURE.md — 音影片分割合併工具

## 工具總覽

CLI 互動工具，讓使用者透過選單選擇音訊/影像的分割或合併操作。
選檔使用 tkinter 視窗，處理核心依賴 ffmpeg，輸出結果放在原始檔案所在目錄。

## 檔案清單

```
media_cut-merge.bat  → 薄 BAT 入口：單行呼叫 launcher.ps1（處理 ExecutionPolicy）
launcher.ps1         → 啟動邏輯：環境檢查（Python、ffmpeg）、自動 winget 安裝 → 執行 main.py
main.py              → 主程式：互動選單、分割邏輯、合併邏輯
```

## 執行流程

```
使用者雙擊 media_cut-merge.bat
  → 以 -ExecutionPolicy Bypass 呼叫 launcher.ps1
      → 檢查 Python 是否存在（沒有則提示用 winget 安裝）
      → 檢查 ffmpeg 是否存在（沒有則提示用 winget 安裝）
      → 執行 main.py
      → 選擇類型（音訊 / 影像）
      → 選擇操作（分割 / 合併）
      ↓
    [分割]
      → tkinter 選擇來源檔案
      → 輸入 N 個 HH:MM:SS 時間點
      → ffmpeg -ss -t -c copy 分段輸出（原檔名_part1, part2...）
      → 輸出至原始檔案所在目錄
    [合併]
      → 依序用 tkinter 選擇 N 個檔案
      → 輸入 done 完成
      → 產生暫存 _merge_list_tmp.txt（concat 清單）
      → ffmpeg -f concat -c copy 合併輸出（merged_原檔名）
      → 清理暫存清單，輸出至第一個檔案所在目錄
```

## 關鍵設計決策

| 項目 | 決策 | 原因 |
|------|------|------|
| 分割指令 | `-ss` 放 `-i` 前，搭配 `-t`（持續時間）| 快速定位，比 `-to` 更穩定 |
| 合併指令 | `ffmpeg concat` + `_merge_list_tmp.txt` | 最穩定的多檔合併方式 |
| 路徑格式 | concat 清單使用正斜線 | 避免 Windows 反斜線被 ffmpeg 誤解 |
| 編碼 | `-c copy` | 串流複製，不重新編碼，速度快且不失真 |

## 輸出命名規則

| 操作 | 輸出格式 |
|------|---------|
| 分割 | `{原檔名}_part1.{副檔名}`、`{原檔名}_part2.{副檔名}`... |
| 合併 | `{第一個檔名}_merge.{副檔名}` |
