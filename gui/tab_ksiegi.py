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

POPPLER_PATH = r"C:\poppler\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TEMP_FILE = "temp_segmentacja_ocr.txt"

X_MIN = 100
X_MAX = 400

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

        self.text_area = ScrolledText(scroll_frame, wrap="word", width=100, height=25)
        self.text_area.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

        self.canvas = tk.Canvas(scroll_frame, width=1000, height=1400)
        self.canvas.grid(row=3, column=0, columnspan=3)

        self.status_label = ttk.Label(scroll_frame, text="Brak danych", foreground="blue")
        self.status_label.grid(row=4, column=1, pady=5)

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.file_path_var.set(path)
            self.status_label.config(text="Plik wybrany")

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
        pil_img = Image.fromarray(img_rgb)
        
        # Scale for canvas display  
        canvas_width = 1000
        canvas_height = 1400
        pil_img_resized = pil_img.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
        
        self.tk_image = ImageTk.PhotoImage(pil_img_resized)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def show_all_ocr(self):
        """Show OCR results from all detected cells, not just invoice numbers"""
        path = self.file_path_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("Brak pliku", "Wybierz poprawny plik PDF.")
            return

        self.text_area.delete("1.0", tk.END)
        
        try:
            images = convert_from_path(path, dpi=400, poppler_path=POPPLER_PATH)
            pil_img = images[0]
            self.image = np.array(pil_img)
            self.cells = self.detect_table_cells(self.image)
            
            # Perform OCR on all cells, not just invoice numbers
            all_results = []
            for i, (x, y, w, h) in enumerate(self.cells):
                roi = self.image[y:y+h, x:x+w]
                text = pytesseract.image_to_string(roi, lang='pol').strip()
                
                # Show OCR confidence and other details
                data = pytesseract.image_to_data(roi, lang='pol', output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                if len(text) >= 2:  # Lower threshold for showing all results
                    is_invoice = self.contains_invoice_number(text)
                    marker = "✓" if is_invoice else "✗"
                    all_results.append((marker, x, y, w, h, avg_confidence, text))
            
            # Sort by y-coordinate (top to bottom), then x-coordinate (left to right)
            all_results.sort(key=lambda item: (item[2], item[1]))
            
            # Display results
            if all_results:
                self.text_area.insert(tk.END, "Wyniki OCR ze wszystkich komórek:\n")
                self.text_area.insert(tk.END, "=" * 80 + "\n")
                
                for marker, x, y, w, h, conf, text in all_results:
                    self.text_area.insert(tk.END, f"{marker}\t{x}\t{y}\t{w}\t{h}\t{conf:.0f}\t{text}\n")
                
                # Save to temp file for debugging
                with open("temp_ocr_table.txt", "w", encoding="utf-8") as f:
                    for marker, x, y, w, h, conf, text in all_results:
                        f.write(f"{marker}\t{x}\t{y}\t{w}\t{h}\t{conf:.0f}\t|{text}\n")
                
                self.status_label.config(text=f"Znaleziono {len(all_results)} komórek z tekstem")
            else:
                self.text_area.insert(tk.END, "Nie znaleziono żadnych komórek z tekstem.")
                self.status_label.config(text="Brak wyników")
                
        except Exception as e:
            messagebox.showerror("Błąd OCR", str(e))
            self.status_label.config(text="Błąd")