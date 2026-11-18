"""Доменные сущности: студент, билет, запись журнала, назначение билета.

Модуль не зависит ни от файлов, ни от Tkinter — только чистые данные и правила.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Mapping

QUESTIONS_PER_TICKET = 3

StudentKey = tuple[str, str, str]


def _norm(value: object) -> str:
    return "" if value is None else str(value).strip().casefold()


def student_key(group: object, surname: object, name: object) -> StudentKey:
    """Ключ сравнения студентов: группа + фамилия + имя без учёта регистра и пробелов по краям.

    Студенты с одинаковыми ФИО из разных групп — разные люди.
    """
    return _norm(group), _norm(surname), _norm(name)


@dataclass(frozen=True)
class Student:
    group: str
    surname: str
    name: str

    @property
    def display_name(self) -> str:
        """Формат для выпадающего списка: «Фамилия Имя»."""
        return f"{self.surname} {self.name}"

    @property
    def key(self) -> StudentKey:
        return student_key(self.group, self.surname, self.name)


@dataclass(frozen=True)
class Ticket:
    number: int
    questions: tuple[str, ...]


@dataclass(frozen=True)
class JournalRow:
    """Одна строка журнала results.xlsx."""
    group: str
    surname: str
    name: str
    ticket_no: int
    timestamp: datetime | None
    repeat: bool

    @property
    def student_key(self) -> StudentKey:
        return student_key(self.group, self.surname, self.name)


@dataclass(frozen=True)
class Assignment:
    """Результат выдачи билета студенту."""
    student: Student
    ticket_no: int
    questions: tuple[str, ...]  # пусто, если билета с этим номером больше нет в tickets.docx
    repeat: bool
    timestamp: datetime

    def to_journal_row(self) -> JournalRow:
        s = self.student
        return JournalRow(s.group, s.surname, s.name, self.ticket_no, self.timestamp, self.repeat)


def first_ticket_of(rows: Iterable[JournalRow], student: Student) -> int | None:
    """Номер билета из самой первой записи студента в журнале или None."""
    key = student.key
    for row in rows:
        if row.student_key == key:
            return row.ticket_no
    return None


class Roster:
    """Список студентов по группам; порядок групп совпадает с порядком листов в книге."""

    def __init__(self, groups: Mapping[str, Iterable[Student]] | None = None):
        self._groups: dict[str, tuple[Student, ...]] = {
            group: tuple(students) for group, students in (groups or {}).items()}

    @property
    def group_names(self) -> tuple[str, ...]:
        return tuple(self._groups)

    def students_of(self, group: str | None) -> tuple[Student, ...]:
        return self._groups.get(group, ()) if group is not None else ()

    def find(self, group: str | None, display_name: str | None) -> Student | None:
        """Поиск студента по группе и строке «Фамилия Имя» из выпадающего списка."""
        for student in self.students_of(group):
            if student.display_name == display_name:
                return student
        return None

    @property
    def total_students(self) -> int:
        return sum(len(students) for students in self._groups.values())

    def __len__(self) -> int:
        return len(self._groups)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Roster) and self._groups == other._groups

    def __repr__(self) -> str:
        return f"Roster({ {g: len(s) for g, s in self._groups.items()} })"
