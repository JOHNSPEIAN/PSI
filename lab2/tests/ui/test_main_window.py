"""UI-тесты главного окна: настоящие виджеты Tk, действия через клики и клавиши."""
import unittest

from tests.gui_support import press, pump, requires_display
from tests.ui.support import MainWindowTestCase


@requires_display
class StartupTest(MainWindowTestCase):
    def test_groups_listed_and_inputs_in_initial_state(self):
        w = self.start()
        self.assertEqual(list(w.group_combo["values"]), ["IA-2301", "IA-2302", "IA-2303"])
        self.assertEqual(str(w.group_combo["state"]), "readonly")
        self.assertEqual(str(w.student_combo["state"]), "disabled")
        self.assertFalse(self.button_enabled())

    def test_stats_tiles_and_success_status(self):
        w = self.start()
        values = {k: t.value.cget("text") for k, t in w.stat_tiles.items()}
        self.assertEqual(values, {"groups": "3", "students": "5", "tickets": "5", "issued": "0"})
        self.assertIn("Загружено: 3 группы", w.status_bar.label.cget("text"))
        self.assertEqual(w.status_bar.dot_color, w.theme.palette.success)

    def test_empty_history_placeholder_is_shown(self):
        w = self.start()
        self.assertEqual(w.history_tree.get_children(), ())
        self.assertTrue(w.history_empty.winfo_ismapped())

    def test_load_error_shows_dialog_and_disables_inputs(self):
        self.students.error = "Файл со списком студентов не найден: students.xlsx"
        with self.assertLogs("ticket_generator.application.data_loader", level="ERROR"):
            w = self.start()
        self.assertEqual(len(self.dialogs.errors), 1)
        self.assertIn("students.xlsx", self.dialogs.errors[0][1])
        self.assertEqual(str(w.group_combo["state"]), "disabled")
        self.assertFalse(self.button_enabled())
        self.assertEqual(w.status_bar.dot_color, w.theme.palette.danger)
        self.assertEqual(w.stat_tiles["groups"].value.cget("text"), "—")


@requires_display
class SelectionTest(MainWindowTestCase):
    def test_group_then_student_enables_button(self):
        w = self.start()
        self.choose("IA-2302")
        self.assertEqual(list(w.student_combo["values"]), ["Морозов Алексей", "Волкова Елена"])
        self.assertEqual(str(w.student_combo["state"]), "readonly")
        self.assertFalse(self.button_enabled())
        self.choose("IA-2302", "Волкова Елена")
        self.assertTrue(self.button_enabled())
        self.assertIn("случайно", w.hint_label.cget("text"))

    def test_empty_group_keeps_student_list_and_button_disabled(self):
        w = self.start()
        self.choose("IA-2303")
        self.assertEqual(list(w.student_combo["values"]), [])
        self.assertEqual(str(w.student_combo["state"]), "disabled")
        self.assertFalse(self.button_enabled())
        self.assertEqual(w.status_bar.dot_color, w.theme.palette.warning)

    def test_changing_group_clears_student(self):
        w = self.start()
        self.choose("IA-2301", "Иванов Иван")
        self.choose("IA-2302")
        self.assertEqual(w.student_var.get(), "")
        self.assertFalse(self.button_enabled())


