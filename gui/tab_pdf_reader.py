import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import os
from pdf2image import convert_from_path
import pytesseract
import textwrap
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR"

class PDFReaderTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.file_path_var = tk.StringVar()

        ttk.Label(self, text="Plik PDF:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self, textvariable=self.file_path_var, width=60).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self, text="Wybierz plik", command=self.select_file).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(self, text="Wczytaj PDF (OCR)", command=self.load_pdf_ocr).grid(row=1, column=1, pady=10)

        self.text_area = ScrolledText(self, wrap="word", width=120, height=35)
        self.text_area.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

        self.status_label = ttk.Label(self, text="Brak danych", foreground="blue")
        self.status_label.grid(row=3, column=1, pady=5)

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")], title="Wybierz zeskanowany plik PDF")
        if path:
            self.file_path_var.set(path)
            self.status_label.config(text="Plik wybrany")

    def load_pdf_ocr(self):
        path = self.file_path_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("Brak pliku", "Wybierz poprawny plik PDF.")
            return

        try:
            extracted = self.extract_text_via_ocr(path)
            if not extracted:
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert(tk.END, "Nie znaleziono danych.")
                self.status_label.config(text="Brak danych")
                return

            self.text_area.delete("1.0", tk.END)
            header = f"{'Data':<10} | {'Lp':<4} | {'Dowód':<25} | {'Kontrahent':<35} | {'Opis':<30}"
            self.text_area.insert(tk.END, header + "\n")
            self.text_area.insert(tk.END, "-" * len(header) + "\n")

            for line in extracted:
                parts = line.split()
                if len(parts) < 4:
                    self.text_area.insert(tk.END, f"[Pominięto] {line}\n")
                    continue

                # Rozpoznanie daty
                data_match = re.match(r"\d{1,2}/\d{2}", parts[0])
                if not data_match:
                    self.text_area.insert(tk.END, f"[Brak daty] {line}\n")
                    continue

                data = parts[0]
                lp = parts[1]

                # Szukamy dowodu
                dowod = ""
                dowod_index = -1
                for i in range(2, len(parts)):
                    if re.search(r"\d+/\d+", parts[i]):
                        dowod = parts[i]
                        dowod_index = i
                        break

                if dowod_index == -1:
                    self.text_area.insert(tk.END, f"[Brak dowodu] {line}\n")
                    continue

                # Kontrahent i opis
                kontrahent = " ".join(parts[dowod_index + 1:-1]) if len(parts) > dowod_index + 2 else ""
                opis = parts[-1]

                # Zawijanie
                kontrahent_wrapped = textwrap.wrap(kontrahent, width=35)
                opis_wrapped = textwrap.wrap(opis, width=30)
                max_lines = max(len(kontrahent_wrapped), len(opis_wrapped))

                for i in range(max_lines):
                    d = data if i == 0 else ""
                    l = lp if i == 0 else ""
                    dw = dowod if i == 0 else ""
                    k = kontrahent_wrapped[i] if i < len(kontrahent_wrapped) else ""
                    o = opis_wrapped[i] if i < len(opis_wrapped) else ""
                    row = f"{d:<10} | {l:<4} | {dw:<25} | {k:<35} | {o:<30}"
                    self.text_area.insert(tk.END, row + "\n")

                self.text_area.insert(tk.END, "-" * len(header) + "\n")

            self.status_label.config(text=f"Znaleziono {len(extracted)} rekordów")

        except Exception as e:
            messagebox.showerror("Błąd OCR", str(e))
            self.status_label.config(text="Błąd OCR")

    def extract_text_via_ocr(self, path):
        results = []
        try:
            images = convert_from_path(path, dpi=300, poppler_path="C:\\poppler\\Library\\bin")
        except Exception as e:
            raise RuntimeError("Błąd konwersji PDF na obraz. Upewnij się, że Poppler jest poprawnie zainstalowany.") from e

        for img in images:
            text = pytesseract.image_to_string(img, lang='pol')
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                if line and self.is_valid_entry(line):
                    results.append(line)
        return results

    def is_valid_entry(self, line):
        return re.search(r"\d{1,2}/\d{2}", line) and "/" in line
