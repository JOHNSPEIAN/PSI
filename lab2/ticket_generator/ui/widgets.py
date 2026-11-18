"""Переиспользуемые элементы интерфейса поверх Tkinter/ttk.

Каждый виджет получает Theme и берёт цвета только из её палитры.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from .theme import Theme, blend, header_pill_color


def rounded_rect(canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, r: float,
                 **options) -> int:
    """Прямоугольник со скруглёнными углами (сглаженный многоугольник)."""
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
              x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(points, smooth=True, **options)


def draw_horizontal_gradient(canvas: tk.Canvas, width: int, height: int, start: str, end: str,
                             tag: str = "gradient") -> None:
    canvas.delete(tag)
    steps = max(width, 1)
    for x in range(0, steps, 2):
        color = blend(start, end, x / steps)
        canvas.create_rectangle(x, 0, x + 2, height, fill=color, outline=color, tags=tag)
    canvas.tag_lower(tag)


class Card(tk.Frame):
    """Карточка: светлая поверхность с тонкой рамкой. Содержимое кладётся в .body."""

    def __init__(self, master: tk.Misc, theme: Theme, padding: int = 20):
        p = theme.palette
        super().__init__(master, background=p.surface, highlightthickness=1,
                         highlightbackground=p.border, highlightcolor=p.border, borderwidth=0)
        self.body = ttk.Frame(self, style="Card.TFrame", padding=theme.px(padding))
        self.body.pack(fill="both", expand=True)


class NumberBadge(tk.Canvas):
    """Кружок с цифрой — номер шага или номер вопроса."""

    def __init__(self, master: tk.Misc, theme: Theme, number: int | str, size: int = 26,
                 background: str | None = None):
        p = theme.palette
        side = theme.px(size)
        super().__init__(master, width=side, height=side, highlightthickness=0, borderwidth=0,
                         background=background or p.surface)
        self.create_oval(1, 1, side - 1, side - 1, fill=p.primary_soft, outline=p.primary_soft)
        self.text_id = self.create_text(side / 2, side / 2, text=str(number), fill=p.on_primary_soft,
                                        font=(theme.fonts.family, max(8, size // 3), "bold"))

    @property
    def text(self) -> str:
        return self.itemcget(self.text_id, "text")


class StatTile(Card):
    """Плитка статистики: крупное число и подпись."""

    def __init__(self, master: tk.Misc, theme: Theme, caption: str):
        super().__init__(master, theme, padding=14)
        self.value = ttk.Label(self.body, text="—", style="StatValue.TLabel")
        self.value.pack(anchor="w")
        self.caption = ttk.Label(self.body, text=caption, style="StatCaption.TLabel")
        self.caption.pack(anchor="w")

    def set(self, value: int | str) -> None:
        self.value.configure(text=str(value))


class GradientHeader(tk.Canvas):
    """Шапка окна: градиент, логотип, заголовок и кнопка-«пилюля» справа."""

    def __init__(self, master: tk.Misc, theme: Theme, title: str, subtitle: str,
                 action_text: str = "", on_action: Callable[[], None] | None = None,
                 height: int = 92):
        self.theme = theme
        p, px = theme.palette, theme.px
        super().__init__(master, height=px(height), highlightthickness=0, borderwidth=0,
                         background=p.header_from)
        self._on_action = on_action
        self._height = px(height)
        logo = px(46)
        top = (self._height - logo) // 2
        rounded_rect(self, px(24), top, px(24) + logo, top + logo, px(12),
                     fill=blend(p.header_from, "#FFFFFF", 0.18), outline="", tags="logo")
        self.create_text(px(24) + logo / 2, top + logo / 2, text="№", fill=p.on_header,
                         font=(theme.fonts.family, 17, "bold"), tags="logo")
        text_x = px(24) + logo + px(16)
        self.title_id = self.create_text(text_x, self._height / 2 - px(11), text=title, anchor="w",
                                         fill=p.on_header, font=theme.fonts.header_title)
        self.subtitle_id = self.create_text(text_x, self._height / 2 + px(15), text=subtitle,
                                            anchor="w", fill=p.on_header_muted, font=theme.fonts.base)
        self.action_text_id: int | None = None
        if on_action is not None:
            # Контраст белого текста на «пилюле» ≥ 4.5 в обеих темах (проверяется тестом).
            self._pill_fill = header_pill_color(p)
            self._pill_hover = blend(p.header_to, "#000000", 0.12)
            self.action_text_id = self.create_text(0, 0, text=action_text, fill=p.on_header,
                                                   font=theme.fonts.label, tags=("action", "action_text"))
            for event, handler in (("<Button-1>", self._click), ("<Enter>", self._hover_on),
                                   ("<Leave>", self._hover_off)):
                self.tag_bind("action", event, handler)
        self.bind("<Configure>", self._redraw)

    @property
    def action_text(self) -> str:
        return self.itemcget(self.action_text_id, "text") if self.action_text_id else ""

    def action_center(self) -> tuple[int, int]:
        x1, y1, x2, y2 = self.bbox("action_pill")
        return (x1 + x2) // 2, (y1 + y2) // 2

    def _redraw(self, event: tk.Event) -> None:
        p, px = self.theme.palette, self.theme.px
        draw_horizontal_gradient(self, event.width, self._height, p.header_from, p.header_to)
        if self.action_text_id is None:
            return
        self.delete("action_pill")
        x1, y1, x2, y2 = self.bbox(self.action_text_id)
        text_w, text_h = x2 - x1, y2 - y1
        right = event.width - px(24)
        left = right - text_w - px(32)
        top = (self._height - text_h - px(16)) / 2
        bottom = top + text_h + px(16)
        rounded_rect(self, left, top, right, bottom, px(16), fill=self._pill_fill, outline="",
                     tags=("action", "action_pill"))
        self.coords(self.action_text_id, (left + right) / 2, (top + bottom) / 2)
        self.tag_raise("action_text")

    def _click(self, _event=None) -> None:
        if self._on_action is not None:
            self._on_action()

    def _hover_on(self, _event=None) -> None:
        self.itemconfigure("action_pill", fill=self._pill_hover)
        self.configure(cursor="hand2")

    def _hover_off(self, _event=None) -> None:
        self.itemconfigure("action_pill", fill=self._pill_fill)
        self.configure(cursor="")


class StatusBar(tk.Frame):
    """Нижняя строка: цветная точка + текст состояния, справа — подсказка по клавишам."""

    def __init__(self, master: tk.Misc, theme: Theme, hint: str):
        self.theme = theme
        p, px = theme.palette, theme.px
        super().__init__(master, background=p.surface, highlightthickness=0, borderwidth=0)
        tk.Frame(self, height=1, background=p.border).pack(side="top", fill="x")
        inner = tk.Frame(self, background=p.surface)
        inner.pack(fill="x", padx=px(20), pady=px(9))
        side = px(10)
        self.dot = tk.Canvas(inner, width=side, height=side, highlightthickness=0,
                             background=p.surface)
        self.dot_id = self.dot.create_oval(1, 1, side - 1, side - 1, fill=p.text_muted, outline="")
        self.dot.pack(side="left", padx=(0, px(8)))
        self.label = ttk.Label(inner, text="", style="Status.TLabel")
        self.label.pack(side="left", fill="x", expand=True)
        self.hint = ttk.Label(inner, text=hint, style="StatusHint.TLabel")
        self.hint.pack(side="right")

    def set(self, text: str, color: str) -> None:
        self.label.configure(text=text)
        self.dot.itemconfigure(self.dot_id, fill=color)

    @property
    def dot_color(self) -> str:
        return self.dot.itemcget(self.dot_id, "fill")
