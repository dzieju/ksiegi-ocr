import tkinter as tk
from tkinter import ttk
from gui.tab_exchange_config import ExchangeConfigTab
from gui.tab_mail_search import MailSearchTab

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Księga Przychodów i Rozchodów")
        self.geometry("900x600")

        # Styl
        style = ttk.Style(self)
        style.theme_use("clam")

        # Notebook (zakładki)
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        # Zakładka: Przeszukiwanie Poczty (pierwsza)
        mail_search_tab = MailSearchTab(notebook)
        notebook.add(mail_search_tab, text="Przeszukiwanie Poczty")

        # Zakładka: Konfiguracja poczty
        exchange_tab = ExchangeConfigTab(notebook)
        notebook.add(exchange_tab, text="Konfiguracja poczty")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