@requires_display
class GenerateTest(MainWindowTestCase):
    def test_click_shows_ticket_and_updates_history(self):
        w = self.start()
        self.choose("IA-2301", "Иванов Иван")
        ticket = self.click_generate()
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.number_text, "№ 3")
        self.assertEqual(len(ticket.question_texts), 3)
        rows = w.history_tree.get_children()
        self.assertEqual(len(rows), 1)
        self.assertEqual(w.history_tree.item(rows[0], "values")[1:], ("Иванов Иван", "IA-2301", "№ 3", "новый"))
        self.assertFalse(w.history_empty.winfo_ismapped())
        self.assertEqual(w.stat_tiles["issued"].value.cget("text"), "1")

    def test_escape_closes_only_ticket_and_resets_student(self):
        w = self.start()
        self.choose("IA-2301", "Иванов Иван")
        ticket = self.click_generate()
        press(ticket, "<Escape>")
        pump(w)
        self.assertIsNone(w.ticket_window)
        self.assertFalse(ticket.winfo_exists())
        self.assertTrue(w.winfo_exists())
        self.assertEqual(w.group_var.get(), "IA-2301")  # группа остаётся
        self.assertEqual(w.student_var.get(), "")       # студент сброшен
        self.assertFalse(self.button_enabled())

    def test_repeat_gives_same_number_and_marks_history(self):
        w = self.start()
        self.choose("IA-2301", "Иванов Иван")
        first = self.click_generate().number_text
        w.ticket_window.close()
        self.choose("IA-2301", "Иванов Иван")
        self.assertIn(first, w.hint_label.cget("text"))
        again = self.click_generate()
        self.assertEqual(again.number_text, first)
        self.assertEqual(again.badge_text, "ПОВТОР")
        newest = w.history_tree.get_children()[0]
        self.assertEqual(w.history_tree.item(newest, "values")[4], "повтор")
        self.assertIn("repeat", w.history_tree.item(newest, "tags"))
        again.close()

    def test_enter_generates_when_ready(self):
        w = self.start()
        self.choose("IA-2301", "Петрова Анна")
        press(w.student_combo, "<Return>")
        pump(w)
        self.assertIsNotNone(w.ticket_window)
        w.ticket_window.close()

    def test_enter_does_nothing_until_student_selected(self):
        w = self.start()
        self.choose("IA-2301")
        press(w.group_combo, "<Return>")
        self.assertIsNone(w.ticket_window)
        self.assertEqual(self.journal.rows(), [])

    def test_locked_journal_retry_then_ticket(self):
        w = self.start()
        self.choose("IA-2301", "Петрова Анна")
        self.journal.locked = True

        def user_closes_excel_and_retries(title, message):
            self.journal.locked = False
            return True

        self.dialogs.ask_retry = user_closes_excel_and_retries
        with self.assertLogs("ticket_generator.application.presenter", level="WARNING"):
            ticket = self.click_generate()
        self.assertIsNotNone(ticket)
        self.assertEqual(len(self.journal.rows()), 1)
        ticket.close()

    def test_locked_journal_cancel_shows_no_ticket(self):
        w = self.start()
        self.choose("IA-2301", "Петрова Анна")
        self.journal.locked = True
        with self.assertLogs("ticket_generator.application.presenter", level="WARNING"):
            self.assertIsNone(self.click_generate())
        self.assertEqual(len(self.dialogs.retry_questions), 1)
        self.assertEqual(w.status_bar.dot_color, w.theme.palette.danger)
        self.assertTrue(w.winfo_exists())


@requires_display
class ShortcutsAndThemeTest(MainWindowTestCase):
    def test_f5_rereads_sources(self):
        w = self.start()
        self.students.groups = {**self.students.groups, "IA-2399": [("Новиков", "Олег")]}
        press(w.group_combo, "<F5>")
        pump(w)
        self.assertIn("IA-2399", list(w.group_combo["values"]))

    def test_reload_is_ignored_while_ticket_is_open(self):
        w = self.start()
        self.choose("IA-2301", "Иванов Иван")
        self.click_generate()
        loads = self.students.loads
        w.on_reload()
        self.assertEqual(self.students.loads, loads)
        w.ticket_window.close()

    def test_ctrl_t_toggles_theme_and_keeps_selection(self):
        w = self.start()
        self.choose("IA-2301", "Иванов Иван")
        press(w.group_combo, "<Control-t>")
        pump(w)
        self.assertTrue(w.theme.palette.is_dark)
        self.assertIn("Светлая", w.header.action_text)
        self.assertEqual((w.group_var.get(), w.student_var.get()), ("IA-2301", "Иванов Иван"))
        self.assertTrue(self.button_enabled())
        self.assertEqual(str(w.cget("background")), w.theme.palette.bg)

    def test_click_on_header_pill_toggles_theme(self):
        w = self.start()
        x, y = w.header.action_center()
        w.header.event_generate("<Enter>", x=x, y=y)
        w.header.event_generate("<Button-1>", x=x, y=y)
        pump(w)
        self.assertTrue(w.theme.palette.is_dark)
        x, y = w.header.action_center()
        w.header.event_generate("<Button-1>", x=x, y=y)
        pump(w)
        self.assertFalse(w.theme.palette.is_dark)


@requires_display
class DarkStartTest(MainWindowTestCase):
    theme = "dark"

    def test_window_starts_in_dark_theme(self):
        w = self.start()
        self.assertTrue(w.theme.palette.is_dark)
        self.assertIn("Светлая", w.header.action_text)
        self.choose("IA-2301", "Иванов Иван")
        ticket = self.click_generate()
        self.assertEqual(str(ticket.cget("background")), w.theme.palette.surface)
        ticket.close()


if __name__ == "__main__":
    unittest.main()
