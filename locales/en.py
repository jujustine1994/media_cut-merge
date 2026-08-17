# locales/en.py
"""locales/en.py — English (translated from the zh_tw master table)"""

from __future__ import annotations

STRINGS: dict[str, str] = {
    # ---- Window & tabs ----
    "gui.win.title":            "Audio & Video Tool",
    "gui.tab.split":            "  Split  ",
    "gui.tab.merge":            "  Merge  ",
    "gui.tab.convert":          "  Convert  ",

    # ---- Section headings ----
    "gui.frame.source_file":    " Source File ",
    "gui.frame.split_times":    " Split Points ",
    "gui.frame.merge_files":    " Source Files (in order) ",
    "gui.frame.outname":        " Output File Name ",
    "gui.frame.source_video":   " Source Video ",
    "gui.frame.format":         " Output Format ",
    "gui.frame.progress":       " Progress ",

    # ---- Buttons ----
    "gui.btn.pick":             "Browse",
    "gui.btn.add_time":         "Add",
    "gui.btn.del_time":         "Remove",
    "gui.btn.split_start":      "▶  Start Split",
    "gui.btn.merge_add":        "+ Add",
    "gui.btn.merge_remove":     "✕ Remove",
    "gui.btn.merge_up":         "↑ Up",
    "gui.btn.merge_down":       "↓ Down",
    "gui.btn.merge_clear":      "Clear List",
    "gui.btn.merge_start":      "▶  Start Merge",
    "gui.btn.convert_start":    "▶  Start Convert",
    "gui.btn.open_folder":      "Open Folder",

    # ---- Labels ----
    "gui.lbl.no_file":          "No file selected",
    "gui.lbl.selected_count":   "{count} file(s) selected",

    # ---- File-dialog type descriptions ----
    "gui.filetype.audio_video": "Audio / Video",
    "gui.filetype.video":       "Video",
    "gui.filetype.all":         "All Files",

    # ---- File-dialog titles ----
    "gui.dlg.pick_split":       "Select the file to split",
    "gui.dlg.pick_merge":       "Select the files to merge (multi-select)",
    "gui.dlg.pick_convert":     "Select the videos to convert",

    # ---- Progress / status ----
    "gui.status.idle":          "Waiting to start...",
    "gui.status.preparing":     "Preparing...",
    "gui.status.merging":       "Merging...",
    "gui.status.done":          "Done!",
    "gui.status.failed":        "An error occurred - see the log above",
    "gui.status.segments":      "{current} / {total} segments",

    # ---- On-screen run log ----
    "gui.log.hint":             "Configure the options above, then press Start.\n",
    "gui.log.unknown_error":    "Unknown error",
    "gui.log.seg_fail":         "[ERROR] Segment {idx} failed: {err}",
    "gui.log.seg_returncode":   "Segment {idx} ffmpeg -> returncode {code}",
    "gui.log.seg_ok":           "[OK] Segment {idx}: {name}",
    "gui.log.split_done":       "\n[OK] Split complete! {count} file(s) created",
    "gui.log.split_partial":    "\n[WARNING] Finished ({success}/{total} succeeded)",
    "gui.log.merge_running":    "[INFO] Merging {count} file(s)...",
    "gui.log.merge_fail":       "[ERROR] Merge failed: {err}",
    "gui.log.merge_returncode": "Merge ffmpeg -> returncode {code}",
    "gui.log.merge_ok":         "[OK] Merge complete: {name}",
    "gui.log.convert_fail":     "[ERROR] Conversion failed: {err}",
    "gui.log.convert_returncode": "File {idx} ffmpeg -> returncode {code}",
    "gui.log.convert_item_error": "File {idx} -> {exc}",
    "gui.log.convert_done":     "\n[OK] Done! ({success}/{total} succeeded)",
    "gui.log.convert_all_fail": "\n[WARNING] All failed (0/{total})",
    "gui.log.unexpected":       "\n[ERROR] Unexpected error: {exc}",
    "gui.log.elapsed_ok":       "Succeeded in {minutes}m {seconds}s",
    "gui.log.elapsed_fail":     "Failed after {minutes}m {seconds}s",
    "gui.log.picker_no_window": "(The file picker returned empty without ever opening "
                                "({elapsed}s). This is a known issue - please restart "
                                "the app and report logs\\app.log)\n",
    "gui.log.picker_cancelled": "(No files added)\n",

    # ---- Message boxes ----
    "gui.msg.format_title":     "Invalid Format",
    "gui.msg.time_required":    "Please enter a time point",
    "gui.msg.time_format":      "The format must be HH:MM:SS (e.g. 00:01:30)",
    "gui.msg.duplicate_title":  "Duplicate",
    "gui.msg.duplicate_body":   "{time} is already in the list",
    "gui.msg.error_title":      "Error",
    "gui.msg.need_source":      "Please select a source file first",
    "gui.msg.need_time":        "Please add at least one time point",
    "gui.msg.need_two_files":   "Please select at least 2 files",
    "gui.msg.need_outname":     "Please enter an output file name",
    "gui.msg.bad_outname":      "The file name must not contain \\ / : * ? \" < > |",
    "gui.msg.need_video":       "Please select a source video first",
    "gui.msg.pick_fail_title":  "File Picker Failed",
    "gui.msg.pick_fail_body":   "The file picker hit an error ({exc}).\n"
                                "Please close and reopen the app, and send "
                                "logs\\app.log to your AI assistant.",
    "gui.msg.close_title":      "Confirm Close",
    "gui.msg.close_body":       "A task is still running. Close the window anyway? "
                                "The task will be aborted.",
}
