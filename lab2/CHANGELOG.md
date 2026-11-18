# Changelog / История изменений

Format: [Keep a Changelog](https://keepachangelog.com/), versions: [SemVer](https://semver.org/).
Формат: [Keep a Changelog](https://keepachangelog.com/ru/), версии: [SemVer](https://semver.org/lang/ru/).

## [2.0.0] — 2026-11-18

### Added / Добавлено

- EN: Redesigned interface: gradient header, selection card with numbered steps, statistics
  tiles, recent issues table, status bar; a ticket window with a large number, NEW/REPEAT
  badge and numbered questions.
  RU: Новый интерфейс: градиентная шапка, карточка выбора с номерами шагов, плитки
  статистики, таблица последних выдач, строка состояния; окно билета с крупным номером,
  бейджем НОВЫЙ/ПОВТОР и нумерованными вопросами.
- EN: Light and dark themes, `--theme system|light|dark`, `Ctrl+T`; dark Windows title bar.
  RU: Светлая и тёмная темы, `--theme system|light|dark`, `Ctrl+T`; тёмный заголовок окна Windows.
- EN: Hint before issuing: “ticket № N was issued earlier — a repeat gets the same one”.
  RU: Подсказка до выдачи: «Ранее выдан билет № N — при повторе выдаётся тот же».
- EN: Keyboard: `Enter` — ticket, `F5`/`Ctrl+R` — reload, also in the Russian layout.
  RU: Клавиши: `Enter` — билет, `F5`/`Ctrl+R` — обновить, в том числе в русской раскладке.
- EN: Crisp text on HiDPI screens, DPI-aware sizes, generated window icon.
  RU: Чёткий текст на экранах с масштабом 125–150 %, размеры под DPI, своя иконка окна.
- EN: Three test levels — unit (114), UI (33), e2e (16); CI runs them as separate steps,
  with `xvfb` on Linux.
  RU: Три уровня тестов — unit (114), UI (33), e2e (16); CI запускает их отдельными шагами,
  на Linux — с `xvfb`.
- EN: Bilingual Git workflow: commit template, `CONTRIBUTING.md`, `.gitattributes`.
  RU: Двуязычные правила Git: шаблон коммита, `CONTRIBUTING.md`, `.gitattributes`.

### Changed / Изменено

- EN: Layered SOLID architecture: `domain`, `application` (ports, services, MVP presenter),
  `infrastructure` (Excel/Word adapters), `ui`, composition root `bootstrap.py`.
  RU: Слоистая архитектура по SOLID: `domain`, `application` (порты, сервисы, презентер MVP),
  `infrastructure` (адаптеры Excel/Word), `ui`, корень композиции `bootstrap.py`.
- EN: `ResultsJournal` → `XlsxJournal`; the “first ticket” rule moved to the domain.
  RU: `ResultsJournal` → `XlsxJournal`; правило «первого билета» перенесено в домен.
- EN: Load errors from all files are shown in one message.
  RU: Ошибки всех файлов показываются одним сообщением.

### Fixed / Исправлено

- EN: `tools/make_sample_data.py` crashed when its output went to a pipe or file on Windows.
  RU: `tools/make_sample_data.py` падал, если вывод в Windows шёл в канал или файл.
- EN: UI tests on Linux CI were silently skipped (no display).
  RU: UI-тесты в CI на Linux молча пропускались (не было дисплея).

## [1.0.0] — 2026-11-04

- EN: First version of Lab 2: Tkinter UI, Excel/Word input, append-only journal, 51 tests.
  RU: Первая версия Лаб 2: интерфейс на Tkinter, данные из Excel/Word, журнал только на
  дописывание, 51 тест.
