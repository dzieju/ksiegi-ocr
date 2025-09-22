import tkinter as tk
from tkinter import ttk
from gui.tab_pdf_reader import PDFReaderTab
from gui.tab_exchange_config import ExchangeConfigTab

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

        # Zakładka: Odczyt PDF
        pdf_tab = PDFReaderTab(notebook)
        notebook.add(pdf_tab, text="Odczyt PDF")

        # Zakładka: Konfiguracja poczty
        exchange_tab = ExchangeConfigTab(notebook)
        notebook.add(exchange_tab, text="Konfiguracja poczty")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
