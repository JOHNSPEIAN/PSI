"""Чтение students.xlsx."""
import unittest

from ticket_generator.domain import StudentsFileError
from ticket_generator.infrastructure.students_xlsx import XlsxStudentsSource, load_students
from tests.helpers import GROUPS, TempDirTestCase, write_students


class LoadStudentsTest(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.path = write_students(self.tmp / "students.xlsx", GROUPS)

    def test_groups_are_sheet_names_in_order(self):
        self.assertEqual(load_students(self.path).group_names, ("IA-2301", "IA-2302", "IA-2303"))

    def test_students_match_sheet_rows(self):
        roster = load_students(self.path)
        for group, rows in GROUPS.items():
            students = roster.students_of(group)
            self.assertEqual([(s.surname, s.name) for s in students], rows)
            self.assertTrue(all(s.group == group for s in students))

    def test_header_row_is_not_a_student(self):
        names = [s.surname for s in load_students(self.path).students_of("IA-2301")]
        self.assertNotIn("Фамилия", names)

    def test_display_name_is_surname_then_name(self):
        self.assertEqual(load_students(self.path).students_of("IA-2301")[0].display_name, "Иванов Иван")

    def test_empty_group_has_empty_list(self):
        self.assertEqual(load_students(self.path).students_of("IA-2303"), ())

    def test_blank_incomplete_and_duplicate_rows_are_skipped(self):
        path = write_students(self.tmp / "dirty.xlsx", {"G": [
            ("  Иванов ", " Иван "), (None, None), ("Петров", None), ("иванов", "иван"), ("Сидоров", "Олег")]})
        with self.assertLogs("ticket_generator.infrastructure.students_xlsx", level="WARNING"):
            students = load_students(path).students_of("G")
        self.assertEqual([s.display_name for s in students], ["Иванов Иван", "Сидоров Олег"])

    def test_trailing_spaces_in_cells_are_trimmed(self):
        """Лишний пробел после фамилии в Excel не попадает в список и журнал."""
        path = write_students(self.tmp / "spaces.xlsx", {"IA-2303 ": [("Пятков ", "Мартин")]})
        roster = load_students(path)
        self.assertEqual(roster.group_names, ("IA-2303",))
        self.assertEqual(roster.students_of("IA-2303")[0].display_name, "Пятков Мартин")

    def test_numbers_in_cells_are_read_as_text(self):
        path = write_students(self.tmp / "numbers.xlsx", {"G": [(123, 45)]})
        self.assertEqual(load_students(path).students_of("G")[0].display_name, "123 45")

    def test_missing_file_raises_clear_error(self):
        with self.assertRaises(StudentsFileError) as ctx:
            load_students(self.tmp / "missing.xlsx")
        self.assertIn("не найден", str(ctx.exception))

    def test_corrupted_file_raises_clear_error(self):
        bad = self.tmp / "bad.xlsx"
        bad.write_text("garbage")
        with self.assertRaises(StudentsFileError):
            load_students(bad)

    def test_source_adapter_reads_same_roster(self):
        self.assertEqual(XlsxStudentsSource(self.path).load(), load_students(self.path))


if __name__ == "__main__":
    unittest.main()
