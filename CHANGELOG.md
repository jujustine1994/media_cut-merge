# CHANGELOG

> 現狀總覽見 ARCHITECTURE.md，本檔案只記錄歷史。

## 2026-08-04

### 修復
- `main.py` `_merge_worker()`：`finally` 區塊的 `os.remove(list_path)` 補上 `try/except OSError`。原本暫存清單檔被鎖住（防毒掃描）時例外會殺掉整個 worker thread，`_done()` 永遠不會被呼叫 → `is_running` 卡在 True、開始按鈕永久反灰、進度條一直轉
- `main.py` `_poll_queue()`：補 `except Exception`。原本只 catch `queue.Empty`，任何其他例外都會讓結尾的 `root.after(100, ...)` 跳過，UI 輪詢從此永久停擺（記錄、進度、完成狀態全部不再更新）

### 新增（診斷儀器，追查「合併清單加不進檔案」用）
- `main.py` `_com_state()`：回報執行緒 COM apartment 狀態（`CoGetApartmentType`），全程包 `except` 不拖垮主程式
- `main.py` `_merge_add_file()`：`askopenfilenames()` 改為包 `try/except`，並在回傳空時落檔記錄回傳型別、`repr`、COM 狀態與清單現有筆數，同時在進度區顯示提示。原本回空是靜默跳過，什麼線索都留不下
- `main.py` `_on_tk_exception()`：掛上 `root.report_callback_exception`，把 tkinter 原本只印到 stderr 的 callback 例外一併落檔
- `PITFALLS.md`：新增「追查中」章節，記錄症狀、已定位層級、**已實測推翻的三個假設**（非 BMP 字元／MAX_PATH／`os.startfile` 鎖 MTA）、已證實的 COM 機制，以及 log 判讀方式

## 2026-07-19

### 新增
- `main.py`：關閉視窗防呆。任務執行中（`self.is_running` 為 True）按右上角 X 會跳出「確認關閉」提示，選否可取消關閉；沒有任務執行中則直接關閉。透過 `root.protocol("WM_DELETE_WINDOW", self._on_close)` 攔截

## 2026-07-17

### 文件修正
- README.md：啟動指令 `start.bat`（舊名）改為 `media_cut-merge.bat`（實際檔名）；「功能」與「支援格式」章節補上轉檔功能說明

### 新增
- 導入執行紀錄（log）規範：`launcher.ps1` 與 `main.py` 皆落檔至 `logs/app.log`（單一檔案累積，不分割）
- `launcher.ps1`：`Write-Log` / `Write-LogHeader`（放在 `trap` 之前，閃退也記得到），記錄啟動、環境就緒、winget 找不到、主程式異常結束、CRASH
- `main.py`：`_find_project_root()` / `_write_log()` / `_write_log_header()`；`_log()` 加 `to_file` 參數（預設 `False`，fail-closed）
- 分割 / 合併 / 轉檔三個 worker 皆採三段式落檔：任務起始（含檔名/段數/格式等關鍵設定）、錯誤（ffmpeg returncode 或例外 `type(e).__name__`，不寫入完整 stderr/例外內容）、任務結果（成功/失敗 + 耗時）
- `.gitignore` 加入 `logs/`

## 2026-06-21

### 修復
- 合併：來源檔名含單引號（`'`）會破壞 ffmpeg concat 清單格式，導致「Error opening input files: Invalid data found when processing input」。修法：合併前先用英文暫存連結（hardlink，失敗則複製）取代原檔名餵給 ffmpeg，完成後清除暫存
- 輸出檔名（合併/分割/轉檔）含非 ASCII 字元時，先輸出到英文暫存檔再用 Python 改名，避免依賴 ffmpeg 對應路徑的處理結果

### 新增
- 合併分頁加「輸出檔名」欄，選檔後自動帶入 `{第一個檔名}_merge`（副檔名隨第一個來源檔），使用者可自行修改；開始前檢查空白與非法字元（`\ / : * ? " < > |`）

### 修改
- 合併來源選擇：`askopenfilename`（單選）→ `askopenfilenames`（多選），一次可選多個檔案加入合併清單

---

## 2026-06-10

### 修正
- `winget install Python` 加入 `--override "/quiet PrependPath=1 Include_pip=1"`，確保靜默安裝後 Python 自動加進 PATH
- `launcher.ps1` 加入全域 `trap`，攔截未處理例外，防止執行失敗時視窗直接閃退

---

## 2026-04-17

### 新增
- 轉檔 Tab 批量轉檔：一次選取多個影片，套用同一格式批量轉，失敗不中止，逐檔回報

### 修改
- 轉檔來源選擇：`readonly Entry`（單選）→ `ttk.Label` + `askopenfilenames`（多選）
- 轉檔進度條：indeterminate → determinate（N / total 顯示）

---

## 2026-04-16

### 新增
- tkinter 完整 GUI 介面（三 Tab：分割 / 合併 / 轉檔）
- 轉檔功能：影像（MP4/MKV/AVI/MOV/WMV/FLV）→ 音訊（MP3/AAC/WAV/FLAC）
- 單元測試：`tests/test_helpers.py`（16 個測試）+ `tests/test_smoke.py`（2 個測試）

### 修改
- 分割 / 合併：操作介面從 CLI 問答改為 GUI（tkinter Notebook Tab）
- 分割 / 合併：選檔格式合併為「音訊 + 影像」（不需預先選類型）
- 進度條：分割用 determinate（段數）；合併 / 轉檔用 indeterminate
- 分割：新增重複時間點防呆
- subprocess：加 `errors='replace'` 防 Windows 中文 stderr 亂碼

### 移除
- CLI 互動流程（`input()` 問答選單）

---

## 2026-03-11
- **架構**: 啟動器改用薄 BAT（2 行）+ launcher.ps1 架構，原 `media_cut-merge.bat` 邏輯全部移至 PS1
- **架構**: launcher.ps1 加 UTF-8 BOM，確保 Windows PowerShell 5.x 正確解析中文
- **修改**: `media_cut-merge.bat` 縮減為 2 行薄殼

## 2026-03-09

### 新增
- `main.py`：主程式，含分割、合併完整邏輯
- `start.bat`：啟動腳本，含 Python 與 ffmpeg 環境檢查
- `README.md`、`ARCHITECTURE.md`、`CHANGELOG.md`、`PITFALLS.md`、`TODO.md`
- `.gitignore`
- `PITFALLS.md` 補充：bat 中文字編碼地雷、if 區塊括號地雷

### 修改
- 合併輸出命名規則改為 `{原檔名}_merge.{副檔名}`（原為 `merged_{原檔名}`）
- `start.bat` 改名為 `media_cut-merge.bat`，並升級前置檢查邏輯（自動安裝 Python / ffmpeg via winget）
- bat 全面英文化（解決 CP950 編碼地雷）
- 修正 if 區塊內 set /p 含括號導致「: was unexpected at this time.」的 bug
