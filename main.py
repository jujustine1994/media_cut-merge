"""
音影片工具 — tkinter GUI
分割、合併、轉檔（影像 → 音訊）
"""

import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import traceback
import uuid
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

import i18n
from config import CONFIG_PATH, load_config, save_config
from i18n import t
from logtext import LOG_TEXT


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
        # 變數不可命名 t：會遮蔽 i18n.t（見本檔頂端 import）
        apt, q = ctypes.c_int(-1), ctypes.c_int(-1)
        hr = ctypes.windll.ole32.CoGetApartmentType(ctypes.byref(apt), ctypes.byref(q))
        if hr != 0:
            return LOG_TEXT["com_not_entered"].format(hr=f"{hr & 0xFFFFFFFF:08X}")
        name = {0: "STA", 1: "MTA", 2: "NA", 3: "MAINSTA"}.get(apt.value, str(apt.value))
        return f"{name}/qual={q.value}"
    except Exception:
        return LOG_TEXT["com_unknown"]


# ---- 常數 ----

# 萬用字元樣式是**資料**（檔案對話框的過濾條件），永遠不翻；
# 只有旁邊的類型說明是介面文字。
AUDIO_VIDEO_PATTERNS = '*.mp3 *.wav *.aac *.flac *.m4a *.ogg *.mp4 *.mkv *.avi *.mov *.wmv *.flv'
VIDEO_PATTERNS = '*.mp4 *.mkv *.avi *.mov *.wmv *.flv'


# ⚠ 這兩個以前是模組層級常數。t() 不可以在 import 時求值——語言是讀完
# config 才設的，常數會凍結在預設語言。改成函式，呼叫時才查表。
def audio_video_filetypes():
    return [(t("gui.filetype.audio_video"), AUDIO_VIDEO_PATTERNS),
            (t("gui.filetype.all"), '*.*')]


def video_filetypes():
    return [(t("gui.filetype.video"), VIDEO_PATTERNS),
            (t("gui.filetype.all"), '*.*')]
CONVERT_CODECS = {
    'MP3':  ['-vn', '-acodec', 'libmp3lame', '-q:a', '2'],
    'AAC':  ['-vn', '-acodec', 'aac', '-b:a', '192k'],
    'WAV':  ['-vn', '-acodec', 'pcm_s16le'],
    'FLAC': ['-vn', '-acodec', 'flac'],
}
CONVERT_EXT = {'MP3': '.mp3', 'AAC': '.aac', 'WAV': '.wav', 'FLAC': '.flac'}


# ---- 純函式（可單元測試）----

def validate_time(value):
    parts = value.strip().split(':')
    if len(parts) != 3:
        return False
    try:
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        return h >= 0 and 0 <= m < 60 and 0 <= s < 60
    except ValueError:
        return False


