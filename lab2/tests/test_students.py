"""Чтение students.xlsx и поиск студента по группе."""
import unittest

from ticket_generator.students import (StudentsFileError, find_student,
                                       load_students)
from tests.helpers import GROUPS, TempDirTestCase, write_students


class LoadStudentsTest(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.path = write_students(self.tmp / "students.xlsx", GROUPS)

    def test_groups_are_sheet_names_in_order(self):
        self.assertEqual(list(load_students(self.path)), ["IA-2301", "IA-2302", "IA-2303"])

    def test_students_match_sheet_rows(self):
        groups = load_students(self.path)
        for group, rows in GROUPS.items():
            self.assertEqual([(s.surname, s.name) for s in groups[group]], rows)
            self.assertTrue(all(s.group == group for s in groups[group]))

    def test_header_row_is_not_a_student(self):
        names = [s.surname for s in load_students(self.path)["IA-2301"]]
        self.assertNotIn("Фамилия", names)

    def test_display_name_is_surname_then_name(self):
        self.assertEqual(load_students(self.path)["IA-2301"][0].display_name, "Иванов Иван")

    def test_empty_group_has_empty_list(self):
        self.assertEqual(load_students(self.path)["IA-2303"], [])

    def test_blank_incomplete_and_duplicate_rows_are_skipped(self):
        path = write_students(self.tmp / "dirty.xlsx", {"G": [
            ("  Иванов ", " Иван "), (None, None), ("Петров", None), ("иванов", "иван"), ("Сидоров", "Олег")]})
        with self.assertLogs("ticket_generator.students", level="WARNING"):
            students = load_students(path)["G"]
        self.assertEqual([s.display_name for s in students], ["Иванов Иван", "Сидоров Олег"])

    def test_missing_file_raises_clear_error(self):
        with self.assertRaises(StudentsFileError) as ctx:
            load_students(self.tmp / "missing.xlsx")
        self.assertIn("не найден", str(ctx.exception))

    def test_corrupted_file_raises_clear_error(self):
        bad = self.tmp / "bad.xlsx"
        bad.write_text("garbage")
        with self.assertRaises(StudentsFileError):
            load_students(bad)


class FindStudentByGroupTest(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.groups = load_students(write_students(self.tmp / "students.xlsx", GROUPS))

    def test_finds_student_in_his_group(self):
        s = find_student(self.groups, "IA-2302", "Волкова Елена")
        self.assertEqual((s.group, s.surname, s.name), ("IA-2302", "Волкова", "Елена"))

    def test_student_from_other_group_is_not_found(self):
        self.assertIsNone(find_student(self.groups, "IA-2301", "Волкова Елена"))

    def test_unknown_group_or_student(self):
        self.assertIsNone(find_student(self.groups, "НЕТ", "Иванов Иван"))
        self.assertIsNone(find_student(self.groups, "IA-2301", "Неизвестный Студент"))


if __name__ == "__main__":
    unittest.main()
