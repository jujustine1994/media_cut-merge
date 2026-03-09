# PITFALLS.md — 已知問題與解決方案

## 已知問題與解決方案

### [ffmpeg concat 路徑反斜線問題]
- 問題：Windows 路徑含反斜線時，ffmpeg 讀取 concat 清單報錯
- 原因：ffmpeg 把 `\` 當跳脫字元
- 解法：寫入清單時用 `fp.replace('\\', '/')` 轉為正斜線
- 禁止：直接把 Windows 原始路徑寫入清單

### [tkinter 視窗被主視窗遮住]
- 問題：選檔視窗跑到背景，使用者看不到
- 原因：tkinter 預設不置頂
- 解法：`root.attributes('-topmost', True)` 強制置頂

### [ffmpeg 找不到 / 未加入 PATH]
- 問題：執行時報「找不到 ffmpeg」
- 原因：使用者只解壓縮 ffmpeg，沒加入系統 PATH
- 解法：start.bat 加入 ffmpeg 檢查，並提示安裝步驟
