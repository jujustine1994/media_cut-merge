# 音影片工具 tkinter GUI 改版 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將 `main.py` 從 CLI 全面改寫為 tkinter 完整 GUI（三個 Tab：分割/合併/轉檔），新增「影像轉音訊」功能。

**Architecture:** 純函式（`validate_time`、`build_split_cmd` 等）與 `ToolApp` class 分離。ToolApp 以 `ttk.Notebook` 組織三 Tab，底部共用進度區，所有背景任務透過 `queue.Queue` 安全更新 UI。分割用 determinate 進度條（按段數）；合併/轉檔用 indeterminate（單一 ffmpeg 呼叫，無法細分進度）。

**Tech Stack:** Python 3.8+、tkinter/ttk（內建）、ffmpeg（外部）、pytest（測試）

---

### Task 1：建立測試環境 + 實作 helper 純函式

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_helpers.py`
- Modify: `main.py`（在舊程式碼最上方加入新常數與純函式，舊 CLI 程式碼暫留）

- [ ] **Step 1：安裝 pytest**

```bash
python -m pip install pytest
```

Expected: `Successfully installed pytest-...`

- [ ] **Step 2：建立 `tests/__init__.py`（空檔）**

內容為空，讓 pytest 能識別 tests 目錄為 package。

- [ ] **Step 3：寫測試（先讓它失敗）**

建立 `tests/test_helpers.py`：

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from main import validate_time, time_to_seconds, build_split_cmd, build_merge_list, build_convert_cmd


class TestValidateTime:
    def test_valid_times(self):
        assert validate_time("00:00:00") is True
        assert validate_time("01:30:45") is True
        assert validate_time("99:59:59") is True

    def test_invalid_minutes(self):
        assert validate_time("00:60:00") is False

    def test_invalid_seconds(self):
        assert validate_time("00:00:60") is False

    def test_wrong_format(self):
        assert validate_time("1:30") is False
        assert validate_time("abc") is False
        assert validate_time("") is False


class TestTimeToSeconds:
    def test_zero(self):
        assert time_to_seconds("00:00:00") == 0

    def test_minutes(self):
        assert time_to_seconds("00:01:30") == 90

    def test_hours(self):
        assert time_to_seconds("01:00:00") == 3600

    def test_combined(self):
        assert time_to_seconds("01:01:01") == 3661


class TestBuildSplitCmd:
    def test_with_end(self):
        cmd = build_split_cmd("in.mp4", "00:01:00", "00:02:00", "out.mp4")
        assert cmd == ['ffmpeg', '-y', '-ss', '00:01:00', '-i', 'in.mp4',
                       '-t', '60', '-c', 'copy', 'out.mp4']

    def test_no_end(self):
        cmd = build_split_cmd("in.mp4", "00:01:00", None, "out.mp4")
        assert cmd == ['ffmpeg', '-y', '-ss', '00:01:00', '-i', 'in.mp4',
                       '-c', 'copy', 'out.mp4']


class TestBuildMergeList:
    def test_creates_file_with_entries(self, tmp_path):
        files = [str(tmp_path / "a.mp4"), str(tmp_path / "b.mp4")]
        list_path = str(tmp_path / "list.txt")
        build_merge_list(files, list_path)
        content = open(list_path, encoding='utf-8').read()
        assert "file '" in content
        assert "a.mp4" in content
        assert "b.mp4" in content

    def test_uses_forward_slashes(self, tmp_path):
        files = [r"C:\Users\test\a.mp4"]
        list_path = str(tmp_path / "list.txt")
        build_merge_list(files, list_path)
        content = open(list_path, encoding='utf-8').read()
        assert "\\" not in content


class TestBuildConvertCmd:
    def test_mp3(self):
        cmd = build_convert_cmd("in.mp4", "out.mp3", "MP3")
        assert cmd == ['ffmpeg', '-y', '-i', 'in.mp4',
                       '-vn', '-acodec', 'libmp3lame', '-q:a', '2', 'out.mp3']

    def test_aac(self):
        cmd = build_convert_cmd("in.mp4", "out.aac", "AAC")
        assert cmd == ['ffmpeg', '-y', '-i', 'in.mp4',
                       '-vn', '-acodec', 'aac', '-b:a', '192k', 'out.aac']

    def test_wav(self):
        cmd = build_convert_cmd("in.mp4", "out.wav", "WAV")
        assert cmd == ['ffmpeg', '-y', '-i', 'in.mp4',
                       '-vn', '-acodec', 'pcm_s16le', 'out.wav']

    def test_flac(self):
        cmd = build_convert_cmd("in.mp4", "out.flac", "FLAC")
        assert cmd == ['ffmpeg', '-y', '-i', 'in.mp4',
                       '-vn', '-acodec', 'flac', 'out.flac']
```

