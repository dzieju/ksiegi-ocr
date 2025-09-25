import tkinter as tk
from tkinter import ttk
from gui.tab_exchange_config import ExchangeConfigTab
from gui.tab_mail_search import MailSearchTab
from gui.tab_system import SystemTab
from gui.tab_zakupy import ZakupiTab
from tools import logger

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        logger.log("Inicjalizacja MainWindow")
        
        self.title("Księga Przychodów i Rozchodów")
        self.geometry("900x600")

        style = ttk.Style(self)
        style.theme_use("clam")
        logger.log("Konfiguracja stylu GUI zakończona")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)
        logger.log("Utworzenie głównego Notebook")

        # Zakładka: Przeszukiwanie Poczty (first tab)
        logger.log("Ładowanie zakładki: Przeszukiwanie Poczty")
        mail_search_tab = MailSearchTab(notebook)
        notebook.add(mail_search_tab, text="Przeszukiwanie Poczty")
        logger.log("Zakładka 'Przeszukiwanie Poczty' załadowana")

        # Zakładka: Konfiguracja poczty
        logger.log("Ładowanie zakładki: Konfiguracja poczty")
        exchange_tab = ExchangeConfigTab(notebook)
        notebook.add(exchange_tab, text="Konfiguracja poczty")
        logger.log("Zakładka 'Konfiguracja poczty' załadowana")

        # Zakładka: Zakupy
        logger.log("Ładowanie zakładki: Zakupy")
        zakupy_tab = ZakupiTab(notebook)
        notebook.add(zakupy_tab, text="Zakupy")
        logger.log("Zakładka 'Zakupy' załadowana")

        # Dodanie rozbudowanej zakładki System
        logger.log("Ładowanie zakładki: System")
        system_tab = SystemTab(notebook)
        notebook.add(system_tab, text="System")
        logger.log("Zakładka 'System' załadowana")
        
        logger.log("MainWindow - wszystkie komponenty załadowane pomyślnie")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()