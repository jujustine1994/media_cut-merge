# Batch Convert Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 讓轉檔 Tab 支援多選檔案批量轉檔，失敗不中止，逐檔回報結果。

**Architecture:** 只改 `main.py` 的轉檔 Tab 相關 4 個方法；新增 `self._convert_files`（tuple）與 `self._convert_label`（Label widget）；`_convert_worker` 改為接收 files list，以 determinate progress bar 逐檔執行。

**Tech Stack:** Python 3.8+, tkinter/ttk, threading, subprocess, ffmpeg

---

### Task 1: 修改 `_build_convert_tab`、`_convert_pick_file`、`_convert_start`、`_convert_worker`

**Files:**
- Modify: `main.py:359-429`（`_build_convert_tab`, `_convert_pick_file`, `_convert_start`, `_convert_worker`）

- [ ] **Step 1: 讀取 `main.py` 確認目前的四個方法（行 359–429）**

用 Read 工具確認目前程式碼，與本計畫所附的舊版一致後繼續。

- [ ] **Step 2: 用 Edit 工具取代 `_build_convert_tab`**

將：
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
```

換成：
```python
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
```

- [ ] **Step 3: 用 Edit 工具取代 `_convert_pick_file`**

將：
```python
    def _convert_pick_file(self):
        path = filedialog.askopenfilename(
            title="選擇要轉檔的影片", filetypes=VIDEO_FILETYPES
        )
        if path:
            self.convert_path_var.set(path)
```

換成：
```python
    def _convert_pick_file(self):
        paths = filedialog.askopenfilenames(
            title="選擇要轉檔的影片", filetypes=VIDEO_FILETYPES
        )
        if paths:
            self._convert_files = paths
            self._convert_label.config(text=f"已選擇 {len(paths)} 個檔案")
```

- [ ] **Step 4: 用 Edit 工具取代 `_convert_start`**

將：
```python
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
```

換成：
```python
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
```

- [ ] **Step 5: 用 Edit 工具取代 `_convert_worker`**

將：
```python
    def _convert_worker(self, input_path, fmt):
        try:
            base_dir = os.path.dirname(input_path)
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            out_path = os.path.join(base_dir, base_name + CONVERT_EXT[fmt])

            self._start_indeterminate(f"轉檔中（→ {fmt}）...")
            self._log(f"[INFO] {os.path.basename(input_path)} → {os.path.basename(out_path)}")

            cmd = build_convert_cmd(input_path, out_path, fmt)
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    encoding='utf-8', errors='replace')

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

換成：
```python
    def _convert_worker(self, files, fmt):
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

                cmd = build_convert_cmd(input_path, out_path, fmt)
                result = subprocess.run(cmd, capture_output=True, text=True,
                                        encoding='utf-8', errors='replace')

                if result.returncode != 0:
                    err = (result.stderr.strip().splitlines()[-1]
                           if result.stderr.strip() else "未知錯誤")
                    self._log(f"[ERROR] 轉檔失敗：{err}")
                else:
                    self._log(f"[OK] {os.path.basename(out_path)}")
                    success_count += 1
                    if not first_success_dir:
                        first_success_dir = os.path.dirname(input_path)
            except Exception as e:
                self._log(f"[ERROR] {e}")
            self._set_progress(idx, total, f"{idx} / {total}")

        if success_count > 0:
            self._log(f"\n[OK] 完成！（{success_count}/{total} 成功）")
        else:
            self._log(f"\n[WARNING] 全部失敗（0/{total}）")
        self._done(first_success_dir, success_count > 0)
```

- [ ] **Step 6: 確認 `_set_progress` 支援 determinate mode**

在 `main.py` 中搜尋 `_set_progress` 方法實作，確認它會把 progress bar 設為 determinate（而非 indeterminate）。若不確定，讀取相關行數確認。

- [ ] **Step 7: 執行 tests 確認沒有 regression**

```bash
python -m pytest tests/ -v
```

Expected：所有現有測試 PASS（`build_convert_cmd` 相關測試不受影響，smoke test 不受影響）。

- [ ] **Step 8: Commit**

```bash
git add main.py
git commit -m "feat: 轉檔 Tab 支援批量多選轉檔"
```
