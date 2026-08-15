# tests/conftest.py
"""共用 fixture。"""

import os
import sys
import tkinter as tk

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def tk_root():
    """整個測試 session 共用一個隱藏的 Tk root。

    ⚠ 不可以每個測試建一個 tk.Tk()：Microsoft Store 版 Python 在短時間內
    反覆建立／銷毀直譯器時，會間歇性地丟
    `TclError: Can't find a usable init.tcl ... No error`——測試看起來隨機紅
    綠，跟被測程式一點關係都沒有。要另一個視窗就開 Toplevel。
    """
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except tk.TclError:
        pass
