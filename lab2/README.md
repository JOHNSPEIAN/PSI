# Лабораторная работа №2 — генератор билетов с UI

Десктопное приложение на **Python + Tkinter**. Студент выбирает группу и свою фамилию,
получает экзаменационный билет из трёх вопросов; каждая выдача пишется в журнал `results.xlsx`.

## Запуск

Все команды выполняются **из папки `lab2`**, а не из корня репозитория: в корне лежит Лаб 1.

### Windows (cmd или PowerShell)

Установите Python 3.10+ с [python.org](https://www.python.org/downloads/) и оставьте включённой
галочку «tcl/tk and IDLE». На Windows Python вызывается командой `py`, а не `python3`,
а программы окружения лежат в `.venv\Scripts\`.

```bat
cd lab2
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

Первые три команды нужны один раз. Дальше запуск такой:

```bat
cd lab2
.venv\Scripts\python.exe main.py
```

В Git Bash те же пути пишутся через прямой слэш: `.venv/Scripts/python.exe main.py`.

### Linux / macOS

```bash
cd lab2
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

### Другая папка с данными

По умолчанию файлы берутся из `lab2/data/`. Другую папку можно указать так:

```bat
.venv\Scripts\python.exe main.py --data-dir D:\exam
```

В папке данных должны лежать:

| Файл | Назначение |
|---|---|
| `students.xlsx` | один лист на группу (имя листа = группа), строка 1 — заголовок, A — Фамилия, B — Имя |
| `tickets.docx` | `Билет N`, затем три абзаца `1. …`, `2. …`, `3. …` (обычный текст или автонумерация Word) |
| `results.xlsx` | журнал; создаётся автоматически при первом запуске |
| `ticket_generator.log` | лог: пропущенные билеты, ошибки чтения, блокировки файла |

Демонстрационные `students.xlsx` и `tickets.docx` уже лежат в `data/`
(пересоздать: `.venv\Scripts\python.exe tools\make_sample_data.py`).

## Как работает

1. При запуске первый список заполняется листами `students.xlsx`.
2. После выбора группы второй список заполняется студентами «Фамилия Имя».
3. Кнопка «Сгенерировать билет» активна, только когда выбраны и группа, и студент.
4. По кнопке открывается окно «Ваш билет № N» с тремя вопросами; строка сразу дописывается в `results.xlsx`.
5. `Esc` закрывает окно билета; приложение остаётся открытым, группа сохраняется, студент сбрасывается.

**Назначение билета.** Если студент (группа + фамилия + имя) уже есть в журнале, берётся номер
из *самой первой* записи, и добавляется новая строка с «Повтор = да». Иначе берётся случайный билет
из корректно разобранных в `tickets.docx`, а строка пишется с «Повтор = нет».

**Журнал** только дописывается: старые строки не меняются, а сохранение идёт атомарно
(во временный файл, затем замена). Поэтому по журналу восстанавливается полная история в хронологическом порядке.

## Устойчивость

- Нет `students.xlsx` / `tickets.docx` или файл повреждён — сообщение в окне, приложение работает
  дальше; после исправления файлов нажмите «Обновить данные».
- Пустая группа — второй список пуст и неактивен, кнопка неактивна.
- `results.xlsx` открыт в Excel — диалог «Повторить / Отмена»; при повторе сохраняется *тот же* билет.
  При отмене билет не показывается и в журнал не попадает.
- Билет с менее чем тремя вопросами, с нераспознанным заголовком (`Билет X`) или с повторяющимся номером
  пропускается, ошибка пишется в лог; остальные билеты используются.

## Структура

```
main.py                      точка входа
ticket_generator/
  students.py                чтение students.xlsx, поиск студента по группе
  tickets.py                 парсинг tickets.docx
  journal.py                 журнал results.xlsx (append-only, блокировка файла)
  service.py                 назначение билета, состояние списков и кнопки
  gui.py                     Tkinter-интерфейс
tests/                       unit-тесты и тесты интерфейса
tools/make_sample_data.py    генерация демо-данных
```

## Тесты

Из папки `lab2`, после установки зависимостей (см. «Запуск»):

```bat
.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

На Linux / macOS: `.venv/bin/python -m unittest discover -s tests -t . -v`.

51 тест покрывает парсинг билетов из Word, поиск студентов по группе, идемпотентность
(повторный выбор → тот же билет и новая строка «да»), неизменность старых строк журнала,
блокировку файла, логику активности кнопки, а также реальный интерфейс: выбор, генерацию,
закрытие по `Esc`, отсутствующие файлы и диалог повтора. Тесты интерфейса автоматически
пропускаются, если нет графической среды.

## Соответствие критериям приёмки

| № | Критерий | Тесты |
|---|---|---|
| 1 | Список студентов соответствует листу | `test_students_match_sheet_rows`, `test_group_selection_fills_students_of_that_sheet`, `test_group_then_student_enables_button` |
| 2 | Кнопка активна только при обоих выборах | `test_button_enabled_only_when_both_selected`, `test_empty_group_*` |
| 3 | Билет и три вопроса отображаются | `test_new_student_gets_random_ticket_from_file`, `test_generate_shows_ticket_and_escape_closes_only_result` |
| 4 | Повторный выбор → тот же номер | `test_repeat_selection_returns_same_ticket`, `test_repeat_survives_restart` |
| 5 | `Esc` закрывает только окно результата | `test_generate_shows_ticket_and_escape_closes_only_result` |
| 6 | Строка появляется сразу, старые не тронуты | `test_row_is_written_immediately_after_generation`, `test_append_keeps_existing_rows_untouched` |
| 7 | Отсутствующий или заблокированный файл не роняет приложение | `test_missing_sources_show_message_without_crash`, `test_locked_journal_*`, `test_missing_file_raises_clear_error` |
| 8 | Повтор — новая строка в конце, тот же номер, «да» | `test_repeat_appends_new_row_with_yes`, `test_find_first_ticket_uses_earliest_row` |
| 9 | Полная история в хронологическом порядке | `test_full_history_in_chronological_order` |
