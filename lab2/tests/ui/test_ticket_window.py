"""UI-тесты окна билета: содержимое, бейджи, закрытие только этого окна."""
import unittest
from datetime import datetime

from tests.gui_support import press, pump, requires_display

QUESTIONS = ("Типы данных в Python.", "Списки и кортежи.", "Словари и множества.")


@requires_display
class TicketWindowTest(unittest.TestCase):
    def setUp(self):
        import tkinter as tk

        from ticket_generator.domain import Assignment, Student
        from ticket_generator.ui.theme import LIGHT, Theme

        self.root = tk.Tk()
        self.theme = Theme(self.root, LIGHT)
        self.theme.apply()
        self.student = Student("IA-2301", "Кузнецова", "Мария")
        self.when = datetime(2026, 11, 18, 14, 3)
        self.make_assignment = lambda **kw: Assignment(**{
            "student": self.student, "ticket_no": 7, "questions": QUESTIONS, "repeat": False,
            "timestamp": self.when, **kw})
        self.closed = 0

    def tearDown(self):
        self.root.destroy()

    def open(self, **kw):
        from ticket_generator.ui.ticket_window import TicketWindow

        def on_close():
            self.closed += 1

        window = TicketWindow(self.root, self.theme, self.make_assignment(**kw), on_close)
        pump(window)
        return window

    def test_shows_number_student_and_three_questions(self):
        w = self.open()
        self.assertEqual(w.number_text, "№ 7")
        self.assertEqual(w.student_text, "Кузнецова Мария · IA-2301 · 18.11.2026 14:03")
        self.assertEqual(w.question_texts, list(QUESTIONS))
        self.assertEqual([b.text for b in w.question_badges], ["1", "2", "3"])
        self.assertEqual(w.title(), "Билет № 7 — Кузнецова Мария")

    def test_new_ticket_badge_and_no_note(self):
        w = self.open()
        self.assertEqual(w.badge_text, "НОВЫЙ")
        self.assertIsNone(w.note_label)

    def test_repeat_ticket_has_badge_and_warning_note(self):
        w = self.open(repeat=True)
        self.assertEqual(w.badge_text, "ПОВТОР")
        self.assertIn("Повторное обращение", w.note_label.cget("text"))
        self.assertEqual(str(w.note_label.cget("style")), "WarningNote.TLabel")

    def test_ticket_missing_from_file_shows_danger_note(self):
        w = self.open(questions=(), repeat=True)
        self.assertEqual(w.question_texts, [])
        self.assertIn("больше нет в tickets.docx", w.note_label.cget("text"))
        self.assertEqual(str(w.note_label.cget("style")), "DangerNote.TLabel")

    def test_window_is_modal(self):
        w = self.open()
        self.assertEqual(str(w.grab_current()), str(w))

    def test_escape_closes_only_this_window(self):
        w = self.open()
        press(w, "<Escape>")
        self.assertFalse(w.winfo_exists())
        self.assertTrue(self.root.winfo_exists())
        self.assertEqual(self.closed, 1)

    def test_enter_and_done_button_close(self):
        w = self.open()
        press(w.close_btn, "<Return>")
        self.assertEqual(self.closed, 1)
        w2 = self.open()
        w2.close_btn.invoke()
        self.assertFalse(w2.winfo_exists())
        self.assertEqual(self.closed, 2)

    def test_close_callback_runs_once(self):
        w = self.open()
        w.close()
        w.close()
        self.assertEqual(self.closed, 1)


if __name__ == "__main__":
    unittest.main()
