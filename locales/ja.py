# locales/ja.py
"""locales/ja.py — 日本語（zh_tw 母表からの翻訳）"""

from __future__ import annotations

STRINGS: dict[str, str] = {
    # ---- ウィンドウ・タブ ----
    "gui.win.title":            "音声・動画ツール",
    "gui.tab.split":            "  分割  ",
    "gui.tab.merge":            "  結合  ",
    "gui.tab.convert":          "  変換  ",

    # ---- セクション見出し ----
    "gui.frame.source_file":    " 入力ファイル ",
    "gui.frame.split_times":    " 分割ポイント ",
    "gui.frame.merge_files":    " 入力ファイル（順番どおり）",
    "gui.frame.outname":        " 出力ファイル名 ",
    "gui.frame.source_video":   " 入力動画 ",
    "gui.frame.format":         " 出力形式 ",
    "gui.frame.progress":       " 処理状況 ",

    # ---- ボタン ----
    "gui.btn.pick":             "選択",
    "gui.btn.add_time":         "追加",
    "gui.btn.del_time":         "選択項目を削除",
    "gui.btn.split_start":      "▶  分割開始",
    "gui.btn.merge_add":        "+ 追加",
    "gui.btn.merge_remove":     "✕ 削除",
    "gui.btn.merge_up":         "↑ 上へ",
    "gui.btn.merge_down":       "↓ 下へ",
    "gui.btn.merge_clear":      "リストを消去",
    "gui.btn.merge_start":      "▶  結合開始",
    "gui.btn.convert_start":    "▶  変換開始",
    "gui.btn.open_folder":      "フォルダーを開く",

    # ---- ラベル ----
    "gui.lbl.no_file":          "未選択",
    "gui.lbl.selected_count":   "{count} 個のファイルを選択",

    # ---- ファイルダイアログの種類説明 ----
    "gui.filetype.audio_video": "音声/動画",
    "gui.filetype.video":       "動画",
    "gui.filetype.all":         "すべてのファイル",

    # ---- ファイルダイアログのタイトル ----
    "gui.dlg.pick_split":       "分割するファイルを選択",
    "gui.dlg.pick_merge":       "結合するファイルを選択（複数選択可）",
    "gui.dlg.pick_convert":     "変換する動画を選択",

    # ---- 進捗・状態 ----
    "gui.status.idle":          "開始待ち...",
    "gui.status.preparing":     "準備中...",
    "gui.status.merging":       "結合中...",
    "gui.status.done":          "完了！",
    "gui.status.failed":        "エラーが発生しました。上のログを確認してください",
    "gui.status.segments":      "{current} / {total} 個",

    # ---- 画面上の実行ログ ----
    "gui.log.hint":             "設定が終わったら「開始」を押してください。\n",
    "gui.log.unknown_error":    "不明なエラー",
    "gui.log.seg_fail":         "[ERROR] {idx} 番目の区間が失敗：{err}",
    "gui.log.seg_returncode":   "{idx} 番目の区間 ffmpeg -> returncode {code}",
    "gui.log.seg_ok":           "[OK] {idx} 番目の区間：{name}",
    "gui.log.split_done":       "\n[OK] 分割完了！ファイル {count} 個",
    "gui.log.split_partial":    "\n[WARNING] 終了（{success}/{total} 成功）",
    "gui.log.merge_running":    "[INFO] {count} 個のファイルを結合中...",
    "gui.log.merge_fail":       "[ERROR] 結合に失敗：{err}",
    "gui.log.merge_returncode": "結合 ffmpeg -> returncode {code}",
    "gui.log.merge_ok":         "[OK] 結合完了：{name}",
    "gui.log.convert_fail":     "[ERROR] 変換に失敗：{err}",
    "gui.log.convert_returncode": "{idx} 番目のファイル ffmpeg -> returncode {code}",
    "gui.log.convert_item_error": "{idx} 番目のファイル -> {exc}",
    "gui.log.convert_done":     "\n[OK] 完了！（{success}/{total} 成功）",
    "gui.log.convert_all_fail": "\n[WARNING] すべて失敗（0/{total}）",
    "gui.log.unexpected":       "\n[ERROR] 予期しないエラー：{exc}",
    "gui.log.elapsed_ok":       "成功、所要時間 {minutes}分{seconds}秒",
    "gui.log.elapsed_fail":     "失敗、所要時間 {minutes}分{seconds}秒",
    "gui.log.picker_no_window": "（ファイル選択ウィンドウが開かないまま空で返りました"
                                "（{elapsed} 秒）。既知の問題です。アプリを再起動し、"
                                "logs\\app.log を報告してください）\n",
    "gui.log.picker_cancelled": "（ファイルは追加されませんでした）\n",

    # ---- メッセージボックス ----
    "gui.msg.format_title":     "形式エラー",
    "gui.msg.time_required":    "時間を入力してください",
    "gui.msg.time_format":      "形式は HH:MM:SS です（例：00:01:30）",
    "gui.msg.duplicate_title":  "重複",
    "gui.msg.duplicate_body":   "{time} はすでにリストにあります",
    "gui.msg.error_title":      "エラー",
    "gui.msg.need_source":      "先に入力ファイルを選択してください",
    "gui.msg.need_time":        "分割ポイントを 1 つ以上追加してください",
    "gui.msg.need_two_files":   "ファイルを 2 つ以上選択してください",
    "gui.msg.need_outname":     "出力ファイル名を入力してください",
    "gui.msg.bad_outname":      "ファイル名に \\ / : * ? \" < > | は使えません",
    "gui.msg.need_video":       "先に入力動画を選択してください",
    "gui.msg.pick_fail_title":  "ファイル選択エラー",
    "gui.msg.pick_fail_body":   "ファイル選択ウィンドウでエラーが発生しました（{exc}）。\n"
                                "アプリを閉じて開き直し、logs\\app.log を "
                                "AI に渡して調べてもらってください。",
    "gui.msg.close_title":      "終了の確認",
    "gui.msg.close_body":       "処理の実行中です。ウィンドウを閉じますか？"
                                "閉じると処理は中止されます。",
}
