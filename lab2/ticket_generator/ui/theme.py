"""Дизайн-система: палитры светлой и тёмной темы, шрифты, масштаб и стили ttk.

Все цвета интерфейса берутся только отсюда. Остальные модули ui/ ссылаются на
токены палитры (palette.surface, palette.primary …), поэтому новая тема — это
новый экземпляр Palette, а не правка окон (принцип открытости/закрытости).
"""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass, fields
from tkinter import ttk


@dataclass(frozen=True)
class Palette:
    name: str
    is_dark: bool
    bg: str                 # фон окна
    surface: str            # карточки
    surface_alt: str        # поля ввода, чередование строк
    border: str
    text: str
    text_muted: str
    primary: str
    primary_hover: str
    primary_pressed: str
    on_primary: str
    primary_soft: str       # фон бейджей и выделения
    on_primary_soft: str
    success: str            # точка статуса
    success_soft: str
    on_success_soft: str
    warning: str
    warning_soft: str
    on_warning_soft: str
    danger: str
    danger_soft: str
    on_danger_soft: str
    header_from: str        # градиент шапки слева направо
    header_to: str
    on_header: str
    on_header_muted: str
    disabled_bg: str
    disabled_text: str
    focus: str


LIGHT = Palette(
    name="light", is_dark=False,
    bg="#F3F5FA", surface="#FFFFFF", surface_alt="#F6F7FB", border="#E0E4EE",
    text="#141A2E", text_muted="#5B6478",
    primary="#4F46E5", primary_hover="#4338CA", primary_pressed="#3730A3", on_primary="#FFFFFF",
    primary_soft="#EEF0FF", on_primary_soft="#3730A3",
    success="#17B26A", success_soft="#E8F8F0", on_success_soft="#0B6B47",
    warning="#F79009", warning_soft="#FFF5E3", on_warning_soft="#9A4206",
    danger="#F04438", danger_soft="#FEF1F0", on_danger_soft="#B42318",
    header_from="#4F46E5", header_to="#7C3AED", on_header="#FFFFFF", on_header_muted="#E2E4FF",
    disabled_bg="#E6E9F0", disabled_text="#8A92A6", focus="#A5B4FC",
)

DARK = Palette(
    name="dark", is_dark=True,
    bg="#0E1117", surface="#161B26", surface_alt="#1D2331", border="#2A3242",
    text="#E8EBF2", text_muted="#A0A9BC",
    primary="#4F46E5", primary_hover="#5B5BE6", primary_pressed="#4338CA", on_primary="#FFFFFF",
    primary_soft="#252A4D", on_primary_soft="#C9CEFF",
    success="#22C55E", success_soft="#12291F", on_success_soft="#6EE7A8",
    warning="#F59E0B", warning_soft="#2D2312", on_warning_soft="#FCD34D",
    danger="#EF4444", danger_soft="#2E1618", on_danger_soft="#FCA5A5",
    header_from="#312E81", header_to="#5B21B6", on_header="#FFFFFF", on_header_muted="#C9CEFF",
    disabled_bg="#232A38", disabled_text="#6B7489", focus="#818CF8",
)

PALETTES = {p.name: p for p in (LIGHT, DARK)}


# ---------- цвет ----------
def _rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def blend(c1: str, c2: str, t: float) -> str:
    """Смесь цветов: t=0 → c1, t=1 → c2."""
    a, b = _rgb(c1), _rgb(c2)
    return "#%02X%02X%02X" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def contrast_ratio(fg: str, bg: str) -> float:
    """Контраст по WCAG 2.1 (≥ 4.5 — норма для обычного текста)."""
    def luminance(color: str) -> float:
        def channel(v: int) -> float:
            s = v / 255
            return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
        r, g, b = (channel(v) for v in _rgb(color))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def header_pill_color(palette: Palette) -> str:
    """Фон кнопки-«пилюли» в шапке: чуть светлее градиента."""
    return blend(palette.header_to, "#FFFFFF", 0.10)


def color_tokens(palette: Palette) -> dict[str, str]:
    return {f.name: getattr(palette, f.name) for f in fields(palette) if f.name not in ("name", "is_dark")}


# ---------- шрифты ----------
FONT_CANDIDATES = ("Segoe UI", "Inter", "SF Pro Text", "Helvetica Neue", "Ubuntu", "Cantarell",
                   "Noto Sans", "DejaVu Sans")
