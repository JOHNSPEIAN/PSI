"""Логика назначения билета и состояние формы (без зависимости от Tkinter)."""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from .journal import JournalRow, ResultsJournal
from .students import Student, find_student
from .tickets import Ticket


@dataclass(frozen=True)
class Assignment:
    student: Student
    ticket_no: int
    questions: tuple[str, ...]  # пусто, если билета с этим номером больше нет в tickets.docx
    repeat: bool
    timestamp: datetime

    def to_journal_row(self) -> JournalRow:
        s = self.student
        return JournalRow(s.group, s.surname, s.name, self.ticket_no, self.timestamp, self.repeat)


class TicketService:
    def __init__(self, tickets: dict[int, Ticket], journal: ResultsJournal,
                 rng: random.Random | None = None,
                 clock: Callable[[], datetime] | None = None):
        if not tickets:
            raise ValueError("Нет ни одного билета")
        self.tickets = tickets
        self.journal = journal
        self.rng = rng or random.Random()
        self.clock = clock or (lambda: datetime.now().replace(microsecond=0))

    def assign(self, student: Student) -> Assignment:
        """Определяет билет: первый из журнала (повтор) или случайный из файла.

        Ничего не записывает — запись делает save(), чтобы при блокировке файла
        повтор попытки сохранял тот же самый билет.
        """
        first = self.journal.find_first_ticket(student.group, student.surname, student.name)
        if first is not None:
            ticket = self.tickets.get(first)
            questions = ticket.questions if ticket else ()
            return Assignment(student, first, questions, True, self.clock())
        number = self.rng.choice(list(self.tickets))
        return Assignment(student, number, self.tickets[number].questions, False, self.clock())

    def save(self, assignment: Assignment) -> None:
        self.journal.append(assignment.to_journal_row())

    def generate(self, student: Student) -> Assignment:
        assignment = self.assign(student)
        self.save(assignment)
        return assignment


class SelectionState:
    """Состояние выпадающих списков и кнопки — то, что отображает GUI."""

    def __init__(self, groups: dict[str, list[Student]] | None = None):
        self.groups = groups or {}
        self.group: str | None = None
        self.student: Student | None = None

    @property
    def group_names(self) -> list[str]:
        return list(self.groups)

    def students_of(self, group: str) -> list[str]:
        return [s.display_name for s in self.groups.get(group, [])]

    def select_group(self, group: str | None) -> list[str]:
        """Выбор группы сбрасывает студента и возвращает список для второго комбобокса."""
        self.group = group if group in self.groups else None
        self.student = None
        return self.students_of(self.group) if self.group else []

    def select_student(self, display_name: str | None) -> None:
        self.student = (find_student(self.groups, self.group, display_name)
                        if self.group and display_name else None)

    def reset_student(self) -> None:
        self.student = None

    @property
    def can_generate(self) -> bool:
        return self.group is not None and self.student is not None
