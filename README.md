規則檔: windows-tool.md
類型: Windows 工具

# media_cut-merge

A Windows CLI tool to split and merge audio/video files using ffmpeg.

分割或合併音訊 / 影像檔案，透過 tkinter 選檔視窗操作，輸出至原始檔案所在目錄。

## 技術棧

- Python 3.x（內建 tkinter）
- ffmpeg（外部依賴，需手動安裝）

## 執行方式

雙擊 `start.bat` 啟動。

## 系統需求

- Python 3.8 以上
- ffmpeg 已安裝並加入 PATH

## 首次設定

1. 安裝 Python：https://www.python.org/
2. 安裝 ffmpeg：https://ffmpeg.org/download.html
   - 下載解壓縮後，將 `bin/` 路徑加入系統環境變數 PATH
3. 雙擊 `start.bat` 即可使用，無需額外套件安裝

## 功能

- **音訊 / 影像分割**：選擇檔案後輸入多個 HH:MM:SS 時間點，自動切成多段
- **音訊 / 影像合併**：依序選擇檔案，合併為單一輸出檔

## 支援格式

| 類型 | 格式 |
|------|------|
| 音訊 | MP3、WAV、AAC、FLAC、M4A、OGG |
| 影像 | MP4、MKV、AVI、MOV、WMV、FLV |

## 輸出命名規則

| 操作 | 輸出格式 |
|------|---------|
| 分割 | `{原檔名}_part1.{副檔名}`、`{原檔名}_part2.{副檔名}`... |
| 合併 | `{第一個檔名}_merge.{副檔名}` |
