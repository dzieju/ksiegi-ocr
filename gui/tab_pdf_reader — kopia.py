import tkinter as tk
from tkinter import filedialog, ttk
from tools.pdf_parser import extract_pdf_data

class PDFReaderTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.create_widgets()

    def create_widgets(self):
        self.button = ttk.Button(self.frame, text="Wybierz plik PDF", command=self.load_pdf)
        self.button.pack(pady=10)

        self.tree = ttk.Treeview(self.frame, columns=("Lp", "Nr dowodu", "Opis"), show="headings")
        self.tree.heading("Lp", text="Lp")
        self.tree.heading("Nr dowodu", text="Nr dowodu księgowego")
        self.tree.heading("Opis", text="Opis zdarzenia")
        self.tree.pack(expand=True, fill='both')

    def load_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            print("Nie wybrano pliku.")
            return

        print(f"Wybrano plik: {file_path}")
        data = extract_pdf_data(file_path)
        print(f"Załadowano {len(data)} rekordów.")

        self.tree.delete(*self.tree.get_children())
        for row in data:
            self.tree.insert("", "end", values=row)
