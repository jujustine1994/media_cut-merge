# tests/test_i18n.py
"""i18n 的三道防線。

1. 四個語言檔的 key 集合必須完全一致（漏翻當場紅燈）
2. placeholder 必須一致（譯文打錯 {count} 會讓 t() 靜默吐出未格式化的字串）
3. 專案的 .py 不得再出現寫死的中日文字面（防止日後功能開發時悄悄退化）

第 3 條是**永久**的：它擋的不是這次遷移，是下一次。新增功能時順手寫一個
中文按鈕標籤最自然不過，沒有它三個月後就又回到全部寫死的狀態。
"""

import ast
import re
from pathlib import Path

import pytest

import i18n

ROOT = Path(__file__).resolve().parent.parent
CJK = re.compile(r"[一-鿿぀-ヿ]")
PLACEHOLDER = re.compile(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}")

LANGS = [code for code, _, _ in i18n.LANGUAGES]


def _strings(lang: str) -> dict:
    return i18n._strings(lang)


# ── 1. key 集合一致 ────────────────────────────────────────────────────────

def test_every_language_has_the_same_keys():
    """任一語言少一條就紅燈。靠人眼比對七十幾條不可能可靠，這條就是替代品。"""
    base = set(_strings(i18n.FALLBACK_LANG))
    assert base, "繁中母表是空的，locale 載入壞了"
    for lang in LANGS:
        keys = set(_strings(lang))
        missing = sorted(base - keys)
        extra = sorted(keys - base)
        assert not missing, f"{lang} 少了 {len(missing)} 條：{missing[:10]}"
        assert not extra, f"{lang} 多了 {len(extra)} 條（母表沒有）：{extra[:10]}"


def test_no_language_table_is_empty():
    for lang in LANGS:
        assert _strings(lang), f"{lang} 的 STRINGS 是空的"


# ── 2. placeholder 一致 ───────────────────────────────────────────────────

def test_placeholders_match_across_languages():
    """譯文的 {count} 打錯或漏掉，t() 會 format 失敗並吐出未格式化的原字串——
    畫面上看到 {count} 殘留，不會 crash 所以特別容易漏掉。"""
    base = _strings(i18n.FALLBACK_LANG)
    for lang in LANGS:
        if lang == i18n.FALLBACK_LANG:
            continue
        table = _strings(lang)
        for key, zh in base.items():
            # 缺 key 由上一條測試負責報告，這裡跳過免得吐 KeyError 蓋掉訊息
            if key not in table:
                continue
            want = set(PLACEHOLDER.findall(zh))
            got = set(PLACEHOLDER.findall(table[key]))
            assert want == got, (
                f"{lang} / {key} 的 placeholder 不一致："
                f"母表 {sorted(want)}、譯文 {sorted(got)}"
            )


def test_no_format_spec_leaks_into_the_tables():
    """`{elapsed:.3f}` 這種格式規格不可以進譯文：翻譯者一改成 `:.0f`
    數字就變了，而且完全不會報錯。呼叫端先算好字串再餵進來。"""
    from logtext import LOG_TEXT
    spec = re.compile(r"\{[a-zA-Z_][a-zA-Z0-9_]*[:!][^}]*\}")
    for lang in LANGS:
        for key, val in _strings(lang).items():
            assert not spec.search(val), f"{lang} / {key} 的譯文含格式規格：{val!r}"
    for key, val in LOG_TEXT.items():
        assert not spec.search(val), f"LOG_TEXT / {key} 含格式規格：{val!r}"


# ── 3. 不得寫死中日文 ─────────────────────────────────────────────────────
#
# 豁免清單。每一條都要有理由——沒理由的豁免等於把這條測試關掉。
ALLOWLIST = {
    # 語言選單的顯示名（「繁體中文」「日本語」）本來就該用各語言自稱，
    # 而且它們住在 i18n.py 自己身上，沒有更上層可以查。
    "i18n.py",
    # logs/app.log 的內容依設計永遠繁中：log 是給維護者除錯用的，跟著使用者
    # 語言變等於自廢。這個檔存在的目的就是把那些字串集中起來，好讓 main.py
    # 能被本條測試涵蓋。
    "logtext.py",
}


