"""Сервис выдачи билета. Зависит только от портов, а не от Excel/Word/Tkinter."""
from __future__ import annotations

import random
from datetime import datetime
from typing import Mapping, Sequence

from ..domain import Assignment, Student, Ticket, first_ticket_of
from .ports import Clock, TicketJournal, TicketPicker


class RandomTicketPicker:
    """Случайный выбор среди корректно разобранных билетов."""

    def __init__(self, rng: random.Random | None = None):
        self._rng = rng or random.Random()

    def pick(self, numbers: Sequence[int]) -> int:
        return self._rng.choice(list(numbers))


def _now() -> datetime:
    return datetime.now().replace(microsecond=0)


class TicketService:
    """Правило выдачи: повторное обращение получает билет из первой записи журнала,
    новый студент — билет, выбранный стратегией TicketPicker."""

    def __init__(self, tickets: Mapping[int, Ticket], journal: TicketJournal,
                 picker: TicketPicker | None = None, clock: Clock | None = None):
        if not tickets:
            raise ValueError("Нет ни одного билета")
        self.tickets = dict(tickets)
        self.journal = journal
        self.picker = picker or RandomTicketPicker()
        self.clock = clock or _now

    def assign(self, student: Student) -> Assignment:
        """Определяет билет, ничего не записывая.

        Запись делает save(): если журнал занят, повтор попытки сохранит тот же билет.
        """
        first = first_ticket_of(self.journal.rows(), student)
        if first is not None:
            ticket = self.tickets.get(first)
            return Assignment(student, first, ticket.questions if ticket else (), True, self.clock())
        number = self.picker.pick(list(self.tickets))
        return Assignment(student, number, self.tickets[number].questions, False, self.clock())

    def save(self, assignment: Assignment) -> None:
        self.journal.append(assignment.to_journal_row())

    def generate(self, student: Student) -> Assignment:
        assignment = self.assign(student)
        self.save(assignment)
        return assignment
