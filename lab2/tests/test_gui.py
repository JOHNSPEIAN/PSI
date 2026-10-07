"""Интеграционные тесты интерфейса (пропускаются, если нет Tkinter или дисплея)."""
import unittest
from unittest import mock

from tests.helpers import GROUPS, TempDirTestCase, ticket_block, write_students, write_tickets

try:
    import tkinter as tk
    _root = tk.Tk()
    _root.destroy()
    HAS_DISPLAY = True
except Exception:  # нет tkinter или нет графической среды
    HAS_DISPLAY = False


@unittest.skipUnless(HAS_DISPLAY, "Tkinter/дисплей недоступны")
class GuiTest(TempDirTestCase):
    def setUp(self):
        super().setUp()
        from ticket_generator import gui
        self.gui = gui
        write_students(self.tmp / "students.xlsx", GROUPS)
        write_tickets(self.tmp / "tickets.docx", ticket_block(1) + ticket_block(2) + ticket_block(3))
        self.mb = mock.patch.object(gui, "messagebox").start()
        self.addCleanup(mock.patch.stopall)
        self.app = None

    def tearDown(self):
        if self.app is not None:
            self.app.destroy()
        super().tearDown()

    def start(self):
        self.app = self.gui.App(self.tmp)
        self.pump()
        return self.app

    def pump(self):
        for _ in range(5):
            self.app.update()

    def choose(self, group, student=None):
        self.app.group_var.set(group)
        self.app.on_group_selected()
        if student is not None:
            self.app.student_var.set(student)
            self.app.on_student_selected()

    def btn_enabled(self):
        return "disabled" not in self.app.generate_btn.state()

    def test_startup_fills_groups_and_creates_results(self):
        app = self.start()
        self.assertEqual(list(app.group_combo["values"]), list(GROUPS))
        self.assertFalse(self.btn_enabled())
        self.assertTrue((self.tmp / "results.xlsx").exists())

    def test_group_then_student_enables_button(self):
        app = self.start()
        self.choose("IA-2302")
        self.assertEqual(list(app.student_combo["values"]), ["Морозов Алексей", "Волкова Елена"])
        self.assertFalse(self.btn_enabled())
        self.choose("IA-2302", "Волкова Елена")
        self.assertTrue(self.btn_enabled())

    def test_empty_group_keeps_button_disabled(self):
        app = self.start()
        self.choose("IA-2303")
        self.assertEqual(list(app.student_combo["values"]), [])
        self.assertEqual(str(app.student_combo["state"]), "disabled")
        self.assertFalse(self.btn_enabled())

    def test_generate_shows_ticket_and_escape_closes_only_result(self):
        app = self.start()
        self.choose("IA-2301", "Иванов Иван")
        app.generate_btn.invoke()
        self.pump()
        win = app.result_window
        self.assertIsNotNone(win)
        texts = [w.cget("text") for w in win.winfo_children()[0].winfo_children()]
        self.assertTrue(any(t.startswith("Ваш билет № ") for t in texts))
        self.assertEqual(sum(1 for t in texts if t[:3] in ("1. ", "2. ", "3. ")), 3)

        win.event_generate("<Escape>")
        self.pump()
        self.assertIsNone(app.result_window)
        self.assertTrue(app.winfo_exists())  # приложение живо
        self.assertFalse(self.btn_enabled())  # готово к следующему студенту

        # повторный выбор — тот же билет
        first_no = int(texts[1].split("№")[1])
        self.choose("IA-2301", "Иванов Иван")
        app.generate_btn.invoke()
        self.pump()
        again = [w.cget("text") for w in app.result_window.winfo_children()[0].winfo_children()]
        self.assertEqual(int(again[1].split("№")[1]), first_no)
        app.result_window.close()

    def test_missing_sources_show_message_without_crash(self):
        (self.tmp / "students.xlsx").unlink()
        (self.tmp / "tickets.docx").unlink()
        app = self.start()
        self.mb.showerror.assert_called_once()
        message = self.mb.showerror.call_args[0][1]
        self.assertIn("students.xlsx", message)
        self.assertIn("tickets.docx", message)
        self.assertEqual(str(app.group_combo["state"]), "disabled")
        self.assertFalse(self.btn_enabled())

    def test_locked_journal_asks_retry_then_saves(self):
        app = self.start()
        self.choose("IA-2301", "Петрова Анна")
        real_save = app.service.save
        calls = {"n": 0}

        def flaky_save(a):
            calls["n"] += 1
            if calls["n"] == 1:
                raise self.gui.JournalLockedError("открыт в Excel")
            real_save(a)

        app.service.save = flaky_save
        self.mb.askretrycancel.return_value = True
        app.generate_btn.invoke()
        self.pump()
        self.mb.askretrycancel.assert_called_once()
        self.assertEqual(calls["n"], 2)
        self.assertIsNotNone(app.result_window)
        app.result_window.close()

    def test_locked_journal_cancel_does_not_show_ticket(self):
        app = self.start()
        self.choose("IA-2301", "Петрова Анна")
        app.service.save = mock.Mock(side_effect=self.gui.JournalLockedError("locked"))
        self.mb.askretrycancel.return_value = False
        app.generate_btn.invoke()
        self.pump()
        self.assertIsNone(app.result_window)
        self.assertTrue(app.winfo_exists())


if __name__ == "__main__":
    unittest.main()
