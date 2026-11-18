"""E2E: запуск скриптов отдельным процессом Python, как это делает пользователь."""
import os
import subprocess
import sys
import unittest
from pathlib import Path

from tests.gui_support import requires_display
from tests.helpers import TempDirTestCase

LAB2 = Path(__file__).resolve().parents[2]

# Запуск настоящего main.main() в отдельном интерпретаторе; окно закрывается само.
LAUNCH_MAIN = """
import sys, tkinter
_mainloop = tkinter.Misc.mainloop
def short_mainloop(self, n=0):
    self.after(1500, self.destroy)
    _mainloop(self, n)
tkinter.Misc.mainloop = short_mainloop
import main
sys.exit(main.main(sys.argv[1:]))
"""


def run(*args, encoding="utf-8", timeout=60, **env):
    environment = {**os.environ, "PYTHONIOENCODING": encoding, **env}
    return subprocess.run([sys.executable, *args], cwd=LAB2, capture_output=True,
                          timeout=timeout, env=environment)


class SampleDataScriptTest(TempDirTestCase):
    def test_creates_both_files(self):
        result = run("tools/make_sample_data.py", str(self.tmp))
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertTrue((self.tmp / "students.xlsx").is_file())
        self.assertTrue((self.tmp / "tickets.docx").is_file())

    def test_output_without_cyrillic_does_not_crash(self):
        """Регрессия: при выводе в канал (cp1252) скрипт падал на print с кириллицей."""
        result = run("tools/make_sample_data.py", str(self.tmp), encoding="cp1252")
        self.assertEqual(result.returncode, 0, result.stderr.decode("cp1252", "replace"))

    def test_generated_data_is_valid_for_the_app(self):
        from ticket_generator.infrastructure.students_xlsx import load_students
        from ticket_generator.infrastructure.tickets_docx import load_tickets
        run("tools/make_sample_data.py", str(self.tmp))
        self.assertEqual(load_students(self.tmp / "students.xlsx").group_names,
                         ("IA-2301", "IA-2302", "IA-2303"))
        self.assertEqual(len(load_tickets(self.tmp / "tickets.docx")), 10)


class MainEntryPointTest(TempDirTestCase):
    def test_help_lists_options(self):
        result = run("main.py", "--help")
        self.assertEqual(result.returncode, 0)
        out = result.stdout.decode("utf-8")
        self.assertIn("--data-dir", out)
        self.assertIn("--theme", out)

    def test_unknown_theme_is_rejected(self):
        result = run("main.py", "--theme", "pink")
        self.assertEqual(result.returncode, 2)

    @requires_display
    def test_app_starts_creates_journal_and_log_then_exits(self):
        run("tools/make_sample_data.py", str(self.tmp))
        for theme in ("light", "dark"):
            with self.subTest(theme=theme):
                result = run("-c", LAUNCH_MAIN, "--data-dir", str(self.tmp), "--theme", theme)
                self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertTrue((self.tmp / "results.xlsx").is_file())
        log = (self.tmp / "ticket_generator.log").read_text(encoding="utf-8")
        self.assertIn("Загружено билетов: 10", log)
        self.assertNotIn("ERROR", log)

    @requires_display
    def test_app_starts_without_data_files(self):
        """Нет students.xlsx и tickets.docx — приложение не падает (сообщение в окне)."""
        script = LAUNCH_MAIN.replace(
            "import main", "import main\nfrom tkinter import messagebox\n"
                           "messagebox.showerror = lambda *a, **k: print('dialog:', a[0])")
        result = run("-c", script, "--data-dir", str(self.tmp), "--theme", "light")
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertIn("dialog: Ошибка загрузки данных", result.stdout.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