- [ ] **Step 4：執行測試，確認全部失敗（函式尚未定義）**

```bash
python -m pytest tests/test_helpers.py -v
```

Expected: `ImportError` 或 `AttributeError`（functions not found in main）

- [ ] **Step 5：在 `main.py` 頂部加入常數與純函式**

將以下程式碼插入 `main.py` 的最頂端（docstring 之後，舊 import 之前）：

```python
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
```

注意：此步驟先只加這些函式，舊的 CLI 程式碼（banner、split_file、merge_files、main 等）暫時保留在下方，Task 2 才整體替換。

- [ ] **Step 6：執行測試，確認全部通過**

```bash
python -m pytest tests/test_helpers.py -v
```

Expected: 全部 PASSED（約 15 個測試）

- [ ] **Step 7：Commit**

```bash
git add tests/__init__.py tests/test_helpers.py main.py
git commit -m "test: 建立 helper 純函式測試 + 實作 helper 函式"
```

---

### Task 2：完整改寫 main.py 為 GUI 骨架

**Files:**
- Modify: `main.py`（完整覆寫，保留 Task 1 的常數與純函式）
- Create: `tests/test_smoke.py`

- [ ] **Step 1：寫 smoke test**

建立 `tests/test_smoke.py`：

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_main_importable():
    import main
    assert callable(getattr(main, 'ToolApp', None)), "ToolApp class not found"


def test_helpers_still_present():
    import main
    for name in ['validate_time', 'time_to_seconds', 'build_split_cmd',
                 'build_merge_list', 'build_convert_cmd', 'show_cth_banner']:
        assert callable(getattr(main, name, None)), f"{name} not found"
