import tkinter as tk
from tkinter import ttk
from gui.tab_exchange_config import ExchangeConfigTab
from gui.tab_mail_search import MailSearchTab
from gui.tab_system import SystemTab
from gui.tab_zakupy import ZakupiTab

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Księga Przychodów i Rozchodów")
        # Default geometry - can be overridden by caller
        self.geometry("900x600")

        style = ttk.Style(self)
        style.theme_use("clam")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        # Zakładka: Przeszukiwanie Poczty (first tab)
        mail_search_tab = MailSearchTab(notebook)
        notebook.add(mail_search_tab, text="Przeszukiwanie Poczty")

        # Zakładka: Konfiguracja poczty
        exchange_tab = ExchangeConfigTab(notebook)
        notebook.add(exchange_tab, text="Konfiguracja poczty")

        # Zakładka: Zakupy
        zakupy_tab = ZakupiTab(notebook)
        notebook.add(zakupy_tab, text="Zakupy")

        # Dodanie rozbudowanej zakładki System
        system_tab = SystemTab(notebook)
        notebook.add(system_tab, text="System")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()