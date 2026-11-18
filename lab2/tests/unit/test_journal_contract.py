"""Контракт журнала — один набор тестов для всех реализаций (принцип подстановки Лисков).

Любая реализация портов JournalReader/JournalWriter/JournalInitializer обязана
проходить эти тесты; тогда сервис и презентер работают с ней без изменений.
"""
import unittest
from datetime import datetime

from ticket_generator.domain import JournalRow
from ticket_generator.infrastructure.journal_xlsx import XlsxJournal
from tests.fakes import InMemoryJournal
from tests.helpers import TempDirTestCase

T1 = datetime(2026, 11, 18, 9, 0, 1)
T2 = datetime(2026, 11, 18, 9, 0, 2)
ROW_A = JournalRow("IA-2301", "Иванов", "Иван", 3, T1, False)
ROW_B = JournalRow("IA-2301", "Иванов", "Иван", 3, T2, True)


class JournalContract:
    """Миксин: наследник задаёт make_journal()."""

    def make_journal(self):
        raise NotImplementedError

    def test_new_journal_is_empty(self):
        self.assertEqual(self.make_journal().rows(), [])

    def test_ensure_exists_creates_only_once(self):
        journal = self.make_journal()
        self.assertTrue(journal.ensure_exists())
        self.assertFalse(journal.ensure_exists())
        self.assertEqual(journal.rows(), [])

    def test_append_then_read_back_same_rows_in_order(self):
        journal = self.make_journal()
        journal.ensure_exists()
        journal.append(ROW_A)
        journal.append(ROW_B)
        self.assertEqual(journal.rows(), [ROW_A, ROW_B])

    def test_append_creates_missing_journal(self):
        journal = self.make_journal()
        journal.append(ROW_A)
        self.assertEqual(journal.rows(), [ROW_A])
        self.assertFalse(journal.ensure_exists())


class XlsxJournalContractTest(JournalContract, TempDirTestCase):
    def make_journal(self):
        return XlsxJournal(self.tmp / "results.xlsx")


class InMemoryJournalContractTest(JournalContract, unittest.TestCase):
    def make_journal(self):
        return InMemoryJournal()


if __name__ == "__main__":
    unittest.main()