```

- [ ] **Step 2：執行 smoke test，確認失敗**

```bash
python -m pytest tests/test_smoke.py -v
```

Expected: `AssertionError: ToolApp class not found`

- [ ] **Step 3：完整覆寫 `main.py`**

用以下內容**完整取代** `main.py`（包含 Task 1 的常數 + 純函式 + 新的 ToolApp 骨架）：

```python
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
```

- [ ] **Step 4：執行全部測試，確認通過**

```bash
python -m pytest tests/ -v
```

Expected: 所有 helpers 測試 PASSED，smoke test PASSED（ToolApp found）

- [ ] **Step 5：Commit**

```bash
git add main.py tests/test_smoke.py
git commit -m "feat: 改寫 main.py 為 tkinter GUI 骨架（三 Tab + 進度區）"
```

---

### Task 3：實作分割 Tab

**Files:**
- Modify: `main.py`（替換 `_build_split_tab` 的 `pass`，新增 split 相關 methods）

- [ ] **Step 1：在 `main.py` 的 ToolApp class 中，將 `_build_split_tab` 的 `pass` 替換為以下完整實作**

找到 `def _build_split_tab(self, parent):` 並替換整個方法（含 pass）：

```python
    def _build_split_tab(self, parent):
        # 來源檔案
        frame_file = ttk.LabelFrame(parent, text=" 來源檔案 ", padding=8)
        frame_file.pack(fill="x", pady=(0, 8))
        frame_file.columnconfigure(0, weight=1)

        self.split_path_var = tk.StringVar()
        ttk.Entry(frame_file, textvariable=self.split_path_var,
                  state="readonly", width=44).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(frame_file, text="選擇", command=self._split_pick_file,
                   width=6).grid(row=0, column=1)

        # 分割時間點
        frame_time = ttk.LabelFrame(parent, text=" 分割時間點 ", padding=8)
        frame_time.pack(fill="x", pady=(0, 8))

        row_input = tk.Frame(frame_time)
        row_input.pack(fill="x")

        SPLIT_PH = "00:00:00"
        self._split_time_ph = SPLIT_PH
        self.split_time_var = tk.StringVar(value=SPLIT_PH)
        self._split_time_entry = ttk.Entry(
            row_input, textvariable=self.split_time_var, width=12, foreground="grey"
        )
        self._split_time_entry.pack(side="left")
        self._split_time_entry.bind(
            "<FocusIn>",
            lambda e: self._ph_focus_in(self._split_time_entry, self.split_time_var, SPLIT_PH)
        )
        self._split_time_entry.bind(
            "<FocusOut>",
            lambda e: self._ph_focus_out(self._split_time_entry, self.split_time_var, SPLIT_PH)
        )
        self._split_time_entry.bind("<Return>", lambda e: self._split_add_time())

        ttk.Button(row_input, text="新增", command=self._split_add_time,
                   width=6).pack(side="left", padx=(6, 0))
        ttk.Button(row_input, text="刪除選取", command=self._split_delete_time,
                   width=8).pack(side="left", padx=(6, 0))

        self.split_listbox = tk.Listbox(frame_time, height=4, font=("Consolas", 9))
        self.split_listbox.pack(fill="x", pady=(6, 0))

        # 開始按鈕
        self.btn_split_start = ttk.Button(
            parent, text="▶  開始分割", command=self._split_start, width=20
        )
        self.btn_split_start.pack(anchor="e", pady=(4, 0))

    def _split_pick_file(self):
        path = filedialog.askopenfilename(
            title="選擇要分割的檔案", filetypes=AUDIO_VIDEO_FILETYPES
        )
        if path:
            self.split_path_var.set(path)

    def _split_add_time(self):
        t = self._get_ph_value(self.split_time_var, self._split_time_ph)
        if not t:
            messagebox.showerror("格式錯誤", "請輸入時間點")
            return
        if not validate_time(t):
            messagebox.showerror("格式錯誤", "格式須為 HH:MM:SS（例：00:01:30）")
            return
        self.split_listbox.insert("end", t)
        self.split_time_var.set(self._split_time_ph)
        self._split_time_entry.configure(foreground="grey")

    def _split_delete_time(self):
        sel = self.split_listbox.curselection()
        if sel:
            self.split_listbox.delete(sel[0])

    def _split_start(self):
        path = self.split_path_var.get().strip()
        if not path:
            messagebox.showerror("錯誤", "請先選擇來源檔案")
            return
        times = list(self.split_listbox.get(0, "end"))
        if not times:
            messagebox.showerror("錯誤", "請至少新增一個時間點")
            return
        self._reset_for_run(self.btn_split_start)
        threading.Thread(
            target=self._split_worker, args=(path, times), daemon=True
        ).start()

    def _split_worker(self, input_path, time_points):
        try:
            time_points = sorted(time_points, key=time_to_seconds)
            base_dir = os.path.dirname(input_path)
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            ext = os.path.splitext(input_path)[1]

            segments = []
            prev = "00:00:00"
            for i, t in enumerate(time_points):
                segments.append((prev, t, i + 1))
                prev = t
            segments.append((prev, None, len(time_points) + 1))

            self._set_progress(0, len(segments), f"0 / {len(segments)} 段")
            success_count = 0
            for start, end, idx in segments:
                out_path = os.path.join(base_dir, f"{base_name}_part{idx}{ext}")
                cmd = build_split_cmd(input_path, start, end, out_path)
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
                if result.returncode != 0:
                    err = (result.stderr.strip().splitlines()[-1]
                           if result.stderr.strip() else "未知錯誤")
                    self._log(f"[ERROR] 第 {idx} 段失敗：{err}")
                else:
                    self._log(f"[OK] 第 {idx} 段：{os.path.basename(out_path)}")
                    success_count += 1
                self._set_progress(idx, len(segments), f"{idx} / {len(segments)} 段")

            if success_count == len(segments):
                self._log(f"\n[OK] 分割完成！共 {len(segments)} 個檔案")
            else:
                self._log(f"\n[WARNING] 完成（{success_count}/{len(segments)} 成功）")
            self._done(base_dir, success_count == len(segments))
        except Exception as e:
            self._log(f"\n[ERROR] {e}")
            self._done("", False)
