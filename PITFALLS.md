# PITFALLS.md — 已知問題與解決方案

## 追查中（未解決）

### [合併清單加不進檔案，只能重開程式]（2026-08-04 起追查）

**症狀（使用者回報）：** 連續做過多次合併之後，「+ 新增」選了檔案，上方合併清單完全沒反應。
按「清空列表」也救不回，**只有重開程式才會好**。console 乾淨、沒有任何 Traceback，`logs/app.log` 也毫無紀錄。

**已定位的層級：** `_merge_add_file()` 中 `filedialog.askopenfilenames()` 回傳空 →
原本 `if paths:` 直接跳過 → 靜默無反應。這唯一符合全部三個現象（卡在 listbox 而非進度區、
console 無例外、清空無效）。

**已實測推翻的假設（不要再重試）：**

| 假設 | 推翻依據 |
|---|---|
| 檔名含非 BMP 字元讓 Listbox insert 拋錯 | Tcl 8.6.15 + Python 3.13 已支援，實測 emoji／超出 BMP 漢字／大括號／超長檔名 8 種全部 insert 成功 |
| Windows MAX_PATH 260 限制 | 該機器 `HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 1` |
| `os.startfile`（開啟資料夾）把主執行緒鎖進 MTA 害 IFileOpenDialog 失效 | 實測 startfile 後確實變 `MTA/IMPLICIT_MTA`，但隨後 `CoInitializeEx(STA)` 仍回 `S_OK`，沒被擋 |

**已證實的機制（但尚未證實由誰觸發）：** Tk 在 Windows 的檔案對話框走 COM 的 `IFileOpenDialog`。
實測 COM 計數歸零後 `CoCreateInstance(FileOpenDialog)` 回 `CO_E_NOTINITIALIZED (0x800401F0)`，
而 **Tk 遇到這種失敗是靜默回傳空字串**——不拋例外、不寫訊息，且**不會自我復原，只有重新
`CoInitializeEx` 才行（＝重啟程式）**。與症狀完全吻合。

另附帶查到的事實：`os.startfile` 會**洩漏一次 COM 初始化且永不釋放**（方向是 +1，所以它本身
不會造成「未初始化」，反而讓 COM 保持初始化）。

**下次怎麼查：** 診斷儀器已經裝在 `main.py` 了，請使用者重現後直接看 `logs/app.log`：

- 出現 `[WARN ] 合併選檔回傳空 | type=... repr=... | COM ... | 清單現有 N 筆`
  → **使用者明明有選檔卻出現這行，就確認是本 bug**；重點看 `COM` 欄位是不是
  `未進入 apartment(hr=0x800401F0)` 或 `MTA`（正常應為 `STA`），以及 `repr` 是 `()` 還是 `''`
- 出現 `[ERROR] 合併選檔 askopenfilenames -> XxxError` → 對話框直接拋例外，是另一條路徑
- 出現 `[ERROR] UI callback -> XxxError` → tkinter 吞掉的例外，看 console 完整 traceback

（使用者按「取消」也會寫 `回傳空` 那行，這是無法從 Python 端區分的，靠使用者自述判讀。）

---

## 已解決

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
