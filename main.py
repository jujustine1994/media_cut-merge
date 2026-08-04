"""
音影片工具 — tkinter GUI
分割、合併、轉檔（影像 → 音訊）
"""

import os
import queue
import shutil
import subprocess
import threading
import time
import traceback
import uuid
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext


# ---- 執行紀錄（logs/app.log，規則見 windows-tool.md「執行紀錄」）----

def _find_project_root() -> str:
    """往上找 launcher.ps1 所在目錄＝專案根目錄。

    不可寫死 os.path.join(SCRIPT_DIR, "..", "logs")：主程式在根目錄的專案會算到
    專案外層（Documents\\Code\\logs），污染其他專案。用這個函式，主程式在根目錄
    或 src/ 都對，日後把 .py 搬進 src/ 也不會壞。
    """
    here = os.path.dirname(os.path.abspath(__file__))
    d = here
    while True:
        if os.path.exists(os.path.join(d, "launcher.ps1")):
            return d
        parent = os.path.dirname(d)
        if parent == d:      # 找到磁碟根目錄仍沒找到，退回自己所在目錄，至少不寫到專案外
            return here
        d = parent


LOG_DIR = os.path.join(_find_project_root(), "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")


def _write_log(msg: str, level: str = "INFO"):
    """寫一行到 logs/app.log。每次開檔→寫→關檔，不持有 handle（地雷十）"""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] [{level:<5}] {msg}\n")
    except OSError:
        pass   # log 掛掉不能拖垮主程式；也涵蓋兩個實例同時跑撞在一起


def _write_log_header(msg: str):
    """任務起始行，唯一有完整日期的行"""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"=== {time.strftime('%Y-%m-%d %H:%M:%S')} {msg} ===\n")
    except OSError:
        pass


def _com_state() -> str:
    """回報目前執行緒的 COM apartment 狀態（診斷用）。

    Tk 在 Windows 的檔案對話框是走 COM 的 IFileOpenDialog，底層失敗時 Tk 會
    「靜默回傳空字串」——不拋例外、不寫任何訊息，而且不會自我復原，只有重啟
    程式才會好。對話框回空時一併記下這個狀態，事後才判斷得出是不是 COM 的問題。
    """
    try:
        import ctypes
        t, q = ctypes.c_int(-1), ctypes.c_int(-1)
        hr = ctypes.windll.ole32.CoGetApartmentType(ctypes.byref(t), ctypes.byref(q))
        if hr != 0:
            return f"未進入 apartment(hr=0x{hr & 0xFFFFFFFF:08X})"
        name = {0: "STA", 1: "MTA", 2: "NA", 3: "MAINSTA"}.get(t.value, str(t.value))
        return f"{name}/qual={q.value}"
    except Exception:
        return "查不到"


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