```

- [ ] **Step 2：執行全部測試，確認無回歸**

```bash
python -m pytest tests/ -v
```

Expected: 全部 PASSED

- [ ] **Step 3：Commit**

```bash
git add main.py
git commit -m "feat: 實作分割 Tab（選檔、時間點管理、背景 worker）"
```

---

### Task 4：實作合併 Tab

**Files:**
- Modify: `main.py`（替換 `_build_merge_tab` 的 `pass`，新增 merge 相關 methods）

- [ ] **Step 1：在 `main.py` 中，將 `_build_merge_tab` 的 `pass` 替換為以下完整實作**

找到 `def _build_merge_tab(self, parent):` 並替換整個方法（含 pass）：

```python
    def _build_merge_tab(self, parent):
        frame_files = ttk.LabelFrame(parent, text=" 來源檔案（依序排列）", padding=8)
        frame_files.pack(fill="x", pady=(0, 8))

        self._merge_files = []  # 儲存完整路徑
        self.merge_listbox = tk.Listbox(frame_files, height=6, font=("Consolas", 9))
        self.merge_listbox.pack(fill="x", pady=(0, 6))

        row_btn = tk.Frame(frame_files)
        row_btn.pack(fill="x")
        ttk.Button(row_btn, text="+ 新增", command=self._merge_add_file,
                   width=8).pack(side="left")
        ttk.Button(row_btn, text="✕ 移除", command=self._merge_remove_file,
                   width=8).pack(side="left", padx=4)
        ttk.Button(row_btn, text="↑ 上移", command=self._merge_move_up,
                   width=8).pack(side="left")
        ttk.Button(row_btn, text="↓ 下移", command=self._merge_move_down,
                   width=8).pack(side="left", padx=4)

        self.btn_merge_start = ttk.Button(
            parent, text="▶  開始合併", command=self._merge_start, width=20
        )
        self.btn_merge_start.pack(anchor="e", pady=(4, 0))

    def _merge_add_file(self):
        path = filedialog.askopenfilename(
            title="選擇要合併的檔案", filetypes=AUDIO_VIDEO_FILETYPES
        )
        if path:
            self._merge_files.append(path)
            self._merge_refresh_listbox()

    def _merge_remove_file(self):
        sel = self.merge_listbox.curselection()
        if sel:
            self._merge_files.pop(sel[0])
            self._merge_refresh_listbox()

    def _merge_move_up(self):
        sel = self.merge_listbox.curselection()
        if sel and sel[0] > 0:
            idx = sel[0]
            self._merge_files[idx - 1], self._merge_files[idx] = (
                self._merge_files[idx], self._merge_files[idx - 1]
            )
            self._merge_refresh_listbox()
            self.merge_listbox.selection_set(idx - 1)

    def _merge_move_down(self):
        sel = self.merge_listbox.curselection()
        if sel and sel[0] < len(self._merge_files) - 1:
            idx = sel[0]
            self._merge_files[idx], self._merge_files[idx + 1] = (
                self._merge_files[idx + 1], self._merge_files[idx]
            )
            self._merge_refresh_listbox()
            self.merge_listbox.selection_set(idx + 1)

    def _merge_refresh_listbox(self):
        self.merge_listbox.delete(0, "end")
        for i, fp in enumerate(self._merge_files, 1):
            self.merge_listbox.insert("end", f"{i}. {os.path.basename(fp)}")

    def _merge_start(self):
        if len(self._merge_files) < 2:
            messagebox.showerror("錯誤", "請至少選擇 2 個檔案")
            return
        self._reset_for_run(self.btn_merge_start)
        threading.Thread(
            target=self._merge_worker, args=(list(self._merge_files),), daemon=True
        ).start()

    def _merge_worker(self, files):
        base_dir = os.path.dirname(files[0])
        base_name = os.path.splitext(os.path.basename(files[0]))[0]
        ext = os.path.splitext(files[0])[1]
        out_path = os.path.join(base_dir, f"{base_name}_merge{ext}")
        list_path = os.path.join(base_dir, "_merge_list_tmp.txt")
        try:
            build_merge_list(files, list_path)
            self._start_indeterminate("合併中...")
            self._log(f"[INFO] 合併 {len(files)} 個檔案...")

            cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                   '-i', list_path, '-c', 'copy', out_path]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

            if os.path.exists(list_path):
                os.remove(list_path)

            if result.returncode != 0:
                err = (result.stderr.strip().splitlines()[-1]
                       if result.stderr.strip() else "未知錯誤")
                self._log(f"[ERROR] 合併失敗：{err}")
                self._done("", False)
            else:
                self._log(f"[OK] 合併完成：{os.path.basename(out_path)}")
                self._done(base_dir, True)
        except Exception as e:
            if os.path.exists(list_path):
                os.remove(list_path)
            self._log(f"\n[ERROR] {e}")
            self._done("", False)
