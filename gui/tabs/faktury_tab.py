import tkinter as tk
from tkinter import filedialog, messagebox
import pdfplumber

class FakturyTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.btn_wczytaj = tk.Button(self, text="Wczytaj plik PDF", command=self.wczytaj_pdf)
        self.btn_wczytaj.pack(pady=10)

        self.text_output = tk.Text(self, width=100, height=25)
        self.text_output.pack(padx=10, pady=10)

    def wczytaj_pdf(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not filepath:
            return

        wynik_linii = []

        try:
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table and len(table) > 3:
                        headers = table[0]
                        print(f"Strona {page.page_number} — nagłówki: {headers}")  # DEBUG

                        try:
                            # Wyszukaj indeksy kolumn po nazwach
                            idx_lp = next(i for i, h in enumerate(headers) if h and "l.p" in h.lower())
                            idx_nr = next(i for i, h in enumerate(headers) if h and "nr dowodu księgowego" in h.lower())
                            idx_koszty = next(i for i, h in enumerate(headers) if h and "koszty prowadzenia działalności" in h.lower())

                            for row in table[2:]:  # Pomijamy dwa pierwsze wiersze
                                if len(row) <= max(idx_lp, idx_nr, idx_koszty):
                                    continue
                                lp = row[idx_lp]
                                nr_dowodu = row[idx_nr]
                                koszty = row[idx_koszty]
                                if lp and nr_dowodu and koszty:
                                    wynik_linii.append((lp, nr_dowodu, koszty))
                        except StopIteration:
                            continue

            self.text_output.delete("1.0", tk.END)
            if wynik_linii:
                self.text_output.insert(tk.END, f"{'L.p.':<10} {'Nr dowodu księgowego':<30} {'Koszty działalności':<40}\n")
                self.text_output.insert(tk.END, "-" * 85 + "\n")
                for lp, nr_dowodu, koszty in wynik_linii:
                    self.text_output.insert(tk.END, f"{lp:<10} {nr_dowodu:<30} {koszty:<40}\n")
            else:
                self.text_output.insert(tk.END, "Nie znaleziono danych w wymaganych kolumnach.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się odczytać pliku:\n{e}")
