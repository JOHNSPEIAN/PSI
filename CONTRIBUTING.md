# Git workflow / Правила работы с Git

The repository is maintained in **two languages**: every commit, tag and
changelog entry has an English and a Russian part.

Репозиторий ведётся **на двух языках**: у каждого коммита, тега и записи
в CHANGELOG есть английская и русская часть.

---

## Branches / Ветки

| Branch / Ветка | EN | RU |
|---|---|---|
| `main` | Stable code: Lab 1 (console) and merged labs | Стабильный код: Лаб 1 (консоль) и слитые лабораторные |
| `lab2-ui-tickets` | Lab 2: Tkinter ticket generator, opened as PR #1 | Лаб 2: генератор билетов на Tkinter, открыт PR #1 |

EN: New work goes to a feature branch and reaches `main` only through a pull
request with green CI. History is never rewritten on shared branches
(no `push --force`).

RU: Новая работа идёт в отдельной ветке и попадает в `main` только через
pull request с зелёным CI. Историю общих веток не переписываем
(без `push --force`).

## Commit messages / Сообщения коммитов

Format — [Conventional Commits](https://www.conventionalcommits.org/) with a
bilingual subject and body.

Формат — [Conventional Commits](https://www.conventionalcommits.org/ru/) с
двуязычным заголовком и телом.

```text
<type>(<scope>): <English summary> — <русское резюме>

EN: what changed and why.

RU: что изменилось и зачем.
```

| Type / Тип | EN | RU |
|---|---|---|
| `feat` | new user-visible feature | новая функция для пользователя |
| `fix` | bug fix | исправление ошибки |
| `refactor` | code change without behaviour change | изменение кода без изменения поведения |
| `test` | tests only | только тесты |
| `docs` | documentation only | только документация |
| `ci` | GitHub Actions | GitHub Actions |
| `chore` | tooling, configs, housekeeping | настройки, служебные файлы |

Scopes / зоны: `core`, `app`, `ui`, `tests`, `ci`, `docs`, `git`, `lab1`.

Rules / правила:

1. EN: one logical change per commit, tests pass after every commit.
   RU: один логический шаг на коммит, тесты зелёные после каждого коммита.
2. EN: imperative mood in English (`add`, not `added`), subject ≤ 72 characters
   per language part.
   RU: в английской части — повелительное наклонение (`add`, а не `added`),
   каждая часть заголовка не длиннее 72 символов.
3. EN: moved files are committed separately from their edits (`git mv`), so
   `git log --follow` keeps the history.
   RU: перенос файлов коммитится отдельно от их правки (`git mv`), чтобы
   `git log --follow` сохранял историю.

A ready-made template / готовый шаблон:

```bash
git config commit.template .gitmessage.txt
```

## Tags / Теги

Releases are annotated tags `lab2-vX.Y.Z` with a bilingual message.
Релизы — аннотированные теги `lab2-vX.Y.Z` с двуязычным описанием.

```bash
git tag -a lab2-v2.0.0 -m "Lab 2 v2.0.0 — Лаб 2 v2.0.0" -m "EN: ..." -m "RU: ..."
git push origin lab2-v2.0.0
```

## Line endings / Окончания строк

EN: `.gitattributes` stores text files with LF; Git converts them to CRLF in
a Windows working copy. Excel and Word files are marked as binary.

RU: `.gitattributes` хранит текстовые файлы с LF, а в рабочей копии Windows
Git сам переводит их в CRLF. Файлы Excel и Word помечены как бинарные.