def _hardcoded_cjk(path: Path) -> list:
    """回傳 (行號, 字串)。docstring 與註解不算——那些是寫給人看的說明。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                docs.add(id(body[0].value))
    hits = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and CJK.search(node.value) and id(node) not in docs):
            hits.append((node.lineno, node.value))
    return sorted(hits)


def _scannable() -> list:
    """⚠ 本專案的 .py 在**根目錄**不是 src/。寫成 ROOT/"src" 會掃到空 list，
    parametrize 收集 0 個 case——測試「通過」但什麼都沒檢查。"""
    skip_dirs = {"venv", ".venv", "locales", "tests", "__pycache__", ".git", "docs"}
    return [p for p in sorted(ROOT.rglob("*.py"))
            if not skip_dirs & set(p.parts)
            and p.name not in ALLOWLIST]


@pytest.mark.parametrize("path", _scannable(), ids=lambda p: p.name)
def test_no_hardcoded_cjk(path):
    """介面文字一律走 t()。真的需要豁免就加進 ALLOWLIST，但要寫清楚理由。"""
    hits = _hardcoded_cjk(path)
    assert not hits, (
        f"{path.name} 有 {len(hits)} 條寫死的中日文字串，請改走 i18n.t()：\n"
        + "\n".join(f"  行 {ln}: {v[:60]!r}" for ln, v in hits[:10])
    )


def test_scannable_actually_covers_the_gui():
    """豁免清單一旦寫太寬，上面那條就等於沒跑。釘住主程式一定在掃描範圍內，
    而且真的收集到檔案（不是空 list）。"""
    files = _scannable()
    assert len(files) > 0, "掃描範圍是空的，上面那條測試等於沒跑"
    names = {p.name for p in files}
    assert {"main.py", "config.py"} <= names, f"主程式不在掃描範圍：{sorted(names)}"


# ── t() 的行為 ────────────────────────────────────────────────────────────

def test_unknown_key_returns_the_key_itself():
    """查不到不回空字串——空白按鈕看不見，key 看得見。"""
    i18n.set_lang("zh_tw")
    assert i18n.t("gui.btn.does_not_exist") == "gui.btn.does_not_exist"


def test_falls_back_to_traditional_chinese(monkeypatch):
    monkeypatch.setitem(i18n._cache, "ja", {})
    i18n.set_lang("ja")
    try:
        assert i18n.t("gui.btn.merge_start") == _strings("zh_tw")["gui.btn.merge_start"]
    finally:
        i18n._cache.pop("ja", None)
        i18n.set_lang("zh_tw")


def test_unknown_lang_falls_back_to_default():
    try:
        assert i18n.set_lang("kl_ingon") == i18n.DEFAULT_LANG
        assert i18n.set_lang(None) == i18n.DEFAULT_LANG
        assert i18n.set_lang("") == i18n.DEFAULT_LANG
    finally:
        i18n.set_lang("zh_tw")


def test_format_failure_returns_the_unformatted_string():
    """譯文的 placeholder 打錯不該讓程式當掉。"""
    i18n.set_lang("zh_tw")
    got = i18n.t("gui.status.segments", current=1)      # 少給 total
    assert "{total}" in got


def test_ui_font_follows_language():
    """微軟正黑體缺日文假名字形，真的要指定字型時日文必須換。
    （本工具目前不呼叫 ui_font，維持 tkinter 預設。）"""
    assert i18n.ui_font("ja") != i18n.ui_font("zh_tw")
    assert i18n.ui_font("ja") == "Yu Gothic"


def test_language_menu_is_generated_from_the_registry():
    """下拉選單的選項不是寫死的——新增語言只改 LANGUAGES 一行。"""
    codes = [c for c, _ in i18n.available_languages()]
    assert codes == LANGS
    assert len(codes) >= 4


# ── 機器鍵不得被翻譯 ──────────────────────────────────────────────────────
#
# 這些字串會被寫進檔名、餵給 ffmpeg，或拿去跟 dict 的鍵比對。翻了會靜默
# 改掉使用者的輸出檔名，或直接讓 ffmpeg 失敗。

MACHINE_VALUES = [
    "_part", "_merge", "_tmp_", "_merge_list_", "_merge_tmp_",   # 檔名樣板
    "ffmpeg", "-acodec", "libmp3lame", "pcm_s16le", "concat", "copy",  # ffmpeg
    "MP3", "AAC", "WAV", "FLAC",                                  # CONVERT_* 的鍵
    ".mp3", ".aac", ".wav", ".flac",                              # 副檔名
]


@pytest.mark.parametrize("lang", LANGS)
def test_machine_keys_are_not_in_any_locale(lang):
    table = _strings(lang)
    for v in MACHINE_VALUES:
        assert v not in table, f"{lang} 把機器鍵 {v!r} 放進語言檔當 key 了"
        assert v not in table.values(), f"{lang} 把機器鍵 {v!r} 當成譯文了"


# ── 不得有任何名稱遮蔽 i18n.t ────────────────────────────────────────────

def test_nothing_shadows_the_translation_function():
    """區域變數／參數叫 `t` 會遮蔽 `from i18n import t`，同一個 scope 裡的
    `t("gui.x")` 就變成「對字串做呼叫」而拋 TypeError——而且只有那條路徑被
    走到時才炸，靜態看不出來。本專案已踩過一次（_split_worker 的迴圈變數）。

    更陰險的版本是專案本來就有 `def t(text)` 這種文字 helper：加上
    `from i18n import t` 之後，所有 t(...) 呼叫**靜默改打到翻譯函式**，
    不 crash、不報錯，畫面整片變空白。
    """
    offenders = []
    for path in _scannable():
        if path.name == "i18n.py":       # t() 的家
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == "t":
                    offenders.append(f"{path.name}:{node.lineno} def t()")
                for a in (node.args.args + node.args.kwonlyargs
                          + node.args.posonlyargs):
                    if a.arg == "t":
                        offenders.append(f"{path.name}:{node.lineno} "
                                         f"{node.name}() 的參數 t")
            if (isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
                    and node.id == "t"):
                offenders.append(f"{path.name}:{node.lineno} 賦值給 t")
    assert not offenders, "有名稱遮蔽 i18n.t：\n  " + "\n  ".join(offenders)


@pytest.mark.parametrize("lang", LANGS)
def test_ffmpeg_arguments_never_go_through_t(lang):
    """CONVERT_CODECS 的每一個參數都不可以出現在任何語言檔裡。"""
    import main
    table = _strings(lang)
    for args in main.CONVERT_CODECS.values():
        for a in args:
            assert a not in table.values(), f"{lang} 翻譯了 ffmpeg 參數 {a!r}"
