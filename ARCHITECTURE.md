# ARCHITECTURE.md — 音影片工具

## 總覽（含現狀）

tkinter GUI 工具，三個功能 Tab（分割 / 合併 / 轉檔）。
選檔使用 tkinter filedialog，處理核心依賴 ffmpeg，輸出至原始檔案所在目錄。

**已完成功能：**
- 音訊 / 影像分割（依 HH:MM:SS 時間點切多段）
- 音訊 / 影像合併（多檔排序後合併，支援上移 / 下移 / 移除 / 清空、自訂輸出檔名）
- 影像 → 音訊轉檔（MP3 / AAC / WAV / FLAC，可多選批量，失敗不中止）
- 非 ASCII 路徑處理：先輸出英文暫存檔再用 Python 改名
- 合併來源檔名含特殊字元處理：先建英文暫存 hardlink（失敗則複製）
- 執行紀錄落檔 `logs/app.log`（launcher.ps1 與 main.py 共用單一檔案）
- 關閉視窗防呆（任務執行中跳確認）
- 錯誤處理與診斷儀器（見下方「錯誤處理與診斷」）
- 多語言介面（繁中 / 简中 / English / 日本語，見下方「多語言（i18n）」）

**尚未完成：** 見 TODO.md（含一個未解 bug：合併清單加不進檔案，詳見 PITFALLS.md）

## 檔案清單

```
media_cut-merge.bat  → 薄 BAT 入口：單行呼叫 launcher.ps1
launcher.ps1         → 啟動邏輯：環境檢查（Python、ffmpeg）→ 執行 main.py
main.py              → 主程式：GUI App + 純函式（helpers）+ log/診斷函式
i18n.py              → 介面文字查表核心（LANGUAGES 註冊表 + t()）
config.py            → 讀寫 config.json（目前只有 language 一個欄位）
config.json          → 使用者設定（.gitignore）
logtext.py           → logs/app.log 的訊息字串，固定繁中不跟介面語言走
locales/
  __init__.py
  zh_tw.py           → 繁體中文（母表，其他語言的翻譯來源）
  zh_cn.py / en.py / ja.py
logs/app.log         → 執行紀錄，單一檔案累積（.gitignore）
README.md            → 專案識別
ARCHITECTURE.md      → 本檔
CHANGELOG.md         → 歷史記錄
PITFALLS.md          → 已知問題（開頭「追查中」章節是未解 bug）
TODO.md              → 待辦
tests/
  __init__.py
  conftest.py        → session 級共用 tk_root
  test_helpers.py    → 純函式單元測試（validate_time、build_*_cmd 等）
  test_smoke.py      → App 可匯入 smoke test
  test_i18n.py       → key 一致 / placeholder 一致 / 不得寫死中日文
  test_gui_build.py  → 四語各建置一次 GUI，確認無殘留 key
  test_first_run_language.py → 首次啟動選語言
  test_output_names.py → 四語輸出檔名與 ffmpeg 參數必須完全相同
```

## 執行流程

```
使用者雙擊 media_cut-merge.bat
  → 呼叫 launcher.ps1
      → 檢查 Python / ffmpeg
      → 執行 main.py
      → show_cth_banner()（終端 ASCII art）
      → tk.Tk()
      → _pick_language_on_first_run()（config.json 沒有合法 language 才跳）
      → ToolApp：load_config → i18n.set_lang → 建 widget
      → 主視窗
          ├─ [語言列] Language: 下拉（選完存檔 + 英文重啟提示）
          ├─ [分割 Tab] 選檔 + 輸入時間點 → ffmpeg -ss -t -c copy（多段）
          ├─ [合併 Tab] 選多檔排序 → ffmpeg concat -c copy
          └─ [轉檔 Tab] 多選影片 + 選格式 → ffmpeg -vn -acodec ...（批量，失敗不中止）
      → 底部共用進度區（queue 安全更新）
```

## 架構設計

### 純函式 vs App class

- **純函式**（module level）：`validate_time`、`time_to_seconds`、`build_split_cmd`、`build_merge_list`、`build_convert_cmd`、`show_cth_banner` — 可直接 pytest 測試
- **ToolApp class**：所有 UI 與執行緒邏輯，透過 `queue.Queue` + `_poll_queue`（每 100ms）安全更新 UI

### 執行緒安全

背景執行緒（worker）只允許呼叫：
- `self._log(msg, level, to_file, log_msg)` — 推 UI 記錄（`to_file=True` 時同時落檔）
- `self._set_progress(current, total, label)` — 更新進度條（determinate）
- `self._start_indeterminate(label)` — 切換為 indeterminate 動畫
- `self._done(output_dir, success)` — 完成通知

## 錯誤處理與診斷

這個 GUI 有三處「例外會造成永久性卡死、但畫面完全看不出來」的要害，都已加防護。改動這些地方時務必保留：

| 位置 | 若例外逃出去會怎樣 | 防護 |
|------|-------------------|------|
| `_poll_queue()` | 結尾的 `root.after(100, ...)` 不執行 → UI 輪詢**永久停擺**，記錄/進度/完成狀態全部不再更新 | `except queue.Empty` 之後補 `except Exception` 落檔 |
| worker 的 `finally` | 直接殺掉 worker thread → `_done()` 永不呼叫 → `is_running` 卡 True、開始按鈕**永久反灰** | 清理暫存的 `os.remove` 包 `try/except OSError`；`rmtree` 用 `ignore_errors=True` |
| tkinter callback | 預設只印 stderr，GUI 不崩，使用者只看到「按了沒反應」，log 毫無紀錄 | `root.report_callback_exception = self._on_tk_exception` 落檔 |

