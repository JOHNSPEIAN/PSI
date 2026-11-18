"""Модальное окно «Билет № N». Esc или Enter закрывают только его."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ..domain import Assignment
from .platform import apply_titlebar
from .theme import Theme
from .widgets import NumberBadge, draw_horizontal_gradient, rounded_rect

WRAP = 470


class TicketWindow(tk.Toplevel):
    def __init__(self, master: tk.Misc, theme: Theme, assignment: Assignment,
                 on_close: Callable[[], None]):
        super().__init__(master)
        self.theme = theme
        self.assignment = assignment
        self._on_close = on_close
        self._closed = False
        p, px = theme.palette, theme.px
        s = assignment.student

        self.title(f"Билет № {assignment.ticket_no} — {s.display_name}")
        self.configure(background=p.surface)
        self.transient(master)
        self.resizable(False, False)

        self._build_band(assignment)

        body = ttk.Frame(self, style="Card.TFrame", padding=(px(28), px(22), px(28), px(8)))
        body.pack(fill="both", expand=True)
        self.question_labels: list[ttk.Label] = []
        self.question_badges: list[NumberBadge] = []
        if assignment.questions:
            for i, question in enumerate(assignment.questions, start=1):
                row = ttk.Frame(body, style="Card.TFrame")
                row.pack(fill="x", pady=(0 if i == 1 else px(6), px(6)))
                badge = NumberBadge(row, theme, i, size=30)
                badge.pack(side="left", anchor="n", padx=(0, px(14)))
                label = ttk.Label(row, text=question, style="Question.TLabel",
                                  wraplength=px(WRAP), justify="left")
                label.pack(side="left", fill="x", expand=True, anchor="w", pady=(px(3), 0))
                self.question_badges.append(badge)
                self.question_labels.append(label)
                if i < len(assignment.questions):
                    tk.Frame(body, height=1, background=p.border).pack(
                        fill="x", pady=(px(6), 0), padx=(px(44), 0))

        self.note_label: ttk.Label | None = None
        if not assignment.questions:
            self.note_label = self._note(body, "Билета с этим номером больше нет в tickets.docx — "
                                               "обратитесь к преподавателю.", "DangerNote.TLabel")
        elif assignment.repeat:
            self.note_label = self._note(body, "Повторное обращение: выдан тот же билет, "
                                               "что и в первый раз.", "WarningNote.TLabel")

        footer = ttk.Frame(self, style="Card.TFrame", padding=(px(28), px(10), px(28), px(22)))
        footer.pack(fill="x")
        ttk.Label(footer, text="Esc — закрыть", style="Hint.TLabel").pack(side="left")
        self.close_btn = ttk.Button(footer, text="Готово", style="Primary.TButton",
                                    command=self.close, cursor="hand2")
        self.close_btn.pack(side="right")

        for key in ("<Escape>", "<Return>", "<KP_Enter>"):
            self.bind(key, self.close)
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.update_idletasks()
        self._center_on(master)
        apply_titlebar(self, p.is_dark)
        self.grab_set()
        self.close_btn.focus_set()

    # ---------- построение ----------
    def _build_band(self, a: Assignment) -> None:
        p, px, f = self.theme.palette, self.theme.px, self.theme.fonts
        width, height = px(WRAP + 100), px(138)
        band = tk.Canvas(self, width=width, height=height, highlightthickness=0, borderwidth=0,
                         background=p.header_from)
        band.pack(fill="x")
        draw_horizontal_gradient(band, width, height, p.header_from, p.header_to)
        left = px(28)
        band.create_text(left, px(26), text="ЭКЗАМЕНАЦИОННЫЙ БИЛЕТ", anchor="w",
                         fill=p.on_header_muted, font=f.badge)
        self.number_id = band.create_text(left - px(2), px(66), text=f"№ {a.ticket_no}", anchor="w",
                                          fill=p.on_header, font=f.ticket_number)
        s = a.student
        when = a.timestamp.strftime("%d.%m.%Y %H:%M")
        self.student_id = band.create_text(left, px(110), anchor="w", fill=p.on_header_muted,
                                           font=f.base, text=f"{s.display_name} · {s.group} · {when}")

        kind = "warning" if a.repeat else "success"
        badge_fill, badge_text_color = getattr(p, f"{kind}_soft"), getattr(p, f"on_{kind}_soft")
        self.badge_id = band.create_text(0, 0, text="ПОВТОР" if a.repeat else "НОВЫЙ",
                                         fill=badge_text_color, font=f.badge)
        x1, y1, x2, y2 = band.bbox(self.badge_id)
        right, top = width - px(28), px(18)
        bw, bh = (x2 - x1) + px(22), (y2 - y1) + px(10)
        rounded_rect(band, right - bw, top, right, top + bh, bh / 2, fill=badge_fill, outline="")
        band.coords(self.badge_id, right - bw / 2, top + bh / 2)
        band.tag_raise(self.badge_id)
        self.band = band

    def _note(self, master: tk.Misc, text: str, style: str) -> ttk.Label:
        px = self.theme.px
        label = ttk.Label(master, text=text, style=style, wraplength=px(WRAP + 30), justify="left",
                          padding=(px(14), px(10)))
        label.pack(fill="x", pady=(px(12), 0))
        return label

    def _center_on(self, master: tk.Misc) -> None:
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_reqwidth()) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    # ---------- данные для тестов и доступности ----------
    @property
    def number_text(self) -> str:
        return self.band.itemcget(self.number_id, "text")

    @property
    def badge_text(self) -> str:
        return self.band.itemcget(self.badge_id, "text")

    @property
    def student_text(self) -> str:
        return self.band.itemcget(self.student_id, "text")

    @property
    def question_texts(self) -> list[str]:
        return [label.cget("text") for label in self.question_labels]

    # ---------- закрытие ----------
    def close(self, _event=None) -> None:
        if self._closed:
            return
        self._closed = True
        self.grab_release()
        self.destroy()
        self._on_close()
