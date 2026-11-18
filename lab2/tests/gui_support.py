"""Поддержка тестов интерфейса: наличие дисплея и надёжная эмуляция клавиш."""
from __future__ import annotations

import os
import unittest


def _detect_display() -> bool:
    try:
        import tkinter as tk
        root = tk.Tk()
        root.destroy()
        return True
    except Exception:  # нет tkinter или нет графической среды
        return False


HAS_DISPLAY = _detect_display()

# В CI выставляется REQUIRE_GUI=1: там тесты интерфейса не должны тихо пропускаться.
if os.environ.get("REQUIRE_GUI") == "1" and not HAS_DISPLAY:
    raise RuntimeError("REQUIRE_GUI=1, но Tkinter/дисплей недоступны")

requires_display = unittest.skipUnless(HAS_DISPLAY, "Tkinter/дисплей недоступны")


def pump(widget, times: int = 5) -> None:
    """Прокручивает цикл событий Tk, чтобы отработали after(0) и перерисовка."""
    for _ in range(times):
        widget.update()


def press(widget, key: str) -> None:
    """Нажатие клавиши в окне виджета.

    Если окно приложения сейчас не активно в ОС (например, во время прогона
    пользователь работает в другой программе), Tk отбрасывает сгенерированные
    клавиши. Событие <FocusIn> сообщает Tk, что фокус у нашего окна, и клавиша
    доставляется так же, как при реальном нажатии.
    """
    widget.winfo_toplevel().event_generate("<FocusIn>", detail="NotifyAncestor")
    widget.focus_set()
    widget.update()
    widget.event_generate(key)
    widget.update()