def time_to_seconds(value):
    h, m, s = value.strip().split(':')
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

        # 語言必須在建任何 widget 之前設好——t() 是建置時查一次表，
        # 設晚了介面會停在預設語言。
        self.cfg = load_config(CONFIG_PATH)
        i18n.set_lang(self.cfg.get("language"))

        self.root.title(t("gui.win.title"))
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

        self._build_language_row()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky="ew", **pad)

        tab_split = ttk.Frame(self.notebook, padding=8)
        tab_merge = ttk.Frame(self.notebook, padding=8)
        tab_convert = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab_split, text=t("gui.tab.split"))
        self.notebook.add(tab_merge, text=t("gui.tab.merge"))
        self.notebook.add(tab_convert, text=t("gui.tab.convert"))

        self._build_split_tab(tab_split)
        self._build_merge_tab(tab_merge)
        self._build_convert_tab(tab_convert)
        self._build_progress_area(pad)

        self.root.columnconfigure(0, weight=1)

    # ---------- 語言列 ----------

    def _build_language_row(self):
        """視窗最上方的語言列。選項由 i18n.LANGUAGES 動態生成，新增語言時
        這裡一個字都不必改。

        標籤固定英文 "Language:"、選項用各語言自稱——任何語言下都認得出來。
        本工具沒有獨立的設定視窗（pattern_i18n.py 第 5 段假設有一個），
        所以直接放主視窗第一列。
        """
        lang_frame = ttk.Frame(self.root)
        lang_frame.grid(row=0, column=0, sticky="e", padx=14, pady=(8, 0))
        ttk.Label(lang_frame, text="Language:").pack(side="left", padx=(0, 8))

        self._lang_choices = i18n.available_languages()
        # ⚠ 讀 config 不讀 i18n.get_lang()：set_lang() 只在 __init__ 跑一次，
        # 使用者選了新語言但按「稍後」不重啟時，runtime 語言還是舊的。
        saved = self.cfg.get("language", "")
        self._lang_saved_code = saved if i18n.is_supported(saved) else i18n.DEFAULT_LANG
        names = [name for _, name in self._lang_choices]
        current = next((n for c, n in self._lang_choices if c == self._lang_saved_code),
                       names[0])
        self._lang_var = tk.StringVar(value=current)
        combo = ttk.Combobox(lang_frame, textvariable=self._lang_var, values=names,
                             width=12, state="readonly")
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", self._on_language_changed)

    def _selected_lang_code(self) -> str:
        """把下拉選單顯示的名稱換回代號。取不到就維持原設定，不亂改。"""
        chosen = self._lang_var.get()
        for code, name in self._lang_choices:
            if name == chosen:
                return code
        return self._lang_saved_code

    def _on_language_changed(self, event=None):
        """選了新語言就存檔並問要不要重開。選同一個不打擾使用者。"""
        new_lang = self._selected_lang_code()
        if new_lang == self._lang_saved_code:
            return
        self.cfg["language"] = new_lang
        save_config(self.cfg, CONFIG_PATH)
        self._lang_saved_code = new_lang
        self._prompt_restart_for_language()

    def _prompt_restart_for_language(self):
        """語言變更後問是否重啟。

        視窗全英文：此刻介面還是舊語言、使用者要的是新語言，用任一方都尷尬，
        英文最中立。
        """
        if messagebox.askyesno(
            "Language Changed",
            "Restart the app to apply the new language.\n\nRestart now?",
        ):
            self._restart_app()

    def _restart_app(self):
        """起一個新行程再關掉自己。

        不用 os.execv：Windows 上它會就地覆寫當前行程，tkinter 還沒釋放的
        視窗 handle 可能殘留，看起來像關不掉的殭屍視窗。
        """
        try:
            subprocess.Popen([sys.executable, *sys.argv], close_fds=True)
        except OSError:
            # 起不了新行程就什麼都不做——使用者下次自己開一樣會生效
            return
        self.root.destroy()

    def _build_split_tab(self, parent):
        # 來源檔案
        frame_file = ttk.LabelFrame(parent, text=t("gui.frame.source_file"), padding=8)
        frame_file.pack(fill="x", pady=(0, 8))
        frame_file.columnconfigure(0, weight=1)

        self.split_path_var = tk.StringVar()
        ttk.Entry(frame_file, textvariable=self.split_path_var,
                  state="readonly", width=44).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(frame_file, text=t("gui.btn.pick"), command=self._split_pick_file,
                   width=6).grid(row=0, column=1)

        # 分割時間點
        frame_time = ttk.LabelFrame(parent, text=t("gui.frame.split_times"), padding=8)
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

        ttk.Button(row_input, text=t("gui.btn.add_time"), command=self._split_add_time,
                   width=6).pack(side="left", padx=(6, 0))
        ttk.Button(row_input, text=t("gui.btn.del_time"), command=self._split_delete_time,
                   width=8).pack(side="left", padx=(6, 0))

        self.split_listbox = tk.Listbox(frame_time, height=4, font=("Consolas", 9))
        self.split_listbox.pack(fill="x", pady=(6, 0))

        # 開始按鈕
        self.btn_split_start = ttk.Button(
            parent, text=t("gui.btn.split_start"), command=self._split_start, width=20
        )
        self.btn_split_start.pack(anchor="e", pady=(4, 0))

    def _split_pick_file(self):
        path = filedialog.askopenfilename(
            title=t("gui.dlg.pick_split"), filetypes=audio_video_filetypes()
        )
        if path:
            self.split_path_var.set(path)

    def _split_add_time(self):
        # 變數不可叫 t（遮蔽 i18n.t）——見 _split_worker 的註解
        tp = self._get_ph_value(self.split_time_var, self._split_time_ph)
        if not tp:
            messagebox.showerror(t("gui.msg.format_title"), t("gui.msg.time_required"))
            return
        if not validate_time(tp):
            messagebox.showerror(t("gui.msg.format_title"), t("gui.msg.time_format"))
            return
        if tp in self.split_listbox.get(0, "end"):
            messagebox.showerror(t("gui.msg.duplicate_title"),
                                 t("gui.msg.duplicate_body", time=tp))
            return
        self.split_listbox.insert("end", tp)
        self.split_time_var.set(self._split_time_ph)
        self._split_time_entry.configure(foreground="grey")

    def _split_delete_time(self):
        sel = self.split_listbox.curselection()
        if sel:
            self.split_listbox.delete(sel[0])

    def _split_start(self):
        path = self.split_path_var.get().strip()
        if not path:
            messagebox.showerror(t("gui.msg.error_title"), t("gui.msg.need_source"))
            return
        times = list(self.split_listbox.get(0, "end"))
        if not times:
            messagebox.showerror(t("gui.msg.error_title"), t("gui.msg.need_time"))
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
            # ⚠ 迴圈變數不可叫 t：會遮蔽 i18n 的 t()，之後同一個 scope 裡
            # 呼叫 t("...") 會變成「對字串做呼叫」而拋 TypeError。
            for i, tp in enumerate(time_points):
                segments.append((prev, tp, i + 1))
                prev = tp
            segments.append((prev, None, len(time_points) + 1))

            _write_log_header(LOG_TEXT["split_start"].format(
                name=os.path.basename(input_path), count=len(segments)))

            self._set_progress(0, len(segments),
                               t("gui.status.segments", current=0, total=len(segments)))
            success_count = 0
            for start, end, idx in segments:
                out_path = os.path.join(base_dir, f"{base_name}_part{idx}{ext}")
                result = run_ffmpeg_to(
                    lambda p: build_split_cmd(input_path, start, end, p), out_path
                )
                if result.returncode != 0:
                    err = (result.stderr.strip().splitlines()[-1]
                           if result.stderr.strip() else t("gui.log.unknown_error"))
                    self._log(t("gui.log.seg_fail", idx=idx, err=err))
                    self._log(t("gui.log.seg_returncode", idx=idx,
                                code=result.returncode),
                              "ERROR", to_file=True,
                              log_msg=LOG_TEXT["split_seg_error"].format(
                                  idx=idx, code=result.returncode))
                else:
                    self._log(t("gui.log.seg_ok", idx=idx,
                                name=os.path.basename(out_path)))
                    success_count += 1
                self._set_progress(idx, len(segments),
                                   t("gui.status.segments", current=idx,
                                     total=len(segments)))

            ok = success_count == len(segments)
            if ok:
                self._log(t("gui.log.split_done", count=len(segments)))
            else:
                self._log(t("gui.log.split_partial", success=success_count,
                            total=len(segments)))
            elapsed = int(time.time() - task_start)
            mins, secs = elapsed // 60, elapsed % 60
            self._log(t("gui.log.elapsed_ok" if ok else "gui.log.elapsed_fail",
                        minutes=mins, seconds=secs),
                      "OK" if ok else "FAIL", to_file=True,
                      log_msg=LOG_TEXT["task_ok" if ok else "task_fail"].format(
                          minutes=mins, seconds=secs))
            self._done(base_dir, ok)
        except Exception as e:
            self._log(f"\n[ERROR] {e}")
            self._log(f"{type(e).__name__}", "ERROR", to_file=True)
            self._done("", False)

    def _build_merge_tab(self, parent):
        frame_files = ttk.LabelFrame(parent, text=t("gui.frame.merge_files"), padding=8)
        frame_files.pack(fill="x", pady=(0, 8))

        self._merge_files = []  # 儲存完整路徑
        self.merge_listbox = tk.Listbox(frame_files, height=6, font=("Consolas", 9))
        self.merge_listbox.pack(fill="x", pady=(0, 6))

        row_btn = tk.Frame(frame_files)
        row_btn.pack(fill="x")
        ttk.Button(row_btn, text=t("gui.btn.merge_add"), command=self._merge_add_file,
                   width=8).pack(side="left")
        ttk.Button(row_btn, text=t("gui.btn.merge_remove"), command=self._merge_remove_file,
                   width=8).pack(side="left", padx=4)
        ttk.Button(row_btn, text=t("gui.btn.merge_up"), command=self._merge_move_up,
                   width=8).pack(side="left")
        ttk.Button(row_btn, text=t("gui.btn.merge_down"), command=self._merge_move_down,
                   width=8).pack(side="left", padx=4)
        ttk.Button(row_btn, text=t("gui.btn.merge_clear"), command=self._merge_clear_files,
                   width=8).pack(side="left", padx=4)

        frame_outname = ttk.LabelFrame(parent, text=t("gui.frame.outname"), padding=8)
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
            parent, text=t("gui.btn.merge_start"), command=self._merge_start, width=20
        )
        self.btn_merge_start.pack(anchor="e", pady=(4, 0))

    def _merge_add_file(self):
        # 診斷中（見 docs/PITFALLS.md「合併清單加不進檔案」）：對話框回空時原本是
        # 靜默跳過，什麼線索都留不下，所以這裡把回傳值與 COM 狀態一併落檔。
        # 對話框「開了多久」是判讀關鍵：秒回代表視窗根本沒開起來（＝故障），
        # 開了好幾秒才回空代表使用者真的看到視窗並按取消（＝正常）。
        t0 = time.monotonic()
        try:
            paths = filedialog.askopenfilenames(
                title=t("gui.dlg.pick_merge"), filetypes=audio_video_filetypes()
            )
        except Exception as e:
            _write_log(LOG_TEXT["pick_exception"].format(
                exc=type(e).__name__, com=_com_state()), "ERROR")
            messagebox.showerror(
                t("gui.msg.pick_fail_title"),
                t("gui.msg.pick_fail_body", exc=type(e).__name__)
            )
            return

        elapsed = time.monotonic() - t0

        if not paths:
            # 空回傳有兩種可能：①使用者按取消（正常）②對話框根本沒開起來（故障）。
            # 用 elapsed 區分：人類不可能在 0.5 秒內開視窗＋按取消。
            never_opened = elapsed < 0.5
            _write_log(
                LOG_TEXT["pick_empty"].format(
                    type=type(paths).__name__, repr=repr(paths),
                    elapsed=f"{elapsed:.3f}",
                    note=LOG_TEXT["pick_never_opened" if never_opened
                                  else "pick_cancelled"],
                    com=_com_state(), count=len(self._merge_files),
                ),
                "WARN"
            )
            if never_opened:
                self._log_raw(t("gui.log.picker_no_window",
                                elapsed=f"{elapsed:.3f}"))
            else:
                self._log_raw(t("gui.log.picker_cancelled"))
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
            messagebox.showerror(t("gui.msg.error_title"), t("gui.msg.need_two_files"))
            return
        outname = self.merge_outname_var.get().strip()
        if not outname:
            messagebox.showerror(t("gui.msg.error_title"), t("gui.msg.need_outname"))
            return
        # 這串字元是**資料**（Windows 檔名的非法字元），不可翻譯
        if any(c in outname for c in '\\/:*?"<>|'):
            messagebox.showerror(t("gui.msg.error_title"), t("gui.msg.bad_outname"))
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
        _write_log_header(LOG_TEXT["merge_start"].format(
            count=len(files), name=f"{outname}{ext}"))
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
            self._start_indeterminate(t("gui.status.merging"))
            self._log(t("gui.log.merge_running", count=len(files)))

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
                _write_log(LOG_TEXT["merge_cleanup_error"].format(
                    exc=type(e).__name__), "ERROR")
            shutil.rmtree(link_dir, ignore_errors=True)

        if result is None:
            ok = False
        elif result.returncode != 0:
            err = (result.stderr.strip().splitlines()[-1]
                   if result.stderr.strip() else t("gui.log.unknown_error"))
            self._log(t("gui.log.merge_fail", err=err))
            self._log(t("gui.log.merge_returncode", code=result.returncode), "ERROR",
                      to_file=True,
                      log_msg=LOG_TEXT["merge_error"].format(code=result.returncode))
            ok = False
        else:
            self._log(t("gui.log.merge_ok", name=os.path.basename(out_path)))
            ok = True

        elapsed = int(time.time() - task_start)
        mins, secs = elapsed // 60, elapsed % 60
        self._log(t("gui.log.elapsed_ok" if ok else "gui.log.elapsed_fail",
                    minutes=mins, seconds=secs),
                  "OK" if ok else "FAIL", to_file=True,
                  log_msg=LOG_TEXT["task_ok" if ok else "task_fail"].format(
                      minutes=mins, seconds=secs))
        self._done(base_dir if ok else "", ok)

    def _build_convert_tab(self, parent):
        # 來源影片
        frame_file = ttk.LabelFrame(parent, text=t("gui.frame.source_video"), padding=8)
        frame_file.pack(fill="x", pady=(0, 8))
        frame_file.columnconfigure(0, weight=1)

        self._convert_files = ()
        self._convert_label = ttk.Label(frame_file, text=t("gui.lbl.no_file"), width=44, anchor="w")
        self._convert_label.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(frame_file, text=t("gui.btn.pick"), command=self._convert_pick_file,
                   width=6).grid(row=0, column=1)

        # 輸出格式
        frame_fmt = ttk.LabelFrame(parent, text=t("gui.frame.format"), padding=8)
        frame_fmt.pack(fill="x", pady=(0, 8))

        self.convert_fmt_var = tk.StringVar(value="MP3")
        for fmt in ["MP3", "AAC", "WAV", "FLAC"]:
            ttk.Radiobutton(
                frame_fmt, text=fmt, variable=self.convert_fmt_var, value=fmt
            ).pack(side="left", padx=10)

        # 開始按鈕
        self.btn_convert_start = ttk.Button(
            parent, text=t("gui.btn.convert_start"), command=self._convert_start, width=20
        )
        self.btn_convert_start.pack(anchor="e", pady=(4, 0))

    def _convert_pick_file(self):
        paths = filedialog.askopenfilenames(
            title=t("gui.dlg.pick_convert"), filetypes=video_filetypes()
        )
        if paths:
            self._convert_files = paths
            self._convert_label.config(text=t("gui.lbl.selected_count", count=len(paths)))

    def _convert_start(self):
        if not self._convert_files:
            messagebox.showerror(t("gui.msg.error_title"), t("gui.msg.need_video"))
            return
        self._reset_for_run(self.btn_convert_start)
        threading.Thread(
            target=self._convert_worker,
            args=(list(self._convert_files), self.convert_fmt_var.get()),
            daemon=True
        ).start()

    def _convert_worker(self, files, fmt):
        task_start = time.time()
        _write_log_header(LOG_TEXT["convert_start"].format(
            count=len(files), fmt=fmt))
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
                               if result.stderr.strip() else t("gui.log.unknown_error"))
                        self._log(t("gui.log.convert_fail", err=err))
                        self._log(t("gui.log.convert_returncode", idx=idx,
                                    code=result.returncode),
                                  "ERROR", to_file=True,
                                  log_msg=LOG_TEXT["convert_error"].format(
                                      idx=idx, code=result.returncode))
                    else:
                        self._log(f"[OK] {os.path.basename(out_path)}")
                        success_count += 1
                        if not first_success_dir:
                            first_success_dir = os.path.dirname(input_path)
                except Exception as e:
                    self._log(f"[ERROR] {e}")
                    self._log(t("gui.log.convert_item_error", idx=idx,
                                exc=type(e).__name__), "ERROR",
                              to_file=True,
                              log_msg=LOG_TEXT["convert_item_error"].format(
                                  idx=idx, exc=type(e).__name__))
                self._set_progress(idx, total, f"{idx} / {total}")

            ok = success_count > 0
            if ok:
                self._log(t("gui.log.convert_done", success=success_count, total=total))
            else:
                self._log(t("gui.log.convert_all_fail", total=total))
            elapsed = int(time.time() - task_start)
            mins, secs = elapsed // 60, elapsed % 60
            self._log(t("gui.log.elapsed_ok" if ok else "gui.log.elapsed_fail",
                        minutes=mins, seconds=secs),
                      "OK" if ok else "FAIL", to_file=True,
                      log_msg=LOG_TEXT["task_ok" if ok else "task_fail"].format(
                          minutes=mins, seconds=secs))
            self._done(first_success_dir, ok)
        except Exception as e:
            self._log(t("gui.log.unexpected", exc=e))
            self._log(f"{type(e).__name__}", "ERROR", to_file=True)
            self._done("", False)

    def _build_progress_area(self, pad):
        frame = ttk.LabelFrame(self.root, text=t("gui.frame.progress"), padding=8)
        frame.grid(row=2, column=0, sticky="ew", **pad)
        frame.columnconfigure(0, weight=1)

        self.progress_label = ttk.Label(frame, text=t("gui.status.idle"))
        self.progress_label.grid(row=0, column=0, sticky="w")
        self.progress_bar = ttk.Progressbar(frame, mode="determinate", length=460)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(4, 8))
        self.log_text = scrolledtext.ScrolledText(
            frame, width=60, height=8, state="disabled", font=("Consolas", 9)
        )
        self.log_text.grid(row=2, column=0, sticky="ew")

        frame_btn = tk.Frame(self.root)
        frame_btn.grid(row=3, column=0, pady=(0, 12))
        self.btn_open_folder = ttk.Button(
            frame_btn, text=t("gui.btn.open_folder"), command=self._open_output_folder
        )
        # 預設不 pack，成功完成後才顯示

        self._log_raw(t("gui.log.hint"))

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
                t("gui.msg.close_title"), t("gui.msg.close_body")
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
        self.progress_label.config(text=t("gui.status.preparing"))

    # ---- 執行緒安全 UI 更新 ----

    def _log_raw(self, msg):
        """主執行緒直接寫入（初始化用）"""
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _log(self, msg, level="INFO", to_file=False, log_msg=None):
        """推 UI queue；to_file=True 時同時落檔（預設 False，漏帶旗標時是少記不是誤記）

        `msg` 是給使用者看的（跟著介面語言走），`log_msg` 是落檔的那份
        （永遠繁中，取自 logtext.LOG_TEXT）。兩者分開才能同時滿足
        「log 固定母語言」與「一個呼叫同時寫檔＋推 UI」兩條規則；
        沒給 log_msg 時退回用 msg，行為與原本一致。
        """
        if to_file:
            _write_log(log_msg if log_msg is not None else msg, level)
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
                        self.progress_label.config(text=t("gui.status.done"))
                        self.btn_open_folder.pack(side="left")
                    else:
                        self.progress_label.config(text=t("gui.status.failed"))
        except queue.Empty:
            pass
        except Exception as e:
            # 例外若逃出這個函式，下面的 root.after 就不會執行，輪詢從此永久停擺，
            # 之後所有記錄、進度、完成狀態都不再更新（畫面看起來像整個卡死）
            _write_log(LOG_TEXT["poll_error"].format(exc=type(e).__name__), "ERROR")
        self.root.after(100, self._poll_queue)


