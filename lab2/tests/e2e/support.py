"""Инструменты e2e-тестов: запуск приложения на настоящих файлах и «Excel-блокировка»."""
from __future__ import annotations

import random
import sys
from pathlib import Path
from unittest import mock

from openpyxl import load_workbook

from tests.fakes import FakeDialogs
from tests.gui_support import pump
from tests.helpers import TempDirTestCase, ticket_block, write_students, write_tickets

E2E_GROUPS = {
    "IA-2301": [("Иванов", "Иван"), ("Петрова", "Анна"), ("Сидоров", "Павел")],
    "IA-2302": [("Морозов", "Алексей"), ("Иванов", "Иван")],  # тёзка из другой группы
    "IA-2303": [],
}


class ExcelLock:
    """Держит файл так же, как открытый в Excel: читать можно, записывать и заменять — нет.

    В Windows файл по-настоящему открывается через CreateFileW с режимом совместного
    доступа «только чтение». В других ОС такой блокировки нет — там подменяется
    замена файла (os.replace), которая и не удалась бы при открытом Excel.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self._handle = None
        self._patch = None
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            create = ctypes.windll.kernel32.CreateFileW
            create.restype = wintypes.HANDLE
            create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                               wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
            generic_read, share_read, open_existing, normal = 0x80000000, 0x1, 3, 0x80
            handle = create(str(self.path), generic_read, share_read, None, open_existing, normal, None)
            if handle in (None, wintypes.HANDLE(-1).value):
                raise OSError(f"не удалось заблокировать {self.path}")
            self._handle = handle
        else:
            self._patch = mock.patch("ticket_generator.infrastructure.journal_xlsx.os.replace",
                                     side_effect=PermissionError("locked"))
            self._patch.start()

    def release(self) -> None:
        if self._handle is not None:
            import ctypes
            ctypes.windll.kernel32.CloseHandle(self._handle)
            self._handle = None
        if self._patch is not None:
            self._patch.stop()
            self._patch = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.release()


def journal_on_disk(path: Path) -> list[list]:
    """Содержимое results.xlsx, прочитанное напрямую openpyxl (без кода приложения)."""
    wb = load_workbook(path)
    try:
        return [list(r) for r in wb.worksheets[0].iter_rows(values_only=True)]
    finally:
        wb.close()


class AppE2ETestCase(TempDirTestCase):
    """Приложение целиком из корня композиции (build_app) на файлах во временной папке."""

    seed = 7

    def setUp(self):
        super().setUp()
        self.students_path = write_students(self.tmp / "students.xlsx", E2E_GROUPS)
        self.tickets_path = write_tickets(
            self.tmp / "tickets.docx", [line for n in range(1, 6) for line in ticket_block(n)])
        self.results_path = self.tmp / "results.xlsx"
        self.dialogs = FakeDialogs()
        self.callback_errors = []
        self.apps = []

    def tearDown(self):
        for app in self.apps:
            try:
                app.destroy()
            except Exception:
                pass
        super().tearDown()
        self.assertEqual(self.callback_errors, [], "ошибки в обработчиках Tk")

    # ---------- запуск ----------
    def launch(self, theme: str = "light"):
        from ticket_generator.application.ticket_service import RandomTicketPicker
        from ticket_generator.bootstrap import build_app
        app = build_app(self.tmp, theme=theme, dialogs=self.dialogs,
                        picker=RandomTicketPicker(random.Random(self.seed)))
        app.report_callback_exception = lambda *exc: self.callback_errors.append(exc)
        self.apps.append(app)
        pump(app)
        return app

    def restart(self, app, theme: str = "light"):
        app.destroy()
        self.apps.remove(app)
        return self.launch(theme)

    # ---------- действия пользователя ----------
    @staticmethod
    def choose(app, group, student=None):
        app.group_var.set(group)
        app.group_combo.event_generate("<<ComboboxSelected>>")
        pump(app, 2)
        if student is not None:
            app.student_var.set(student)
            app.student_combo.event_generate("<<ComboboxSelected>>")
            pump(app, 2)

    @staticmethod
    def get_ticket(app):
        app.generate_btn.invoke()
        pump(app)
        return app.ticket_window

    def take_ticket(self, app, group, student) -> str:
        """Полный цикл: выбрать, получить билет, запомнить номер, закрыть по Esc."""
        from tests.gui_support import press
        self.choose(app, group, student)
        window = self.get_ticket(app)
        self.assertIsNotNone(window, f"билет не выдан: {group} {student}")
        number = window.number_text
        press(window, "<Escape>")
        pump(app)
        return number