```

- [ ] **Step 2：執行全部測試，確認無回歸**

```bash
python -m pytest tests/ -v
```

Expected: 全部 PASSED

- [ ] **Step 3：Commit**

```bash
git add main.py
git commit -m "feat: 實作合併 Tab（檔案清單排序、concat worker）"
```

---

### Task 5：實作轉檔 Tab

**Files:**
- Modify: `main.py`（替換 `_build_convert_tab` 的 `pass`，新增 convert 相關 methods）

- [ ] **Step 1：在 `main.py` 中，將 `_build_convert_tab` 的 `pass` 替換為以下完整實作**

找到 `def _build_convert_tab(self, parent):` 並替換整個方法（含 pass）：

```python
    def _build_convert_tab(self, parent):
        # 來源影片
        frame_file = ttk.LabelFrame(parent, text=" 來源影片 ", padding=8)
        frame_file.pack(fill="x", pady=(0, 8))
        frame_file.columnconfigure(0, weight=1)

        self.convert_path_var = tk.StringVar()
        ttk.Entry(frame_file, textvariable=self.convert_path_var,
                  state="readonly", width=44).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(frame_file, text="選擇", command=self._convert_pick_file,
                   width=6).grid(row=0, column=1)

        # 輸出格式
        frame_fmt = ttk.LabelFrame(parent, text=" 輸出格式 ", padding=8)
        frame_fmt.pack(fill="x", pady=(0, 8))

        self.convert_fmt_var = tk.StringVar(value="MP3")
        for fmt in ["MP3", "AAC", "WAV", "FLAC"]:
            ttk.Radiobutton(
                frame_fmt, text=fmt, variable=self.convert_fmt_var, value=fmt
            ).pack(side="left", padx=10)

        # 開始按鈕
        self.btn_convert_start = ttk.Button(
            parent, text="▶  開始轉檔", command=self._convert_start, width=20
        )
        self.btn_convert_start.pack(anchor="e", pady=(4, 0))

    def _convert_pick_file(self):
        path = filedialog.askopenfilename(
            title="選擇要轉檔的影片", filetypes=VIDEO_FILETYPES
        )
        if path:
            self.convert_path_var.set(path)

    def _convert_start(self):
        path = self.convert_path_var.get().strip()
        if not path:
            messagebox.showerror("錯誤", "請先選擇來源影片")
            return
        self._reset_for_run(self.btn_convert_start)
        threading.Thread(
            target=self._convert_worker,
            args=(path, self.convert_fmt_var.get()),
            daemon=True
        ).start()

    def _convert_worker(self, input_path, fmt):
        try:
            base_dir = os.path.dirname(input_path)
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            out_path = os.path.join(base_dir, base_name + CONVERT_EXT[fmt])

            self._start_indeterminate(f"轉檔中（→ {fmt}）...")
            self._log(f"[INFO] {os.path.basename(input_path)} → {os.path.basename(out_path)}")

            cmd = build_convert_cmd(input_path, out_path, fmt)
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

            if result.returncode != 0:
                err = (result.stderr.strip().splitlines()[-1]
                       if result.stderr.strip() else "未知錯誤")
                self._log(f"[ERROR] 轉檔失敗：{err}")
                self._done("", False)
            else:
                self._log(f"[OK] 轉檔完成：{os.path.basename(out_path)}")
                self._done(base_dir, True)
        except Exception as e:
            self._log(f"\n[ERROR] {e}")
            self._done("", False)
```

- [ ] **Step 2：執行全部測試，確認無回歸**

```bash
python -m pytest tests/ -v
```

Expected: 全部 PASSED

- [ ] **Step 3：手動啟動 GUI，目測三個 Tab 是否正常顯示**

```bash
python main.py
```

確認：
- 視窗出現，標題「音影片工具」
- 三個 Tab 都有對應的輸入控件
- 進度區在底部

- [ ] **Step 4：Commit**

```bash
git add main.py
git commit -m "feat: 實作轉檔 Tab（影像轉音訊，支援 MP3/AAC/WAV/FLAC）"
```

---

### Task 6：更新文件

**Files:**
- Modify: `ARCHITECTURE.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1：更新 `ARCHITECTURE.md`**

將整個檔案內容替換為：

