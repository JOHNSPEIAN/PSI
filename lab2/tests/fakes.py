"""Тестовые реализации портов (in-memory).

Они подставляются вместо Excel/Word там же, где и настоящие адаптеры, — это и есть
проверка принципа подстановки Лисков: прикладной слой не замечает разницы.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Mapping, Sequence

from ticket_generator.domain import (JournalError, JournalLockedError, JournalRow, Roster,
                                     Student, StudentsFileError, Ticket, TicketsFileError)


class InMemoryJournal:
    def __init__(self, rows: Iterable[JournalRow] = ()):
        self._rows = list(rows)
        self.exists = bool(self._rows)
        self.locked = False      # True — append() ведёт себя как файл, открытый в Excel
        self.broken = False      # True — журнал не читается
        self.append_calls = 0

    def ensure_exists(self) -> bool:
        if self.broken:
            raise JournalError("Не удалось прочитать results.xlsx: файл повреждён")
        created, self.exists = not self.exists, True
        return created

    def rows(self) -> list[JournalRow]:
        if self.broken:
            raise JournalError("Не удалось прочитать results.xlsx: файл повреждён")
        return list(self._rows)

    def append(self, row: JournalRow) -> None:
        self.append_calls += 1
        if self.locked:
            raise JournalLockedError("Файл results.xlsx недоступен для записи — возможно, он открыт в Excel.")
        self.exists = True
        self._rows.append(row)


class InMemoryStudentsSource:
    def __init__(self, groups: Mapping[str, Iterable] | None = None, error: str | None = None):
        self.groups = groups or {}
        self.error = error
        self.loads = 0

    def load(self) -> Roster:
        self.loads += 1
        if self.error:
            raise StudentsFileError(self.error)
        return Roster({g: [s if isinstance(s, Student) else Student(g, *s) for s in rows]
                       for g, rows in self.groups.items()})


class InMemoryTicketsSource:
    def __init__(self, tickets: Mapping[int, Ticket] | None = None, error: str | None = None):
        self.tickets = dict(tickets or {})
        self.error = error

    def load(self) -> dict[int, Ticket]:
        if self.error:
            raise TicketsFileError(self.error)
        return dict(self.tickets)


def make_tickets(n: int = 5) -> dict[int, Ticket]:
    return {i: Ticket(i, tuple(f"Вопрос {i}.{q}" for q in (1, 2, 3))) for i in range(1, n + 1)}


class FixedPicker:
    """Детерминированная стратегия выбора — вторая реализация TicketPicker."""

    def __init__(self, *numbers: int):
        self._numbers = list(numbers)
        self.calls: list[list[int]] = []

    def pick(self, numbers: Sequence[int]) -> int:
        self.calls.append(list(numbers))
        return self._numbers.pop(0) if self._numbers else numbers[0]


class FakeClock:
    def __init__(self, start: datetime = datetime(2026, 11, 18, 9, 0, 0)):
        self.now = start

    def __call__(self) -> datetime:
        self.now += timedelta(seconds=1)
        return self.now


class FakeDialogs:
    """Записывает показанные сообщения; ответ на «Повторить?» задаётся очередью."""

    def __init__(self, retry_answers: Iterable[bool] = ()):
        self.errors: list[tuple[str, str]] = []
        self.retry_questions: list[tuple[str, str]] = []
        self._answers = list(retry_answers)

    def show_error(self, title: str, message: str) -> None:
        self.errors.append((title, message))

    def ask_retry(self, title: str, message: str) -> bool:
        self.retry_questions.append((title, message))
        return self._answers.pop(0) if self._answers else False
