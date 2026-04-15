# Spec: 音影片工具 tkinter GUI 改版 + 轉檔功能

**日期：** 2026-04-15
**狀態：** 已確認

---

## 目標

將現有 CLI 工具（`main.py`）全面改為 tkinter 完整 GUI，並新增「影像轉音訊」功能。使用者雙擊 BAT 後直接看到視窗，不再需要在終端輸入指令。

---

## 架構

### 視窗結構

- 單一主視窗，固定寬度 520px，可縱向縮放
- `ttk.Notebook` 三個 Tab：分割 / 合併 / 轉檔
- 底部共用「處理進度區」（所有 Tab 共用同一個 log 與進度條）
- 執行時 disable 輸入控件與開始按鈕，完成後顯示「開啟資料夾」按鈕

### 檔案結構（不變）

```
media_cut-merge.bat   → 薄 BAT，呼叫 launcher.ps1
launcher.ps1          → 環境檢查 + 啟動 main.py
main.py               → 主程式（本次全面重寫）
```

---

## 格式常數

```python
AUDIO_VIDEO_FILETYPES = [
    ('音訊/影像', '*.mp3 *.wav *.aac *.flac *.m4a *.ogg *.mp4 *.mkv *.avi *.mov *.wmv *.flv'),
    ('所有檔案', '*.*')
]
VIDEO_FILETYPES = [
    ('影像', '*.mp4 *.mkv *.avi *.mov *.wmv *.flv'),
    ('所有檔案', '*.*')
]
```

---

## Tab 1：分割

**輸入區：**
- LabelFrame「來源檔案」：唯讀 Entry（顯示路徑）+ 選擇按鈕，選檔格式 `AUDIO_VIDEO_FILETYPES`
- LabelFrame「分割時間點」：
  - Entry（placeholder `00:00:00`，灰字）+ 新增按鈕
  - 支援 Enter 鍵直接新增
  - Listbox 顯示已加入的時間點
  - 刪除選取按鈕

**執行邏輯：**
- 至少選一個檔案 + 一個時間點，否則 `messagebox.showerror`
- 時間點在執行前自動排序
- 輸出命名：`{原檔名}_part1.{副檔名}`、`_part2`...
- 使用 `ffmpeg -ss -t -c copy`（與現有邏輯相同）

---

## Tab 2：合併

**輸入區：**
- LabelFrame「來源檔案（依序排列）」：
  - Listbox 顯示已選檔案（含編號）
  - 按鈕列：新增 / 移除 / ↑ 上移 / ↓ 下移
  - 選檔格式 `AUDIO_VIDEO_FILETYPES`

**執行邏輯：**
- 至少 2 個檔案，否則 `messagebox.showerror`
- 輸出命名：`{第一個檔名}_merge.{副檔名}`（同第一個檔案的副檔名）
- 使用 `ffmpeg concat`，暫存 `_merge_list_tmp.txt`（完成後刪除）

---

## Tab 3：轉檔（新功能）

**輸入區：**
- LabelFrame「來源影片」：唯讀 Entry + 選擇按鈕，選檔格式 `VIDEO_FILETYPES`
- LabelFrame「輸出格式」：Radio buttons — MP3（預設）/ AAC / WAV / FLAC

**執行邏輯：**
- 必須選檔案，否則 `messagebox.showerror`
- 輸出命名：`{原檔名}.{輸出格式副檔名}`，同原始資料夾
- ffmpeg codec 對應：

| 格式 | ffmpeg 參數 |
|------|------------|
| MP3  | `-vn -acodec libmp3lame -q:a 2` |
| AAC  | `-vn -acodec aac -b:a 192k` |
| WAV  | `-vn -acodec pcm_s16le` |
| FLAC | `-vn -acodec flac` |

---

## 共用進度區

- `ttk.Label`：顯示當前狀態文字
- `ttk.Progressbar`（determinate mode）
- `scrolledtext.ScrolledText`：Consolas 9pt，唯讀，自動捲到底
- 「開啟資料夾」按鈕：完成後才顯示（`pack`），下次執行前 `pack_forget`

---

## 執行緒安全

使用骨架的 `queue.Queue` + `_poll_queue`（每 100ms）模式，背景執行緒只透過 `_log` / `_set_progress` / `_done` 發訊息，不直接操作 UI 控件。

---

## Pattern 使用清單

| Pattern | 用途 |
|---------|------|
| `skeleton.py` | 骨架：queue、進度區、開啟資料夾 |
| `pattern_placeholder.py` | 分割時間點 Entry 的灰字 placeholder |
| `pattern_topmost.py` | 視窗置頂啟動（短暫置頂後取消） |
| `pattern_cth_banner.py` | 終端 ASCII banner（視窗開啟前） |

---

## 不在本次範圍

- 拖曳選檔
- 進度條顯示 ffmpeg 實際百分比（分割/合併用 determinate 段數進度，轉檔用 indeterminate）
- 批次處理多個檔案
