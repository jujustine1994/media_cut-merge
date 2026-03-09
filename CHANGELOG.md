# CHANGELOG

## 現狀總覽

**目前狀態：** 初版完成，可正常使用

**既有功能：**
- 音訊 / 影像分割（依 HH:MM:SS 時間點切段）
- 音訊 / 影像合併（多檔依序合併）
- tkinter 選檔視窗
- start.bat 環境自動檢查

**尚未完成：**
- 無（初版功能完整）

---

## 更新記錄

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
