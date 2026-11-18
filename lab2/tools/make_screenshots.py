"""Снимки экрана для README: главное окно и окно билета в светлой и тёмной теме.

Запуск (нужен Pillow, только Windows/macOS): python tools/make_screenshots.py [ПАПКА]
По умолчанию снимки сохраняются в docs/screenshots. Работает на копии демо-данных
во временной папке, настоящий журнал не трогает.
"""
from __future__ import annotations

import random
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import ImageGrab  # noqa: E402

from ticket_generator.application.ticket_service import RandomTicketPicker  # noqa: E402
from ticket_generator.bootstrap import build_app  # noqa: E402
from ticket_generator.domain import JournalRow  # noqa: E402
from ticket_generator.infrastructure.journal_xlsx import XlsxJournal  # noqa: E402
from ticket_generator.ui.platform import enable_hidpi  # noqa: E402
from tools.make_sample_data import make_students, make_tickets  # noqa: E402

HISTORY = [("IA-2302", "Лебедев", "Никита", 7, False), ("IA-2301", "Кузнецова", "Мария", 4, False),
           ("IA-2301", "Попов", "Дмитрий", 5, False), ("IA-2301", "Кузнецова", "Мария", 4, True),
           ("IA-2302", "Волкова", "Елена", 2, False), ("IA-2301", "Иванов", "Иван", 8, False)]


class SilentDialogs:
    def show_error(self, title, message):
        print(f"[{title}] {message}")

    def ask_retry(self, title, message):
        return False


def window_rect(win) -> tuple[int, int, int, int]:
    """Границы окна вместе с рамкой и заголовком (Windows), иначе — клиентская область."""
    win.update_idletasks()
    try:
        import ctypes
        from ctypes import wintypes
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        rect = wintypes.RECT()
        ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect))
        return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        x, y = win.winfo_rootx(), win.winfo_rooty()
        return x, y, x + win.winfo_width(), y + win.winfo_height()


def grab(win, path: Path) -> None:
    win.attributes("-topmost", True)
    win.lift()
    for _ in range(10):
        win.update()
        time.sleep(0.05)
    ImageGrab.grab(bbox=window_rect(win), all_screens=True).save(path)
    print("сохранён", path)


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "screenshots"
    out.mkdir(parents=True, exist_ok=True)
    enable_hidpi()
    for theme in ("light", "dark"):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            make_students(data / "students.xlsx")
            make_tickets(data / "tickets.docx")
            journal = XlsxJournal(data / "results.xlsx")
            start = datetime.now().replace(second=0, microsecond=0) - timedelta(minutes=40)
            for i, (group, surname, name, ticket, repeat) in enumerate(HISTORY):
                journal.append(JournalRow(group, surname, name, ticket, start + timedelta(minutes=6 * i),
                                          repeat))

            app = build_app(data, theme=theme, dialogs=SilentDialogs(),
                            picker=RandomTicketPicker(random.Random(3)))
            app.update()
            app.group_var.set("IA-2301")
            app.on_group_selected()
            app.student_var.set("Кузнецова Мария")
            app.on_student_selected()
            grab(app, out / f"main-{theme}.png")

            app.generate_btn.invoke()
            grab(app.ticket_window, out / f"ticket-repeat-{theme}.png")
            app.ticket_window.close()

            app.student_var.set("Сидоров Павел")
            app.on_student_selected()
            app.generate_btn.invoke()
            grab(app.ticket_window, out / f"ticket-new-{theme}.png")
            app.ticket_window.close()
            app.destroy()


if __name__ == "__main__":
    main()
