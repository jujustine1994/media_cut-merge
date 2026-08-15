# tests/test_gui_build.py
"""GUI 建置 smoke test：四種語言各建一次，確認畫面上沒有殘留的 key 字串。

t() 查不到時回 key 本身（`gui.btn.merge_start`），所以「漏翻」的症狀就是畫面上
出現一串點分隔的英文小寫。這支測試把整棵 widget 樹走過一遍去找那種字串——
比人眼開四次程式可靠。

刻意**不進 mainloop**：建好、withdraw()、走訪、destroy。
"""

import json
import re
import tkinter as tk
from tkinter import ttk

import pytest

import i18n
import main

KEY_LIKE = re.compile(r"[a-z][a-z0-9_]*(\.[a-z0-9_]+)+")
# Entry / Spinbox 的 cget("text") 會回 PY_VAR0 這種變數名，是雜訊不是漏翻
VARNAME = re.compile(r"PY_VAR\d+")


def _looks_like_a_key(text: str) -> bool:
    return bool(KEY_LIKE.fullmatch(text.strip()))


def _all_texts(widget, out=None):
    """收集整棵樹上所有會顯示給使用者的字串。

    Notebook 的分頁標題與 Combobox 的 values 用 cget("text") 拿不到，要另外抓。
    """
    if out is None:
        out = []
    try:
        v = widget.cget("text")
        if isinstance(v, str) and v and not VARNAME.fullmatch(v):
            out.append(v)
    except (tk.TclError, AttributeError):
        pass
    if isinstance(widget, ttk.Combobox):
        out.extend(str(v) for v in widget.cget("values"))
    if isinstance(widget, ttk.Notebook):
        for tab in widget.tabs():
            out.append(widget.tab(tab, "text"))
    for child in widget.winfo_children():
        _all_texts(child, out)
    return out


@pytest.fixture
def app_factory(tmp_path, monkeypatch, tk_root):
    """用一份臨時 config.json 建 App，不碰使用者真正的設定檔。

    視窗用 Toplevel 不用 tk.Tk()——原因見 tests/conftest.py 的 tk_root。
    """
    created = []

    def _make(lang):
        cfg_path = tmp_path / f"config_{lang}.json"
        cfg_path.write_text(json.dumps({"language": lang}), encoding="utf-8")
        monkeypatch.setattr(main, "CONFIG_PATH", cfg_path)
        win = tk.Toplevel(tk_root)
        win.withdraw()
        app = main.ToolApp(win)
        created.append(win)
        return app, win

    yield _make

    for win in created:
        try:
            win.destroy()
        except tk.TclError:
            pass
    i18n.set_lang("zh_tw")


@pytest.mark.parametrize("lang", [code for code, _, _ in i18n.LANGUAGES])
def test_gui_builds_in_every_language_without_residual_keys(lang, app_factory):
    app, root = app_factory(lang)

    assert i18n.get_lang() == lang, "App 沒有依 config 設定語言"

    texts = _all_texts(root) + [root.title()]
    texts.append(app.log_text.get("1.0", "end-1c"))
    residual = [s for s in texts if _looks_like_a_key(s)]
    assert not residual, f"{lang} 畫面上有殘留的 key：{residual}"

    # 譯文真的被套上去了（不是整批退回母表）
    table = i18n._strings(lang)
    assert root.title() == table["gui.win.title"]
    for key in ("gui.btn.split_start", "gui.btn.merge_start",
                "gui.btn.convert_start", "gui.btn.open_folder"):
        assert table[key] in texts, f"{lang} 的 {key} 沒吃到譯文"


@pytest.mark.parametrize("lang", [code for code, _, _ in i18n.LANGUAGES])
def test_language_row_shows_the_saved_language(lang, app_factory):
    """語言選單顯示的是 config 存的那個，不是 runtime 值（見 pattern 第 5 段）。"""
    app, root = app_factory(lang)
    expected = dict(i18n.available_languages())[lang]
    assert app._lang_var.get() == expected
    assert app._selected_lang_code() == lang


@pytest.mark.parametrize("lang", [code for code, _, _ in i18n.LANGUAGES])
def test_filetypes_are_evaluated_at_call_time(lang, app_factory):
    """檔案類型以前是模組層級常數，t() 在 import 時求值會凍結在預設語言。
    改成函式後必須跟著當下語言走，但**萬用字元樣式永遠不變**（那是資料）。"""
    app_factory(lang)
    table = i18n._strings(lang)
    av = main.audio_video_filetypes()
    vid = main.video_filetypes()
    assert av[0][0] == table["gui.filetype.audio_video"]
    assert av[1][0] == table["gui.filetype.all"]
    assert vid[0][0] == table["gui.filetype.video"]
    # 樣式是資料
    assert av[0][1] == main.AUDIO_VIDEO_PATTERNS
    assert av[1][1] == "*.*"
    assert vid[0][1] == main.VIDEO_PATTERNS


def test_language_combobox_lists_every_registered_language(app_factory):
    app, root = app_factory("en")
    texts = _all_texts(root)
    for _, name in i18n.available_languages():
        assert name in texts, f"語言選單少了 {name}"
