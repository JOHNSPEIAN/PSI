"""Парсинг списка билетов из tickets.docx.

Формат:
    Билет 1
    1. Вопрос первый
    2. Вопрос второй
    3. Вопрос третий

Заголовок — строка «Билет N». Вопросы — абзацы «N. текст»; также
поддерживаются абзацы с автонумерацией Word (нумерованный список), у которых
номер не входит в текст абзаца.

Некорректные билеты (меньше 3 вопросов, нераспознанный заголовок, дубликат
номера) пропускаются с записью в лог, остальные билеты используются.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from docx import Document

log = logging.getLogger(__name__)

QUESTIONS_PER_TICKET = 3

HEADER_RE = re.compile(r"^\s*Билет\s*№?\s*(\d+)\s*[.:]?\s*$", re.IGNORECASE)
# Строка, похожая на заголовок, но не распознанная (например, «Билет X» или «Билет»).
HEADER_LIKE_RE = re.compile(r"^\s*Билет\b", re.IGNORECASE)
QUESTION_RE = re.compile(r"^\s*(\d+)\s*[.)]\s*(.+?)\s*$")


@dataclass(frozen=True)
class Ticket:
    number: int
    questions: tuple[str, ...]


class TicketsFileError(Exception):
    """tickets.docx отсутствует, не читается или не содержит ни одного корректного билета."""


def _is_numbered_paragraph(paragraph) -> bool:
    """Абзац оформлен как элемент нумерованного списка Word (автонумерация)."""
    p_pr = paragraph._p.pPr
    return p_pr is not None and p_pr.numPr is not None


def _docx_lines(path: Path) -> list[tuple[str, bool]]:
    doc = Document(str(path))
    return [(p.text, _is_numbered_paragraph(p)) for p in doc.paragraphs]


def parse_ticket_lines(lines: Iterable[str | tuple[str, bool]]) -> dict[int, Ticket]:
    """Разбирает последовательность абзацев на билеты.

    Элемент — либо строка, либо пара (текст, является_ли_автонумерованным).
    Возвращает {номер: Ticket}, отсортированный по номеру.
    """
    tickets: dict[int, Ticket] = {}
    current_no: int | None = None
    current_questions: list[str] = []
    in_bad_block = False  # вопросы под нераспознанным заголовком

    def flush() -> None:
        nonlocal current_no, current_questions
        if current_no is None:
            return
        if len(current_questions) < QUESTIONS_PER_TICKET:
            log.error("Билет %d пропущен: найдено вопросов %d, нужно %d",
                      current_no, len(current_questions), QUESTIONS_PER_TICKET)
        elif current_no in tickets:
            log.error("Билет %d пропущен: номер билета повторяется", current_no)
        else:
            if len(current_questions) > QUESTIONS_PER_TICKET:
                log.warning("Билет %d: вопросов %d, используются первые %d",
                            current_no, len(current_questions), QUESTIONS_PER_TICKET)
            tickets[current_no] = Ticket(current_no, tuple(current_questions[:QUESTIONS_PER_TICKET]))
        current_no = None
        current_questions = []

    for item in lines:
        text, auto_numbered = (item, False) if isinstance(item, str) else item
        text = (text or "").strip()
        if not text:
            continue

        header = HEADER_RE.match(text)
        if header:
            flush()
            current_no = int(header.group(1))
            in_bad_block = False
            if current_no < 1:
                log.error("Заголовок «%s» не распознан: номер билета должен быть ≥ 1", text)
                current_no = None
                in_bad_block = True
            continue
        if HEADER_LIKE_RE.match(text):
            flush()
            log.error("Заголовок «%s» не распознан — билет пропущен", text)
            in_bad_block = True
            continue

        question = QUESTION_RE.match(text)
        question_text = question.group(2) if question else (text if auto_numbered else None)

        if question_text is None:
            log.warning("Строка «%s» не распознана как заголовок или вопрос — пропущена", text)
            continue
        if current_no is None:
            if not in_bad_block:
                log.warning("Вопрос «%s» вне билета — пропущен", text)
            continue
        current_questions.append(question_text)

    flush()
    return dict(sorted(tickets.items()))


def load_tickets(path: str | Path) -> dict[int, Ticket]:
    path = Path(path)
    if not path.is_file():
        raise TicketsFileError(f"Файл с билетами не найден: {path}")
    try:
        lines = _docx_lines(path)
    except Exception as exc:
        raise TicketsFileError(f"Не удалось прочитать {path.name}: {exc}") from exc
    tickets = parse_ticket_lines(lines)
    if not tickets:
        raise TicketsFileError(f"В {path.name} нет ни одного корректного билета "
                               f"(нужен заголовок «Билет N» и {QUESTIONS_PER_TICKET} вопроса)")
    log.info("Загружено билетов: %d", len(tickets))
    return tickets
