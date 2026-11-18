"""Общая подготовка UI-тестов: окно на in-memory данных, без файлов."""
from __future__ import annotations

import unittest

from tests.fakes import (FakeClock, FakeDialogs, FixedPicker, InMemoryJournal,
                         InMemoryStudentsSource, InMemoryTicketsSource, make_tickets)
from tests.gui_support import pump
from tests.helpers import GROUPS


class MainWindowTestCase(unittest.TestCase):
    """Настоящее окно MainWindow + настоящий презентер, но данные в памяти."""

    theme = "light"

    def setUp(self):
        from ticket_generator.application.data_loader import DataLoader
        from ticket_generator.application.presenter import MainPresenter
        from ticket_generator.application.ticket_service import TicketService
        from ticket_generator.ui.main_window import MainWindow

        self.students = InMemoryStudentsSource(GROUPS)
        self.tickets = InMemoryTicketsSource(make_tickets(5))
        self.journal = InMemoryJournal()
        self.dialogs = FakeDialogs()
        self.picker = FixedPicker(3, 5, 1)
        self.callback_errors = []
        self.window = MainWindow(theme=self.theme)
        self.window.report_callback_exception = lambda *exc: self.callback_errors.append(exc)
        self.presenter = MainPresenter(
            DataLoader(self.students, self.tickets, self.journal),
            lambda tickets: TicketService(tickets, self.journal, self.picker, FakeClock()),
            self.journal, self.dialogs)

    def tearDown(self):
        window, self.window = self.window, None
        if window is not None:
            window.destroy()
        self.assertEqual(self.callback_errors, [], "ошибки в обработчиках Tk")

    # ---------- действия пользователя ----------
    def start(self):
        self.window.connect(self.presenter)
        pump(self.window)
        return self.window

    def choose(self, group, student=None):
        """Выбор из выпадающих списков так, как это делает пользователь мышью."""
        w = self.window
        w.group_var.set(group)
        w.group_combo.event_generate("<<ComboboxSelected>>")
        pump(w, 2)
        if student is not None:
            w.student_var.set(student)
            w.student_combo.event_generate("<<ComboboxSelected>>")
            pump(w, 2)

    def click_generate(self):
        self.window.generate_btn.invoke()
        pump(self.window)
        return self.window.ticket_window

    def button_enabled(self):
        return not self.window.generate_btn.instate(["disabled"])
