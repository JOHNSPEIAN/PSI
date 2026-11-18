"""Порты — интерфейсы, от которых зависит прикладной слой (принцип инверсии зависимостей).

Реализации лежат в infrastructure/ (Excel, Word, память) и ui/ (диалоги, окно).
Интерфейсы узкие (принцип разделения интерфейсов): например, истории выдач нужен
только JournalReader, а загрузчику данных — только JournalInitializer.
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable, Mapping, Protocol, Sequence

from ..domain import JournalRow, Roster, Ticket

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
