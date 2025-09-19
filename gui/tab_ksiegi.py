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

        # NOWY PRZYCISK: Odczytaj folder
        ttk.Button(scroll_frame, text="Odczytaj folder", command=self.select_folder_and_generate_csv).grid(row=2, column=1, pady=10)
        
        # NOWY PRZYCISK: Porównaj CSV
        ttk.Button(scroll_frame, text="Porównaj", command=self.compare_csv_files).grid(row=2, column=2, pady=10)

        self.text_area = ScrolledText(scroll_frame, wrap="word", width=100, height=25)
        self.text_area.grid(row=3, column=0, columnspan=4, padx=10, pady=10)

        self.canvas = tk.Canvas(scroll_frame, width=1000, height=1400)
        self.canvas.grid(row=4, column=0, columnspan=4)

        self.status_label = ttk.Label(scroll_frame, text="Brak danych", foreground="blue")
        self.status_label.grid(row=5, column=1, pady=5)

    def _ensure_ksiegi_folder(self):
        """
        Tworzy folder 'Ksiegi' w głównym katalogu aplikacji, jeśli nie istnieje.
        Zwraca ścieżkę do folderu 'Ksiegi'.
        """
        # Pobierz katalog główny aplikacji (tam gdzie znajduje się wyniki.csv)
        main_dir = os.path.dirname(os.path.abspath("wyniki.csv"))
        ksiegi_folder = os.path.join(main_dir, "Ksiegi")
        
        # Utwórz folder, jeśli nie istnieje
        os.makedirs(ksiegi_folder, exist_ok=True)
        
        return ksiegi_folder

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.file_path_var.set(path)
            self.status_label.config(text="Plik wybrany")

    def run_column_ocr(self):
        """
        Prosty OCR wszystkich stron kolumny z numerami faktur (pełny crop, bez segmentacji komórek, bez scalania).
        Zapisuje wyniki do pliku CSV z kolumnami: strona, linia, tekst.
        """
        path = self.file_path_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("Brak pliku", "Wybierz poprawny plik PDF.")
            return

        self.text_area.delete("1.0", tk.END)
        try:
            images = convert_from_path(path, dpi=300, poppler_path=POPPLER_PATH)
            all_lines = []
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

            # Zapisz wyniki do pliku wyniki.csv w folderze Ksiegi
            try:
                ksiegi_folder = self._ensure_ksiegi_folder()
                csv_path = os.path.join(ksiegi_folder, "wyniki.csv")
                with open(csv_path, "w", encoding="utf-8", newline='') as csvfile:
                    writer = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
                    # Zapisz nagłówek
                    writer.writerow(["strona", "linia", "numer faktury"])
                    # Zapisz dane
                    for i, (page_num, line) in enumerate(all_lines, 1):
                        writer.writerow([page_num, i, line])
            except Exception as e:
                messagebox.showerror("Błąd zapisu pliku CSV", f"Nie udało się zapisać pliku wyniki.csv: {str(e)}")
                self.status_label.config(text="Błąd zapisu pliku CSV")
                return

            self.status_label.config(text=f"OCR z kolumny gotowy, {len(all_lines)} linii z {len(images)} stron, zapisano do Ksiegi/wyniki.csv")

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

    def select_folder_and_generate_csv(self):
        """
        Wybiera folder i generuje plik CSV z nazwami tylko widocznych plików PDF (bez rozszerzeń)
        znajdujących się w tym folderze. Pomija ukryte pliki oraz pliki o innych rozszerzeniach.
        Plik CSV ma nazwę identyczną jak folder i jest zapisywany w folderze "Ksiegi".
        """
        folder_path = filedialog.askdirectory(title="Wybierz folder do odczytu")
        if not folder_path:
            return
        
        try:
            # Pobierz nazwę folderu (bez pełnej ścieżki) - normalizuj ścieżkę dla kompatybilności z różnymi systemami
            folder_path = os.path.normpath(folder_path)
            folder_name = os.path.basename(folder_path)
            csv_filename = f"{folder_name}.csv"
            
            # Zapisz CSV w folderze Ksiegi
            ksiegi_folder = self._ensure_ksiegi_folder()
            csv_path = os.path.join(ksiegi_folder, csv_filename)
            
            # Odczytaj tylko widoczne pliki PDF z folderu (bez podfolderów)
            filenames_without_extension = []
            if os.path.exists(folder_path):
                for item in os.listdir(folder_path):
                    item_path = os.path.join(folder_path, item)
                    # Sprawdź czy to plik (nie folder)
                    if os.path.isfile(item_path):
                        # Pomijaj ukryte pliki (zaczynające się od kropki)
                        if item.startswith('.'):
                            continue
                        # Sprawdź czy plik ma rozszerzenie .pdf (case-insensitive)
                        if item.lower().endswith('.pdf'):
                            # Pobierz nazwę bez rozszerzenia
                            name_without_ext = os.path.splitext(item)[0]
                            filenames_without_extension.append(name_without_ext)
            
            # Zapisz do pliku CSV
            with open(csv_path, 'w', encoding='utf-8', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for filename in filenames_without_extension:
                    writer.writerow([filename])
            
            # Pokaż wyniki w obszarze tekstowym
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, f"Odczytano folder: {folder_path}\n")
            self.text_area.insert(tk.END, f"Znaleziono {len(filenames_without_extension)} plików PDF (pomijając ukryte pliki i inne rozszerzenia):\n\n")
            
            for filename in filenames_without_extension:
                self.text_area.insert(tk.END, f"{filename}\n")
            
            self.text_area.insert(tk.END, f"\nPlik CSV zapisany jako: {csv_path}")
            
            # Aktualizuj status
            self.status_label.config(text=f"Zapisano {len(filenames_without_extension)} plików PDF do {csv_filename} w folderze Ksiegi")
            
            messagebox.showinfo("Sukces", f"Pomyślnie zapisano {len(filenames_without_extension)} plików PDF do {csv_filename}\nLokalizacja: {csv_path}")
            
        except Exception as e:
            error_msg = f"Błąd podczas przetwarzania folderu: {str(e)}"
            messagebox.showerror("Błąd", error_msg)
            self.status_label.config(text="Błąd przetwarzania folderu")
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, error_msg)

    def compare_csv_files(self):
        """
        Porównuje dwa pliki CSV i wyświetla różnice pomiędzy nimi.
        Użytkownik może wybrać dwa pliki CSV przez osobne przyciski PLIK1 i PLIK2.
        """
        # Utwórz nowe okno dialogowe dla porównania
        compare_window = tk.Toplevel(self)
        compare_window.title("Porównaj pliki CSV")
        compare_window.geometry("600x500")
        compare_window.transient(self)
        compare_window.grab_set()
        
        # Zmienne do przechowywania ścieżek plików
        file1_var = tk.StringVar()
        file2_var = tk.StringVar()
        
        # Interfejs użytkownika
        ttk.Label(compare_window, text="Porównanie plików CSV", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=3, pady=10)
        
        # PLIK1
        ttk.Label(compare_window, text="PLIK1:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(compare_window, textvariable=file1_var, width=50, state="readonly").grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(compare_window, text="PLIK1", command=lambda: self._select_csv_file(file1_var, "Wybierz pierwszy plik CSV")).grid(row=1, column=2, padx=5, pady=5)
        
        # PLIK2
        ttk.Label(compare_window, text="PLIK2:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(compare_window, textvariable=file2_var, width=50, state="readonly").grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(compare_window, text="PLIK2", command=lambda: self._select_csv_file(file2_var, "Wybierz drugi plik CSV")).grid(row=2, column=2, padx=5, pady=5)
        
        # Przycisk porównaj
        ttk.Button(compare_window, text="Porównaj pliki", command=lambda: self._perform_csv_comparison(file1_var.get(), file2_var.get(), compare_window)).grid(row=3, column=1, pady=10)
        
        # Obszar wyników
        result_frame = ttk.Frame(compare_window)
        result_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        
        compare_window.grid_rowconfigure(4, weight=1)
        compare_window.grid_columnconfigure(1, weight=1)
        
        result_text = ScrolledText(result_frame, wrap="word", width=70, height=20)
        result_text.pack(fill="both", expand=True)
        
        # Przechowaj referencję do obszaru tekstowego
        compare_window.result_text = result_text

    def _select_csv_file(self, file_var, title):
        """
        Pomocnicza funkcja do wyboru pliku CSV.
        """
        file_path = filedialog.askopenfilename(
            title=title,
            filetypes=[("CSV files", "*.csv"), ("Wszystkie pliki", "*.*")]
        )
        if file_path:
            file_var.set(file_path)

    def _perform_csv_comparison(self, file1_path, file2_path, window):
        """
        Wykonuje porównanie dwóch plików CSV i wyświetla wyniki.
        """
        if not file1_path or not file2_path:
            messagebox.showwarning("Błąd", "Proszę wybrać oba pliki CSV.")
            return
        
        if not os.path.exists(file1_path) or not os.path.exists(file2_path):
            messagebox.showerror("Błąd", "Jeden lub oba wybrane pliki nie istnieją.")
            return
        
        try:
            # Wykryj separatory dla każdego pliku
            delimiter1 = self._detect_csv_delimiter(file1_path)
            delimiter2 = self._detect_csv_delimiter(file2_path)
            
            # Wczytaj dane z plików CSV
            data1 = self._read_csv_file(file1_path)
            data2 = self._read_csv_file(file2_path)
            
            # Wykonaj porównanie
            only_in_file1 = []
            only_in_file2 = []
            
            for row in data1:
                if row not in data2:
                    only_in_file1.append(row)
            
            for row in data2:
                if row not in data1:
                    only_in_file2.append(row)
            
            # Wyświetl wyniki
            result_text = window.result_text
            result_text.delete("1.0", tk.END)
            
            # Informacje ogólne
            result_text.insert(tk.END, "=== PORÓWNANIE PLIKÓW CSV ===\n\n")
            
            # Informacje o wykrytych separatorach
            delimiter1_name = {',' : 'przecinek', ';' : 'średnik', '\t' : 'tabulacja', '|' : 'pionowa kreska', ':' : 'dwukropek'}.get(delimiter1, repr(delimiter1))
            delimiter2_name = {',' : 'przecinek', ';' : 'średnik', '\t' : 'tabulacja', '|' : 'pionowa kreska', ':' : 'dwukropek'}.get(delimiter2, repr(delimiter2))
            
            result_text.insert(tk.END, f"PLIK1: {os.path.basename(file1_path)} ({len(data1)} wierszy, separator: {delimiter1_name})\n")
            result_text.insert(tk.END, f"PLIK2: {os.path.basename(file2_path)} ({len(data2)} wierszy, separator: {delimiter2_name})\n\n")
            
            # Wiersze tylko w PLIK1
            result_text.insert(tk.END, f"=== WIERSZE TYLKO W PLIK1 ({len(only_in_file1)} wierszy) ===\n")
            if only_in_file1:
                for i, row in enumerate(only_in_file1, 1):
                    result_text.insert(tk.END, f"{i}. {', '.join(row)}\n")
            else:
                result_text.insert(tk.END, "(Brak różnic)\n")
            
            result_text.insert(tk.END, "\n")
            
            # Wiersze tylko w PLIK2
            result_text.insert(tk.END, f"=== WIERSZE TYLKO W PLIK2 ({len(only_in_file2)} wierszy) ===\n")
            if only_in_file2:
                for i, row in enumerate(only_in_file2, 1):
                    result_text.insert(tk.END, f"{i}. {', '.join(row)}\n")
            else:
                result_text.insert(tk.END, "(Brak różnic)\n")
            
            result_text.insert(tk.END, "\n")
            
            # Podsumowanie
            total_differences = len(only_in_file1) + len(only_in_file2)
            if total_differences == 0:
                result_text.insert(tk.END, "=== PODSUMOWANIE ===\n")
                result_text.insert(tk.END, "Pliki są identyczne - nie znaleziono różnic.\n")
            else:
                result_text.insert(tk.END, "=== PODSUMOWANIE ===\n")
                result_text.insert(tk.END, f"Znaleziono łącznie {total_differences} różnic:\n")
                result_text.insert(tk.END, f"- {len(only_in_file1)} wierszy tylko w PLIK1\n")
                result_text.insert(tk.END, f"- {len(only_in_file2)} wierszy tylko w PLIK2\n")
            
            # Przewiń na górę
            result_text.see("1.0")
            
            messagebox.showinfo("Sukces", f"Porównanie ukończone. Znaleziono {total_differences} różnic.")
            
        except Exception as e:
            error_msg = f"Błąd podczas porównywania plików: {str(e)}"
            messagebox.showerror("Błąd", error_msg)
            if hasattr(window, 'result_text'):
                window.result_text.delete("1.0", tk.END)
                window.result_text.insert(tk.END, error_msg)

    def _detect_csv_delimiter(self, file_path):
        """
        Wykrywa separator CSV używając kilku metod w kolejności priorytetu.
        Zwraca wykryty delimiter lub None jeśli się nie uda.
        """
        # Popularne separatory w kolejności preferencji
        common_delimiters = [';', ',', '\t', '|', ':']
        
        try:
            with open(file_path, 'r', encoding='utf-8', newline='') as csvfile:
                # Sprawdź czy plik nie jest pusty
                content = csvfile.read()
                if not content.strip():
                    raise ValueError("Plik CSV jest pusty")
                
                csvfile.seek(0)
                
                # Odczytaj pierwsze kilka linii do analizy
                sample_lines = []
                for i in range(5):  # Analiza maksymalnie 5 pierwszych linii
                    line = csvfile.readline()
                    if not line:
                        break
                    sample_lines.append(line.strip())
                
                if not sample_lines:
                    raise ValueError("Plik nie zawiera czytelnych linii")
                
                # Metoda 1: Użyj csv.Sniffer (najnowocześniejszy sposób)
                csvfile.seek(0)
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                try:
                    sniffer = csv.Sniffer()
                    detected = sniffer.sniff(sample).delimiter
                    if detected in common_delimiters:
                        # Zweryfikuj wykryty delimiter poprzez próbę odczytu
                        reader = csv.reader(csvfile, delimiter=detected)
                        first_row = next(reader, None)
                        if first_row and len(first_row) > 1:
                            csvfile.seek(0)
                            return detected
                except Exception:
                    pass  # Sniffer zawiódł, przejdź do następnej metody
                
                # Metoda 2: Zlicz występowania każdego separatora
                delimiter_counts = {}
                for delimiter in common_delimiters:
                    count = 0
                    for line in sample_lines:
                        count += line.count(delimiter)
                    delimiter_counts[delimiter] = count
                
                # Znajdź najczęściej występujący separator (z przynajmniej jednym wystąpieniem)
                best_delimiter = None
                max_count = 0
                
                for delimiter in common_delimiters:  # Zachowaj kolejność preferencji
                    count = delimiter_counts[delimiter]
                    if count > max_count:
                        max_count = count
                        best_delimiter = delimiter
                
                if best_delimiter and max_count > 0:
                    # Zweryfikuj poprzez próbę odczytu
                    try:
                        csvfile.seek(0)
                        reader = csv.reader(csvfile, delimiter=best_delimiter)
                        rows = list(reader)
                        if rows and any(len(row) > 1 for row in rows):
                            csvfile.seek(0)
                            return best_delimiter
                    except Exception:
                        pass
                
                # Metoda 3: Sprawdź konsystencję liczby pól dla każdego delimitera
                for delimiter in common_delimiters:
                    try:
                        csvfile.seek(0)
                        reader = csv.reader(csvfile, delimiter=delimiter)
                        rows = list(reader)
                        if not rows:
                            continue
                        
                        # Sprawdź czy liczba pól jest spójna
                        field_counts = [len(row) for row in rows if row]
                        if not field_counts:
                            continue
                        
                        # Znajdź najczęstszą liczbę pól
                        most_common_count = max(set(field_counts), key=field_counts.count)
                        if most_common_count > 1:  # Musi być więcej niż jedno pole
                            # Sprawdź spójność (co najmniej 80% wierszy ma tę samą liczbę pól)
                            consistency = field_counts.count(most_common_count) / len(field_counts)
                            if consistency >= 0.8:
                                csvfile.seek(0)
                                return delimiter
                    except Exception:
                        continue
                
                # Jeśli wszystko zawiodło, sprawdź czy to może być plik z jedną kolumną
                # (każda linia to jedna wartość)
                if len(sample_lines) > 0 and all(delimiter not in line for line in sample_lines for delimiter in common_delimiters):
                    # To może być plik z jedną kolumną na linię - użyj przecinka jako separatora zastępczego
                    csvfile.seek(0)
                    return ','
                
                return None  # Nie udało się wykryć separatora
                
        except Exception as e:
            raise ValueError(f"Błąd podczas analizy pliku CSV: {str(e)}")

    def _read_csv_file(self, file_path):
        """
        Pomocnicza funkcja do wczytywania pliku CSV z automatycznym wykrywaniem separatora.
        Zwraca listę wierszy jako tuple.
        """
        rows = []
        
        try:
            # Wykryj separator
            delimiter = self._detect_csv_delimiter(file_path)
            if delimiter is None:
                raise ValueError(
                    "Nie udało się automatycznie wykryć separatora w pliku CSV.\n"
                    "Sprawdź czy plik zawiera poprawnie sformatowane dane CSV "
                    "z jednym z popularnych separatorów: ; , Tab |"
                )
            
            # Wczytaj plik z wykrytym separatorem
            with open(file_path, 'r', encoding='utf-8', newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter=delimiter)
                for row in reader:
                    # Ignoruj puste wiersze
                    if row and any(cell.strip() for cell in row):
                        # Konwertuj na tuple dla porównania
                        rows.append(tuple(cell.strip() for cell in row))
            
            if not rows:
                raise ValueError("Plik CSV nie zawiera żadnych danych do przetworzenia")
            
            return rows
            
        except Exception as e:
            # Przekaż błąd wyżej z dodatkowym kontekstem
            raise ValueError(f"Błąd odczytu pliku CSV '{os.path.basename(file_path)}': {str(e)}")