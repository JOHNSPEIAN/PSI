"""Модель представления: всё, что главное окно должно показать, в готовом виде."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class StatusKind(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Stats:
    groups: int = 0
    students: int = 0
    tickets: int = 0
    issued: int = 0   # студентов, уже получивших билет (первые выдачи)
    repeats: int = 0  # повторных обращений


@dataclass(frozen=True)
class HistoryItem:
    when: str
    student: str
    group: str
    ticket_no: int
    repeat: bool


@dataclass(frozen=True)
class ViewState:
    loaded: bool = False
    groups: tuple[str, ...] = ()
    group: str | None = None
    students: tuple[str, ...] = ()
    student: str | None = None
    can_generate: bool = False
    hint: str = ""
    status: str = "Загрузка данных…"
    status_kind: StatusKind = StatusKind.INFO
    stats: Stats = field(default_factory=Stats)
    history: tuple[HistoryItem, ...] = ()
