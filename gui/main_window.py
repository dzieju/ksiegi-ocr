import tkinter as tk
from tkinter import ttk
from gui.tab_pdf_reader import PDFReaderTab
from gui.tab_exchange_config import ExchangeConfigTab
from gui.tab_invoice_search import InvoiceSearchTab
from gui.tab_ksiegi import KsiegiTab
from gui.tab_system import SystemTab
from gui.tab_zakupy import ZakupiTab

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Księga Przychodów i Rozchodów")
        self.geometry("900x600")

        style = ttk.Style(self)
        style.theme_use("clam")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        pdf_tab = PDFReaderTab(notebook)
        notebook.add(pdf_tab, text="Odczyt PDF")

        exchange_tab = ExchangeConfigTab(notebook)
        notebook.add(exchange_tab, text="Konfiguracja poczty")

        invoice_tab = InvoiceSearchTab(notebook)
        notebook.add(invoice_tab, text="Wyszukiwanie NIP")

        ksiegi_tab = KsiegiTab(notebook)
        notebook.add(ksiegi_tab, text="Księgi")

        zakupy_tab = ZakupiTab(notebook)
        notebook.add(zakupy_tab, text="Zakupy")

        # Dodanie rozbudowanej zakładki System
        system_tab = SystemTab(notebook)
        notebook.add(system_tab, text="System")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()