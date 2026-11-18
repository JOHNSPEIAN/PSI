"""MainPresenter — логика главного экрана без Tkinter."""
import unittest
from datetime import datetime

from ticket_generator.application.data_loader import DataLoader
from ticket_generator.application.presenter import HISTORY_LIMIT, MainPresenter
from ticket_generator.application.ticket_service import TicketService
from ticket_generator.application.view_state import StatusKind
from ticket_generator.domain import JournalError, JournalRow
from tests.fakes import (FakeClock, FakeDialogs, FixedPicker, InMemoryJournal,
                         InMemoryStudentsSource, InMemoryTicketsSource, make_tickets)
from tests.helpers import GROUPS


class FakeView:
    def __init__(self):
        self.states = []
        self.tickets = []

    def render(self, state):
        self.states.append(state)

    def show_ticket(self, assignment):
        self.tickets.append(assignment)

    @property
    def last(self):
        return self.states[-1]


class PresenterTestCase(unittest.TestCase):
    def setUp(self):
        self.students = InMemoryStudentsSource(GROUPS)
        self.tickets = InMemoryTicketsSource(make_tickets(5))
        self.journal = InMemoryJournal()
        self.dialogs = FakeDialogs()
        self.picker = FixedPicker(3, 5, 1)
        self.view = FakeView()
        self.presenter = self.make_presenter()

    def make_presenter(self):
        return MainPresenter(
            DataLoader(self.students, self.tickets, self.journal),
            lambda tickets: TicketService(tickets, self.journal, self.picker, FakeClock()),
            self.journal, self.dialogs)

    def start(self):
        self.presenter.attach(self.view)
        self.presenter.reload()
        return self.view.last

    def choose(self, group, student=None):
        self.presenter.select_group(group)
        if student is not None:
            self.presenter.select_student(student)
        return self.view.last


class LoadingTest(PresenterTestCase):
    def test_attach_renders_initial_loading_state(self):
        self.presenter.attach(self.view)
        state = self.view.last
        self.assertFalse(state.loaded)
        self.assertFalse(state.can_generate)
        self.assertIn("Загрузка", state.status)

    def test_reload_fills_groups_and_stats(self):
        state = self.start()
        self.assertTrue(state.loaded)
        self.assertEqual(state.groups, ("IA-2301", "IA-2302", "IA-2303"))
        self.assertEqual((state.stats.groups, state.stats.students, state.stats.tickets), (3, 5, 5))
        self.assertEqual(state.status_kind, StatusKind.SUCCESS)
        self.assertEqual(state.status, "Загружено: 3 группы, 5 студентов, 5 билетов.")
        self.assertTrue(self.journal.exists)

    def test_load_errors_show_one_dialog_with_all_problems(self):
        self.students.error = "Файл со списком студентов не найден: students.xlsx"
        self.tickets.error = "Файл с билетами не найден: tickets.docx"
        with self.assertLogs("ticket_generator.application.data_loader", level="ERROR"):
            state = self.start()
        self.assertFalse(state.loaded)
        self.assertEqual(state.groups, ())
        self.assertEqual(state.status_kind, StatusKind.ERROR)
        self.assertEqual(len(self.dialogs.errors), 1)
        title, message = self.dialogs.errors[0]
        self.assertIn("students.xlsx", message)
        self.assertIn("tickets.docx", message)

    def test_reload_after_fixing_files_recovers(self):
        self.students.error = "нет файла"
        with self.assertLogs("ticket_generator.application.data_loader", level="ERROR"):
            self.start()
        self.students.error = None
        self.presenter.reload()
        self.assertTrue(self.view.last.loaded)
        self.assertEqual(len(self.view.last.groups), 3)

    def test_reload_resets_selection(self):
        self.start()
        self.choose("IA-2301", "Иванов Иван")
        self.presenter.reload()
        self.assertIsNone(self.view.last.group)
        self.assertFalse(self.view.last.can_generate)

    def test_unreadable_history_does_not_block_loading(self):
        def broken_rows():
            raise JournalError("Не удалось прочитать results.xlsx")

        self.journal.rows = broken_rows
        with self.assertLogs("ticket_generator.application.presenter", level="WARNING"):
            state = self.start()
        self.assertTrue(state.loaded)
        self.assertEqual(state.history, ())


class SelectionTest(PresenterTestCase):
    def test_group_fills_students_button_still_disabled(self):
        self.start()
        state = self.choose("IA-2302")
        self.assertEqual(state.students, ("Морозов Алексей", "Волкова Елена"))
        self.assertFalse(state.can_generate)
        self.assertIn("2 студента", state.status)

    def test_group_and_student_enable_button(self):
        self.start()
        state = self.choose("IA-2302", "Волкова Елена")
        self.assertEqual(state.student, "Волкова Елена")
        self.assertTrue(state.can_generate)
        self.assertIn("случайно", state.hint)

    def test_empty_group_warns_and_keeps_button_disabled(self):
        self.start()
        state = self.choose("IA-2303")
        self.assertEqual(state.students, ())
        self.assertFalse(state.can_generate)
        self.assertEqual(state.status_kind, StatusKind.WARNING)

    def test_changing_group_resets_student(self):
        self.start()
        self.choose("IA-2301", "Иванов Иван")
        state = self.choose("IA-2302")
        self.assertIsNone(state.student)
        self.assertFalse(state.can_generate)

    def test_cannot_generate_before_loading(self):
        self.presenter.attach(self.view)
        self.presenter.select_group("IA-2301")
        self.assertIsNone(self.presenter.generate())
        self.assertEqual(self.journal.rows(), [])


