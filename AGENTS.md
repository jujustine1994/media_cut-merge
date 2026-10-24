# AI 工作入口 — Video-Combiner

media_cut-merge；用途、需求與常用指令查 README 對應段落。

## 初始化（同一對話一次）

1. 本檔與工具已注入的入口視為已讀；若有根目錄 `PROGRESS.md`，只讀本次任務相關交接，續作時先確認位置。
2. 讀 `C:/Users/CTH/.claude/project-rules/templates/doc-init-protocol.md` 的「通用規範」「執行紀律」「共用程式碼庫」；再讀 `C:/Users/CTH/.claude/project-rules/general.md` 的「權限與全域存取規範」「資安規則」。詳細技巧依觸發條件載入。定位時只列標題，再擷取並輸出指定章節；不得以輸出全檔代替按需閱讀。
3. 依下表讀任務相關章節及要修改的檔案，不預載完整 README、架構、TODO 或歷史。回指已讀入口、類型規則或模板不重啟初始化，不執行共用檔「沒有 AGENTS」流程。

## 任務閱讀範圍

下列全域相對路徑均以 `C:/Users/CTH/.claude/project-rules/` 為基準；本機詳細規則維持原位置，不複製第二套。

| 任務 | 修改／執行前閱讀 |
|---|---|
| README／文件 | 要改的完整段落；更新 README 前讀 `signature.md`，保留 CTH 簽名；文件位置規範見 `templates/doc-init-protocol.md`「文件放置位置」，不為套範本搬檔 |
| 程式／功能 | `docs/ARCHITECTURE.md` 先看標題、再讀相關模組／流程／設計／測試章節；`docs/PITFALLS.md` 相關地雷；`docs/TODO.md` 相關問題與刻意保留的設計；再讀要修改的程式，不能憑歷史敘述推定現行行為 |
| GUI／多語言／log | `windows-tool.md`「Tkinter UI 模式庫」「多語言（i18n）」「執行紀錄（log）」及任務涉及的本地設計；保留資料鍵／格式與介面文字分離，本地既有 log 語言／輪替例外先釐清，不順手統一 |
| 啟動器／依賴／環境 | `windows-tool.md`「元件自動安裝原則」「venv 位置」「專案文件規範」及本地環境說明；依該檔觸發條件讀 Windows templates／pitfalls，啟動器與無黑窗驗收不可省略 |
| 新檔／結構／發布 | `windows-tool.md`「專案目錄結構」「專案文件規範」；建立程式檔先讀 `signature.md`；發布另讀 `windows-tool/windows-tool-release.md`，推 tag／建 Release 依既有要求確認 |
| 待辦／續作／追溯 | `docs/TODO.md` 相關項目；有 `PROGRESS.md` 時讀相關交接；只有追溯原因時才查 CHANGELOG 對應日期 |

`windows-tool.md` 的其餘適用限制仍生效；任務跨範圍就合併相關章節，並遵守下方本地界線。全域安全、隱私、權限、原稿與手改內容保護不因精簡閱讀取消。

## 本專案界線

- 分割／合併／轉檔前讀 `docs/ARCHITECTURE.md`「執行流程」「錯誤處理與診斷」「輸出命名規則」及 `docs/PITFALLS.md`。
- 原始媒體與手改輸出保留；不因入口遷移調整 ffmpeg、外部依賴或命名。README 與架構入口若有舊新差異，先核對實際啟動檔，不依模板還原程式。

## 驗證與收尾

- 純文件：重讀修改段落，檢查引用路徑／章節、閱讀範圍、無重複初始化／循環載入；跑 `git diff --check`，核對只含本次差異。
- 程式：先查 `docs/ARCHITECTURE.md` 的相關驗證要求，既有一鍵檢查優先；單元測試入口為 `tests/`；再依 `templates/execution-protocol.md` 驗收受影響功能，不以單元測試取代 GUI／啟動器／真實輸出驗證。不為文件驗收執行有副作用的工具。
- 安全：檢查 `.gitignore` 排除 `.env`、`*.pem` 及實際金鑰／個人設定／執行資料；不輸出敏感內容，發布前確認未被追蹤。不刪 `scripts/` 腳本，修改 README 或腳本前先查現有 `scripts/README.md`（若有）。
- 在 `docs/CHANGELOG.md` 記錄本次變更；架構／行為有改才同步架構文件。TODO 完成項先記 CHANGELOG 再移除，不刪設計判斷。保留其他對話的未提交改動，只暫存本次檔案／差異，不 push。
- 未執行的檢查明列未實測，不沿用舊測試數。入口遷移不授權修改程式、套件、部署、外部工具、原稿或正式資料；功能任務另依當次授權處理。
