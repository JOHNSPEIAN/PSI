"""Адаптер порта Dialogs на стандартные окна сообщений Tkinter."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox


class TkDialogs:
    def __init__(self, parent: tk.Misc):
        self._parent = parent

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message, parent=self._parent)

    def ask_retry(self, title: str, message: str) -> bool:
        return bool(messagebox.askretrycancel(title, message, parent=self._parent))
