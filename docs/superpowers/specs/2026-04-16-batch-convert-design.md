# Spec: 轉檔 Tab 批量轉檔

**日期：** 2026-04-16
**狀態：** 已確認

---

## 目標

讓轉檔 Tab 支援一次選取多個影片檔案，全部套用同一輸出格式批量轉檔，失敗不中止，逐檔回報結果。

---

## 變動範圍

只改 `main.py` 的轉檔 Tab 相關方法，不影響分割/合併 Tab。

---

## UI 變動

### 來源影片區

原本：`readonly Entry`（顯示單一路徑）

新：`ttk.Label`（顯示選取狀態文字）

| 狀態 | 顯示文字 |
|------|---------|
| 未選擇 | `未選擇` |
| 已選擇 | `已選擇 N 個檔案` |

選擇按鈕改用 `filedialog.askopenfilenames`（允許 Ctrl+Click 多選），回傳 tuple，儲存於 `self._convert_files`（初始為空 tuple，在 `_build_convert_tab` 初始化）。Label widget 儲存為 `self._convert_label`，選完後更新文字。

### 輸出格式 / 開始按鈕

不變。格式選擇套用於全部選取的檔案。

---

## 執行邏輯

### `_convert_start` 驗證

- `self._convert_files` 為空 → `messagebox.showerror("錯誤", "請先選擇來源影片")`，return

### 方法簽名變更

`_convert_worker(self, input_path, fmt)` → `_convert_worker(self, files, fmt)`（`files` 為路徑 list）
`_convert_start` 傳入 `list(self._convert_files)`

### `_convert_worker(files, fmt)` 行為

1. `_set_progress(0, len(files), f"0 / {len(files)}")`
2. 對每個 `input_path` in `files`：
   - `out_path = 同目錄 / base_name + CONVERT_EXT[fmt]`
   - `_log(f"[INFO] {basename(input_path)} → {basename(out_path)}")`
   - 執行 `build_convert_cmd`，`subprocess.run(..., encoding='utf-8', errors='replace')`
   - 成功 → `_log("[OK] {basename(out_path)}")` + `success_count += 1` + 記錄 `first_success_dir`
   - 失敗 → `_log(f"[ERROR] 轉檔失敗：{err}")`
   - `_set_progress(idx, len(files), f"{idx} / {len(files)}")`
3. 完成後：
   - `_log(f"\n[OK] 完成！（{success_count}/{len(files)} 成功）")` 若有成功
   - `_log(f"\n[WARNING] 全部失敗（0/{len(files)}）")` 若全失敗
4. `_done(first_success_dir, success_count > 0)`
   - `first_success_dir`：第一個成功檔案的目錄；全失敗時傳 `""`

### 進度條

改用 determinate mode（原本單一檔案用 indeterminate）。

---

## 測試

新增至 `tests/test_helpers.py`：`build_convert_cmd` 已有測試，無需新增純函式測試。

Smoke test 不需改動（ToolApp 結構不變）。

---

## 不在本次範圍

- 不同檔案套用不同格式
- 轉檔完成後自動清除選取清單
- 顯示各檔案的轉檔時間
