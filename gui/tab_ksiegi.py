import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import os
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
import re
import csv

POPPLER_PATH = r"C:\poppler\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TEMP_FILE = "temp_segmentacja_ocr.txt"

X_MIN = 100
X_MAX = 400

# Ustalony crop do kolumny numerów faktur (pełna kolumna na stronie PDF)
CROP_LEFT, CROP_RIGHT = 503, 771
CROP_TOP, CROP_BOTTOM = 332, 2377

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

class KsiegiTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.file_path_var = tk.StringVar()
        self.cells = []
        self.ocr_results = []
        self.image = None
        self.tk_image = None

        ttk.Label(scroll_frame, text="Plik PDF (księgi):").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(scroll_frame, textvariable=self.file_path_var, width=60).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(scroll_frame, text="Wybierz plik", command=self.select_file).grid(row=0, column=2, padx=5, pady=5)

        ttk.Button(scroll_frame, text="Segmentuj tabelę i OCR", command=self.process_pdf).grid(row=1, column=1, pady=10)
        ttk.Button(scroll_frame, text="Pokaż wszystkie komórki OCR", command=self.show_all_ocr).grid(row=1, column=2, pady=10)
        # NOWY PRZYCISK: OCR z kolumny (pełny crop, wszystkie strony PDF)
        ttk.Button(scroll_frame, text="OCR z kolumny (wszystkie strony)", command=self.run_column_ocr).grid(row=1, column=3, padx=5, pady=10)

        self.text_area = ScrolledText(scroll_frame, wrap="word", width=100, height=25)
        self.text_area.grid(row=2, column=0, columnspan=4, padx=10, pady=10)

        self.canvas = tk.Canvas(scroll_frame, width=1000, height=1400)
        self.canvas.grid(row=3, column=0, columnspan=4)

        self.status_label = ttk.Label(scroll_frame, text="Brak danych", foreground="blue")
        self.status_label.grid(row=4, column=1, pady=5)

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.file_path_var.set(path)
            self.status_label.config(text="Plik wybrany")

    def run_column_ocr(self):
        """
        Prosty OCR wszystkich stron kolumny z numerami faktur (pełny crop, bez segmentacji komórek, bez scalania).
        Automatycznie zapisuje rozpoznane numery faktur do pliku ksiegi.csv.
        """
        path = self.file_path_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("Brak pliku", "Wybierz poprawny plik PDF.")
            return

        self.text_area.delete("1.0", tk.END)
        try:
            images = convert_from_path(path, dpi=300, poppler_path=POPPLER_PATH)
            all_lines = []
            invoice_numbers = []  # Lista rozpoznanych numerów faktur
            
            for page_num, pil_img in enumerate(images, 1):
                crop = pil_img.crop((CROP_LEFT, CROP_TOP, CROP_RIGHT, CROP_BOTTOM))
                ocr_text = pytesseract.image_to_string(crop, lang='pol+eng')
                self.text_area.insert(tk.END, f"\n=== STRONA {page_num} ===\n")
                self.text_area.insert(tk.END, ocr_text)
                self.text_area.insert(tk.END, "\n")
                # Dodatkowo: linie osobno
                lines = [l.strip() for l in ocr_text.split('\n') if l.strip()]
                all_lines.extend([(page_num, l) for l in lines])

            self.text_area.insert(tk.END, "\n---- Linie OCR z wszystkich stron ----\n")
            for i, (page_num, line) in enumerate(all_lines, 1):
                self.text_area.insert(tk.END, f"strona {page_num}, linia {i}: {line}\n")

            # Filtruj rozpoznane numery faktur
            self.text_area.insert(tk.END, "\n---- Rozpoznane numery faktur ----\n")
            for page_num, line in all_lines:
                if self.contains_invoice_number(line):
                    invoice_numbers.append(line.strip())
                    self.text_area.insert(tk.END, f"FAKTURA: {line}\n")

            # Zapisz do pliku CSV
            csv_saved = False
            csv_path = ""
            if invoice_numbers:
                try:
                    csv_path = self.save_invoice_numbers_to_csv(invoice_numbers)
                    csv_saved = True
                    self.text_area.insert(tk.END, f"\n✓ Zapisano {len(invoice_numbers)} numerów faktur do pliku: {csv_path}\n")
                except Exception as csv_error:
                    self.text_area.insert(tk.END, f"\n✗ Błąd podczas zapisywania CSV: {str(csv_error)}\n")
            else:
                self.text_area.insert(tk.END, "\nBrak rozpoznanych numerów faktur do zapisania.\n")

            # Zaktualizuj status
            status_message = f"OCR z kolumny gotowy, {len(all_lines)} linii z {len(images)} stron, {len(invoice_numbers)} faktur rozpoznanych"
            if csv_saved:
                status_message += f" → zapisano do CSV"
            self.status_label.config(text=status_message, foreground="green" if csv_saved else "blue")

        except Exception as e:
            messagebox.showerror("Błąd OCR z kolumny", str(e))
            self.status_label.config(text="Błąd OCR kolumny")

    def process_pdf(self):
        path = self.file_path_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("Brak pliku", "Wybierz poprawny plik PDF.")
            return

        self.text_area.delete("1.0", tk.END)
        self.canvas.delete("all")
        self.cells.clear()
        self.ocr_results.clear()

        try:
            images = convert_from_path(path, dpi=400, poppler_path=POPPLER_PATH)
            pil_img = images[0]
            self.image = np.array(pil_img)
            self.cells = self.detect_table_cells(self.image)
            self.ocr_results = self.perform_ocr_on_cells(self.image, self.cells)
            self.display_image_with_boxes()

            if not self.ocr_results:
                self.text_area.insert(tk.END, "Nie znaleziono numerów faktur.")
                self.status_label.config(text="Brak wyników")
                return

            for x, y, text in self.ocr_results:
                self.text_area.insert(tk.END, f"x={x} y={y} → {text}\n")

            with open(TEMP_FILE, "w", encoding="utf-8") as f:
                for x, y, text in self.ocr_results:
                    f.write(f"x={x} y={y} → {text}\n")

            self.status_label.config(text=f"Znaleziono {len(self.ocr_results)} wpisów")

        except Exception as e:
            messagebox.showerror("Błąd segmentacji", str(e))
            self.status_label.config(text="Błąd")

    def detect_table_cells(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blur, 180, 255, cv2.THRESH_BINARY_INV)

        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)

        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)

        table_mask = cv2.add(vertical_lines, horizontal_lines)
        contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cells = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) > 1000]
        cells.sort(key=lambda b: (b[1], b[0]))
        return cells

    def perform_ocr_on_cells(self, image, cells):
        results = []
        for (x, y, w, h) in cells:
            roi = image[y:y+h, x:x+w]
            text = pytesseract.image_to_string(roi, lang='pol').strip()
            if len(text) < 5:
                continue
            if not (X_MIN <= x <= X_MAX):
                continue
            if self.contains_invoice_number(text):
                results.append((x, y, text))
        return results

    def contains_invoice_number(self, text):
        patterns = [
            r"\bF/\d{5}/\d{2}/\d{2}/M1\b",
            r"\b\d{5}/\d{2}/\d{4}/UP\b",
            r"\b\d{5}/\d{2}\b",
            r"\b\d{3}/\d{4}\b",
            r"\bF/M\d{2}/\d{7}/\d{2}/\d{2}\b",
            r"\b\d{2}/\d{2}/\d{4}\b",
            r"\b\d{1,2}/\d{2}/\d{4}\b"  # nowy wzorzec np. 1/08/2025
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False

    def save_invoice_numbers_to_csv(self, invoice_numbers):
        """
        Zapisuje rozpoznane numery faktur do pliku ksiegi.csv w folderze /Ksiegi
        """
        try:
            # Ścieżka do pliku CSV względem katalogu głównego projektu
            csv_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Ksiegi", "ksiegi.csv")
            
            # Upewnij się, że katalog istnieje
            os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
            
            # Zapisz do pliku CSV (nadpisuje poprzedni plik)
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Zapisz każdy numer faktury w osobnej kolumnie A
                for invoice_number in invoice_numbers:
                    writer.writerow([invoice_number])
            
            return csv_file_path
        except Exception as e:
            raise Exception(f"Błąd podczas zapisywania CSV: {str(e)}")

    def display_image_with_boxes(self):
        img_copy = self.image.copy()
        for (x, y, w, h) in self.cells:
            roi = self.image[y:y+h, x:x+w]
            text = pytesseract.image_to_string(roi, lang='pol').strip()
            if self.contains_invoice_number(text):
                color = (0, 0, 255)  # czerwony = trafienie
            elif X_MIN <= x <= X_MAX:
                color = (0, 255, 0)  # zielony = w kolumnie
            else:
                color = (180, 180, 180)  # szary = poza zakresem
            cv2.rectangle(img_copy, (x, y), (x+w, y+h), color, 2)

        img_rgb = cv2.cvtColor(img_copy, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_pil = img_pil.resize((1000, 1400)) if img_pil.width > 1000 or img_pil.height > 1400 else img_pil
        self.tk_image = ImageTk.PhotoImage(img_pil)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

    def show_all_ocr(self):
        self.text_area.delete("1.0", tk.END)
        if not self.cells or self.image is None:
            self.text_area.insert(tk.END, "Brak wysegmentowanych komórek do wyświetlenia.\n")
            return

        for (x, y, w, h) in self.cells:
            roi = self.image[y:y+h, x:x+w]
            text = pytesseract.image_to_string(roi, lang='pol').strip()
            self.text_area.insert(tk.END, f"x={x} y={y} → {text}\n")