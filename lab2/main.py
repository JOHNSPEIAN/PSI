"""Точка входа: python main.py [--data-dir ПАПКА] [--theme system|light|dark]

По умолчанию файлы students.xlsx, tickets.docx и results.xlsx ищутся в папке data
рядом с main.py.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def setup_logging(log_file: Path) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    try:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    except OSError:
        pass  # нет прав на запись лога — пишем только в консоль
    logging.basicConfig(level=logging.INFO, handlers=handlers,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Генератор экзаменационных билетов")
    parser.add_argument("--data-dir", type=Path, default=BASE_DIR / "data",
                        help="папка с students.xlsx, tickets.docx и results.xlsx")
    parser.add_argument("--theme", choices=("system", "light", "dark"), default="system",
                        help="оформление: как в Windows (по умолчанию), светлое или тёмное")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    data_dir: Path = args.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(data_dir / "ticket_generator.log")

    # импорт после настройки логов
    from ticket_generator.bootstrap import build_app
    from ticket_generator.ui.platform import enable_hidpi, system_theme

    enable_hidpi()  # до создания первого окна
    theme = system_theme() if args.theme == "system" else args.theme
    build_app(data_dir, theme=theme).mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
