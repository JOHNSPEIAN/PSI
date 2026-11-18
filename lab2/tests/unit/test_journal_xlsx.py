"""Особенности журнала в Excel: заголовок, атомарная запись, блокировка файла."""
import unittest
from datetime import datetime
from unittest import mock

from openpyxl import load_workbook

from ticket_generator.domain import JournalError, JournalLockedError, JournalRow
from ticket_generator.infrastructure.journal_xlsx import HEADERS, XlsxJournal
from tests.helpers import TempDirTestCase

JOURNAL_MODULE = "ticket_generator.infrastructure.journal_xlsx"


def sheet_values(path):
    wb = load_workbook(path)
    try:
        return [list(r) for r in wb.worksheets[0].iter_rows(values_only=True)]
    finally:
        wb.close()


class XlsxJournalTest(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.journal = XlsxJournal(self.tmp / "results.xlsx")
        self.t = datetime(2026, 1, 1, 10, 0, 0)

    def test_created_with_header_if_missing(self):
        self.assertTrue(self.journal.ensure_exists())
        self.assertEqual(sheet_values(self.journal.path), [list(HEADERS)])
        self.assertFalse(self.journal.ensure_exists())  # второй раз не пересоздаётся

    def test_cells_layout_matches_assignment(self):
        self.journal.append(JournalRow("G", "Иванов", "Иван", 3, self.t, True))
        self.assertEqual(sheet_values(self.journal.path)[-1], ["G", "Иванов", "Иван", 3, self.t, "да"])

    def test_append_keeps_existing_rows_untouched(self):
        self.journal.append(JournalRow("G", "А", "Б", 1, self.t, False))
        before = sheet_values(self.journal.path)
        self.journal.append(JournalRow("G", "В", "Г", 2, self.t, False))
        after = sheet_values(self.journal.path)
        self.assertEqual(after[:len(before)], before)
        self.assertEqual(after[-1], ["G", "В", "Г", 2, self.t, "нет"])

    def test_rows_skip_blank_and_invalid_lines(self):
        self.journal.append(JournalRow("G", "А", "Б", 1, self.t, False))
        wb = load_workbook(self.journal.path)
        ws = wb.worksheets[0]
        ws.append([None] * 6)
        ws.append(["G", "В", "Г", "не число", self.t, "нет"])
        ws.append(["G", "Д", "Е", "4", self.t, " Да "])
        wb.save(self.journal.path)
        with self.assertLogs(JOURNAL_MODULE, level="WARNING"):
            rows = self.journal.rows()
        self.assertEqual([(r.surname, r.ticket_no, r.repeat) for r in rows],
                         [("А", 1, False), ("Д", 4, True)])

    def test_corrupted_journal_raises_journal_error(self):
        self.journal.path.write_text("not xlsx")
        with self.assertRaises(JournalError):
            self.journal.rows()

    def test_locked_file_on_write_raises_locked_error(self):
        self.journal.ensure_exists()
        before = sheet_values(self.journal.path)
        with mock.patch(f"{JOURNAL_MODULE}.open", side_effect=PermissionError, create=True):
            with self.assertRaises(JournalLockedError) as ctx:
                self.journal.append(JournalRow("G", "А", "Б", 1, datetime.now(), False))
        self.assertIn("открыт в Excel", str(ctx.exception))
        self.assertEqual(sheet_values(self.journal.path), before)

    def test_locked_file_on_replace_raises_locked_error_and_leaves_no_temp(self):
        self.journal.ensure_exists()
        with mock.patch(f"{JOURNAL_MODULE}.os.replace", side_effect=PermissionError):
            with self.assertRaises(JournalLockedError):
                self.journal.append(JournalRow("G", "А", "Б", 1, datetime.now(), False))
        self.assertEqual([p.name for p in self.tmp.iterdir()], ["results.xlsx"])


if __name__ == "__main__":
    unittest.main()
