"""SelectionState: списки «группа → студент» и активность кнопки."""
import unittest

from ticket_generator.application.selection import SelectionState
from tests.fakes import InMemoryStudentsSource
from tests.helpers import GROUPS


class SelectionStateTest(unittest.TestCase):
    def setUp(self):
        self.state = SelectionState(InMemoryStudentsSource(GROUPS).load())

    def test_initially_button_disabled_and_groups_listed(self):
        self.assertEqual(self.state.group_names, ["IA-2301", "IA-2302", "IA-2303"])
        self.assertFalse(self.state.can_generate)

    def test_group_selection_fills_students_of_that_sheet(self):
        self.assertEqual(self.state.select_group("IA-2302"), ["Морозов Алексей", "Волкова Елена"])
        self.assertFalse(self.state.can_generate)  # только группа — кнопка неактивна

    def test_button_enabled_only_when_both_selected(self):
        self.state.select_group("IA-2301")
        self.state.select_student("Петрова Анна")
        self.assertTrue(self.state.can_generate)
        self.state.select_group("IA-2302")  # смена группы сбрасывает студента
        self.assertFalse(self.state.can_generate)

    def test_empty_group_gives_empty_list_and_disabled_button(self):
        self.assertEqual(self.state.select_group("IA-2303"), [])
        self.state.select_student("Иванов Иван")
        self.assertFalse(self.state.can_generate)

    def test_unknown_group_is_ignored(self):
        self.assertEqual(self.state.select_group("НЕТ"), [])
        self.assertIsNone(self.state.group)

    def test_student_without_group_or_unknown_does_not_enable(self):
        self.state.select_student("Иванов Иван")
        self.assertFalse(self.state.can_generate)
        self.state.select_group("IA-2301")
        self.state.select_student("Волкова Елена")  # из другой группы
        self.assertFalse(self.state.can_generate)

    def test_reset_student_disables_button(self):
        self.state.select_group("IA-2301")
        self.state.select_student("Иванов Иван")
        self.state.reset_student()
        self.assertFalse(self.state.can_generate)
        self.assertEqual(self.state.group, "IA-2301")

    def test_empty_state(self):
        state = SelectionState()
        self.assertEqual(state.group_names, [])
        self.assertFalse(state.can_generate)


if __name__ == "__main__":
    unittest.main()