HEADING_CANDIDATES = ("Segoe UI Semibold",)


@dataclass(frozen=True)
class Fonts:
    family: str
    heading_family: str

    @classmethod
    def resolve(cls, root: tk.Misc) -> Fonts:
        available = set(tkfont.families(root))
        family = next((f for f in FONT_CANDIDATES if f in available),
                      tkfont.nametofont("TkDefaultFont", root).actual("family"))
        heading = next((f for f in HEADING_CANDIDATES if f in available), family)
        return cls(family, heading)

    @property
    def base(self):
        return (self.family, 10)

    @property
    def small(self):
        return (self.family, 9)

    @property
    def label(self):
        return (self.heading_family, 10, "bold") if self.heading_family == self.family \
            else (self.heading_family, 10)

    @property
    def button(self):
        return (self.heading_family, 10, "bold") if self.heading_family == self.family \
            else (self.heading_family, 11)

    @property
    def card_title(self):
        return (self.heading_family, 12, "bold") if self.heading_family == self.family \
            else (self.heading_family, 13)

    @property
    def header_title(self):
        return (self.heading_family, 17, "bold") if self.heading_family == self.family \
            else (self.heading_family, 18)

    @property
    def stat(self):
        return (self.heading_family, 20, "bold") if self.heading_family == self.family \
            else (self.heading_family, 21)

    @property
    def ticket_number(self):
        return (self.family, 34, "bold")

    @property
    def question(self):
        return (self.family, 11)

    @property
    def badge(self):
        return (self.family, 8, "bold")


