"""Доменные сущности: студент, список групп, запись журнала, правило «первого билета»."""
import unittest
from datetime import datetime

from ticket_generator.domain import (Assignment, JournalRow, Roster, Student, first_ticket_of,
                                     student_key)

IVANOV = Student("IA-2301", "Иванов", "Иван")
T = datetime(2026, 11, 18, 10, 0, 0)


class StudentTest(unittest.TestCase):
    def test_display_name_is_surname_then_name(self):
        self.assertEqual(IVANOV.display_name, "Иванов Иван")

    def test_key_ignores_case_and_outer_spaces(self):
        self.assertEqual(Student(" ia-2301 ", "ИВАНОВ ", "иван").key, IVANOV.key)

    def test_same_name_in_other_group_has_other_key(self):
        self.assertNotEqual(Student("IA-2302", "Иванов", "Иван").key, IVANOV.key)

    def test_student_key_handles_none(self):
        self.assertEqual(student_key(None, "A", None), ("", "a", ""))


class RosterTest(unittest.TestCase):
    def setUp(self):
        self.roster = Roster({
            "IA-2301": [IVANOV, Student("IA-2301", "Петрова", "Анна")],
            "IA-2302": [Student("IA-2302", "Волкова", "Елена")],
            "IA-2303": [],
        })

    def test_group_names_keep_sheet_order(self):
        self.assertEqual(self.roster.group_names, ("IA-2301", "IA-2302", "IA-2303"))

    def test_counts(self):
        self.assertEqual(len(self.roster), 3)
        self.assertEqual(self.roster.total_students, 3)

    def test_students_of_unknown_or_none_group_is_empty(self):
        self.assertEqual(self.roster.students_of("НЕТ"), ())
        self.assertEqual(self.roster.students_of(None), ())

    def test_find_student_in_his_group(self):
        self.assertEqual(self.roster.find("IA-2301", "Иванов Иван"), IVANOV)

    def test_student_from_other_group_is_not_found(self):
        self.assertIsNone(self.roster.find("IA-2301", "Волкова Елена"))

    def test_unknown_group_or_student(self):
        self.assertIsNone(self.roster.find("НЕТ", "Иванов Иван"))
        self.assertIsNone(self.roster.find("IA-2301", "Неизвестный Студент"))
        self.assertIsNone(self.roster.find(None, None))

    def test_equality(self):
        self.assertEqual(Roster({"G": [IVANOV]}), Roster({"G": (IVANOV,)}))
        self.assertNotEqual(Roster({"G": [IVANOV]}), Roster({"G": []}))


class JournalRuleTest(unittest.TestCase):
    def test_first_ticket_is_taken_from_earliest_row(self):
        rows = [JournalRow("IA-2301", "Петрова", "Анна", 2, T, False),
                JournalRow("IA-2301", "Иванов", "Иван", 4, T, False),
                JournalRow("IA-2301", "Иванов", "Иван", 9, T, True)]  # подделка «руками»
        self.assertEqual(first_ticket_of(rows, IVANOV), 4)

    def test_first_ticket_matching_is_case_insensitive(self):
        rows = [JournalRow(" ia-2301", "ИВАНОВ", "иван ", 5, T, False)]
        self.assertEqual(first_ticket_of(rows, IVANOV), 5)

    def test_no_rows_for_student(self):
        rows = [JournalRow("IA-2302", "Иванов", "Иван", 5, T, False)]
        self.assertIsNone(first_ticket_of(rows, IVANOV))
        self.assertIsNone(first_ticket_of([], IVANOV))

    def test_assignment_to_journal_row(self):
        a = Assignment(IVANOV, 7, ("a", "b", "c"), True, T)
        self.assertEqual(a.to_journal_row(), JournalRow("IA-2301", "Иванов", "Иван", 7, T, True))


if __name__ == "__main__":
    unittest.main()
