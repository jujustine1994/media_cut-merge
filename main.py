"""
音影片分割合併工具主程式
使用 ffmpeg 處理音訊/影像的分割與合併操作
"""

import subprocess
import sys
import os
import tkinter as tk
from tkinter import filedialog


# ---- 常數 ----

AUDIO_FILETYPES = [('音訊檔案', '*.mp3 *.wav *.aac *.flac *.m4a *.ogg'), ('所有檔案', '*.*')]
VIDEO_FILETYPES = [('影像檔案', '*.mp4 *.mkv *.avi *.mov *.wmv *.flv'), ('所有檔案', '*.*')]


# ---- 工具函式 ----

def clear():
    os.system('cls')


def banner():
    clear()
    b = "\033[90m"
    c = "\033[96m"
    y = "\033[93m"
    r = "\033[0m"
    print(f"{b}/*  ================================  *\\{r}")
    print(f"{b} *                                    *{r}")
    print(f"{b} *    {c}██████╗████████╗██╗  ██╗{b}        *{r}")
    print(f"{b} *   {c}██╔════╝   ██║   ██║  ██║{b}        *{r}")
    print(f"{b} *   {c}██║        ██║   ███████║{b}        *{r}")
    print(f"{b} *   {c}██║        ██║   ██╔══██║{b}        *{r}")
    print(f"{b} *   {c}╚██████╗   ██║   ██║  ██║{b}        *{r}")
    print(f"{b} *    {c}╚═════╝   ╚═╝   ╚═╝  ╚═╝{b}        *{r}")
    print(f"{b} *                                    *{r}")
    print(f"{b} *    {y}音影片分割合併工具{b}              *{r}")
    print(f"{b} *          {y}created by CTH{b}            *{r}")
    print(f"{b}\\*  ================================  */{r}")
    print()


def pick_file(file_type, title='選擇檔案'):
    """開啟 tkinter 選檔視窗，回傳路徑字串，取消則回傳空字串"""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)  # 確保視窗不被遮住
    filetypes = AUDIO_FILETYPES if file_type == 'audio' else VIDEO_FILETYPES
    path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy()
    return path


def validate_time(t):
    """
    驗證時間格式是否為 HH:MM:SS
    分鐘與秒數需在 0-59 之間
    """
    parts = t.strip().split(':')
    if len(parts) != 3:
        return False
    try:
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        return h >= 0 and 0 <= m < 60 and 0 <= s < 60
    except ValueError:
        return False


def time_to_seconds(t):
    """HH:MM:SS 轉換為秒數，用於排序比較"""
    h, m, s = t.strip().split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


# ---- 分割功能 ----