# ---------- тема ----------
class Theme:
    """Палитра + шрифты + масштаб, применённые к ttk.Style конкретного окна."""

    def __init__(self, root: tk.Misc, palette: Palette):
        self.root = root
        self.palette = palette
        self.fonts = Fonts.resolve(root)
        # Пиксельные размеры масштабируются вместе с DPI экрана (на 96 dpi — 1.0).
        self.scale = max(1.0, root.winfo_fpixels("1i") / 96.0)

    def px(self, value: float) -> int:
        return int(round(value * self.scale))

    def apply(self) -> None:
        p, f, px = self.palette, self.fonts, self.px
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(".", background=p.bg, foreground=p.text, font=f.base,
                        bordercolor=p.border, lightcolor=p.bg, darkcolor=p.bg,
                        troughcolor=p.surface_alt, focuscolor=p.focus,
                        selectbackground=p.primary_soft, selectforeground=p.on_primary_soft,
                        insertcolor=p.text)
        style.configure("TFrame", background=p.bg)
        style.configure("Card.TFrame", background=p.surface)
        style.configure("TLabel", background=p.bg, foreground=p.text)
        style.configure("Card.TLabel", background=p.surface, foreground=p.text)
        style.configure("CardTitle.TLabel", background=p.surface, foreground=p.text, font=f.card_title)
        style.configure("CardMuted.TLabel", background=p.surface, foreground=p.text_muted, font=f.small)
        style.configure("Field.TLabel", background=p.surface, foreground=p.text, font=f.label)
        style.configure("Hint.TLabel", background=p.surface, foreground=p.text_muted, font=f.small)
        style.configure("StatValue.TLabel", background=p.surface, foreground=p.text, font=f.stat)
        style.configure("StatCaption.TLabel", background=p.surface, foreground=p.text_muted, font=f.small)
        style.configure("Status.TLabel", background=p.surface, foreground=p.text, font=f.base)
        style.configure("StatusHint.TLabel", background=p.surface, foreground=p.text_muted, font=f.small)
        style.configure("Question.TLabel", background=p.surface, foreground=p.text, font=f.question)
        style.configure("Empty.TLabel", background=p.surface, foreground=p.text_muted, font=f.base)
        for kind in ("success", "warning", "danger"):
            style.configure(f"{kind.capitalize()}Note.TLabel", font=f.base,
                            background=getattr(p, f"{kind}_soft"),
                            foreground=getattr(p, f"on_{kind}_soft"))
        style.configure("InfoNote.TLabel", font=f.base, background=p.primary_soft,
                        foreground=p.on_primary_soft)

        # Кнопки: вместо пунктирной рамки фокуса — кольцо цвета акцента по краю кнопки.
        button_layout = [("Button.border", {"sticky": "nswe", "border": "1", "children": [
            ("Button.padding", {"sticky": "nswe", "children": [
                ("Button.label", {"sticky": "nswe"})]})]})]
        style.layout("Primary.TButton", button_layout)
        style.layout("Secondary.TButton", button_layout)

        def edge(normal_states: list) -> list:
            return [("disabled", p.disabled_bg), ("focus", p.focus)] + normal_states

        style.configure("Primary.TButton", font=f.button, padding=(px(18), px(10)),
                        background=p.primary, foreground=p.on_primary, borderwidth=2,
                        bordercolor=p.primary, lightcolor=p.primary, darkcolor=p.primary,
                        anchor="center")
        pressed_or_hover = [("pressed", p.primary_pressed), ("active", p.primary_hover)]
        style.map("Primary.TButton",
                  background=[("disabled", p.disabled_bg)] + pressed_or_hover,
                  foreground=[("disabled", p.disabled_text)],
                  bordercolor=edge(pressed_or_hover), lightcolor=edge(pressed_or_hover),
                  darkcolor=edge(pressed_or_hover))
        style.configure("Secondary.TButton", font=f.base, padding=(px(14), px(8)),
                        background=p.surface, foreground=p.text, borderwidth=1,
                        bordercolor=p.border, lightcolor=p.surface, darkcolor=p.surface,
                        anchor="center")
        style.map("Secondary.TButton",
                  background=[("disabled", p.surface), ("pressed", p.primary_soft),
                              ("active", p.surface_alt)],
                  foreground=[("disabled", p.disabled_text), ("pressed", p.on_primary_soft)],
                  bordercolor=[("focus", p.primary), ("active", p.focus)])

        # Выпадающие списки
        style.configure("TCombobox", padding=(px(10), px(7)), arrowsize=px(14),
                        foreground=p.text, background=p.surface_alt, fieldbackground=p.surface_alt,
                        bordercolor=p.border, lightcolor=p.surface_alt, darkcolor=p.surface_alt,
                        arrowcolor=p.text_muted)
        style.map("TCombobox",
                  fieldbackground=[("disabled", p.disabled_bg), ("readonly", p.surface_alt)],
                  background=[("disabled", p.disabled_bg), ("active", p.primary_soft),
                              ("readonly", p.surface_alt)],
                  foreground=[("disabled", p.disabled_text)],
                  arrowcolor=[("disabled", p.disabled_text), ("active", p.primary)],
                  bordercolor=[("focus", p.primary), ("active", p.focus)],
                  lightcolor=[("focus", p.surface_alt)], darkcolor=[("focus", p.surface_alt)],
                  selectbackground=[("readonly", p.surface_alt)],
                  selectforeground=[("readonly", p.text)])
        # Выпадающая часть комбобокса — обычный Listbox, его цвета задаются через option database.
        for option, value in (("background", p.surface), ("foreground", p.text),
                              ("selectBackground", p.primary), ("selectForeground", p.on_primary),
                              ("font", f.base), ("borderWidth", 0), ("relief", "flat")):
            self.root.option_add(f"*TCombobox*Listbox.{option}", value)

        # Таблица истории
        style.configure("History.Treeview", background=p.surface, fieldbackground=p.surface,
                        foreground=p.text, rowheight=px(30), borderwidth=0, relief="flat",
                        font=f.base)
        style.map("History.Treeview",
                  background=[("selected", p.primary_soft)],
                  foreground=[("selected", p.on_primary_soft)])
        style.configure("History.Treeview.Heading", background=p.surface, foreground=p.text_muted,
                        font=f.small, relief="flat", borderwidth=0, padding=(px(6), px(6)),
                        bordercolor=p.border, lightcolor=p.surface, darkcolor=p.surface)
        style.map("History.Treeview.Heading", background=[("active", p.surface_alt)])
        style.layout("History.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        style.configure("Vertical.TScrollbar", background=p.surface_alt, troughcolor=p.surface,
                        bordercolor=p.surface, lightcolor=p.surface_alt, darkcolor=p.surface_alt,
                        arrowcolor=p.text_muted, gripcount=0)
        style.map("Vertical.TScrollbar", background=[("active", p.border)])
        style.configure("TSeparator", background=p.border)

        self.root.configure(background=p.bg)
