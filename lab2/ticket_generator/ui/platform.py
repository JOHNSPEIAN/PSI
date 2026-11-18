"""Интеграция с ОС: чёткий шрифт на HiDPI, тёмный заголовок окна, системная тема, иконка.

Все функции безопасны на любой платформе: если возможность недоступна, ничего не делают.
"""
from __future__ import annotations

import logging
import sys
import tkinter as tk

from .theme import Palette, blend

log = logging.getLogger(__name__)


def enable_hidpi() -> None:
    """Windows: без этого при масштабе 125–150 % окно растягивается и текст размыт."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # system DPI aware
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception as exc:  # pragma: no cover — зависит от версии Windows
        log.debug("HiDPI недоступен: %s", exc)


def system_theme() -> str:
    """'dark' или 'light' по настройке Windows «Режим приложений по умолчанию»."""
    if sys.platform != "win32":
        return "light"
    try:
        import winreg
        key = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
            value, _ = winreg.QueryValueEx(handle, "AppsUseLightTheme")
        return "light" if value else "dark"
    except OSError:
        return "light"


def apply_titlebar(window: tk.Misc, dark: bool) -> None:
    """Windows 10/11: тёмная или светлая системная рамка окна под цвет темы."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(1 if dark else 0)
        for attribute in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (новые и старые сборки)
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)) == 0:
                break
    except Exception as exc:  # pragma: no cover
        log.debug("Не удалось перекрасить заголовок окна: %s", exc)


def make_icon(master: tk.Misc, palette: Palette, size: int = 32) -> tk.PhotoImage:
    """Иконка окна, нарисованная по пикселям: градиентный квадрат с «билетом»."""
    image = tk.PhotoImage(master=master, width=size, height=size)
    radius = size // 5
    rows = []
    for y in range(size):
        row = []
        for x in range(size):
            # скруглённые углы — прозрачные пиксели вне скругления
            cx = min(max(x, radius), size - 1 - radius)
            cy = min(max(y, radius), size - 1 - radius)
            if (x - cx) ** 2 + (y - cy) ** 2 > radius ** 2:
                row.append(None)
                continue
            color = blend(palette.header_from, palette.header_to, (x + y) / (2 * size))
            in_ticket = size * 0.22 <= x <= size * 0.78 and size * 0.3 <= y <= size * 0.7
            notch = (x - size * 0.22) ** 2 + (y - size / 2) ** 2 <= (size * 0.07) ** 2 or \
                    (x - size * 0.78) ** 2 + (y - size / 2) ** 2 <= (size * 0.07) ** 2
            stripe = in_ticket and abs(y - size * 0.44) < 1.2 and x < size * 0.66
            if in_ticket and not notch:
                color = palette.primary if stripe else "#FFFFFF"
            row.append(color)
        rows.append(row)
    for y, row in enumerate(rows):
        for x, color in enumerate(row):
            if color is None:  # прямой вызов Tk: метод transparency_set есть не во всех Python
                image.tk.call(image.name, "transparency", "set", x, y, True)
            else:
                image.put(color, (x, y))
    return image