**診斷函式：**
- `_com_state()` — 回報執行緒 COM apartment 狀態（`CoGetApartmentType`）。Tk 在 Windows 的檔案對話框走 COM 的 `IFileOpenDialog`，失敗時是**靜默回傳空字串**，不拋例外也不自我復原
- `_merge_add_file()` 在 `askopenfilenames()` 回空時落檔記錄回傳型別、`repr`、COM 狀態、清單筆數 — 追查未解 bug 用，詳見 PITFALLS.md

## 關鍵設計決策

| 項目 | 決策 | 原因 |
|------|------|------|
| 分割指令 | `-ss` 放 `-i` 前，搭配 `-t`（持續時間）| 快速定位，比 `-to` 更穩定 |
| 合併指令 | `ffmpeg concat` + `_merge_list_tmp.txt` | 最穩定的多檔合併方式 |
| 路徑格式 | concat 清單使用正斜線 | 避免 Windows 反斜線被 ffmpeg 誤解 |
| 編碼（分割/合併）| `-c copy` | 串流複製，不重新編碼，速度快 |
| 轉檔進度條 | determinate（批量） | 以檔案數計算進度（N/total） |
| `_active_start_btn` | 追蹤當前執行中的按鈕 | 統一 _done 處理，不需 per-tab 判斷 |
| subprocess encoding | `errors='replace'` | 防止 Windows 中文路徑 stderr UnicodeDecodeError |
| log 路徑 | `_find_project_root()` 往上找 `launcher.ps1` | 不可寫死 `SCRIPT_DIR/../logs`，主程式在根目錄時會寫到專案外污染別的專案 |
| `_log(to_file=)` | 預設 `False` | fail-closed：漏帶旗標時是少記，不是把敏感資料誤記上磁碟 |
| `_log(log_msg=)` | 選填，落檔用的另一份文字 | UI 那份走 `t()` 跟語言變、落檔那份走 `LOG_TEXT` 固定繁中，但仍維持**一個呼叫同時處理兩邊**（不維護兩套呼叫，否則一定有地方漏記）。不給就退回用 `msg` |
| 錯誤行內容 | 只記 `type(e).__name__` + returncode | 禁止 `f"{e}"`，例外訊息會挾帶完整路徑與 stderr 片段 |

## 多語言（i18n）

完整做法見全域 `project-rules/windows-tool/tkinter-ui/pattern_i18n.py`。本專案的落點：

| 層 | 檔案 | 說明 |
|---|---|---|
| 查表核心 | `i18n.py` | `t(key, **fmt)`；查不到回 **key 本身**不回空字串（空按鈕看不見，`gui.btn.run` 看得見） |
| 語言註冊 | `i18n.LANGUAGES` | 新增語言＝加一行 + 複製一個 locale 檔，選單與測試自動涵蓋 |
| 譯文 | `locales/*.py` | 只匯出 `STRINGS`，四語 key 集合必須完全一致（有測試把關） |
| 設定 | `config.py` | `language` 預設**空字串**，用來分辨「沒選過」與「選了繁中」 |
| log 文字 | `logtext.py` | **固定繁中**，不跟介面語言走 |

**硬性規則（改動前必讀）：**

| 規則 | 理由 |
|---|---|
| **重開生效，不做即時切換** | 即時切換要建 widget 登記表逐一 `config(text=...)`，漏一個就是中英混雜 |
| `t()` **不可在 import 時求值** | 語言是讀完 config 才設的。`AUDIO_VIDEO_FILETYPES` 就是為此改成函式的 |
| 區域變數／參數**不可命名為 `t`** | 會遮蔽 `i18n.t`，同 scope 的 `t("...")` 變成對字串做呼叫而 `TypeError`。已踩過一次（`_split_worker`） |
| 帶變數的訊息用**具名** placeholder | `{count}` 而不是 `{0}`——翻譯時語序一變位置參數就錯位 |
| 格式規格不進字串表 | `{elapsed:.3f}` 留在譯文裡，翻譯者改成 `:.0f` 會把數字弄錯且不報錯。呼叫端先算好字串 |
| 首次啟動的語言視窗**不翻譯** | 那時還不知道使用者要哪個語言 |

**哪些字串是「資料」永遠不翻**（會被寫進檔案或拿去比對的）：
輸出檔名樣板 `_part{n}` / `_merge`、暫存檔名前綴 `_tmp_` / `_merge_list_` / `_merge_tmp_`、
concat 清單的 `file '...'` 格式、ffmpeg 參數與 codec 名、`CONVERT_EXT` 的副檔名、
格式選項 MP3/AAC/WAV/FLAC（同時是 `CONVERT_CODECS` 的鍵）、檔案類型的萬用字元樣式
（`AUDIO_VIDEO_PATTERNS` / `VIDEO_PATTERNS`）、Windows 檔名非法字元集合。
翻了的後果是使用者切語言後輸出到不同檔名、舊檔案對不起來，或 ffmpeg 直接失敗——
而且都是靜默發生的。`tests/test_output_names.py` 把這條釘死。

## 輸出命名規則

| 操作 | 輸出格式 |
|------|---------|
| 分割 | `{原檔名}_part1.{副檔名}`、`_part2`... |
| 合併 | `{第一個檔名}_merge.{副檔名}` |
| 轉檔 | `{原檔名}.{輸出格式副檔名}` |
