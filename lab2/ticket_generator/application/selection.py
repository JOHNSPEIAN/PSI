"""Состояние выбора «группа → студент» и правило активности кнопки."""
from __future__ import annotations

from ..domain import Roster, Student


class SelectionState:
    def __init__(self, roster: Roster | None = None):
        self.roster = roster or Roster()
        self.group: str | None = None
        self.student: Student | None = None

    @property
    def group_names(self) -> list[str]:
        return list(self.roster.group_names)

    def students_of(self, group: str | None) -> list[str]:
        return [s.display_name for s in self.roster.students_of(group)]

    def select_group(self, group: str | None) -> list[str]:
        """Выбор группы сбрасывает студента и возвращает список для второго комбобокса."""
        self.group = group if group in self.roster.group_names else None
        self.student = None
        return self.students_of(self.group)

    def select_student(self, display_name: str | None) -> None:
        self.student = self.roster.find(self.group, display_name) if display_name else None

    def reset_student(self) -> None:
        self.student = None

    @property
    def can_generate(self) -> bool:
        return self.group is not None and self.student is not None
