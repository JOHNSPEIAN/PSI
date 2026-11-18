"""Презентер главного окна (MVP, пассивное представление).

Вся логика экрана — загрузка данных, выбор, выдача билета, повтор при блокировке
журнала, статусы и история — здесь, без Tkinter. Окно лишь показывает ViewState
и передаёт сюда действия пользователя, поэтому логика проверяется обычными
модульными тестами.
"""
from __future__ import annotations

import logging
from typing import Callable, Mapping

from ..domain import Assignment, JournalError, JournalLockedError, JournalRow, Ticket, first_ticket_of
from .data_loader import DataLoader
from .formatting import format_when, plural
from .ports import Dialogs, JournalReader, MainView, TicketIssuer
from .selection import SelectionState
from .view_state import HistoryItem, Stats, StatusKind, ViewState

log = logging.getLogger(__name__)

IssuerFactory = Callable[[Mapping[int, Ticket]], TicketIssuer]

HISTORY_LIMIT = 30


class MainPresenter:
    def __init__(self, loader: DataLoader, make_issuer: IssuerFactory,
                 history: JournalReader, dialogs: Dialogs):
        self._loader = loader
        self._make_issuer = make_issuer
        self._history = history
        self._dialogs = dialogs
        self._view: MainView | None = None
        self._selection = SelectionState()
        self._issuer: TicketIssuer | None = None
        self._tickets_count = 0
        self._rows: list[JournalRow] = []
        self._status = ViewState().status
        self._status_kind = StatusKind.INFO
        self._state = ViewState()

    @property
    def state(self) -> ViewState:
        return self._state

    def attach(self, view: MainView) -> None:
        self._view = view
        self._publish()

    # ---------- действия пользователя ----------
    def reload(self) -> None:
        """Перечитывает students.xlsx, tickets.docx и журнал."""
        self._issuer = None
        self._selection = SelectionState()
        self._tickets_count = 0
        self._rows = []
        result = self._loader.load()
        if not result.ok:
            self._set_status("Данные не загружены. Исправьте файлы и нажмите «Обновить данные».",
                             StatusKind.ERROR)
            self._publish()
            self._dialogs.show_error("Ошибка загрузки данных", "\n\n".join(result.errors))
            return
        self._selection = SelectionState(result.roster)
        self._issuer = self._make_issuer(result.tickets)
        self._tickets_count = len(result.tickets)
        self._rows = self._read_history()
        roster = result.roster
        self._set_status(
            f"Загружено: {plural(len(roster), 'группа', 'группы', 'групп')}, "
            f"{plural(roster.total_students, 'студент', 'студента', 'студентов')}, "
            f"{plural(self._tickets_count, 'билет', 'билета', 'билетов')}.", StatusKind.SUCCESS)
        self._publish()

    def select_group(self, group: str | None) -> None:
        names = self._selection.select_group(group or None)
        selected = self._selection.group
        if selected is None:
            self._set_status("Выберите группу.", StatusKind.INFO)
        elif not names:
            self._set_status(f"В группе {selected} нет студентов.", StatusKind.WARNING)
        else:
            self._set_status(f"Группа {selected}: "
                             f"{plural(len(names), 'студент', 'студента', 'студентов')}. "
                             f"Выберите себя в списке.", StatusKind.INFO)
        self._publish()

    def select_student(self, display_name: str | None) -> None:
        self._selection.select_student(display_name or None)
        if self._selection.can_generate:
            self._set_status("Нажмите «Сгенерировать билет» или Enter.", StatusKind.INFO)
        self._publish()

    def generate(self) -> Assignment | None:
        """Выдаёт билет выбранному студенту. None — если билет не выдан."""
        student = self._selection.student
        if self._issuer is None or student is None or not self._selection.can_generate:
            return None
        try:
            assignment = self._issuer.assign(student)
        except JournalError as exc:
            self._fail("Ошибка журнала", exc)
            return None
        if not self._save_with_retry(assignment):
            return None
        self._rows = self._read_history()
        if assignment.repeat:
            self._set_status(f"{student.display_name}: повторное обращение, "
                             f"выдан тот же билет № {assignment.ticket_no}.", StatusKind.INFO)
        else:
            self._set_status(f"{student.display_name} получает билет № {assignment.ticket_no}.",
                             StatusKind.SUCCESS)
        self._publish()
        if self._view is not None:
            self._view.show_ticket(assignment)
        return assignment

    def ticket_closed(self) -> None:
        """Окно билета закрыто: группа остаётся, студент сбрасывается — готово к следующему."""
        self._selection.reset_student()
        self._publish()

    # ---------- внутреннее ----------
    def _save_with_retry(self, assignment: Assignment) -> bool:
        """Сохраняет сразу после выдачи; если журнал открыт в Excel — предлагает повторить."""
        while True:
            try:
                self._issuer.save(assignment)
                return True
            except JournalLockedError as exc:
                log.warning("%s", exc)
                if not self._dialogs.ask_retry("Журнал недоступен", str(exc)):
                    self._set_status("Билет не выдан: журнал не удалось сохранить.", StatusKind.ERROR)
                    self._publish()
                    return False
            except JournalError as exc:
                self._fail("Ошибка журнала", exc)
                return False

    def _fail(self, title: str, exc: Exception) -> None:
        log.error("%s", exc)
        self._set_status(f"{title}: билет не выдан.", StatusKind.ERROR)
        self._publish()
        self._dialogs.show_error(title, str(exc))

    def _read_history(self) -> list[JournalRow]:
        try:
            return self._history.rows()
        except JournalError as exc:
            log.warning("История выдач недоступна: %s", exc)
            return []

    def _set_status(self, text: str, kind: StatusKind) -> None:
        self._status, self._status_kind = text, kind

    def _hint(self) -> str:
        student = self._selection.student
        if student is None:
            return ""
        first = first_ticket_of(self._rows, student)
        if first is None:
            return "Билет ещё не выдавался — номер будет выбран случайно."
        return f"Ранее выдан билет № {first} — при повторном обращении выдаётся тот же."

    def _stats(self) -> Stats:
        roster = self._selection.roster
        repeats = sum(1 for row in self._rows if row.repeat)
        return Stats(len(roster), roster.total_students, self._tickets_count,
                     len(self._rows) - repeats, repeats)

    def _history_items(self) -> tuple[HistoryItem, ...]:
        recent = self._rows[-HISTORY_LIMIT:][::-1]
        return tuple(HistoryItem(format_when(r.timestamp), f"{r.surname} {r.name}", r.group,
                                 r.ticket_no, r.repeat) for r in recent)

    def _publish(self) -> None:
        sel = self._selection
        self._state = ViewState(
            loaded=self._issuer is not None,
            groups=tuple(sel.group_names),
            group=sel.group,
            students=tuple(sel.students_of(sel.group)),
            student=sel.student.display_name if sel.student else None,
            can_generate=self._issuer is not None and sel.can_generate,
            hint=self._hint(),
            status=self._status,
            status_kind=self._status_kind,
            stats=self._stats(),
            history=self._history_items(),
        )
        if self._view is not None:
            self._view.render(self._state)