def split_file(file_type):
    """
    分割流程：
    1. 選擇來源檔案
    2. 輸入多個時間點（HH:MM:SS）
    3. 依時間點分段，輸出至同一資料夾
    """
    banner()
    print("[分割模式]")
    print()

    # 選擇來源檔案
    print("[INFO] 請在彈出視窗中選擇要分割的檔案...")
    input_path = pick_file(file_type, title='選擇要分割的檔案')
    if not input_path:
        print("[WARNING] 未選擇檔案，返回主選單")
        input("\n按 Enter 結束...")
        return

    print(f"[OK] 已選擇：{input_path}")
    print()

    # 輸入時間點
    print("─" * 56)
    print("[INFO] 請輸入分割時間點")
    print("[INFO] 格式：HH:MM:SS（例：00:01:30 代表 1 分 30 秒）")
    print("[INFO] 每次輸入一個時間點，全部輸入完畢後輸入 done")
    print("─" * 56)
    print()

    time_points = []
    while True:
        raw = input("時間點（或輸入 done 完成）：").strip()

        if raw.lower() == 'done':
            if not time_points:
                print("[WARNING] 至少需要輸入一個時間點")
                continue
            break

        if not validate_time(raw):
            print("[ERROR] 格式錯誤，請依照 HH:MM:SS 輸入（例：00:01:30）")
            continue

        time_points.append(raw)
        print(f"[OK] 已加入第 {len(time_points)} 個時間點：{raw}")

    # 依時間排序，避免使用者輸入順序錯誤
    time_points.sort(key=time_to_seconds)

    # 取得輸出目錄與檔名資訊
    base_dir = os.path.dirname(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    ext = os.path.splitext(input_path)[1]

    # 建立分段列表：每段為 (開始時間, 結束時間, 段號)
    # 最後一段結束時間為 None，讓 ffmpeg 自動到檔案結尾
    segments = []
    prev = "00:00:00"
    for i, t in enumerate(time_points):
        segments.append((prev, t, i + 1))
        prev = t
    segments.append((prev, None, len(time_points) + 1))

    print()
    print(f"[INFO] 共分為 {len(segments)} 段，開始分割...")
    print()

    success_count = 0
    for start, end, idx in segments:
        out_path = os.path.join(base_dir, f"{base_name}_part{idx}{ext}")

        # -ss 放在 -i 前面：快速定位但不精確到畫面
        # 搭配 -c copy 做串流複製，速度快且不重新編碼
        cmd = ['ffmpeg', '-y', '-ss', start, '-i', input_path]
        if end:
            # 計算這段的持續時間，比 -to 更穩定
            duration = time_to_seconds(end) - time_to_seconds(start)
            cmd += ['-t', str(duration)]
        cmd += ['-c', 'copy', out_path]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            print(f"[ERROR] 第 {idx} 段失敗")
            print(f"        {result.stderr.strip().splitlines()[-1] if result.stderr.strip() else '未知錯誤'}")
        else:
            print(f"[OK] 第 {idx} 段：{os.path.basename(out_path)}")
            success_count += 1

    print()
    if success_count == len(segments):
        print(f"[OK] 分割完成！共 {len(segments)} 個檔案")
    else:
        print(f"[WARNING] 完成（{success_count}/{len(segments)} 成功）")
    print(f"[INFO] 輸出位置：{base_dir}")


# ---- 合併功能 ----

def merge_files(file_type):
    """
    合併流程：
    1. 依序選擇要合併的檔案
    2. 輸入 done 完成選擇
    3. 使用 ffmpeg concat 合併，輸出至第一個檔案的資料夾
    """
    banner()
    print("[合併模式]")
    print()
    print("[INFO] 請依序選擇要合併的檔案（選擇順序即合併順序）")
    print("[INFO] 每選完一個檔案後，按 Enter 繼續選下一個")
    print("[INFO] 全部選完後輸入 done 開始合併")
    print()

    files = []
    while True:
        hint = f"目前已選 {len(files)} 個檔案"
        print(hint)
        action = input("按 Enter 選擇檔案，或輸入 done 完成：").strip()

        if action.lower() == 'done':
            if len(files) < 2:
                print("[WARNING] 合併需要至少 2 個檔案，請繼續選擇")
                continue
            break

        # 非 done 且非空白都當作要繼續選檔，空白也繼續選
        path = pick_file(file_type, title=f'選擇第 {len(files) + 1} 個檔案')
        if not path:
            print("[WARNING] 未選擇檔案，請重試或輸入 done 完成")
            continue

        files.append(path)
        print(f"[OK] [{len(files)}] {os.path.basename(path)}")
        print()

    # 輸出目錄同第一個檔案
    base_dir = os.path.dirname(files[0])
    base_name = os.path.splitext(os.path.basename(files[0]))[0]
    ext = os.path.splitext(files[0])[1]
    out_path = os.path.join(base_dir, f"{base_name}_merge{ext}")

    # 建立 ffmpeg concat 清單（暫存於輸出目錄）
    # 使用正斜線避免 ffmpeg 在 Windows 解析路徑時出錯
    list_path = os.path.join(base_dir, '_merge_list_tmp.txt')
    with open(list_path, 'w', encoding='utf-8') as f:
        for fp in files:
            safe_path = fp.replace('\\', '/')
            f.write(f"file '{safe_path}'\n")

    print()
    print(f"[INFO] 開始合併 {len(files)} 個檔案...")

    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',       # 允許絕對路徑（預設只允許相對路徑）
        '-i', list_path,
        '-c', 'copy',
        out_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

    # 清理暫存清單
    if os.path.exists(list_path):
        os.remove(list_path)

    print()
    if result.returncode != 0:
        print("[ERROR] 合併失敗")
        print(f"        {result.stderr.strip().splitlines()[-1] if result.stderr.strip() else '未知錯誤'}")
    else:
        print(f"[OK] 合併完成！輸出：{os.path.basename(out_path)}")
        print(f"[INFO] 輸出位置：{base_dir}")


# ---- 主流程 ----

def main():
    banner()

    # 步驟一：選擇檔案類型
    print("請選擇要處理的檔案類型：")
    print("  [1] 音訊（MP3、WAV、AAC、FLAC...）")
    print("  [2] 影像（MP4、MKV、AVI、MOV...）")
    print()

    while True:
        choice = input("請輸入選項（1 或 2）：").strip()
        if choice == '1':
            file_type = 'audio'
            print("[OK] 已選擇：音訊")
            break
        elif choice == '2':
            file_type = 'video'
            print("[OK] 已選擇：影像")
            break
        else:
            print("[ERROR] 請輸入 1 或 2")

    print()

    # 步驟二：選擇操作
    print("請選擇操作：")
    print("  [1] 分割 — 將一個檔案依時間點切成多段")
    print("  [2] 合併 — 將多個檔案依序合併成一個")
    print()

    while True:
        op = input("請輸入選項（1 或 2）：").strip()
        if op == '1':
            print("[OK] 已選擇：分割")
            print()
            split_file(file_type)
            break
        elif op == '2':
            print("[OK] 已選擇：合併")
            print()
            merge_files(file_type)
            break
        else:
            print("[ERROR] 請輸入 1 或 2")


if __name__ == '__main__':
    main()
    print()
    input("按 Enter 結束...")
