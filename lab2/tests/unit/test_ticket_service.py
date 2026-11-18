"""TicketService: правило выдачи, идемпотентность повторов, запись в журнал."""
import random
import unittest
from datetime import datetime
from unittest import mock

from openpyxl import load_workbook

from ticket_generator.application.ticket_service import RandomTicketPicker, TicketService
from ticket_generator.domain import JournalLockedError, JournalRow, Student
from ticket_generator.infrastructure.journal_xlsx import XlsxJournal
from ticket_generator.infrastructure.tickets_docx import parse_ticket_lines
from tests.fakes import FakeClock, FixedPicker, InMemoryJournal, make_tickets
from tests.helpers import TempDirTestCase, ticket_block

IVANOV = Student("IA-2301", "Иванов", "Иван")
PETROVA = Student("IA-2301", "Петрова", "Анна")


def sheet_values(path):
    wb = load_workbook(path)
    try:
        return [list(r) for r in wb.worksheets[0].iter_rows(values_only=True)]
    finally:
        wb.close()


class TicketServiceRulesTest(unittest.TestCase):
    """Правила выдачи на in-memory журнале — без файлов, быстро и детерминированно."""

    def setUp(self):
        self.tickets = make_tickets(5)
        self.journal = InMemoryJournal()
        self.picker = FixedPicker(4)
        self.service = TicketService(self.tickets, self.journal, self.picker, FakeClock())

    def test_new_student_gets_ticket_chosen_by_picker(self):
        a = self.service.generate(IVANOV)
        self.assertEqual((a.ticket_no, a.repeat), (4, False))
        self.assertEqual(a.questions, self.tickets[4].questions)
        self.assertEqual(self.picker.calls, [[1, 2, 3, 4, 5]])

    def test_repeat_does_not_call_picker(self):
        self.service.generate(IVANOV)
        self.service.generate(IVANOV)
        self.assertEqual(len(self.picker.calls), 1)

    def test_repeat_selection_returns_same_ticket(self):
        """Идемпотентность: повторный выбор того же студента → тот же билет."""
        first = self.service.generate(IVANOV)
        for _ in range(5):
            again = self.service.generate(IVANOV)
            self.assertEqual((again.ticket_no, again.questions), (first.ticket_no, first.questions))
            self.assertTrue(again.repeat)

    def test_same_name_in_other_group_is_different_student(self):
        self.service.generate(IVANOV)
        self.assertFalse(self.service.assign(Student("IA-2302", "Иванов", "Иван")).repeat)

    def test_assign_does_not_write(self):
        self.service.assign(IVANOV)
        self.assertEqual(self.journal.rows(), [])

    def test_retry_after_lock_saves_same_ticket(self):
        assignment = self.service.assign(IVANOV)
        self.journal.locked = True
        with self.assertRaises(JournalLockedError):
            self.service.save(assignment)
        self.assertEqual(self.journal.rows(), [])
        self.journal.locked = False
        self.service.save(assignment)  # «Повторить» после закрытия Excel
        self.assertEqual(self.journal.rows(), [assignment.to_journal_row()])

    def test_repeat_of_ticket_removed_from_file(self):
        self.journal.append(JournalRow("IA-2301", "Иванов", "Иван", 99, datetime.now(), False))
        a = self.service.assign(IVANOV)
        self.assertEqual((a.ticket_no, a.questions, a.repeat), (99, (), True))

    def test_timestamps_come_from_clock(self):
        a, b = self.service.generate(IVANOV), self.service.generate(PETROVA)
        self.assertLess(a.timestamp, b.timestamp)

    def test_no_tickets_is_rejected(self):
        with self.assertRaises(ValueError):
            TicketService({}, self.journal)


class RandomPickerTest(unittest.TestCase):
    def test_picks_only_given_numbers_and_varies(self):
        picker = RandomTicketPicker(random.Random(42))
        seen = {picker.pick([1, 3, 5]) for _ in range(50)}
        self.assertEqual(seen, {1, 3, 5})

    def test_random_choice_only_among_valid_tickets(self):
        with self.assertLogs("ticket_generator.infrastructure.tickets_docx", level="ERROR"):
            tickets = parse_ticket_lines(ticket_block(1) + ticket_block(2, count=1) + ticket_block(3))
        service = TicketService(tickets, InMemoryJournal(), RandomTicketPicker(random.Random(0)))
        numbers = {service.assign(Student("G", f"S{i}", "N")).ticket_no for i in range(50)}
        self.assertEqual(numbers, {1, 3})


class TicketServiceWithExcelTest(TempDirTestCase):
    """Те же правила, но с настоящим results.xlsx — проверяем, что пишется в файл."""

    def setUp(self):
        super().setUp()
        self.tickets = make_tickets(5)
        self.journal = XlsxJournal(self.tmp / "results.xlsx")
        self.journal.ensure_exists()
        self.service = TicketService(self.tickets, self.journal, RandomTicketPicker(random.Random(42)),
                                     FakeClock())

    def test_new_students_get_random_tickets_from_file(self):
        seen = set()
        for i in range(30):
            a = self.service.generate(Student("G", f"Студент{i}", "Тест"))
            self.assertIn(a.ticket_no, self.tickets)
            self.assertEqual(len(a.questions), 3)
            self.assertFalse(a.repeat)
            seen.add(a.ticket_no)
        self.assertGreater(len(seen), 1, "билеты должны выбираться случайно")

    def test_row_is_written_immediately_after_generation(self):
        self.service.generate(PETROVA)
        self.assertEqual(sheet_values(self.journal.path)[-1][1:3], ["Петрова", "Анна"])

    def test_repeat_appends_new_row_with_yes(self):
        first = self.service.generate(IVANOV)
        rows_before = sheet_values(self.journal.path)
        self.service.generate(IVANOV)
        rows_after = sheet_values(self.journal.path)
        self.assertEqual(len(rows_after), len(rows_before) + 1)
        self.assertEqual(rows_after[:len(rows_before)], rows_before)  # старые строки не тронуты
        self.assertEqual(rows_after[-1][:4], ["IA-2301", "Иванов", "Иван", first.ticket_no])
        self.assertEqual(rows_after[-1][5], "да")
        self.assertEqual(rows_before[-1][5], "нет")

    def test_repeat_survives_restart(self):
        first = self.service.generate(IVANOV)
        restarted = TicketService(self.tickets, XlsxJournal(self.journal.path),
                                  RandomTicketPicker(random.Random(999)))
        self.assertEqual(restarted.generate(IVANOV).ticket_no, first.ticket_no)

    def test_full_history_in_chronological_order(self):
        for s in [IVANOV, PETROVA, IVANOV, PETROVA, IVANOV]:
            self.service.generate(s)
        rows = self.journal.rows()
        self.assertEqual([(r.surname, r.repeat) for r in rows],
                         [("Иванов", False), ("Петрова", False), ("Иванов", True),
                          ("Петрова", True), ("Иванов", True)])
        stamps = [r.timestamp for r in rows]
        self.assertEqual(stamps, sorted(stamps))
        self.assertTrue(all(isinstance(t, datetime) for t in stamps))

    def test_locked_excel_then_retry_saves_same_ticket(self):
        assignment = self.service.assign(IVANOV)
        with mock.patch("ticket_generator.infrastructure.journal_xlsx.os.replace",
                        side_effect=PermissionError):
            with self.assertRaises(JournalLockedError):
                self.service.save(assignment)
        self.assertEqual(self.journal.rows(), [])
        self.service.save(assignment)
        self.assertEqual([r.ticket_no for r in self.journal.rows()], [assignment.ticket_no])


if __name__ == "__main__":
    unittest.main()
