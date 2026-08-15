# logtext.py
"""logs/app.log 的訊息字串——**永遠繁體中文，不跟使用者介面語言走**。

log 是給維護者除錯用的：跟著使用者語言變，等於自己看不懂自己的 log。
所以這些字串刻意不進 i18n，也刻意集中在這個檔——main.py 才能被
tests/test_i18n.py 的「不得寫死中日文」那條測試涵蓋，本檔則列入豁免清單。

用法：
    from logtext import LOG_TEXT
    _write_log_header(LOG_TEXT["split_start"].format(name=..., count=3))

格式一律具名 placeholder（`{count}` 不是 `{0}`），且**不放格式規格**
（`{elapsed:.3f}` 這種）——呼叫端先算好字串再餵進來，否則改譯文時一個
`:.0f` 就把數字改掉，而且不會報錯。
"""

from __future__ import annotations

LOG_TEXT: dict[str, str] = {
    # 分割任務三段式：起始 / 錯誤 / 結果
    "split_start":      "分割 {name} | {count}段",
    "split_seg_error":  "第 {idx} 段 ffmpeg -> returncode {code}",
    # 合併任務
    "merge_start":      "合併 {count}個檔案 -> {name}",
    "merge_error":      "合併 ffmpeg -> returncode {code}",
    "merge_cleanup_error": "清除暫存清單 -> {exc}",
    # 轉檔任務
    "convert_start":    "轉檔 {count}個檔案 -> {fmt}",
    "convert_error":    "第 {idx} 個檔案 ffmpeg -> returncode {code}",
    "convert_item_error": "第 {idx} 個檔案 -> {exc}",
    # 三種任務共用的結果行
    "task_ok":          "成功，耗時 {minutes}分{seconds}秒",
    "task_fail":        "失敗，耗時 {minutes}分{seconds}秒",
    # 合併選檔的診斷儀器（見 PITFALLS.md「合併清單加不進檔案」）
    "pick_exception":   "合併選檔 askopenfilenames -> {exc} | COM {com}",
    "pick_empty":       ("合併選檔回傳空 | type={type} repr={repr} | "
                         "耗時 {elapsed}s{note} | COM {com} | 清單現有 {count} 筆"),
    "pick_never_opened": "（視窗未開啟）",
    "pick_cancelled":   "（使用者取消）",
    # COM apartment 狀態
    "com_not_entered":  "未進入 apartment(hr=0x{hr})",
    "com_unknown":      "查不到",
    # UI 輪詢迴圈自己爆掉
    "poll_error":       "UI 輪詢 -> {exc}",
}
