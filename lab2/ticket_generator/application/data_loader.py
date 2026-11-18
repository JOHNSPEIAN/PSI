"""Загрузка всех источников данных с накоплением ошибок."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Mapping

from ..domain import DataSourceError, Roster, Ticket, TicketsFileError
from .ports import JournalInitializer, StudentsSource, TicketsSource

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoadResult:
    roster: Roster = field(default_factory=Roster)
    tickets: Mapping[int, Ticket] = field(default_factory=dict)
    errors: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errors


class DataLoader:
    """Читает студентов и билеты, создаёт журнал при необходимости.

    Ошибка одного источника не мешает проверить остальные: пользователь сразу
    видит все проблемы, а не по одной за запуск.
    """

    def __init__(self, students: StudentsSource, tickets: TicketsSource,
                 journal: JournalInitializer):
        self._students = students
        self._tickets = tickets
        self._journal = journal

    def load(self) -> LoadResult:
        errors: list[str] = []
        roster, tickets = Roster(), {}
        try:
            roster = self._students.load()
        except DataSourceError as exc:
            errors.append(self._report(exc))
        try:
            tickets = dict(self._tickets.load())
            if not tickets:
                raise TicketsFileError("Нет ни одного корректного билета")
        except DataSourceError as exc:
            errors.append(self._report(exc))
        try:
            self._journal.ensure_exists()
        except DataSourceError as exc:
            errors.append(self._report(exc))
        if errors:
            return LoadResult(errors=tuple(errors))
        return LoadResult(roster, tickets)

    @staticmethod
    def _report(exc: DataSourceError) -> str:
        log.error("%s", exc)
        return str(exc)
