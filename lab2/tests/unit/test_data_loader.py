"""DataLoader: собирает данные из всех источников и копит ошибки."""
import unittest

from ticket_generator.application.data_loader import DataLoader
from tests.fakes import InMemoryJournal, InMemoryStudentsSource, InMemoryTicketsSource, make_tickets

GROUPS = {"IA-2301": [("Иванов", "Иван")], "IA-2303": []}


class DataLoaderTest(unittest.TestCase):
    def test_success_returns_roster_tickets_and_creates_journal(self):
        journal = InMemoryJournal()
        result = DataLoader(InMemoryStudentsSource(GROUPS), InMemoryTicketsSource(make_tickets(3)),
                            journal).load()
        self.assertTrue(result.ok)
        self.assertEqual(result.roster.group_names, ("IA-2301", "IA-2303"))
        self.assertEqual(list(result.tickets), [1, 2, 3])
        self.assertTrue(journal.exists)

    def test_all_errors_are_collected_not_only_the_first(self):
        journal = InMemoryJournal()
        journal.broken = True
        with self.assertLogs("ticket_generator.application.data_loader", level="ERROR"):
            result = DataLoader(InMemoryStudentsSource(error="нет students.xlsx"),
                                InMemoryTicketsSource(error="нет tickets.docx"), journal).load()
        self.assertFalse(result.ok)
        self.assertEqual(len(result.errors), 3)
        self.assertIn("нет students.xlsx", result.errors[0])
        self.assertIn("нет tickets.docx", result.errors[1])
        self.assertIn("results.xlsx", result.errors[2])

    def test_source_without_tickets_is_an_error(self):
        with self.assertLogs("ticket_generator.application.data_loader", level="ERROR"):
            result = DataLoader(InMemoryStudentsSource(GROUPS), InMemoryTicketsSource({}),
                                InMemoryJournal()).load()
        self.assertFalse(result.ok)
        self.assertIn("Нет ни одного корректного билета", result.errors[0])

    def test_partial_failure_returns_no_data(self):
        with self.assertLogs("ticket_generator.application.data_loader", level="ERROR"):
            result = DataLoader(InMemoryStudentsSource(GROUPS),
                                InMemoryTicketsSource(error="нет tickets.docx"),
                                InMemoryJournal()).load()
        self.assertFalse(result.ok)
        self.assertEqual(len(result.roster), 0)
        self.assertEqual(dict(result.tickets), {})


if __name__ == "__main__":
    unittest.main()
