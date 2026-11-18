"""Форматирование текстов для интерфейса: русские формы множественного числа, даты."""
from __future__ import annotations

from datetime import datetime


def plural_form(n: int, one: str, few: str, many: str) -> str:
    """Форма слова для числа n: 1 билет, 2 билета, 5 билетов, 11 билетов, 21 билет."""
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def plural(n: int, one: str, few: str, many: str) -> str:
    return f"{n} {plural_form(n, one, few, many)}"


def format_when(value: object) -> str:
    """Время выдачи для таблицы истории: «18.11 14:03»."""
    return value.strftime("%d.%m %H:%M") if isinstance(value, datetime) else "—"
