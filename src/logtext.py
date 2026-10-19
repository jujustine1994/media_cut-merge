# logtext.py
"""logs/app.log 的訊息字串——**一律英文，不跟使用者介面語言走**。

log 的讀者是維護者與 AI：跟著使用者語言變，grep 就找不到；PS1＋Python
混寫時中文也會撞上 cp950（規則見 windows-tool.md「執行紀錄」第 9 條）。
所以這些字串刻意不進 i18n，集中在這個檔；本檔也在
tests/test_i18n.py「不得寫死中日文」的掃描範圍內，混進中文會直接紅。

用法：
    from logtext import LOG_TEXT
    _write_log_header(LOG_TEXT["split_start"].format(name=..., count=3))

格式一律具名 placeholder（`{count}` 不是 `{0}`），且**不放格式規格**
（`{elapsed:.3f}` 這種）——呼叫端先算好字串再餵進來（耗時用
main.format_elapsed()），否則一個 `:.0f` 就把數字改掉，而且不會報錯。
"""

from __future__ import annotations

LOG_TEXT: dict[str, str] = {
    # 分割任務三段式：起始 / 錯誤 / 結果
    "split_start":      "Split {name} | {count} segments",
    "split_seg_error":  "segment {idx} ffmpeg -> returncode {code}",
    # 合併任務
    "merge_start":      "Merge {count} files -> {name}",
    "merge_error":      "merge ffmpeg -> returncode {code}",
    "merge_cleanup_error": "remove temp list -> {exc}",
    # 轉檔任務
    "convert_start":    "Convert {count} files -> {fmt}",
    "convert_error":    "file {idx} ffmpeg -> returncode {code}",
    "convert_item_error": "file {idx} -> {exc}",
    # 三種任務共用的結果行（elapsed 由 format_elapsed() 先算好，如 `1m 54s`）
    "task_ok":          "OK, elapsed {elapsed}",
    "task_fail":        "FAILED, elapsed {elapsed}",
    # 合併選檔的診斷儀器（見 docs/PITFALLS.md「合併清單加不進檔案」）
    "pick_exception":   "merge pick askopenfilenames -> {exc} | COM {com}",
    "pick_empty":       ("merge pick returned empty | type={type} repr={repr} | "
                         "elapsed {elapsed}s{note} | COM {com} | list has {count}"),
    "pick_never_opened": " (dialog never opened)",
    "pick_cancelled":   " (user cancelled)",
    # COM apartment 狀態
    "com_not_entered":  "not in apartment(hr=0x{hr})",
    "com_unknown":      "unknown",
    # UI 輪詢迴圈自己爆掉
    "poll_error":       "UI poll -> {exc}",
}
