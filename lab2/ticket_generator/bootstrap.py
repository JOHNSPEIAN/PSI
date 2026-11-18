"""Корень композиции: единственное место, где создаются конкретные классы.

Здесь выбираются реализации портов (Excel, Word, Tkinter) и связываются слои.
Остальной код зависит только от абстракций, поэтому тесты подставляют свои
реализации через параметры build_app (принцип инверсии зависимостей).
"""
from __future__ import annotations

import logging
from pathlib import Path

from .application.data_loader import DataLoader
from .application.ports import Clock, Dialogs, TicketPicker
from .application.presenter import MainPresenter
from .application.ticket_service import RandomTicketPicker, TicketService
from .infrastructure.journal_xlsx import XlsxJournal
from .infrastructure.students_xlsx import XlsxStudentsSource
from .infrastructure.tickets_docx import DocxTicketsSource
from .ui.dialogs import TkDialogs
from .ui.main_window import MainWindow

log = logging.getLogger(__name__)

STUDENTS_FILE = "students.xlsx"
TICKETS_FILE = "tickets.docx"
RESULTS_FILE = "results.xlsx"


def build_app(data_dir: str | Path, *, theme: str = "light", dialogs: Dialogs | None = None,
              picker: TicketPicker | None = None, clock: Clock | None = None) -> MainWindow:
    data_dir = Path(data_dir)
    journal = XlsxJournal(data_dir / RESULTS_FILE)
    loader = DataLoader(XlsxStudentsSource(data_dir / STUDENTS_FILE),
                        DocxTicketsSource(data_dir / TICKETS_FILE), journal)
    picker = picker or RandomTicketPicker()

    window = MainWindow(theme=theme)
    dialogs = dialogs or TkDialogs(window)

    def report_unexpected(exc_type, exc, tb) -> None:
        log.error("Непредвиденная ошибка", exc_info=(exc_type, exc, tb))
        dialogs.show_error("Ошибка", f"Непредвиденная ошибка: {exc}\nПодробности в журнале логов.")

    window.report_callback_exception = report_unexpected
    presenter = MainPresenter(
        loader, lambda tickets: TicketService(tickets, journal, picker, clock), journal, dialogs)
    window.connect(presenter)
    return window