```markdown
# ARCHITECTURE.md — 音影片工具

## 工具總覽

tkinter GUI 工具，三個功能 Tab（分割 / 合併 / 轉檔）。
選檔使用 tkinter filedialog，處理核心依賴 ffmpeg，輸出至原始檔案所在目錄。

## 檔案清單

```
media_cut-merge.bat  → 薄 BAT 入口：單行呼叫 launcher.ps1
launcher.ps1         → 啟動邏輯：環境檢查（Python、ffmpeg）→ 執行 main.py
main.py              → 主程式：GUI App + 純函式（helpers）
tests/
  __init__.py
  test_helpers.py    → 純函式單元測試（validate_time、build_*_cmd 等）
  test_smoke.py      → App 可匯入 smoke test
```

## 執行流程

```
使用者雙擊 media_cut-merge.bat
  → 呼叫 launcher.ps1
      → 檢查 Python / ffmpeg
      → 執行 main.py
      → show_cth_banner()（終端 ASCII art）
      → tk.Tk() 主視窗
          ├─ [分割 Tab] 選檔 + 輸入時間點 → ffmpeg -ss -t -c copy（多段）
          ├─ [合併 Tab] 選多檔排序 → ffmpeg concat -c copy
          └─ [轉檔 Tab] 選影片 + 選格式 → ffmpeg -vn -acodec ...
      → 底部共用進度區（queue 安全更新）
```

## 架構設計

### 純函式 vs App class

- **純函式**（module level）：`validate_time`、`time_to_seconds`、`build_split_cmd`、`build_merge_list`、`build_convert_cmd`、`show_cth_banner` — 可直接 pytest 測試
- **ToolApp class**：所有 UI 與執行緒邏輯，透過 `queue.Queue` + `_poll_queue`（每 100ms）安全更新 UI

### 執行緒安全

背景執行緒（worker）只允許呼叫：
- `self._log(msg)` — 寫入 log
- `self._set_progress(current, total, label)` — 更新進度條（determinate）
- `self._start_indeterminate(label)` — 切換為 indeterminate 動畫
- `self._done(output_dir, success)` — 完成通知

## 關鍵設計決策

| 項目 | 決策 | 原因 |
|------|------|------|
| 分割指令 | `-ss` 放 `-i` 前，搭配 `-t`（持續時間）| 快速定位，比 `-to` 更穩定 |
| 合併指令 | `ffmpeg concat` + `_merge_list_tmp.txt` | 最穩定的多檔合併方式 |
| 路徑格式 | concat 清單使用正斜線 | 避免 Windows 反斜線被 ffmpeg 誤解 |
| 編碼（分割/合併）| `-c copy` | 串流複製，不重新編碼，速度快 |
| 轉檔進度條 | indeterminate | ffmpeg 無法從 stdout 取得進度百分比 |
| `_active_start_btn` | 追蹤當前執行中的按鈕 | 統一 _done 處理，不需 per-tab 判斷 |

## 輸出命名規則

| 操作 | 輸出格式 |
|------|---------|
| 分割 | `{原檔名}_part1.{副檔名}`、`_part2`... |
| 合併 | `{第一個檔名}_merge.{副檔名}` |
| 轉檔 | `{原檔名}.{輸出格式副檔名}` |
```

- [ ] **Step 2：在 `CHANGELOG.md` 最上方加入新版本記錄**

在現有內容最前面插入：

```markdown
## 2026-04-16

### 新增
- tkinter 完整 GUI 介面（三 Tab：分割 / 合併 / 轉檔）
- 轉檔功能：影像（MP4/MKV/AVI/MOV/WMV/FLV）→ 音訊（MP3/AAC/WAV/FLAC）
- 單元測試：`tests/test_helpers.py`（15 個測試）
- Smoke test：`tests/test_smoke.py`

### 修改
- 分割 / 合併：操作介面從 CLI 問答改為 GUI（tkinter Notebook Tab）
- 分割 / 合併：選檔格式合併為「音訊 + 影像」（不需預先選類型）
- 進度條：分割用 determinate（段數）；合併 / 轉檔用 indeterminate

### 移除
- CLI 互動流程（`input()` 問答選單）
```

- [ ] **Step 3：Commit**

```bash
git add ARCHITECTURE.md CHANGELOG.md
git commit -m "docs: 更新 ARCHITECTURE.md 與 CHANGELOG.md（GUI 改版）"
```
