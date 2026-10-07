"""Графический интерфейс на Tkinter."""
from __future__ import annotations

import logging
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import messagebox, ttk

from .journal import JournalError, JournalLockedError, ResultsJournal
from .service import Assignment, SelectionState, TicketService
from .students import StudentsFileError, load_students
from .tickets import TicketsFileError, load_tickets

log = logging.getLogger(__name__)

STUDENTS_FILE = "students.xlsx"
TICKETS_FILE = "tickets.docx"
RESULTS_FILE = "results.xlsx"


class ResultWindow(tk.Toplevel):
    """Окно «Ваш билет № N». ESC закрывает только это окно."""

    def __init__(self, master: tk.Misc, assignment: Assignment, on_close):
        super().__init__(master)
        self._on_close = on_close
        s = assignment.student
        self.title(f"Билет — {s.surname} {s.name}")
        self.transient(master)
        self.resizable(False, False)

        body = ttk.Frame(self, padding=24)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text=f"{s.surname} {s.name}, группа {s.group}",
                  style="Muted.TLabel").pack(anchor="w")
        ttk.Label(body, text=f"Ваш билет № {assignment.ticket_no}",
                  style="Ticket.TLabel").pack(anchor="w", pady=(4, 12))

        if assignment.questions:
            for i, question in enumerate(assignment.questions, start=1):
                ttk.Label(body, text=f"{i}. {question}", wraplength=520,
                          justify="left", style="Question.TLabel").pack(anchor="w", pady=3)
        else:
            ttk.Label(body, text="Билета с этим номером больше нет в tickets.docx — "
                                 "обратитесь к преподавателю.",
                      wraplength=520, foreground="#b42318").pack(anchor="w")

        if assignment.repeat:
            ttk.Label(body, text="Повторное обращение: выдан тот же билет, что и в первый раз.",
                      style="Muted.TLabel", wraplength=520).pack(anchor="w", pady=(12, 0))

        ttk.Label(body, text="Esc — закрыть", style="Muted.TLabel").pack(anchor="e", pady=(16, 0))

        self.bind("<Escape>", self.close)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.update_idletasks()
        self._center_on(master)
        self.grab_set()
        self.focus_force()

    def _center_on(self, master: tk.Misc) -> None:
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_reqwidth()) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def close(self, _event=None) -> None:
        self.grab_release()
        self.destroy()
        self._on_close()


