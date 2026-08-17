# locales/zh_cn.py
"""locales/zh_cn.py — 简体中文（译自 zh_tw 母表）"""

from __future__ import annotations

STRINGS: dict[str, str] = {
    # ---- 视窗与分页 ----
    "gui.win.title":            "音视频工具",
    "gui.tab.split":            "  分割  ",
    "gui.tab.merge":            "  合并  ",
    "gui.tab.convert":          "  转换  ",

    # ---- 区块标题 ----
    "gui.frame.source_file":    " 来源文件 ",
    "gui.frame.split_times":    " 分割时间点 ",
    "gui.frame.merge_files":    " 来源文件（按顺序排列）",
    "gui.frame.outname":        " 输出文件名 ",
    "gui.frame.source_video":   " 来源视频 ",
    "gui.frame.format":         " 输出格式 ",
    "gui.frame.progress":       " 处理进度 ",

    # ---- 按钮 ----
    "gui.btn.pick":             "选择",
    "gui.btn.add_time":         "新增",
    "gui.btn.del_time":         "删除选中",
    "gui.btn.split_start":      "▶  开始分割",
    "gui.btn.merge_add":        "+ 新增",
    "gui.btn.merge_remove":     "✕ 移除",
    "gui.btn.merge_up":         "↑ 上移",
    "gui.btn.merge_down":       "↓ 下移",
    "gui.btn.merge_clear":      "清空列表",
    "gui.btn.merge_start":      "▶  开始合并",
    "gui.btn.convert_start":    "▶  开始转换",
    "gui.btn.open_folder":      "打开文件夹",

    # ---- 标签 ----
    "gui.lbl.no_file":          "未选择",
    "gui.lbl.selected_count":   "已选择 {count} 个文件",

    # ---- 文件对话框的类型说明 ----
    "gui.filetype.audio_video": "音频/视频",
    "gui.filetype.video":       "视频",
    "gui.filetype.all":         "所有文件",

    # ---- 文件对话框标题 ----
    "gui.dlg.pick_split":       "选择要分割的文件",
    "gui.dlg.pick_merge":       "选择要合并的文件（可多选）",
    "gui.dlg.pick_convert":     "选择要转换的视频",

    # ---- 进度／状态 ----
    "gui.status.idle":          "等待开始...",
    "gui.status.preparing":     "准备中...",
    "gui.status.merging":       "合并中...",
    "gui.status.done":          "完成！",
    "gui.status.failed":        "发生错误，请查看上方记录",
    "gui.status.segments":      "{current} / {total} 段",

    # ---- 画面上的执行记录 ----
    "gui.log.hint":             "请设置完成后按「开始」。\n",
    "gui.log.unknown_error":    "未知错误",
    "gui.log.seg_fail":         "[ERROR] 第 {idx} 段失败：{err}",
    "gui.log.seg_returncode":   "第 {idx} 段 ffmpeg -> returncode {code}",
    "gui.log.seg_ok":           "[OK] 第 {idx} 段：{name}",
    "gui.log.split_done":       "\n[OK] 分割完成！共 {count} 个文件",
    "gui.log.split_partial":    "\n[WARNING] 完成（{success}/{total} 成功）",
    "gui.log.merge_running":    "[INFO] 合并 {count} 个文件...",
    "gui.log.merge_fail":       "[ERROR] 合并失败：{err}",
    "gui.log.merge_returncode": "合并 ffmpeg -> returncode {code}",
    "gui.log.merge_ok":         "[OK] 合并完成：{name}",
    "gui.log.convert_fail":     "[ERROR] 转换失败：{err}",
    "gui.log.convert_returncode": "第 {idx} 个文件 ffmpeg -> returncode {code}",
    "gui.log.convert_item_error": "第 {idx} 个文件 -> {exc}",
    "gui.log.convert_done":     "\n[OK] 完成！（{success}/{total} 成功）",
    "gui.log.convert_all_fail": "\n[WARNING] 全部失败（0/{total}）",
    "gui.log.unexpected":       "\n[ERROR] 未预期错误：{exc}",
    "gui.log.elapsed_ok":       "成功，耗时 {minutes}分{seconds}秒",
    "gui.log.elapsed_fail":     "失败，耗时 {minutes}分{seconds}秒",
    "gui.log.picker_no_window": "（选择文件窗口没有打开就直接返回空（{elapsed} 秒），"
                                "这是已知问题，请重开程序并反馈 logs\\app.log）\n",
    "gui.log.picker_cancelled": "（未加入任何文件）\n",

    # ---- 消息框 ----
    "gui.msg.format_title":     "格式错误",
    "gui.msg.time_required":    "请输入时间点",
    "gui.msg.time_format":      "格式须为 HH:MM:SS（例：00:01:30）",
    "gui.msg.duplicate_title":  "重复",
    "gui.msg.duplicate_body":   "{time} 已存在列表中",
    "gui.msg.error_title":      "错误",
    "gui.msg.need_source":      "请先选择来源文件",
    "gui.msg.need_time":        "请至少新增一个时间点",
    "gui.msg.need_two_files":   "请至少选择 2 个文件",
    "gui.msg.need_outname":     "请输入输出文件名",
    "gui.msg.bad_outname":      "文件名不可包含 \\ / : * ? \" < > |",
    "gui.msg.need_video":       "请先选择来源视频",
    "gui.msg.pick_fail_title":  "选择文件失败",
    "gui.msg.pick_fail_body":   "文件选择窗口发生错误（{exc}）。\n"
                                "请关闭程序重新打开，并把 logs\\app.log 提供给 AI 查询。",
    "gui.msg.close_title":      "确认关闭",
    "gui.msg.close_body":       "任务执行中，确定要关闭窗口吗？关闭后任务会被中止。",
}