def run_ffmpeg_to(cmd_builder, out_path):
    """執行 ffmpeg 並輸出到 out_path。

    ffmpeg 在 Windows 上若輸出路徑含非 ASCII 字元（如中文）會把檔名寫壞，
    因此非 ASCII 路徑先輸出到英文暫存檔，成功後用 Python 改名（不受影響）。
    """
    if out_path.isascii():
        cmd = cmd_builder(out_path)
        return subprocess.run(cmd, capture_output=True, text=True,
                               encoding='utf-8', errors='replace')
    base_dir = os.path.dirname(out_path)
    ext = os.path.splitext(out_path)[1]
    tmp_path = os.path.join(base_dir, f"_tmp_{uuid.uuid4().hex}{ext}")
    cmd = cmd_builder(tmp_path)
    result = subprocess.run(cmd, capture_output=True, text=True,
                             encoding='utf-8', errors='replace')
    if result.returncode == 0 and os.path.exists(tmp_path):
        os.replace(tmp_path, out_path)
    elif os.path.exists(tmp_path):
        os.remove(tmp_path)
    return result


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
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        # tkinter 預設把 callback 例外印到 stderr 就算了：GUI 不會崩，使用者只看到
        # 「按了沒反應」，log 也完全沒有紀錄。攔下來落檔，否則永遠查不到。
        self.root.report_callback_exception = self._on_tk_exception

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
        if t in self.split_listbox.get(0, "end"):
            messagebox.showerror("重複", f"{t} 已存在清單中")
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
        task_start = time.time()
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

            _write_log_header(f"分割 {os.path.basename(input_path)} | {len(segments)}段")

            self._set_progress(0, len(segments), f"0 / {len(segments)} 段")
            success_count = 0
            for start, end, idx in segments:
                out_path = os.path.join(base_dir, f"{base_name}_part{idx}{ext}")
                result = run_ffmpeg_to(
                    lambda p: build_split_cmd(input_path, start, end, p), out_path
                )
                if result.returncode != 0:
                    err = (result.stderr.strip().splitlines()[-1]
                           if result.stderr.strip() else "未知錯誤")
                    self._log(f"[ERROR] 第 {idx} 段失敗：{err}")
                    self._log(f"第 {idx} 段 ffmpeg -> returncode {result.returncode}",
                              "ERROR", to_file=True)
                else:
                    self._log(f"[OK] 第 {idx} 段：{os.path.basename(out_path)}")
                    success_count += 1
                self._set_progress(idx, len(segments), f"{idx} / {len(segments)} 段")

            ok = success_count == len(segments)
            if ok:
                self._log(f"\n[OK] 分割完成！共 {len(segments)} 個檔案")
            else:
                self._log(f"\n[WARNING] 完成（{success_count}/{len(segments)} 成功）")
            elapsed = int(time.time() - task_start)
            self._log(f"{'成功' if ok else '失敗'}，耗時 {elapsed // 60}分{elapsed % 60}秒",
                      "OK" if ok else "FAIL", to_file=True)
            self._done(base_dir, ok)
        except Exception as e:
            self._log(f"\n[ERROR] {e}")
            self._log(f"{type(e).__name__}", "ERROR", to_file=True)
            self._done("", False)

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
        ttk.Button(row_btn, text="清空列表", command=self._merge_clear_files,
                   width=8).pack(side="left", padx=4)

        frame_outname = ttk.LabelFrame(parent, text=" 輸出檔名 ", padding=8)
        frame_outname.pack(fill="x", pady=(0, 8))
        frame_outname.columnconfigure(0, weight=1)

        self.merge_outname_var = tk.StringVar()
        self._merge_outname_auto = True
        self.merge_outname_entry = ttk.Entry(frame_outname, textvariable=self.merge_outname_var)
        self.merge_outname_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.merge_outname_entry.bind("<KeyRelease>", self._merge_outname_edited)
        self.merge_outname_ext_label = ttk.Label(frame_outname, text="")
        self.merge_outname_ext_label.grid(row=0, column=1)

        self.btn_merge_start = ttk.Button(
            parent, text="▶  開始合併", command=self._merge_start, width=20
        )
        self.btn_merge_start.pack(anchor="e", pady=(4, 0))

    def _merge_add_file(self):
        # 診斷中（見 docs/PITFALLS.md「合併清單加不進檔案」）：對話框回空時原本是
        # 靜默跳過，什麼線索都留不下，所以這裡把回傳值與 COM 狀態一併落檔。
        try:
            paths = filedialog.askopenfilenames(
                title="選擇要合併的檔案（可多選）", filetypes=AUDIO_VIDEO_FILETYPES
            )
        except Exception as e:
            _write_log(f"合併選檔 askopenfilenames -> {type(e).__name__} | COM {_com_state()}",
                       "ERROR")
            messagebox.showerror(
                "選檔失敗",
                f"檔案選取視窗發生錯誤（{type(e).__name__}）。\n"
                "請關閉程式重新開啟，並把 logs\\app.log 提供給 AI 查詢。"
            )
            return

        if not paths:
            # 空回傳有兩種可能，Python 端無法區分：①使用者按取消（正常）
            # ②Tk 的 COM 對話框故障（靜默回空，永久性，重啟才會好）。
            # 一律落檔；判讀方式：使用者明明有選檔卻出現這行 = ②。
            _write_log(
                f"合併選檔回傳空 | type={type(paths).__name__} repr={paths!r} | "
                f"COM {_com_state()} | 清單現有 {len(self._merge_files)} 筆",
                "WARN"
            )
            self._log_raw("（未加入任何檔案。若你剛才確實有選檔案，"
                          "這是已知問題，請重開程式並回報 logs\\app.log）\n")
            return

        self._merge_files.extend(paths)
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

    def _merge_clear_files(self):
        self._merge_files.clear()
        self._merge_outname_auto = True
        self.merge_outname_var.set("")
        self._merge_refresh_listbox()

    def _merge_refresh_listbox(self):
        self.merge_listbox.delete(0, "end")
        for i, fp in enumerate(self._merge_files, 1):
            self.merge_listbox.insert("end", f"{i}. {os.path.basename(fp)}")
        if self._merge_files:
            ext = os.path.splitext(self._merge_files[0])[1]
            self.merge_outname_ext_label.config(text=ext)
            if self._merge_outname_auto:
                base_name = os.path.splitext(os.path.basename(self._merge_files[0]))[0]
                self.merge_outname_var.set(f"{base_name}_merge")
        else:
            self.merge_outname_ext_label.config(text="")

    def _merge_outname_edited(self, event):
        self._merge_outname_auto = False

    def _merge_start(self):
        if len(self._merge_files) < 2:
            messagebox.showerror("錯誤", "請至少選擇 2 個檔案")
            return
        outname = self.merge_outname_var.get().strip()
        if not outname:
            messagebox.showerror("錯誤", "請輸入輸出檔名")
            return
        if any(c in outname for c in '\\/:*?"<>|'):
            messagebox.showerror("錯誤", '檔名不可包含 \\ / : * ? " < > |')
            return
        self._reset_for_run(self.btn_merge_start)
        threading.Thread(
            target=self._merge_worker, args=(list(self._merge_files), outname), daemon=True
        ).start()

    def _merge_worker(self, files, outname):
        task_start = time.time()
        base_dir = os.path.dirname(files[0])
        ext = os.path.splitext(files[0])[1]
        out_path = os.path.join(base_dir, f"{outname}{ext}")
        list_path = os.path.join(base_dir, f"_merge_list_{uuid.uuid4().hex}.txt")
        link_dir = os.path.join(base_dir, f"_merge_tmp_{uuid.uuid4().hex}")
        result = None
        _write_log_header(f"合併 {len(files)}個檔案 -> {outname}{ext}")
        try:
            # 來源檔名若含單引號等特殊字元會破壞 concat 清單格式解析，
            # 先用英文暫存連結（同磁碟用 hardlink 不佔額外空間，失敗則複製）避開此問題
            os.makedirs(link_dir, exist_ok=True)
            safe_files = []
            for i, fp in enumerate(files):
                link_path = os.path.join(link_dir, f"{i}{os.path.splitext(fp)[1]}")
                try:
                    os.link(fp, link_path)
                except OSError:
                    shutil.copy2(fp, link_path)
                safe_files.append(link_path)

            build_merge_list(safe_files, list_path)
            self._start_indeterminate("合併中...")
            self._log(f"[INFO] 合併 {len(files)} 個檔案...")

            cmd_builder = lambda p: ['ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                                      '-i', list_path, '-c', 'copy', p]
            result = run_ffmpeg_to(cmd_builder, out_path)
        except Exception as e:
            self._log(f"\n[ERROR] {e}")
            self._log(f"{type(e).__name__}", "ERROR", to_file=True)
        finally:
            # 這裡若拋例外會直接殺掉整個 worker thread，下面的 _done() 就永遠不會被
            # 呼叫 —— is_running 卡在 True、開始按鈕永久反灰、進度條一直轉。
            # 暫存清單檔被防毒掃描鎖住時就會這樣，所以務必吞掉。
            try:
                if os.path.exists(list_path):
                    os.remove(list_path)
            except OSError as e:
                _write_log(f"清除暫存清單 -> {type(e).__name__}", "ERROR")
            shutil.rmtree(link_dir, ignore_errors=True)

        if result is None:
            ok = False
        elif result.returncode != 0:
            err = (result.stderr.strip().splitlines()[-1]
                   if result.stderr.strip() else "未知錯誤")
            self._log(f"[ERROR] 合併失敗：{err}")
            self._log(f"合併 ffmpeg -> returncode {result.returncode}", "ERROR", to_file=True)
            ok = False
        else:
            self._log(f"[OK] 合併完成：{os.path.basename(out_path)}")
            ok = True

        elapsed = int(time.time() - task_start)
        self._log(f"{'成功' if ok else '失敗'}，耗時 {elapsed // 60}分{elapsed % 60}秒",
                  "OK" if ok else "FAIL", to_file=True)
        self._done(base_dir if ok else "", ok)

    def _build_convert_tab(self, parent):
        # 來源影片
        frame_file = ttk.LabelFrame(parent, text=" 來源影片 ", padding=8)
        frame_file.pack(fill="x", pady=(0, 8))
        frame_file.columnconfigure(0, weight=1)

        self._convert_files = ()
        self._convert_label = ttk.Label(frame_file, text="未選擇", width=44, anchor="w")
        self._convert_label.grid(row=0, column=0, sticky="ew", padx=(0, 6))
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
        paths = filedialog.askopenfilenames(
            title="選擇要轉檔的影片", filetypes=VIDEO_FILETYPES
        )
        if paths:
            self._convert_files = paths
            self._convert_label.config(text=f"已選擇 {len(paths)} 個檔案")

    def _convert_start(self):
        if not self._convert_files:
            messagebox.showerror("錯誤", "請先選擇來源影片")
            return
        self._reset_for_run(self.btn_convert_start)
        threading.Thread(
            target=self._convert_worker,
            args=(list(self._convert_files), self.convert_fmt_var.get()),
            daemon=True
        ).start()

    def _convert_worker(self, files, fmt):
        task_start = time.time()
        _write_log_header(f"轉檔 {len(files)}個檔案 -> {fmt}")
        try:
            success_count = 0
            first_success_dir = ""
            total = len(files)
            self._set_progress(0, total, f"0 / {total}")
            for idx, input_path in enumerate(files, start=1):
                try:
                    base_name = os.path.splitext(os.path.basename(input_path))[0]
                    out_path = os.path.join(os.path.dirname(input_path),
                                            base_name + CONVERT_EXT[fmt])
                    self._log(f"[INFO] {os.path.basename(input_path)} → {os.path.basename(out_path)}")

                    result = run_ffmpeg_to(
                        lambda p: build_convert_cmd(input_path, p, fmt), out_path
                    )

                    if result.returncode != 0:
                        err = (result.stderr.strip().splitlines()[-1]
                               if result.stderr.strip() else "未知錯誤")
                        self._log(f"[ERROR] 轉檔失敗：{err}")
                        self._log(f"第 {idx} 個檔案 ffmpeg -> returncode {result.returncode}",
                                  "ERROR", to_file=True)
                    else:
                        self._log(f"[OK] {os.path.basename(out_path)}")
                        success_count += 1
                        if not first_success_dir:
                            first_success_dir = os.path.dirname(input_path)
                except Exception as e:
                    self._log(f"[ERROR] {e}")
                    self._log(f"第 {idx} 個檔案 -> {type(e).__name__}", "ERROR", to_file=True)
                self._set_progress(idx, total, f"{idx} / {total}")

            ok = success_count > 0
            if ok:
                self._log(f"\n[OK] 完成！（{success_count}/{total} 成功）")
            else:
                self._log(f"\n[WARNING] 全部失敗（0/{total}）")
            elapsed = int(time.time() - task_start)
            self._log(f"{'成功' if ok else '失敗'}，耗時 {elapsed // 60}分{elapsed % 60}秒",
                      "OK" if ok else "FAIL", to_file=True)
            self._done(first_success_dir, ok)
        except Exception as e:
            self._log(f"\n[ERROR] 未預期錯誤：{e}")
            self._log(f"{type(e).__name__}", "ERROR", to_file=True)
            self._done("", False)

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

    def _on_tk_exception(self, exc_type, exc_value, exc_tb):
        """tkinter callback 內未處理的例外：落檔 + 照樣印到 console"""
        _write_log(f"UI callback -> {exc_type.__name__}", "ERROR")
        traceback.print_exception(exc_type, exc_value, exc_tb)

    def _on_close(self):
        """關閉視窗前若有任務執行中，跳出確認提示"""
        if self.is_running:
            if not messagebox.askyesno(
                "確認關閉", "任務執行中，確定要關閉視窗嗎？關閉後任務會被中止。"
            ):
                return
        self.root.destroy()

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
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _log(self, msg, level="INFO", to_file=False):
        """推 UI queue；to_file=True 時同時落檔（預設 False，漏帶旗標時是少記不是誤記）"""
        if to_file:
            _write_log(msg, level)
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
                        self.progress_label.config(text="完成！")
                        self.btn_open_folder.pack(side="left")
                    else:
                        self.progress_label.config(text="發生錯誤，請查看上方記錄")
        except queue.Empty:
            pass
        except Exception as e:
            # 例外若逃出這個函式，下面的 root.after 就不會執行，輪詢從此永久停擺，
            # 之後所有記錄、進度、完成狀態都不再更新（畫面看起來像整個卡死）
            _write_log(f"UI 輪詢 -> {type(e).__name__}", "ERROR")
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
