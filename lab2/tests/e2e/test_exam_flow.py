"""E2E: сценарии экзамена от запуска до файла results.xlsx на диске.

Приложение собирается настоящим корнем композиции (Excel, Word, Tkinter),
действия выполняются только через виджеты, результат проверяется на экране
и в файле, прочитанном напрямую openpyxl. Подменены лишь модальные диалоги:
стандартный messagebox нельзя нажать из теста.
"""
import unittest
from datetime import datetime

from tests.e2e.support import AppE2ETestCase, ExcelLock, journal_on_disk
from tests.gui_support import pump, requires_display
from tests.helpers import ticket_block, write_students, write_tickets

HEADER = ["Группа", "Фамилия", "Имя", "Номер билета", "Дата и время", "Повтор (да/нет)"]


@requires_display
class ExamSessionTest(AppE2ETestCase):
    def test_first_start_creates_journal_with_header(self):
        self.assertFalse(self.results_path.exists())
        app = self.launch()
        self.assertEqual(journal_on_disk(self.results_path), [HEADER])
        self.assertEqual(list(app.group_combo["values"]), ["IA-2301", "IA-2302", "IA-2303"])
        self.assertEqual(self.dialogs.errors, [])

    def test_full_session_with_repeat(self):
        app = self.launch()
        ivanov = self.take_ticket(app, "IA-2301", "Иванов Иван")
        petrova = self.take_ticket(app, "IA-2301", "Петрова Анна")
        morozov = self.take_ticket(app, "IA-2302", "Морозов Алексей")
        again = self.take_ticket(app, "IA-2301", "Иванов Иван")
        self.assertEqual(again, ivanov)

        rows = journal_on_disk(self.results_path)
        self.assertEqual(rows[0], HEADER)
        self.assertEqual([r[:3] + [r[5]] for r in rows[1:]], [
            ["IA-2301", "Иванов", "Иван", "нет"], ["IA-2301", "Петрова", "Анна", "нет"],
            ["IA-2302", "Морозов", "Алексей", "нет"], ["IA-2301", "Иванов", "Иван", "да"]])
        self.assertEqual([f"№ {r[3]}" for r in rows[1:]], [ivanov, petrova, morozov, ivanov])
        stamps = [r[4] for r in rows[1:]]
        self.assertTrue(all(isinstance(t, datetime) for t in stamps))
        self.assertEqual(stamps, sorted(stamps))

        # экран: история, статистика, состояние формы
        self.assertEqual(len(app.history_tree.get_children()), 4)
        self.assertEqual(app.stat_tiles["issued"].value.cget("text"), "3")
        self.assertEqual(app.group_var.get(), "IA-2301")
        self.assertEqual(app.student_var.get(), "")
        self.assertTrue(app.generate_btn.instate(["disabled"]))

    def test_repeat_survives_restart_and_is_announced(self):
        app = self.launch()
        first = self.take_ticket(app, "IA-2301", "Сидоров Павел")
        app = self.restart(app, theme="dark")
        self.choose(app, "IA-2301", "Сидоров Павел")
        self.assertIn(first, app.hint_label.cget("text"))
        window = self.get_ticket(app)
        self.assertEqual((window.number_text, window.badge_text), (first, "ПОВТОР"))
        self.assertIn("Повторное обращение", window.note_label.cget("text"))
        window.close()
        self.assertEqual([r[5] for r in journal_on_disk(self.results_path)[1:]], ["нет", "да"])

    def test_same_name_in_other_group_is_another_student(self):
        app = self.launch()
        self.take_ticket(app, "IA-2301", "Иванов Иван")
        self.choose(app, "IA-2302", "Иванов Иван")
        window = self.get_ticket(app)
        self.assertEqual(window.badge_text, "НОВЫЙ")
        window.close()

    def test_empty_group_cannot_get_ticket(self):
        app = self.launch()
        self.choose(app, "IA-2303")
        self.assertEqual(str(app.student_combo["state"]), "disabled")
        app.generate_btn.invoke()
        pump(app)
        self.assertIsNone(app.ticket_window)
        self.assertEqual(journal_on_disk(self.results_path), [HEADER])


@requires_display
class FileProblemsTest(AppE2ETestCase):
    def test_missing_files_then_fixed_and_reloaded(self):
        self.students_path.unlink()
        self.tickets_path.unlink()
        with self.assertLogs("ticket_generator.application.data_loader", level="ERROR"):
            app = self.launch()
        self.assertEqual(len(self.dialogs.errors), 1)
        message = self.dialogs.errors[0][1]
        self.assertIn("students.xlsx", message)
        self.assertIn("tickets.docx", message)
        self.assertEqual(str(app.group_combo["state"]), "disabled")

        # преподаватель вернул файлы и нажал «Обновить данные»
        write_students(self.students_path, {"IA-2301": [("Иванов", "Иван")]})
        write_tickets(self.tickets_path, ticket_block(1))
        app.reload_btn.invoke()
        pump(app)
        self.assertEqual(list(app.group_combo["values"]), ["IA-2301"])
        self.assertEqual(self.take_ticket(app, "IA-2301", "Иванов Иван"), "№ 1")

    def test_invalid_tickets_are_skipped_and_logged(self):
        write_tickets(self.tickets_path,
                      ticket_block(1) + ticket_block(2, count=2) + ["Билет X", "1. a", "2. b", "3. c"]
                      + ticket_block(3))
        with self.assertLogs("ticket_generator.infrastructure.tickets_docx", level="ERROR") as logs:
            app = self.launch()
        self.assertEqual(app.stat_tiles["tickets"].value.cget("text"), "2")
        self.assertTrue(any("Билет 2 пропущен" in m for m in logs.output))
        self.assertTrue(any("Билет X" in m for m in logs.output))
        self.assertIn(self.take_ticket(app, "IA-2301", "Петрова Анна"), ("№ 1", "№ 3"))

    def test_journal_open_in_excel_retry_after_closing(self):
        app = self.launch()
        self.choose(app, "IA-2301", "Петрова Анна")
        lock = ExcelLock(self.results_path)

        def user_closes_excel_and_retries(title, message):
            self.assertIn("открыт в Excel", message)
            lock.release()
            return True

        self.dialogs.ask_retry = user_closes_excel_and_retries
        with self.assertLogs("ticket_generator.application.presenter", level="WARNING"):
            window = self.get_ticket(app)
        lock.release()
        self.assertIsNotNone(window)
        rows = journal_on_disk(self.results_path)
        self.assertEqual(len(rows), 2)  # ровно одна запись, без дублей
        self.assertEqual(f"№ {rows[1][3]}", window.number_text)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir() if p.name.startswith(".~")), [])
        window.close()

    def test_journal_open_in_excel_cancel_keeps_file_intact(self):
        app = self.launch()
        self.take_ticket(app, "IA-2301", "Иванов Иван")
        before = journal_on_disk(self.results_path)
        self.choose(app, "IA-2301", "Петрова Анна")
        with ExcelLock(self.results_path):
            with self.assertLogs("ticket_generator.application.presenter", level="WARNING"):
                self.assertIsNone(self.get_ticket(app))
        self.assertEqual(len(self.dialogs.retry_questions), 1)
        self.assertEqual(journal_on_disk(self.results_path), before)
        self.assertIn("не выдан", app.status_bar.label.cget("text"))
        # после закрытия Excel та же попытка проходит
        window = self.get_ticket(app)
        self.assertIsNotNone(window)
        window.close()
        self.assertEqual(len(journal_on_disk(self.results_path)), len(before) + 1)


if __name__ == "__main__":
    unittest.main()
