# locales/zh_tw.py
"""locales/zh_tw.py — 繁體中文（母表）

改這裡的譯文不影響任何邏輯：程式一律用 key 比對。改錯最壞的情況只是
畫面顯示怪怪的。

**不在這裡的東西**（它們是資料，翻了會靜默弄壞使用者的檔案）：
輸出檔名樣板 `_part{n}` / `_merge`、暫存檔名前綴 `_tmp_` /
`_merge_list_` / `_merge_tmp_`、concat 清單檔的 `file '...'` 格式、
ffmpeg 參數與 codec 名、CONVERT_EXT 的副檔名、檔案類型的萬用字元樣式、
格式選項的 MP3/AAC/WAV/FLAC（同時是 CONVERT_CODECS 的鍵）。
"""

from __future__ import annotations

STRINGS: dict[str, str] = {
    # ---- 視窗與分頁 ----
    "gui.win.title":            "音影片工具",
    "gui.tab.split":            "  分割  ",
    "gui.tab.merge":            "  合併  ",
    "gui.tab.convert":          "  轉檔  ",

    # ---- 區塊標題 ----
    "gui.frame.source_file":    " 來源檔案 ",
    "gui.frame.split_times":    " 分割時間點 ",
    "gui.frame.merge_files":    " 來源檔案（依序排列）",
    "gui.frame.outname":        " 輸出檔名 ",
    "gui.frame.source_video":   " 來源影片 ",
    "gui.frame.format":         " 輸出格式 ",
    "gui.frame.progress":       " 處理進度 ",

    # ---- 按鈕 ----
    "gui.btn.pick":             "選擇",
    "gui.btn.add_time":         "新增",
    "gui.btn.del_time":         "刪除選取",
    "gui.btn.split_start":      "▶  開始分割",
    "gui.btn.merge_add":        "+ 新增",
    "gui.btn.merge_remove":     "✕ 移除",
    "gui.btn.merge_up":         "↑ 上移",
    "gui.btn.merge_down":       "↓ 下移",
    "gui.btn.merge_clear":      "清空列表",
    "gui.btn.merge_start":      "▶  開始合併",
    "gui.btn.convert_start":    "▶  開始轉檔",
    "gui.btn.open_folder":      "開啟資料夾",

    # ---- 標籤 ----
    "gui.lbl.no_file":          "未選擇",
    "gui.lbl.selected_count":   "已選擇 {count} 個檔案",

    # ---- 檔案對話框的類型說明（萬用字元樣式本身是資料，不在這裡）----
    "gui.filetype.audio_video": "音訊/影像",
    "gui.filetype.video":       "影像",
    "gui.filetype.all":         "所有檔案",

    # ---- 檔案對話框標題 ----
    "gui.dlg.pick_split":       "選擇要分割的檔案",
    "gui.dlg.pick_merge":       "選擇要合併的檔案（可多選）",
    "gui.dlg.pick_convert":     "選擇要轉檔的影片",

    # ---- 進度／狀態 ----
    "gui.status.idle":          "等待開始...",
    "gui.status.preparing":     "準備中...",
    "gui.status.merging":       "合併中...",
    "gui.status.done":          "完成！",
    "gui.status.failed":        "發生錯誤，請查看上方記錄",
    "gui.status.segments":      "{current} / {total} 段",

    # ---- 畫面上的執行記錄（落檔的那份在 logtext.py，永遠繁中）----
    "gui.log.hint":             "請設定完成後按「開始」。\n",
    "gui.log.unknown_error":    "未知錯誤",
    "gui.log.seg_fail":         "[ERROR] 第 {idx} 段失敗：{err}",
    "gui.log.seg_returncode":   "第 {idx} 段 ffmpeg -> returncode {code}",
    "gui.log.seg_ok":           "[OK] 第 {idx} 段：{name}",
    "gui.log.split_done":       "\n[OK] 分割完成！共 {count} 個檔案",
    "gui.log.split_partial":    "\n[WARNING] 完成（{success}/{total} 成功）",
    "gui.log.merge_running":    "[INFO] 合併 {count} 個檔案...",
    "gui.log.merge_fail":       "[ERROR] 合併失敗：{err}",
    "gui.log.merge_returncode": "合併 ffmpeg -> returncode {code}",
    "gui.log.merge_ok":         "[OK] 合併完成：{name}",
    "gui.log.convert_fail":     "[ERROR] 轉檔失敗：{err}",
    "gui.log.convert_returncode": "第 {idx} 個檔案 ffmpeg -> returncode {code}",
    "gui.log.convert_item_error": "第 {idx} 個檔案 -> {exc}",
    "gui.log.convert_done":     "\n[OK] 完成！（{success}/{total} 成功）",
    "gui.log.convert_all_fail": "\n[WARNING] 全部失敗（0/{total}）",
    "gui.log.unexpected":       "\n[ERROR] 未預期錯誤：{exc}",
    "gui.log.elapsed_ok":       "成功，耗時 {minutes}分{seconds}秒",
    "gui.log.elapsed_fail":     "失敗，耗時 {minutes}分{seconds}秒",
    "gui.log.picker_no_window": "（選檔視窗沒有開啟就直接回空（{elapsed} 秒），"
                                "這是已知問題，請重開程式並回報 logs\\app.log）\n",
    "gui.log.picker_cancelled": "（未加入任何檔案）\n",

    # ---- 訊息框 ----
    "gui.msg.format_title":     "格式錯誤",
    "gui.msg.time_required":    "請輸入時間點",
    "gui.msg.time_format":      "格式須為 HH:MM:SS（例：00:01:30）",
    "gui.msg.duplicate_title":  "重複",
    "gui.msg.duplicate_body":   "{time} 已存在清單中",
    "gui.msg.error_title":      "錯誤",
    "gui.msg.need_source":      "請先選擇來源檔案",
    "gui.msg.need_time":        "請至少新增一個時間點",
    "gui.msg.need_two_files":   "請至少選擇 2 個檔案",
    "gui.msg.need_outname":     "請輸入輸出檔名",
    "gui.msg.bad_outname":      "檔名不可包含 \\ / : * ? \" < > |",
    "gui.msg.need_video":       "請先選擇來源影片",
    "gui.msg.pick_fail_title":  "選檔失敗",
    "gui.msg.pick_fail_body":   "檔案選取視窗發生錯誤（{exc}）。\n"
                                "請關閉程式重新開啟，並把 logs\\app.log 提供給 AI 查詢。",
    "gui.msg.close_title":      "確認關閉",
    "gui.msg.close_body":       "任務執行中，確定要關閉視窗嗎？關閉後任務會被中止。",
}
