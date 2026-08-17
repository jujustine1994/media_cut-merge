# TODO.md

## 進行中：合併清單加不進檔案（未解決）

- [ ] **等重現** — 症狀：多次合併後「+ 新增」選了檔案，上方合併清單沒反應，清空列表也救不回，只有重開程式才好
  - 診斷儀器已裝好（2026-08-04），**下次遇到請立刻把 `logs/app.log` 給 AI 看**，不要先重開
  - 根因分析、已推翻的三個假設、log 判讀方式 → 全寫在 **`PITFALLS.md` 開頭「追查中」章節**，AI 請先讀那裡再動手
  - 已定位到 `main.py` 的 `_merge_add_file()`：`askopenfilenames()` 回傳空。機制已證實（Tk 的 COM 對話框失敗時靜默回空且不自我復原），但**觸發者尚未證實**

## 待辦事項

- [ ] **實際跑 GUI 驗收**（2026-08-04 改了 `main.py` 的錯誤處理，只用 monkeypatch 測過新程式碼路徑，尚未實際雙擊啟動器驗收）
  - 分割 / 合併 / 轉檔各跑一次，確認正常完成、進度條與「開啟資料夾」都正常
  - 確認 `logs/app.log` 有正常落檔，且沒有多出非預期的 `[WARN ]` / `[ERROR]` 行
- [ ] `git push`（本地 main 領先 origin，尚未推）
- [ ] 測試各種音影片格式（mp3, wav, mp4, mkv）
- [ ] 測試含空格的檔案路徑
- [ ] MD 文件搬入 `docs/`（規則要求根目錄只留 README；搬移前須先列清單確認，見 `templates\doc-init-protocol.md`）

## i18n 遷移順手發現的問題（2026-08-15，本次未動）

- [ ] **沒有 `requirements.txt` / `requirements_test.txt`**：測試目前靠全域安裝的 pytest 跑，
  `launcher.ps1` 也沒有建 venv。換一台機器或全域套件被動到就會炸，且沒有任何檔案記錄依賴。
  **建議做法**：至少補一份 `requirements_test.txt`（pytest），`launcher.ps1` 比照
  另外三個同批專案建 venv。本次沒動是因為那會改到啟動流程，不該混進 i18n 的 commit。
- [ ] **`_log(to_file=True)` 的技術診斷行會同時出現在 UI**（`main.py` 第 886–895 行）：
  給了 `to_file=True` 但沒給 `log_msg` 時，落檔那份就直接沿用 `msg`，
  所以像 `returncode` 這種給維護者看的診斷訊息也會出現在使用者的 log 面板上。
  **這是遷移前就有的既有行為，刻意原樣保留**（改了畫面就跟遷移前不一樣，無法用外觀驗證）。
  要修的話：凡是 `to_file=True` 的呼叫都補一個對應的使用者向 `msg`。
- [ ] **`.py` 檔在專案根目錄不在 `src/`**，不符 `windows-tool.md`（MD 搬 `docs/` 已列在上面）。
  本次刻意未搬——搬檔案會讓 i18n 的 diff 變成「整份檔案重寫」，
  之後就查不出「哪一行字串被改成 `t()`」。要搬請獨立 commit 且只做 `git mv`。
  （附帶確認：`__pycache__` 目前**沒有**被 git 追蹤，`.gitignore` 生效中，不需要 `git rm --cached`。）
- [ ] **`PITFALLS.md` 那個未解 bug 本次完全沒碰**（見本檔開頭），診斷儀器一行沒動、完整保留。

## i18n 譯文待校對

`locales/zh_cn.py`、`locales/en.py`、`locales/ja.py` 的譯文是 AI 產出的，**沒有母語者校對過**。
改譯文**不影響任何邏輯**（程式一律用 key 比對），改錯最壞只是畫面顯示怪。
校對時**只改 value、不要動 key**，`{current}` / `{total}` / `{name}` / `{count}` 這類具名
placeholder 必須保留（測試有檢查四語 placeholder 一致，改掉會紅）。

- [ ] **工具名稱是自己取的，沒有既定的英日名稱**：
  | key | zh_tw | zh_cn | en | ja |
  |---|---|---|---|---|
  | `gui.win.title` | `音影片工具` | `音视频工具` | `Audio & Video Tool` | `音声・動画ツール` |
  （`zh_tw.py` 18 行、`zh_cn.py` 8 行、`en.py` 8 行、`ja.py` 8 行）
- [ ] **三個分頁標籤的用詞**（`zh_tw.py` 19–21 行、其餘三檔 9–11 行）：
  | key | zh_tw | zh_cn | en | ja |
  |---|---|---|---|---|
  | `gui.tab.split` | `  分割  ` | `  分割  ` | `  Split  ` | `  分割  ` |
  | `gui.tab.merge` | `  合併  ` | `  合并  ` | `  Merge  ` | `  結合  ` |
  | `gui.tab.convert` | `  轉檔  ` | `  转换  ` | `  Convert  ` | `  変換  ` |
  「轉檔」简中用「转换」、日文用「変換」；「合併」日文用「結合」而不是外來語「マージ」——
  影音處理領域日文習慣用「結合」，但沒有把握。
  **⚠ 前後各兩個半形空格四語都保留了**，那是為了維持 tab 原本的寬度，校對時不要清掉。
- [ ] **`gui.status.segments` 英文沒做單複數**：`"{current} / {total} segments"`
  （`en.py` 第 56 行），`{total}` 是 1 的時候會顯示 `1 / 1 segments`。
  中日文沒這問題（`{total} 段` / `{total} 個`）。為一條訊息做 plural rule 不划算，
  但如果英文變成主力語言就該補。

## 可能的未來功能（有需要再做）

- 分割時顯示進度條
- 支援輸出格式轉換（不只 copy）
- 批次分割多個檔案
