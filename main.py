"""
音影片工具 — tkinter GUI
分割、合併、轉檔（影像 → 音訊）
"""

import os
import queue
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext


# ---- 常數 ----

AUDIO_VIDEO_FILETYPES = [
    ('音訊/影像', '*.mp3 *.wav *.aac *.flac *.m4a *.ogg *.mp4 *.mkv *.avi *.mov *.wmv *.flv'),
    ('所有檔案', '*.*')
]
VIDEO_FILETYPES = [
    ('影像', '*.mp4 *.mkv *.avi *.mov *.wmv *.flv'),
    ('所有檔案', '*.*')
]
CONVERT_CODECS = {
    'MP3':  ['-vn', '-acodec', 'libmp3lame', '-q:a', '2'],
    'AAC':  ['-vn', '-acodec', 'aac', '-b:a', '192k'],
    'WAV':  ['-vn', '-acodec', 'pcm_s16le'],
    'FLAC': ['-vn', '-acodec', 'flac'],
}
CONVERT_EXT = {'MP3': '.mp3', 'AAC': '.aac', 'WAV': '.wav', 'FLAC': '.flac'}


# ---- 純函式（可單元測試）----

def validate_time(t):
    parts = t.strip().split(':')
    if len(parts) != 3:
        return False
    try:
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        return h >= 0 and 0 <= m < 60 and 0 <= s < 60
    except ValueError:
        return False


def time_to_seconds(t):
    h, m, s = t.strip().split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


def build_split_cmd(input_path, start, end, out_path):
    cmd = ['ffmpeg', '-y', '-ss', start, '-i', input_path]
    if end:
        duration = time_to_seconds(end) - time_to_seconds(start)
        cmd += ['-t', str(duration)]
    cmd += ['-c', 'copy', out_path]
    return cmd


def build_merge_list(files, list_path):
    with open(list_path, 'w', encoding='utf-8') as f:
        for fp in files:
            safe_path = fp.replace('\\', '/')
            f.write(f"file '{safe_path}'\n")


def build_convert_cmd(input_path, out_path, fmt):
    return ['ffmpeg', '-y', '-i', input_path] + CONVERT_CODECS[fmt] + [out_path]


def show_cth_banner():
    b = "\033[90m"; c = "\033[96m"; y = "\033[93m"; r = "\033[0m"
    print(f"{b}/*  ================================  *\\{r}")
    print(f"{b} *                                    *{r}")
    print(f"{b} *    {c}██████╗████████╗██╗  ██╗{b}        *{r}")
    print(f"{b} *   {c}██╔════╝   ██║   ██║  ██║{b}        *{r}")
    print(f"{b} *   {c}██║        ██║   ███████║{b}        *{r}")
    print(f"{b} *   {c}██║        ██║   ██╔══██║{b}        *{r}")
    print(f"{b} *   {c}╚██████╗   ██║   ██║  ██║{b}        *{r}")
    print(f"{b} *    {c}╚═════╝   ╚═╝   ╚═╝  ╚═╝{b}        *{r}")
    print(f"{b} *                                    *{r}")
    print(f"{b} *          {y}created by CTH{b}            *{r}")
    print(f"{b}\\*  ================================  */{r}")
    print()


# ---- App ----

class ToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("音影片工具")
        self.root.resizable(False, False)

        self.msg_queue = queue.Queue()
        self.is_running = False
        self._last_output_dir = ""
        self._active_start_btn = None  # 追蹤當前執行中的開始按鈕

        self._build_ui()
        self._poll_queue()

    # ---------- UI 建構 ----------

    def _build_ui(self):
        pad = {"padx": 14, "pady": 6}

        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="ew", **pad)

        tab_split = ttk.Frame(self.notebook, padding=8)
        tab_merge = ttk.Frame(self.notebook, padding=8)
        tab_convert = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab_split, text="  分割  ")
        self.notebook.add(tab_merge, text="  合併  ")
        self.notebook.add(tab_convert, text="  轉檔  ")

        self._build_split_tab(tab_split)
        self._build_merge_tab(tab_merge)
        self._build_convert_tab(tab_convert)
        self._build_progress_area(pad)

        self.root.columnconfigure(0, weight=1)

    def _build_split_tab(self, parent):
        pass  # Task 3

    def _build_merge_tab(self, parent):
        pass  # Task 4

    def _build_convert_tab(self, parent):
        pass  # Task 5

    def _build_progress_area(self, pad):
        frame = ttk.LabelFrame(self.root, text=" 處理進度 ", padding=8)
        frame.grid(row=1, column=0, sticky="ew", **pad)
        frame.columnconfigure(0, weight=1)

        self.progress_label = ttk.Label(frame, text="等待開始...")
        self.progress_label.grid(row=0, column=0, sticky="w")
        self.progress_bar = ttk.Progressbar(frame, mode="determinate", length=460)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(4, 8))
        self.log_text = scrolledtext.ScrolledText(
            frame, width=60, height=8, state="disabled", font=("Consolas", 9)
        )
        self.log_text.grid(row=2, column=0, sticky="ew")

        frame_btn = tk.Frame(self.root)
        frame_btn.grid(row=2, column=0, pady=(0, 12))
        self.btn_open_folder = ttk.Button(
            frame_btn, text="開啟資料夾", command=self._open_output_folder
        )
        # 預設不 pack，成功完成後才顯示

        self._log_raw("請設定完成後按「開始」。\n")

    # ---------- Placeholder helpers ----------

    def _ph_focus_in(self, entry, var, ph):
        if var.get() == ph:
            var.set("")
            entry.configure(foreground="black")

    def _ph_focus_out(self, entry, var, ph):
        if not var.get().strip():
            var.set(ph)
            entry.configure(foreground="grey")

    def _get_ph_value(self, var, ph):
        v = var.get().strip()
        return "" if v == ph else v

    # ---------- 分割 Tab ----------
    # (Task 3 補充)

    # ---------- 合併 Tab ----------
    # (Task 4 補充)

    # ---------- 轉檔 Tab ----------
    # (Task 5 補充)

    # ---------- 共用 ----------

    def _open_output_folder(self):
        if self._last_output_dir and os.path.exists(self._last_output_dir):
            os.startfile(self._last_output_dir)

    def _reset_for_run(self, btn):
        """執行前重置 UI 狀態，disable 開始按鈕"""
        self._active_start_btn = btn
        btn.config(state="disabled")
        self.is_running = True
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")
        self.btn_open_folder.pack_forget()
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate")
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = 1
        self.progress_label.config(text="準備中...")

    # ---- 執行緒安全 UI 更新 ----

    def _log_raw(self, msg):
        """主執行緒直接寫入（初始化用）"""
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg)
        self.log_text.config(state="disabled")

    def _log(self, msg):
        self.msg_queue.put(("log", msg))

    def _set_progress(self, current, total, label):
        self.msg_queue.put(("progress", (current, total, label)))

    def _start_indeterminate(self, label):
        self.msg_queue.put(("indeterminate", label))

    def _done(self, output_dir, success):
        self.msg_queue.put(("done", (output_dir, success)))

    def _poll_queue(self):
        try:
            while True:
                msg_type, data = self.msg_queue.get_nowait()
                if msg_type == "log":
                    self.log_text.config(state="normal")
                    self.log_text.insert("end", data + "\n")
                    self.log_text.see("end")
                    self.log_text.config(state="disabled")
                elif msg_type == "progress":
                    current, total, label = data
                    self.progress_bar["maximum"] = total
                    self.progress_bar["value"] = current
                    self.progress_label.config(text=label)
                elif msg_type == "indeterminate":
                    self.progress_bar.config(mode="indeterminate")
                    self.progress_bar.start(15)
                    self.progress_label.config(text=data)
                elif msg_type == "done":
                    output_dir, success = data
                    self.is_running = False
                    self.progress_bar.stop()
                    self.progress_bar.config(mode="determinate")
                    if self._active_start_btn:
                        self._active_start_btn.config(state="normal")
                    if success:
                        self._last_output_dir = output_dir
                        self.progress_bar["maximum"] = 1
                        self.progress_bar["value"] = 1
                        self.btn_open_folder.pack(side="left")
                    else:
                        self.progress_label.config(text="發生錯誤，請查看上方記錄")
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)


def main():
    show_cth_banner()
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.update()
    root.attributes("-topmost", False)
    ToolApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
