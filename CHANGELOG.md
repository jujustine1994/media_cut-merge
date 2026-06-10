# CHANGELOG

## 2026-06-10

### 修正
- `winget install Python` 加入 `--override "/quiet PrependPath=1 Include_pip=1"`，確保靜默安裝後 Python 自動加進 PATH

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

## 現狀總覽

**目前狀態：** 穩定，可正常使用

**既有功能：**
- 音訊 / 影像分割（依 HH:MM:SS 時間點切段）
- 音訊 / 影像合併（多檔依序合併）
- tkinter 選檔視窗
- 啟動器環境自動檢查（Python、ffmpeg）
- 啟動器架構：薄 BAT（2 行）+ launcher.ps1（UTF-8 BOM），無中文亂碼

**尚未完成：**
- 無（初版功能完整）

---

## 更新記錄

### 2026-03-11
- **架構**: 啟動器改用薄 BAT（2 行）+ launcher.ps1 架構，原 `media_cut-merge.bat` 邏輯全部移至 PS1
- **架構**: launcher.ps1 加 UTF-8 BOM，確保 Windows PowerShell 5.x 正確解析中文
- **修改**: `media_cut-merge.bat` 縮減為 2 行薄殼

### 2026-03-09

**新增**
- `main.py`：主程式，含分割、合併完整邏輯
- `start.bat`：啟動腳本，含 Python 與 ffmpeg 環境檢查
- `README.md`、`ARCHITECTURE.md`、`CHANGELOG.md`、`PITFALLS.md`、`TODO.md`
- `.gitignore`

**修改**
- 合併輸出命名規則改為 `{原檔名}_merge.{副檔名}`（原為 `merged_{原檔名}`）
- `start.bat` 改名為 `media_cut-merge.bat`，並升級前置檢查邏輯（自動安裝 Python / ffmpeg via winget）
- bat 全面英文化（解決 CP950 編碼地雷）
- 修正 if 區塊內 set /p 含括號導致「: was unexpected at this time.」的 bug

**新增**
- `PITFALLS.md` 補充：bat 中文字編碼地雷、if 區塊括號地雷