class App(tk.Tk):
    def __init__(self, data_dir: str | Path):
        super().__init__()
        self.data_dir = Path(data_dir)
        self.selection = SelectionState()
        self.service: TicketService | None = None
        self.result_window: ResultWindow | None = None

        self.title("Генератор билетов")
        self.minsize(460, 0)
        self.report_callback_exception = self._on_unexpected_error
        self._init_styles()
        self._build()
        self.after(0, self.reload_sources)

    # ---------- построение UI ----------
    def _init_styles(self) -> None:
        style = ttk.Style(self)
        family = tkfont.nametofont("TkDefaultFont").actual("family")
        style.configure("Title.TLabel", font=(family, 14, "bold"))
        style.configure("Ticket.TLabel", font=(family, 18, "bold"))
        style.configure("Question.TLabel", font=(family, 11))
        style.configure("Muted.TLabel", foreground="#667085")
        style.configure("Accent.TButton", padding=(12, 6))

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Генератор экзаменационных билетов",
                  style="Title.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        ttk.Label(frame, text="Группа:").grid(row=1, column=0, sticky="w", pady=4, padx=(0, 10))
        self.group_var = tk.StringVar()
        self.group_combo = ttk.Combobox(frame, textvariable=self.group_var, state="disabled")
        self.group_combo.grid(row=1, column=1, sticky="ew", pady=4)
        self.group_combo.bind("<<ComboboxSelected>>", self.on_group_selected)

        ttk.Label(frame, text="Студент:").grid(row=2, column=0, sticky="w", pady=4, padx=(0, 10))
        self.student_var = tk.StringVar()
        self.student_combo = ttk.Combobox(frame, textvariable=self.student_var, state="disabled")
        self.student_combo.grid(row=2, column=1, sticky="ew", pady=4)
        self.student_combo.bind("<<ComboboxSelected>>", self.on_student_selected)

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        self.generate_btn = ttk.Button(buttons, text="Сгенерировать билет", style="Accent.TButton",
                                       command=self.on_generate, state="disabled")
        self.generate_btn.pack(side="left")
        self.reload_btn = ttk.Button(buttons, text="Обновить данные", command=self.reload_sources)
        self.reload_btn.pack(side="right")

        self.status_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.status_var, style="Muted.TLabel",
                  wraplength=420, justify="left").grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 0))

    # ---------- загрузка данных ----------
    def reload_sources(self) -> None:
        """Читает students.xlsx и tickets.docx; при ошибке — сообщение, приложение работает дальше."""
        self.service = None
        self.selection = SelectionState()
        self._refresh_combos()

        errors: list[str] = []
        groups = {}
        tickets = {}
        try:
            groups = load_students(self.data_dir / STUDENTS_FILE)
        except StudentsFileError as exc:
            log.error("%s", exc)
            errors.append(str(exc))
        try:
            tickets = load_tickets(self.data_dir / TICKETS_FILE)
        except TicketsFileError as exc:
            log.error("%s", exc)
            errors.append(str(exc))

        journal = ResultsJournal(self.data_dir / RESULTS_FILE)
        try:
            journal.ensure_exists()
        except JournalError as exc:
            log.error("%s", exc)
            errors.append(str(exc))

        if errors:
            self.status_var.set("Данные не загружены. Исправьте файлы и нажмите «Обновить данные».")
            messagebox.showerror("Ошибка загрузки данных", "\n\n".join(errors), parent=self)
            return

        self.selection = SelectionState(groups)
        self.service = TicketService(tickets, journal)
        self._refresh_combos()
        total = sum(len(v) for v in groups.values())
        self.status_var.set(f"Групп: {len(groups)}, студентов: {total}, билетов: {len(tickets)}.")

    def _refresh_combos(self) -> None:
        self.group_combo["values"] = self.selection.group_names
        self.group_combo.configure(state="readonly" if self.selection.group_names else "disabled")
        self.group_var.set(self.selection.group or "")
        self._fill_students(self.selection.students_of(self.selection.group) if self.selection.group else [])

    def _fill_students(self, names: list[str]) -> None:
        self.student_combo["values"] = names
        self.student_var.set("")
        self.student_combo.configure(state="readonly" if names else "disabled")
        self._update_button()

    def _update_button(self) -> None:
        enabled = self.selection.can_generate and self.service is not None
        self.generate_btn.configure(state="normal" if enabled else "disabled")

    # ---------- обработчики ----------
    def on_group_selected(self, _event=None) -> None:
        names = self.selection.select_group(self.group_var.get())
        self._fill_students(names)
        if self.selection.group and not names:
            self.status_var.set(f"В группе {self.selection.group} нет студентов.")

    def on_student_selected(self, _event=None) -> None:
        self.selection.select_student(self.student_var.get())
        self._update_button()

    def on_generate(self) -> None:
        if not (self.selection.can_generate and self.service):
            return
        try:
            assignment = self.service.assign(self.selection.student)
        except JournalError as exc:
            log.error("%s", exc)
            messagebox.showerror("Ошибка журнала", str(exc), parent=self)
            return
        if not self._save_with_retry(assignment):
            return
        self.result_window = ResultWindow(self, assignment, on_close=self.on_result_closed)

    def _save_with_retry(self, assignment: Assignment) -> bool:
        """Сохраняет сразу после генерации; при блокировке файла предлагает повторить."""
        while True:
            try:
                self.service.save(assignment)
                return True
            except JournalLockedError as exc:
                log.warning("%s", exc)
                if not messagebox.askretrycancel("Журнал недоступен", str(exc), parent=self):
                    self.status_var.set("Билет не выдан: журнал не удалось сохранить.")
                    return False
            except JournalError as exc:
                log.error("%s", exc)
                messagebox.showerror("Ошибка журнала", str(exc), parent=self)
                return False

    def on_result_closed(self) -> None:
        """Возврат к выбору: группа остаётся, студент сбрасывается — готово к следующему."""
        self.result_window = None
        self.selection.reset_student()
        self.student_var.set("")
        self._update_button()
        self.student_combo.focus_set()

    def _on_unexpected_error(self, exc_type, exc, tb) -> None:
        log.exception("Непредвиденная ошибка", exc_info=(exc_type, exc, tb))
        messagebox.showerror("Ошибка", f"Непредвиденная ошибка: {exc}\nПодробности в журнале логов.",
                             parent=self)
