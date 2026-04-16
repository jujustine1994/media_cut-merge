# ARCHITECTURE.md — 音影片工具

## 工具總覽

tkinter GUI 工具，三個功能 Tab（分割 / 合併 / 轉檔）。
選檔使用 tkinter filedialog，處理核心依賴 ffmpeg，輸出至原始檔案所在目錄。

## 檔案清單

```
media_cut-merge.bat  → 薄 BAT 入口：單行呼叫 launcher.ps1
launcher.ps1         → 啟動邏輯：環境檢查（Python、ffmpeg）→ 執行 main.py
main.py              → 主程式：GUI App + 純函式（helpers）
tests/
  __init__.py
  test_helpers.py    → 純函式單元測試（validate_time、build_*_cmd 等）
  test_smoke.py      → App 可匯入 smoke test
```

## 執行流程

```
使用者雙擊 media_cut-merge.bat
  → 呼叫 launcher.ps1
      → 檢查 Python / ffmpeg
      → 執行 main.py
      → show_cth_banner()（終端 ASCII art）
      → tk.Tk() 主視窗
          ├─ [分割 Tab] 選檔 + 輸入時間點 → ffmpeg -ss -t -c copy（多段）
          ├─ [合併 Tab] 選多檔排序 → ffmpeg concat -c copy
          └─ [轉檔 Tab] 選影片 + 選格式 → ffmpeg -vn -acodec ...
      → 底部共用進度區（queue 安全更新）
```

## 架構設計

### 純函式 vs App class

- **純函式**（module level）：`validate_time`、`time_to_seconds`、`build_split_cmd`、`build_merge_list`、`build_convert_cmd`、`show_cth_banner` — 可直接 pytest 測試
- **ToolApp class**：所有 UI 與執行緒邏輯，透過 `queue.Queue` + `_poll_queue`（每 100ms）安全更新 UI

### 執行緒安全

背景執行緒（worker）只允許呼叫：
- `self._log(msg)` — 寫入 log
- `self._set_progress(current, total, label)` — 更新進度條（determinate）
- `self._start_indeterminate(label)` — 切換為 indeterminate 動畫
- `self._done(output_dir, success)` — 完成通知

## 關鍵設計決策

| 項目 | 決策 | 原因 |
|------|------|------|
| 分割指令 | `-ss` 放 `-i` 前，搭配 `-t`（持續時間）| 快速定位，比 `-to` 更穩定 |
| 合併指令 | `ffmpeg concat` + `_merge_list_tmp.txt` | 最穩定的多檔合併方式 |
| 路徑格式 | concat 清單使用正斜線 | 避免 Windows 反斜線被 ffmpeg 誤解 |
| 編碼（分割/合併）| `-c copy` | 串流複製，不重新編碼，速度快 |
| 轉檔進度條 | indeterminate | ffmpeg 無法從 stdout 取得進度百分比 |
| `_active_start_btn` | 追蹤當前執行中的按鈕 | 統一 _done 處理，不需 per-tab 判斷 |
| subprocess encoding | `errors='replace'` | 防止 Windows 中文路徑 stderr UnicodeDecodeError |

## 輸出命名規則

| 操作 | 輸出格式 |
|------|---------|
| 分割 | `{原檔名}_part1.{副檔名}`、`_part2`... |
| 合併 | `{第一個檔名}_merge.{副檔名}` |
| 轉檔 | `{原檔名}.{輸出格式副檔名}` |
