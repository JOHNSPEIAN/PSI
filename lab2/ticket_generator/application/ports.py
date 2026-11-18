"""Порты — интерфейсы, от которых зависит прикладной слой (принцип инверсии зависимостей).

Реализации лежат в infrastructure/ (Excel, Word, память) и ui/ (диалоги, окно).
Интерфейсы узкие (принцип разделения интерфейсов): например, истории выдач нужен
только JournalReader, а загрузчику данных — только JournalInitializer.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Callable, Mapping, Protocol, Sequence

from ..domain import Assignment, JournalRow, Roster, Student, Ticket

if TYPE_CHECKING:
    from .view_state import ViewState

Clock = Callable[[], datetime]


class StudentsSource(Protocol):
    def load(self) -> Roster:
        """Возвращает список студентов; при ошибке — StudentsFileError."""


class TicketsSource(Protocol):
    def load(self) -> Mapping[int, Ticket]:
        """Возвращает корректные билеты {номер: билет}; при ошибке — TicketsFileError."""


class JournalReader(Protocol):
    def rows(self) -> list[JournalRow]:
        """Все записи журнала в хронологическом порядке; при ошибке — JournalError."""


class JournalWriter(Protocol):
    def append(self, row: JournalRow) -> None:
        """Дописывает строку в конец журнала; если файл занят — JournalLockedError."""


class JournalInitializer(Protocol):
    def ensure_exists(self) -> bool:
        """Создаёт пустой журнал, если его нет. True — если журнал был создан."""


class TicketJournal(JournalReader, JournalWriter, Protocol):
    """То, что нужно сервису выдачи: прочитать историю и дописать строку."""


class TicketPicker(Protocol):
    def pick(self, numbers: Sequence[int]) -> int:
        """Выбирает номер билета для нового студента (принцип открытости/закрытости:
        новая стратегия выбора добавляется новым классом, сервис не меняется)."""


class TicketIssuer(Protocol):
    """Выдача билета: определить (без записи) и сохранить. Реализация — TicketService."""

    def assign(self, student: Student) -> Assignment: ...

    def save(self, assignment: Assignment) -> None: ...


class Dialogs(Protocol):
    """Модальные сообщения пользователю. Реализация — ui/dialogs.py (messagebox)."""

    def show_error(self, title: str, message: str) -> None: ...

    def ask_retry(self, title: str, message: str) -> bool: ...


class MainView(Protocol):
    """Пассивное представление: только отображает то, что передал презентер."""

    def render(self, state: ViewState) -> None: ...

    def show_ticket(self, assignment: Assignment) -> None: ...
