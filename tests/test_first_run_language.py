# tests/test_first_run_language.py
"""首次啟動選語言：問一次、記住、不再跳。

判斷依據是 config.json 的 `language` 不是合法代號（預設空字串）。
真的開一次對話框驗證存檔，但用 `after()` 排一個模擬點擊——不可以讓
`wait_window` 卡住測試。
"""

import json
import tkinter as tk
from tkinter import ttk

import pytest

import config
import i18n
import main


@pytest.fixture
def cfg_path(tmp_path):
    return tmp_path / "config.json"


def _saved(path):
    return json.loads(path.read_text(encoding="utf-8"))


# ── 「還沒選過」的判斷 ────────────────────────────────────────────────────

def test_fresh_config_has_no_language_chosen():
    """預設值必須是空字串。填 "zh_tw" 就分不出「選了繁中」與「沒選過」，
    首次啟動的對話框永遠不會出現。"""
    assert config.DEFAULT_CONFIG["language"] == ""
    assert not i18n.is_supported(config.DEFAULT_CONFIG["language"])


def test_missing_key_counts_as_not_chosen(cfg_path):
    cfg_path.write_text(json.dumps({}), encoding="utf-8")
    cfg = config.load_config(cfg_path)
    assert not i18n.is_supported(cfg.get("language", ""))


@pytest.mark.parametrize("value", ["zh_tw", "zh_cn", "en", "ja"])
def test_a_real_choice_is_never_asked_again(cfg_path, value):
    cfg_path.write_text(json.dumps({"language": value}), encoding="utf-8")
    assert i18n.is_supported(config.load_config(cfg_path)["language"])


@pytest.mark.parametrize("value", ["", "kl_ingon", "zh", "EN"])
def test_garbage_language_values_ask_again(cfg_path, value):
    """舊版留下的怪值、手改壞的值——當成沒選過再問一次，比靜默用預設好。"""
    cfg_path.write_text(json.dumps({"language": value}), encoding="utf-8")
    assert not i18n.is_supported(config.load_config(cfg_path)["language"])


def test_choice_survives_a_round_trip(cfg_path):
    cfg = config.load_config(cfg_path)
    cfg["language"] = "ja"
    config.save_config(cfg, cfg_path)
    assert _saved(cfg_path)["language"] == "ja"
    assert config.load_config(cfg_path)["language"] == "ja"


def test_broken_config_file_falls_back_to_defaults(cfg_path):
    cfg_path.write_text("{ this is not json", encoding="utf-8")
    assert config.load_config(cfg_path) == config.DEFAULT_CONFIG


# ── 對話框本身 ────────────────────────────────────────────────────────────

def test_picker_is_skipped_when_already_chosen(cfg_path, monkeypatch):
    """已選過時必須在建任何 widget 之前就 return。
    用一個會爆的 Toplevel 釘住：只要它動手建視窗就會失敗。"""
    cfg_path.write_text(json.dumps({"language": "en"}), encoding="utf-8")
    monkeypatch.setattr(main, "CONFIG_PATH", cfg_path)

    def _boom(*a, **k):
        raise AssertionError("已經選過語言了，不該再跳對話框")

    monkeypatch.setattr(main.tk, "Toplevel", _boom)
    main._pick_language_on_first_run(root=None)      # 沒建 widget 就用不到 root


def _click_language_button(root, wanted_name, tries=40):
    """在對話框裡找到指定語言的按鈕並按下去。找不到就再排一次。"""
    for win in root.winfo_children():
        if isinstance(win, tk.Toplevel):
            for w in win.winfo_children():
                if isinstance(w, ttk.Button) and w.cget("text") == wanted_name:
                    w.invoke()
                    return
    if tries:
        root.after(50, lambda: _click_language_button(root, wanted_name, tries - 1))
    else:                                   # 保險：別讓測試永遠掛在那
        for win in root.winfo_children():
            if isinstance(win, tk.Toplevel):
                win.destroy()


def test_first_run_dialog_opens_saves_and_never_returns(cfg_path, monkeypatch, tk_root):
    """第一次啟動：對話框開得起來、點下去有存檔、第二次啟動不再跳。

    視窗用 Toplevel 不用 tk.Tk()——原因見 tests/conftest.py 的 tk_root。
    """
    monkeypatch.setattr(main, "CONFIG_PATH", cfg_path)
    root = tk.Toplevel(tk_root)
    root.withdraw()
    try:
        root.after(50, lambda: _click_language_button(root, "日本語"))
        main._pick_language_on_first_run(root)

        assert cfg_path.exists(), "選完語言沒有存檔"
        assert _saved(cfg_path)["language"] == "ja"

        # 第二次：不該再建任何 Toplevel
        monkeypatch.setattr(main.tk, "Toplevel",
                            lambda *a, **k: pytest.fail("第二次啟動又跳了語言視窗"))
        main._pick_language_on_first_run(root)
    finally:
        root.destroy()
        i18n.set_lang("zh_tw")


def test_closing_the_dialog_still_saves_a_choice(cfg_path, monkeypatch, tk_root):
    """直接關掉＝接受第一個選項並照樣存——關掉還一直跳才是煩人。"""
    monkeypatch.setattr(main, "CONFIG_PATH", cfg_path)
    root = tk.Toplevel(tk_root)
    root.withdraw()

    def _close(tries=40):
        for win in root.winfo_children():
            if isinstance(win, tk.Toplevel):
                win.destroy()
                return
        if tries:
            root.after(50, lambda: _close(tries - 1))

    try:
        root.after(50, _close)
        main._pick_language_on_first_run(root)
        assert _saved(cfg_path)["language"] == i18n.LANGUAGES[0][0]
    finally:
        root.destroy()
        i18n.set_lang("zh_tw")


def test_language_menu_offers_every_registered_language():
    """對話框的按鈕是從 LANGUAGES 生出來的，新增語言不必改那支函式。"""
    codes = [c for c, _ in i18n.available_languages()]
    assert codes == [c for c, _, _ in i18n.LANGUAGES]
    assert len(codes) >= 4
