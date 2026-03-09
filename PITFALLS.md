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

### [bat 裡的中文字造成語法錯誤]
- 問題：bat 內含中文的行被 cmd.exe 亂碼解析，出現「不是內部或外部命令」錯誤
- 原因：cmd.exe 用 CP950（Big5）解析 bat 檔本身，Write 工具存 UTF-8，編碼不符導致中文字節被誤判為指令
- 解法：bat 全程只用英文；中文互動訊息交給 Python 程式處理
- 禁止：在 bat 裡放任何中文字，包含 echo、set /p、:: 註解

### [if 區塊內的 echo / set /p 不能含括號]
- 問題：執行到含括號的那行時出現「: was unexpected at this time.」
- 原因：batch 的 `if ( ... )` 區塊解析器看到 `)` 就認為 if 區塊結束，後面的 `:` 就成了非法字元
- 解法：if 區塊內的 echo 和 set /p 文字一律不放 `(` 和 `)`，改用 `-` 或其他符號代替
- 禁止：`set /p VAR=說明文字 (按 Enter 同意):` ← 這樣寫一定壞
