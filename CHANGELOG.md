# CHANGELOG

> 現狀總覽見 ARCHITECTURE.md，本檔案只記錄歷史。

## 2026-08-15

### 新增（多語言 i18n：繁體中文／简体中文／English／日本語）
- `i18n.py`：介面文字查表核心。查找順序「目標語言 → 繁中母表 → key 本身」，永不 raise、永不回空字串
- `config.py` + `config.json`（已加入 `.gitignore`）：`language` 預設**空字串**，用來分辨「還沒選過」與「選了繁中」
- `locales/{zh_tw,zh_cn,en,ja}.py`：各 74 條字串，key 集合與 placeholder 四語完全一致
- `logtext.py`：`logs/app.log` 的訊息字串，**固定繁體中文不跟介面語言走**。抽出來的另一個目的是讓 `main.py` 能被「不得寫死中日文」那條測試涵蓋（否則只能整檔豁免＝等於把測試關掉）
- 首次啟動語言選擇視窗（全英文，不翻譯——那時還不知道使用者要哪個語言）；直接關掉＝採用第一個選項並照樣存檔
- 主視窗第一列語言下拉（本工具無設定視窗），選完存檔並跳英文重啟提示。**重開生效，不做即時切換**

### 變更
- `main.py`：127 條寫死的中日文字面全部改走 `t()`（AST 逐節點取代）
- `AUDIO_VIDEO_FILETYPES` / `VIDEO_FILETYPES` 兩個模組層級常數改為函式 `audio_video_filetypes()` / `video_filetypes()`：`t()` 不可在 import 時求值，常數會凍結在預設語言。萬用字元樣式留在 `AUDIO_VIDEO_PATTERNS` / `VIDEO_PATTERNS`（那是資料）
- `_log()` 新增 `log_msg` 參數：一個呼叫同時寫檔（繁中）＋推 UI（跟語言走）；不給 `log_msg` 時行為與原本一致
- 主視窗 grid row 0/1/2 整批下移為 1/2/3（讓出第 0 列給語言列）

### 修復
- `_split_worker()` 與 `_split_add_time()` 的區域變數 `t` 會遮蔽 `i18n.t`，導致同 scope 內 `t("...")` 變成對字串做呼叫而拋 `TypeError`（分割功能會整個失效）。改名為 `tp`
- **上面那條是遷移當場炸出的真 bug，不是預防性修改**：`_split_worker()`（`main.py` 第 406 行起）的
  `for i, t in enumerate(...)` 讓迴圈之後所有 `t(...)` 都變成「對字串做呼叫」→ `TypeError`，
  **分割功能整條路徑會掛掉**；`_split_add_time()`（第 370 行）同樣中招。
  另有三處潛伏但同樣危險：`_com_state()`（第 68 行）、`validate_time(t)`（第 117 行）、
  `time_to_seconds(t)`（第 128 行），已一併改名為 `apt` / `value`——
  這三個函式的呼叫端全部是位置參數，改參數名不影響任何行為
- 已加 `test_nothing_shadows_the_translation_function` 永久釘住：AST 掃描，任何函式把 `t` 綁成
  參數或區域名稱就紅燈。這類 bug 靜態看程式碼完全正常，只有那條 code path 真的跑到才炸，人眼複查擋不住

### 判斷紀錄
- **判成「資料」不翻**：輸出檔名樣板 `_part{n}` / `_merge`、暫存前綴 `_tmp_` / `_merge_list_` / `_merge_tmp_`
  （`main.py` 第 165、430、623–624 行）、concat 清單的 `file '...'` 格式、ffmpeg 全部參數與 codec 名
  （`CONVERT_CODECS`，第 106–111 行）、`CONVERT_EXT` 的副檔名與格式選項 `MP3`/`AAC`/`WAV`/`FLAC`
  （第 112 行；這四個同時是 `CONVERT_CODECS` 的鍵，翻了 `CONVERT_EXT[fmt]` 當場 `KeyError`）、
  檔案類型萬用字元樣式、Windows 檔名非法字元集合、`"00:00:00"` placeholder、log level 與 queue 訊息型別
- **`i18n.ui_font()` 建了但不呼叫**（`i18n.py` 第 98 行）：一接字型繁中外觀就跟遷移前不一樣，
  無法用「畫面長得一模一樣」驗證遷移沒改壞東西
- **未動 `PITFALLS.md` 的未解 bug**（合併清單加不進檔案）：診斷儀器完整保留，一行沒碰
- 其餘順手發現但未處理的問題（缺 `requirements.txt`、文件未收進 `docs/` 等）與待校對譯文見 `TODO.md`

### 測試（18 → 96 條，既有 18 條一條未改）
- `tests/test_i18n.py`：key 集合一致／placeholder 一致／不得寫死中日文（豁免清單只有 `i18n.py` 與 `logtext.py`，並用反向測試釘住 `main.py` 一定在掃描範圍且範圍非空）
- `tests/test_gui_build.py`：四語各建置一次 GUI（`withdraw()`，不進 mainloop），確認畫面無殘留 key
- `tests/test_first_run_language.py`：首次啟動視窗開得起來、點下去有存檔、第二次不再跳
- `tests/test_output_names.py`：四語的輸出檔名／暫存檔名／concat 清單格式／ffmpeg 參數必須完全相同（ffmpeg 全程 mock）
- `tests/conftest.py`：session 級共用 `tk_root`（避免反覆建立 Tcl 直譯器造成間歇性 `TclError`）

### 不翻譯的東西（資料，翻了是靜默污染）
輸出檔名樣板 `_part{n}` / `_merge`、暫存檔名前綴 `_tmp_` / `_merge_list_` / `_merge_tmp_`、
concat 清單的 `file '...'` 格式、ffmpeg 參數與 codec 名、`CONVERT_EXT` 的副檔名、
格式選項 MP3/AAC/WAV/FLAC（同時是 `CONVERT_CODECS` 的鍵）、檔案類型的萬用字元樣式、
Windows 檔名非法字元集合、`logs/app.log` 的內容。

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