def _pick_language_on_first_run(root) -> None:
    """首次啟動時問一次語言，選完寫進 config.json，之後不再出現。

    判斷依據是 config.json 的 language 不是合法代號（預設空字串）。

    視窗刻意**不翻譯**：這時候還不知道使用者要哪個語言，用任一種當說明都
    在賭。只有一個英文抬頭，其餘全是各語言的自稱。

    直接關掉視窗＝接受第一個選項並**照樣存檔**——需求是「選完就記住不要再
    跳」，關掉還一直跳才是煩人。選錯了在主視窗的語言選單隨時能改。
    """
    cfg = load_config(CONFIG_PATH)
    if i18n.is_supported(cfg.get("language", "")):
        return                      # 選過了，直接進主畫面

    choices = i18n.available_languages()
    chosen = {"code": choices[0][0]}

    dlg = tk.Toplevel(root)
    dlg.title("Language")
    dlg.resizable(False, False)
    dlg.attributes("-topmost", True)

    ttk.Label(dlg, text="Select your language",
              font=("", 12, "bold")).pack(padx=28, pady=(20, 4))
    ttk.Label(dlg, text="You can change this later in the main window.",
              foreground="#555555").pack(padx=28, pady=(0, 14))

    def _choose(code: str) -> None:
        chosen["code"] = code
        dlg.destroy()

    for code, name in choices:
        ttk.Button(dlg, text=name, width=20,
                   command=lambda c=code: _choose(c)).pack(padx=28, pady=3)
    ttk.Frame(dlg, height=10).pack()

    dlg.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - dlg.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - dlg.winfo_height()) // 3
    dlg.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    dlg.grab_set()
    dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)   # 關掉＝用預設值，照樣存
    root.wait_window(dlg)

    cfg["language"] = chosen["code"]
    save_config(cfg, CONFIG_PATH)


def main():
    show_cth_banner()
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.update()
    root.attributes("-topmost", False)
    _pick_language_on_first_run(root)
    ToolApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
