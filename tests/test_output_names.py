# tests/test_output_names.py
"""輸出檔名／暫存檔名／ffmpeg 參數：四種語言必須完全相同。

這些字串會被寫進磁碟或餵給 ffmpeg，所以是**資料不是介面文字**。翻了以後
同一個使用者切語言就會存到不同檔名，舊檔案找不到，而且是靜默發生的。

ffmpeg 全程 mock，不真的跑轉檔。
"""

import json
import os
import re
import tkinter as tk

import pytest

import i18n
import main

LANGS = [code for code, _, _ in i18n.LANGUAGES]
UUID_RE = re.compile(r"[0-9a-f]{32}")


class _FakeResult:
    returncode = 0
    stderr = ""
    stdout = ""


@pytest.fixture
def app_factory(tmp_path, monkeypatch, tk_root):
    created = []

    def _make(lang):
        cfg_path = tmp_path / f"config_{lang}.json"
        cfg_path.write_text(json.dumps({"language": lang}), encoding="utf-8")
        monkeypatch.setattr(main, "CONFIG_PATH", cfg_path)
        win = tk.Toplevel(tk_root)
        win.withdraw()
        app = main.ToolApp(win)
        created.append(win)
        return app

    yield _make

    for win in created:
        try:
            win.destroy()
        except tk.TclError:
            pass
    i18n.set_lang("zh_tw")


def _norm(paths, base):
    base = str(base).replace("\\", "/")
    out = []
    for p in paths:
        s = str(p).replace("\\", "/").replace(base, "<DIR>")
        out.append(UUID_RE.sub("<UUID>", s))
    return out


# ── ffmpeg 參數（純函式，與語言無關）────────────────────────────────────

@pytest.mark.parametrize("lang", LANGS)
def test_ffmpeg_commands_are_identical_in_every_language(lang):
    i18n.set_lang(lang)
    try:
        assert main.build_split_cmd("in.mp4", "00:01:00", "00:02:00", "out.mp4") == [
            "ffmpeg", "-y", "-ss", "00:01:00", "-i", "in.mp4",
            "-t", "60", "-c", "copy", "out.mp4"]
        assert main.build_convert_cmd("in.mp4", "out.mp3", "MP3") == [
            "ffmpeg", "-y", "-i", "in.mp4",
            "-vn", "-acodec", "libmp3lame", "-q:a", "2", "out.mp3"]
        assert main.CONVERT_EXT == {"MP3": ".mp3", "AAC": ".aac",
                                    "WAV": ".wav", "FLAC": ".flac"}
    finally:
        i18n.set_lang("zh_tw")


@pytest.mark.parametrize("lang", LANGS)
def test_concat_list_format_is_identical_in_every_language(lang, tmp_path):
    """concat 清單檔的 `file '...'` 是 ffmpeg 的語法，翻了直接失敗。"""
    i18n.set_lang(lang)
    try:
        list_path = tmp_path / f"list_{lang}.txt"
        main.build_merge_list([r"C:\a b\影片 1.mp4", r"D:\x\y.mkv"], str(list_path))
        assert list_path.read_text(encoding="utf-8") == (
            "file 'C:/a b/影片 1.mp4'\nfile 'D:/x/y.mkv'\n")
    finally:
        i18n.set_lang("zh_tw")


@pytest.mark.parametrize("lang", LANGS)
def test_temp_file_name_is_identical_in_every_language(lang, tmp_path, monkeypatch):
    """非 ASCII 輸出路徑會先寫到 `_tmp_<uuid><ext>`——前綴是資料。"""
    i18n.set_lang(lang)
    monkeypatch.setattr(main.subprocess, "run", lambda *a, **k: _FakeResult())
    seen = []
    try:
        main.run_ffmpeg_to(lambda p: seen.append(p) or ["ffmpeg"],
                           str(tmp_path / "中文.mp4"))
        assert _norm(seen, tmp_path) == ["<DIR>/_tmp_<UUID>.mp4"]
    finally:
        i18n.set_lang("zh_tw")


# ── worker 內嵌的檔名組裝 ────────────────────────────────────────────────

@pytest.mark.parametrize("lang", LANGS)
def test_split_output_names_are_identical_in_every_language(lang, app_factory,
                                                            tmp_path, monkeypatch):
    captured = []
    monkeypatch.setattr(main, "run_ffmpeg_to",
                        lambda builder, out: captured.append(out) or _FakeResult())
    app = app_factory(lang)
    app._split_worker(str(tmp_path / "我的 影片.mkv"), ["00:00:30", "00:00:10"])
    assert _norm(captured, tmp_path) == [
        "<DIR>/我的 影片_part1.mkv",
        "<DIR>/我的 影片_part2.mkv",
        "<DIR>/我的 影片_part3.mkv",
    ]


@pytest.mark.parametrize("lang", LANGS)
def test_convert_output_names_are_identical_in_every_language(lang, app_factory,
                                                              tmp_path, monkeypatch):
    captured = []
    monkeypatch.setattr(main, "run_ffmpeg_to",
                        lambda builder, out: captured.append(out) or _FakeResult())
    app = app_factory(lang)
    app._convert_worker([str(tmp_path / "clip 甲.mp4"),
                         str(tmp_path / "clip_b.mov")], "MP3")
    assert _norm(captured, tmp_path) == ["<DIR>/clip 甲.mp3", "<DIR>/clip_b.mp3"]


@pytest.mark.parametrize("lang", LANGS)
def test_merge_output_name_is_identical_in_every_language(lang, app_factory,
                                                          tmp_path, monkeypatch):
    captured = []
    monkeypatch.setattr(main, "run_ffmpeg_to",
                        lambda builder, out: captured.append(out) or _FakeResult())
    files = []
    for n in ("a 甲.mp4", "b.mp4"):
        p = tmp_path / n
        p.write_bytes(b"x")
        files.append(str(p))
    app = app_factory(lang)
    app._merge_worker(files, "我的_merge")
    assert _norm(captured, tmp_path) == ["<DIR>/我的_merge.mp4"]
    # 暫存目錄與清單檔都要清乾淨（名字是資料，不跟語言走）
    leftovers = [n for n in os.listdir(tmp_path)
                 if n.startswith("_merge_list_") or n.startswith("_merge_tmp_")]
    assert not leftovers, f"暫存檔沒清乾淨：{leftovers}"


@pytest.mark.parametrize("lang", LANGS)
def test_auto_output_name_template_is_identical_in_every_language(lang, app_factory,
                                                                  tmp_path):
    """合併分頁自動帶出的預設輸出檔名 `<第一個檔名>_merge` 是資料：
    翻了以後使用者切語言就會存成不同檔名。"""
    app = app_factory(lang)
    app._merge_files = [str(tmp_path / "a 甲.mp4"), str(tmp_path / "b.mp4")]
    app._merge_refresh_listbox()
    assert app.merge_outname_var.get() == "a 甲_merge"
    assert app.merge_outname_ext_label.cget("text") == ".mp4"
