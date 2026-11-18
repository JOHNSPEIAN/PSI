"""Ошибки источников данных.

Все ошибки наследуются от DataSourceError: прикладной слой ловит базовый класс
и не знает, Excel это, Word или память (принцип подстановки Лисков).
Текст ошибки предназначен для пользователя и показывается в диалоге.
"""


class DataSourceError(Exception):
    """Источник данных отсутствует, повреждён или недоступен."""


class StudentsFileError(DataSourceError):
    """students.xlsx отсутствует или не читается."""


class TicketsFileError(DataSourceError):
    """tickets.docx отсутствует, не читается или не содержит ни одного корректного билета."""


class JournalError(DataSourceError):
    """Журнал не читается (повреждён, не xlsx и т.п.)."""


class JournalLockedError(JournalError):
    """Журнал недоступен для записи — обычно открыт в Excel. Операцию можно повторить."""