class GenerateTest(PresenterTestCase):
    def test_generate_writes_journal_and_shows_ticket(self):
        self.start()
        self.choose("IA-2301", "Иванов Иван")
        assignment = self.presenter.generate()
        self.assertEqual((assignment.ticket_no, assignment.repeat), (3, False))
        self.assertEqual(self.view.tickets, [assignment])
        self.assertEqual([r.ticket_no for r in self.journal.rows()], [3])
        state = self.view.last
        self.assertEqual(state.status_kind, StatusKind.SUCCESS)
        self.assertEqual((state.stats.issued, state.stats.repeats), (1, 0))
        self.assertEqual(state.history[0].student, "Иванов Иван")

    def test_repeat_gives_same_ticket_and_hint(self):
        self.start()
        self.choose("IA-2301", "Иванов Иван")
        first = self.presenter.generate()
        self.presenter.ticket_closed()
        state = self.choose("IA-2301", "Иванов Иван")
        self.assertIn(f"№ {first.ticket_no}", state.hint)
        again = self.presenter.generate()
        self.assertEqual(again.ticket_no, first.ticket_no)
        self.assertTrue(again.repeat)
        self.assertIn("повторное обращение", self.view.last.status)
        self.assertEqual((self.view.last.stats.issued, self.view.last.stats.repeats), (1, 1))

    def test_ticket_closed_keeps_group_and_resets_student(self):
        self.start()
        self.choose("IA-2301", "Иванов Иван")
        self.presenter.generate()
        self.presenter.ticket_closed()
        state = self.view.last
        self.assertEqual(state.group, "IA-2301")
        self.assertIsNone(state.student)
        self.assertFalse(state.can_generate)

    def test_history_newest_first_and_limited(self):
        t = datetime(2026, 11, 18, 8, 0)
        self.journal = InMemoryJournal(
            [JournalRow("G", f"S{i}", "N", 1, t, False) for i in range(HISTORY_LIMIT + 5)])
        self.presenter = self.make_presenter()
        state = self.start()
        self.assertEqual(len(state.history), HISTORY_LIMIT)
        self.assertEqual(state.history[0].student, f"S{HISTORY_LIMIT + 4} N")
        self.assertEqual(state.history[0].when, "18.11 08:00")
        self.assertEqual(state.stats.issued, HISTORY_LIMIT + 5)

    def test_locked_journal_retry_then_success(self):
        self.start()
        self.choose("IA-2301", "Петрова Анна")
        self.journal.locked = True
        answers = iter([True])

        def ask_retry(title, message):
            self.journal.locked = False  # «пользователь закрыл Excel и нажал Повторить»
            return next(answers)

        self.dialogs.ask_retry = ask_retry
        with self.assertLogs("ticket_generator.application.presenter", level="WARNING"):
            assignment = self.presenter.generate()
        self.assertIsNotNone(assignment)
        self.assertEqual(self.journal.append_calls, 2)
        self.assertEqual(self.view.tickets, [assignment])

    def test_locked_journal_cancel_shows_nothing_and_writes_nothing(self):
        self.start()
        self.choose("IA-2301", "Петрова Анна")
        self.journal.locked = True
        self.dialogs = self.presenter._dialogs = FakeDialogs(retry_answers=[False])
        with self.assertLogs("ticket_generator.application.presenter", level="WARNING"):
            self.assertIsNone(self.presenter.generate())
        self.assertEqual(self.view.tickets, [])
        self.assertEqual(self.journal.rows(), [])
        self.assertEqual(len(self.dialogs.retry_questions), 1)
        self.assertIn("открыт в Excel", self.dialogs.retry_questions[0][1])
        self.assertEqual(self.view.last.status_kind, StatusKind.ERROR)
        self.assertTrue(self.view.last.can_generate)  # можно попробовать ещё раз

    def test_unreadable_journal_on_assign_shows_error(self):
        self.start()
        self.choose("IA-2301", "Петрова Анна")
        self.journal.broken = True
        with self.assertLogs("ticket_generator.application.presenter", level="ERROR"):
            self.assertIsNone(self.presenter.generate())
        self.assertEqual(self.dialogs.errors[0][0], "Ошибка журнала")
        self.assertEqual(self.view.tickets, [])


if __name__ == "__main__":
    unittest.main()
