"""Главное окно — пассивное представление (MVP).

Окно ничего не решает само: показывает ViewState от презентера и передаёт ему
действия пользователя. Тема оформления — единственное, чем окно управляет само.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .. import __version__
from ..application.presenter import MainPresenter
from ..application.view_state import StatusKind, ViewState
from ..domain import Assignment
from .platform import apply_titlebar, make_icon
from .theme import PALETTES, Theme
from .ticket_window import TicketWindow
from .widgets import Card, GradientHeader, NumberBadge, StatTile, StatusBar

APP_TITLE = "Экзаменационные билеты"
APP_SUBTITLE = f"ПСИ · Лабораторная работа №2 · версия {__version__}"
SHORTCUTS = "Enter — билет · F5 — обновить · Ctrl+T — тема"

HISTORY_COLUMNS = (
    ("when", "Время", 96, "w"),
    ("student", "Студент", 190, "w"),
    ("group", "Группа", 84, "w"),
    ("ticket", "Билет", 62, "center"),
    ("kind", "Тип", 78, "center"),
)


class MainWindow(tk.Tk):
    def __init__(self, theme: str = "light"):
        super().__init__()
        self.title(APP_TITLE)
        self.theme = Theme(self, PALETTES.get(theme, PALETTES["light"]))
        self.presenter: MainPresenter | None = None
        self.ticket_window: TicketWindow | None = None
        self._state = ViewState()
        self._container: tk.Frame | None = None
        self._icon: tk.PhotoImage | None = None
        self._apply_theme()
        self._build()
        self._bind_shortcuts()
        self._place_on_screen()

    # ---------- связь с презентером ----------
    def connect(self, presenter: MainPresenter) -> None:
        self.presenter = presenter
        presenter.attach(self)
        # Данные читаются после появления окна: сообщение об ошибке откроется поверх него.
        self.after(0, presenter.reload)

    def render(self, state: ViewState) -> None:
        self._state = state
        p = self.theme.palette

        self.group_combo.configure(values=state.groups,
                                   state="readonly" if state.groups else "disabled")
        self.group_var.set(state.group or "")
        self.student_combo.configure(values=state.students,
                                     state="readonly" if state.students else "disabled")
        self.student_var.set(state.student or "")
        self.hint_label.configure(text=state.hint)
        self.generate_btn.state(["!disabled"] if state.can_generate else ["disabled"])

        stats = state.stats
        for key, value in (("groups", stats.groups), ("students", stats.students),
                           ("tickets", stats.tickets), ("issued", stats.issued)):
            self.stat_tiles[key].set(value if state.loaded else "—")
        self.repeats_label.configure(text=f"повторных обращений: {stats.repeats}" if stats.repeats else "")

        self.history_tree.delete(*self.history_tree.get_children())
        for i, item in enumerate(state.history):
            tags = ("repeat" if item.repeat else "new", "odd" if i % 2 else "even")
            self.history_tree.insert("", "end", values=(
                item.when, item.student, item.group, f"№ {item.ticket_no}",
                "повтор" if item.repeat else "новый"), tags=tags)
        if state.history:
            self.history_empty.place_forget()
        else:
            self.history_empty.place(relx=0.5, rely=0.45, anchor="center")

        dot = {StatusKind.SUCCESS: p.success, StatusKind.WARNING: p.warning,
               StatusKind.ERROR: p.danger, StatusKind.INFO: p.primary}[state.status_kind]
        self.status_bar.set(state.status, dot)

    def show_ticket(self, assignment: Assignment) -> None:
        self.ticket_window = TicketWindow(self, self.theme, assignment, on_close=self._ticket_closed)

    # ---------- тема ----------
    def toggle_theme(self) -> None:
        self.set_theme("light" if self.theme.palette.is_dark else "dark")

    def set_theme(self, name: str) -> None:
        if name == self.theme.palette.name or name not in PALETTES:
            return
        self.theme = Theme(self, PALETTES[name])
        self._apply_theme()
        self._build()
        self.render(self._state)

    def _apply_theme(self) -> None:
        self.theme.apply()
        self._icon = make_icon(self, self.theme.palette)
        self.iconphoto(True, self._icon)
        apply_titlebar(self, self.theme.palette.is_dark)

    # ---------- построение ----------
    def _build(self) -> None:
        if self._container is not None:
            self._container.destroy()
        p, px = self.theme.palette, self.theme.px
        self._container = root = tk.Frame(self, background=p.bg)
        root.pack(fill="both", expand=True)

        theme_label = "☀  Светлая тема" if p.is_dark else "☾  Тёмная тема"
        self.header = GradientHeader(root, self.theme, APP_TITLE, APP_SUBTITLE,
                                     action_text=theme_label, on_action=self.toggle_theme)
        self.header.pack(fill="x")

        self.status_bar = StatusBar(root, self.theme, SHORTCUTS)
        self.status_bar.pack(side="bottom", fill="x")

        content = tk.Frame(root, background=p.bg)
        content.pack(fill="both", expand=True, padx=px(20), pady=px(20))
        content.columnconfigure(0, weight=0, minsize=px(330))
        content.columnconfigure(1, weight=1)
        content.rowconfigure(1, weight=1)

        self._build_selection_card(content).grid(row=0, column=0, rowspan=2, sticky="nsew",
                                                 padx=(0, px(16)))
        self._build_stats(content).grid(row=0, column=1, sticky="ew", pady=(0, px(16)))
        self._build_history_card(content).grid(row=1, column=1, sticky="nsew")

    def _build_selection_card(self, master: tk.Misc) -> Card:
        px = self.theme.px
        card = Card(master, self.theme, padding=22)
        body = card.body
        ttk.Label(body, text="Получение билета", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(body, text="Выберите группу, затем себя в списке.",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(px(2), px(16)))

        self.group_var = tk.StringVar(master=self)
        self.group_combo = self._field(body, 1, "Группа", self.group_var)
        self.group_combo.bind("<<ComboboxSelected>>", self.on_group_selected)

        self.student_var = tk.StringVar(master=self)
        self.student_combo = self._field(body, 2, "Студент", self.student_var)
        self.student_combo.bind("<<ComboboxSelected>>", self.on_student_selected)

        self.hint_label = ttk.Label(body, text="", style="Hint.TLabel", wraplength=px(280),
                                    justify="left")
        self.hint_label.pack(anchor="w", fill="x", pady=(px(8), 0))

        spacer = ttk.Frame(body, style="Card.TFrame")
        spacer.pack(fill="both", expand=True)

        self.generate_btn = ttk.Button(body, text="Сгенерировать билет  →", style="Primary.TButton",
                                       command=self.on_generate, cursor="hand2")
        self.generate_btn.pack(fill="x", pady=(px(18), px(8)))
        self.generate_btn.state(["disabled"])
        self.reload_btn = ttk.Button(body, text="⟳  Обновить данные", style="Secondary.TButton",
                                     command=self.on_reload, cursor="hand2")
        self.reload_btn.pack(fill="x")
        return card

    def _field(self, master: tk.Misc, step: int, caption: str, variable: tk.StringVar) -> ttk.Combobox:
        px = self.theme.px
        row = ttk.Frame(master, style="Card.TFrame")
        row.pack(fill="x", pady=(px(4), px(6)))
        NumberBadge(row, self.theme, step, size=22).pack(side="left", padx=(0, px(8)))
        ttk.Label(row, text=caption, style="Field.TLabel").pack(side="left")
        combo = ttk.Combobox(master, textvariable=variable, state="disabled", height=12,
                             font=self.theme.fonts.base)
        combo.pack(fill="x", pady=(0, px(8)))
        return combo

    def _build_stats(self, master: tk.Misc) -> tk.Frame:
        px = self.theme.px
        row = tk.Frame(master, background=self.theme.palette.bg)
        self.stat_tiles: dict[str, StatTile] = {}
        for i, (key, caption) in enumerate((("groups", "групп"), ("students", "студентов"),
                                            ("tickets", "билетов"), ("issued", "выдано"))):
            row.columnconfigure(i, weight=1, uniform="stats")
            tile = StatTile(row, self.theme, caption)
            tile.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else px(12), 0))
            self.stat_tiles[key] = tile
        return row

    def _build_history_card(self, master: tk.Misc) -> Card:
        p, px = self.theme.palette, self.theme.px
        card = Card(master, self.theme, padding=18)
        head = ttk.Frame(card.body, style="Card.TFrame")
        head.pack(fill="x", pady=(0, px(10)))
        ttk.Label(head, text="Последние выдачи", style="CardTitle.TLabel").pack(side="left")
        self.repeats_label = ttk.Label(head, text="", style="CardMuted.TLabel")
        self.repeats_label.pack(side="right")

        table = ttk.Frame(card.body, style="Card.TFrame")
        table.pack(fill="both", expand=True)
        self.history_tree = ttk.Treeview(table, style="History.Treeview", show="headings",
                                         columns=[c[0] for c in HISTORY_COLUMNS], height=8,
                                         selectmode="browse")
        for key, title, width, anchor in HISTORY_COLUMNS:
            self.history_tree.heading(key, text=title.upper(), anchor=anchor)
            self.history_tree.column(key, width=px(width), minwidth=px(width) // 2, anchor=anchor,
                                     stretch=key == "student")
        self.history_tree.tag_configure("odd", background=p.surface_alt)
        self.history_tree.tag_configure("even", background=p.surface)
        self.history_tree.tag_configure("repeat", foreground=p.text_muted)
        self.history_tree.tag_configure("new", foreground=p.text)
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scroll.set)
        self.history_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.history_empty = ttk.Label(table, text="Пока никто не получил билет",
                                       style="Empty.TLabel")
        return card

    def _bind_shortcuts(self) -> None:
        # Вторые варианты — для русской раскладки (Ctrl+К и Ctrl+Е на тех же клавишах).
        for key in ("<Return>", "<KP_Enter>"):
            self.bind(key, self._on_enter)
        for key in ("<F5>", "<Control-r>", "<Control-Cyrillic_ka>"):
            self.bind(key, lambda _e: self.on_reload())
        for key in ("<Control-t>", "<Control-Cyrillic_ie>"):
            self.bind(key, lambda _e: self.toggle_theme())

    def _place_on_screen(self) -> None:
        self.update_idletasks()
        width = max(self.winfo_reqwidth(), self.theme.px(940))
        height = max(self.winfo_reqheight(), self.theme.px(600))
        x = max((self.winfo_screenwidth() - width) // 2, 0)
        y = max((self.winfo_screenheight() - height) // 3, 0)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

    # ---------- действия пользователя → презентер ----------
    def on_group_selected(self, _event=None) -> None:
        if self.presenter:
            self.presenter.select_group(self.group_var.get())
            if self._state.students:
                self.student_combo.focus_set()

    def on_student_selected(self, _event=None) -> None:
        if self.presenter:
            self.presenter.select_student(self.student_var.get())
            if self._state.can_generate:
                self.generate_btn.focus_set()

    def on_generate(self) -> None:
        if self.presenter and self.ticket_window is None:
            self.presenter.generate()

    def on_reload(self) -> None:
        if self.presenter and self.ticket_window is None:
            self.presenter.reload()

    def _on_enter(self, _event=None) -> str:
        if self._state.can_generate:
            self.on_generate()
        return "break"

    def _ticket_closed(self) -> None:
        self.ticket_window = None
        if self.presenter:
            self.presenter.ticket_closed()
        self.student_combo.focus_set()
