"""E2E: запуск скриптов отдельным процессом Python, как это делает пользователь."""
import os
import subprocess
import sys
import unittest
from pathlib import Path

from tests.helpers import TempDirTestCase

LAB2 = Path(__file__).resolve().parents[2]


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


if __name__ == "__main__":
    unittest.main()
