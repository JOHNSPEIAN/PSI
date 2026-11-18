"""Русские формы множественного числа и формат времени."""
import unittest
from datetime import datetime

from ticket_generator.application.formatting import format_when, plural, plural_form


class PluralTest(unittest.TestCase):
    def test_russian_plural_forms(self):
        cases = {0: "билетов", 1: "билет", 2: "билета", 4: "билета", 5: "билетов", 11: "билетов",
                 12: "билетов", 14: "билетов", 21: "билет", 22: "билета", 25: "билетов",
                 101: "билет", 111: "билетов"}
        for n, expected in cases.items():
            with self.subTest(n=n):
                self.assertEqual(plural_form(n, "билет", "билета", "билетов"), expected)

    def test_plural_includes_number(self):
        self.assertEqual(plural(3, "группа", "группы", "групп"), "3 группы")


class FormatWhenTest(unittest.TestCase):
    def test_datetime(self):
        self.assertEqual(format_when(datetime(2026, 11, 8, 9, 5, 59)), "08.11 09:05")

    def test_missing_value(self):
        self.assertEqual(format_when(None), "—")
        self.assertEqual(format_when("вчера"), "—")


if __name__ == "__main__":
    unittest.main()
