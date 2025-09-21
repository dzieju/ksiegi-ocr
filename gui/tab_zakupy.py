import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import os
import pytesseract
from pdf2image import convert_from_path

# Configuration paths (same as in tab_ksiegi.py)
POPPLER_PATH = r"C:\poppler\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Crop coordinates for invoice numbers column (same as in tab_ksiegi.py)
CROP_LEFT, CROP_RIGHT = 503, 771
CROP_TOP, CROP_BOTTOM = 332, 2377

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


class ZakupiTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Initialize file path variable
        self.file_path_var = tk.StringVar()
        
        # Create UI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Title label
        title_label = ttk.Label(
            self, 
            text="Zakładka Zakupy - Odczyt numerów faktur", 
            font=("Arial", 12),
            foreground="blue"
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # PDF file selection
        ttk.Label(self, text="Plik PDF:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self, textvariable=self.file_path_var, width=60).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(self, text="Wybierz plik", command=self.wybierz_plik_pdf).grid(row=1, column=2, padx=5, pady=5)
        
        # Invoice reading button
        ttk.Button(self, text="Odczytaj numery faktur", command=self.odczytaj_numery_faktur).grid(row=2, column=1, pady=20)
        
        # Status label
        self.status_label = ttk.Label(self, text="Brak wybranego pliku", foreground="blue")
        self.status_label.grid(row=3, column=1, pady=5)
        
        # Text area for OCR results
        self.text_area = ScrolledText(self, wrap="word", width=100, height=25)
        self.text_area.grid(row=4, column=0, columnspan=3, padx=10, pady=10)
        
    def wybierz_plik_pdf(self):
        """Funkcja do wyboru pliku PDF"""
        filepath = filedialog.askopenfilename(
            title="Wybierz plik PDF", 
            filetypes=[("PDF files", "*.pdf")]
        )
        if filepath:
            self.file_path_var.set(filepath)
            self.status_label.config(text="Plik wybrany", foreground="green")
            
    def odczytaj_numery_faktur(self):
        """OCR funkcja odczytu numerów faktur z kolumny - oparta na run_column_ocr z tab_ksiegi.py"""
        filepath = self.file_path_var.get().strip()
        
        if not filepath:
            messagebox.showwarning("Brak pliku", "Proszę najpierw wybrać plik PDF.")
            return
            
        if not os.path.exists(filepath):
            messagebox.showwarning("Brak pliku", "Wybierz poprawny plik PDF.")
            return

        self.text_area.delete("1.0", tk.END)
        try:
            images = convert_from_path(filepath, dpi=300, poppler_path=POPPLER_PATH)
            all_lines = []
            for page_num, pil_img in enumerate(images, 1):
                crop = pil_img.crop((CROP_LEFT, CROP_TOP, CROP_RIGHT, CROP_BOTTOM))
                ocr_text = pytesseract.image_to_string(crop, lang='pol+eng')
                # Dodatkowo: linie osobno
                lines = [l.strip() for l in ocr_text.split('\n') if l.strip()]
                all_lines.extend([(page_num, l) for l in lines])

            # Wyświetl tylko linie OCR (bez nagłówków stron)
            self.text_area.insert(tk.END, "----- Linie OCR -----\n")
            for i, (page_num, line) in enumerate(all_lines, 1):
                self.text_area.insert(tk.END, f"strona {page_num}, linia {i}: {line}\n")

            # Zmniejsz szerokość okna wyników do 50%
            current_width = self.text_area.cget("width")
            new_width = int(current_width * 0.5)
            self.text_area.config(width=new_width)

            self.status_label.config(text=f"OCR z kolumny gotowy, {len(all_lines)} linii z {len(images)} stron", foreground="green")

        except Exception as e:
            messagebox.showerror("Błąd OCR z kolumny", str(e))
            self.status_label.config(text="Błąd OCR kolumny", foreground="red")