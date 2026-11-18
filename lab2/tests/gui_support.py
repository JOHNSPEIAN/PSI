"""Поддержка тестов интерфейса: наличие дисплея и надёжная эмуляция клавиш."""
from __future__ import annotations

import os
import re
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


_MODIFIERS = {"Control": 4, "Shift": 1, "Alt": 8}
_PERCENT = re.compile(r"%(.)")
TCL_BREAK = 3


def _dispatch_by_bindtags(widget, sequence: str) -> None:
    """Выполняет привязки клавиши так же, как Tk: по bindtags виджета, с учётом break."""
    parts = sequence.strip("<>").split("-")
    keysym = parts[-1]
    state = sum(_MODIFIERS.get(p, 0) for p in parts[:-1])
    fields = {"W": str(widget), "K": keysym, "A": "{}", "s": str(state), "T": "2", "%": "%",
              "#": "0", "k": "0", "x": "0", "y": "0", "X": "0", "Y": "0", "N": "0", "E": "1"}
    for tag in widget.bindtags():
        script = widget.tk.call("bind", tag, sequence)
        if not script:
            continue
        script = _PERCENT.sub(lambda m: fields.get(m.group(1), "??"), str(script))
        code = int(widget.tk.call("catch", script))
        if code == TCL_BREAK:
            break


def _is_modified_letter(sequence: str) -> bool:
    parts = sequence.strip("<>").split("-")
    return len(parts) > 1 and len(parts[-1]) == 1


def press(widget, sequence: str) -> None:
    """Нажатие клавиши в виджете.

    Tk доставляет клавиши только окну, у которого есть фокус ОС. Если тесты идут,
    пока пользователь работает в другой программе, Windows не отдаёт фокус нашему
    окну и сгенерированное событие теряется. Тогда привязки выполняются напрямую —
    по bindtags виджета (сам виджет, его класс, окно, all), как это делает Tk.
    Так же обрабатываются сочетания «Ctrl + буква»: Tk для Windows генерирует их
    с keysym '??', и привязка <Control-t> не срабатывает (настоящее нажатие — работает).
    В остальных случаях используется обычный event_generate.
    """
    widget.focus_force()
    pump(widget, 2)
    if widget.focus_get() is not None and not _is_modified_letter(sequence):
        widget.focus_set()
        widget.update()
        widget.event_generate(sequence)
    else:
        _dispatch_by_bindtags(widget, sequence)
    pump(widget, 2)
