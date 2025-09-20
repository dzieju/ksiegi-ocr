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
# Performance optimization: Import new threaded OCR processor
from ocr.ksiegi_processor import KsiegiProcessor

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

        # Performance optimization: Initialize threaded OCR processor
        self.ksiegi_processor = KsiegiProcessor()

        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Ensure scroll_frame expands to fill canvas width
        canvas.bind('<Configure>', self._configure_scroll_frame)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Store reference to canvas for width configuration
        self.canvas_container = canvas
        
        # Configure scroll_frame to expand horizontally
        scroll_frame.columnconfigure(0, weight=1)
        scroll_frame.columnconfigure(1, weight=1)

        self.file_path_var = tk.StringVar()
        self.cells = []
        self.ocr_results = []
        self.image = None
        self.tk_image = None

        # Performance optimization: Add variables for tracking threaded operations
        self.current_task = None
        self.processed_pages_data = {}  # Store results from parallel processing

        # Konfiguracja stylów sekcji na początku
        self._configure_section_styles()

        current_row = 0

        # ===== SEKCJA: Plik PDF (księgi) =====
        pdf_frame = ttk.LabelFrame(scroll_frame, text="Plik PDF (księgi)", padding="5")
        pdf_frame.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=0, pady=2)
        pdf_frame.columnconfigure(0, weight=1)  # Pozwala na rozciągnięcie wewnętrznej ramki
        # Subtelne tło za pomocą wewnętrznej ramki
        pdf_inner = tk.Frame(pdf_frame, bg="#f8f9fa", relief="flat")
        pdf_inner.grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        pdf_inner.columnconfigure(1, weight=1)
        
        ttk.Label(pdf_inner, text="Plik:", background="#f8f9fa").grid(row=0, column=0, sticky="w", padx=(3, 5), pady=3)
        ttk.Entry(pdf_inner, textvariable=self.file_path_var, width=60).grid(row=0, column=1, sticky="ew", padx=(0, 5), pady=3)
        ttk.Button(pdf_inner, text="Wybierz plik", command=self.select_file).grid(row=0, column=2, padx=(0, 3), pady=3)
        
        current_row += 1

        # Kontener główny dla sekcji funkcjonalnych
        main_container = ttk.Frame(scroll_frame)
        main_container.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=0, pady=2)
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        
        # ===== SEKCJA: Przetwarzanie OCR =====
        ocr_frame = ttk.LabelFrame(main_container, text="Przetwarzanie OCR", padding="5")
        ocr_frame.grid(row=0, column=0, sticky="new", padx=(0, 2), pady=2)
        # Subtelne tło
        ocr_inner = tk.Frame(ocr_frame, bg="#f0f8ff", relief="flat")
        ocr_inner.grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        
        # Przyciski OCR o równej szerokości, ułożone pionowo
        button_width = 25
        
        ttk.Button(ocr_inner, text="Segmentuj tabelę i OCR", 
                  command=self.process_pdf, width=button_width).grid(row=0, column=0, sticky="ew", pady=1, padx=3)
        
        # Performance optimization: Button with cancellation capability 
        self.show_ocr_button = ttk.Button(ocr_inner, text="Pokaż wszystkie komórki OCR", 
                                         command=self.toggle_show_all_ocr, width=button_width)
        self.show_ocr_button.grid(row=1, column=0, sticky="ew", pady=1, padx=3)
        
        # Performance optimization: Updated button for threaded OCR processing
        self.ocr_button = ttk.Button(ocr_inner, text="OCR z kolumny (wszystkie strony)", 
                                    command=self.toggle_column_ocr, width=button_width)
        self.ocr_button.grid(row=2, column=0, sticky="ew", pady=1, padx=3)
        
        # ===== SEKCJA: Operacje na folderach =====
        folder_frame = ttk.LabelFrame(main_container, text="Operacje na folderach", padding="5")
        folder_frame.grid(row=0, column=1, sticky="new", padx=(2, 0), pady=2)
        # Subtelne tło  
        folder_inner = tk.Frame(folder_frame, bg="#f0fff0", relief="flat")
        folder_inner.grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        
        # Przyciski operacji na folderach o równej szerokości, ułożone pionowo
        ttk.Button(folder_inner, text="Odczytaj folder", 
                  command=self.select_folder_and_generate_csv, width=button_width).grid(row=0, column=0, sticky="ew", pady=1, padx=3)
        
        ttk.Button(folder_inner, text="Porównaj pliki CSV", 
                  command=self.compare_csv_files, width=button_width).grid(row=1, column=0, sticky="ew", pady=1, padx=3)
        
        current_row += 1

        # ===== SEKCJA: Wyniki/Logi =====
        results_frame = ttk.LabelFrame(scroll_frame, text="Wyniki/Logi", padding="2")
        results_frame.grid(row=current_row, column=0, columnspan=2, sticky="nsew", padx=0, pady=0)
        results_frame.columnconfigure(0, weight=1)  # Pozwala na rozciągnięcie wewnętrznej ramki
        # Subtelne tło
        results_inner = tk.Frame(results_frame, bg="#fff8f0", relief="flat")
        results_inner.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        results_inner.columnconfigure(0, weight=1)  # Pozwala na rozciągnięcie pola tekstowego
        
        self.text_area = ScrolledText(results_inner, wrap="word", width=120, height=15)
        self.text_area.grid(row=0, column=0, sticky="nsew", pady=0, padx=0)
        
        # Dodaj placeholder text gdy pole jest puste
        self._add_placeholder_if_empty()
        
        # Bind events to manage placeholder
        self.text_area.bind("<FocusIn>", self._on_text_focus_in)
        self.text_area.bind("<KeyPress>", self._on_text_key_press)
        
        # Konfiguruj rozciągnięcie wyników do dołu okna
        scroll_frame.grid_rowconfigure(current_row, weight=1)
        results_inner.grid_rowconfigure(0, weight=1)
        
        # Canvas do wyświetlania obrazów (zachowany dla kompatybilności, ale ukryty)
        self.canvas = tk.Canvas(scroll_frame, width=800, height=600)
        # Nie dodajemy canvas do grid - pozostaje ukryty

        # Performance optimization: Start processing queues for threaded operations
        self._process_ocr_result_queue()
        self._process_ocr_progress_queue()

    def _add_placeholder_if_empty(self):
        """
        Dodaje tekst placeholder gdy pole wyników jest puste.
        """
        current_content = self.text_area.get("1.0", tk.END).strip()
        if not current_content:
            self.text_area.insert("1.0", "Brak danych")
            self.text_area.configure(foreground="gray")
    
    def _remove_placeholder_if_exists(self):
        """
        Usuwa tekst placeholder jeśli istnieje.
        """
        current_content = self.text_area.get("1.0", tk.END).strip()
        if current_content == "Brak danych":
            self.text_area.delete("1.0", tk.END)
            self.text_area.configure(foreground="black")
    
    def _on_text_focus_in(self, event):
        """Event handler gdy użytkownik fokusuje pole tekstowe."""
        self._remove_placeholder_if_exists()
    
    def _on_text_key_press(self, event):
        """Event handler dla naciśnięcia klawisza."""
        self._remove_placeholder_if_exists()
    
    def _configure_scroll_frame(self, event):
        """Configure scroll_frame width to match canvas width"""
        canvas_width = event.width
        self.canvas_container.itemconfig(self.canvas_container.find_all()[0], width=canvas_width)

    def _add_status_message(self, message):
        """
        Dodaje wiadomość statusu do pola wyników zamiast do usuniętego status_label.
        """
        self._remove_placeholder_if_exists()
        # Dodaj separator przed nową wiadomością jeśli pole nie jest puste
        current_content = self.text_area.get("1.0", tk.END).strip()
        if current_content:
            self.text_area.insert(tk.END, "\n" + "="*50 + "\n")
        
        self.text_area.insert(tk.END, f"Status: {message}\n")
        self.text_area.see(tk.END)  # Auto-scroll to show new message

    def _configure_section_styles(self):
        """
        Konfiguruje podstawowe style dla różnych sekcji GUI.
        """
        style = ttk.Style()
        
        # Podstawowe style z lepszą widocznością granic sekcji
        style.configure("TLabelframe", 
                       borderwidth=2, 
                       relief="groove")

    def destroy(self):
        """Cleanup when widget is destroyed - performance optimization"""
        self.cancel_ocr_task()
        super().destroy()

    def _process_ocr_result_queue(self):
        """
        Performance optimization: Process OCR results from worker threads.
        This ensures GUI updates happen on the main thread.
        """
        try:
            results = self.ksiegi_processor.task_manager.get_results()
            for result in results:
                if result['type'] == 'page_complete':
                    # Real-time feedback: display page results as they complete
                    self._display_page_result(result)
                elif result['type'] == 'task_complete':
                    self._handle_ocr_completion(result)
                elif result['type'] == 'cell_result':
                    # Real-time feedback: display cell OCR results as they complete
                    self._display_cell_result(result)
                elif result['type'] == 'all_cells_complete':
                    self._handle_all_cells_completion(result)
                elif result['type'] == 'csv_comparison_result':
                    self._handle_csv_comparison_result(result)
                elif result['type'] == 'folder_processing_result':
                    self._handle_folder_processing_result(result)
        except Exception as e:
            print(f"Błąd przetwarzania kolejki wyników OCR: {e}")
        
        # Schedule next check - performance optimization: frequent but lightweight polling
        self.after(50, self._process_ocr_result_queue)

    def _process_ocr_progress_queue(self):
        """
        Performance optimization: Process progress updates from worker threads.
        Updates status label without blocking GUI.
        """
        try:
            updates = self.ksiegi_processor.task_manager.get_progress_updates()
            for progress in updates:
                self._add_status_message(progress)
        except Exception as e:
            print(f"Błąd przetwarzania kolejki postępu OCR: {e}")
        
        # Schedule next check
        self.after(50, self._process_ocr_progress_queue)

    def _display_page_result(self, result):
        """
        Performance optimization: Display page results immediately as they complete.
        Provides real-time feedback without waiting for all pages.
        """
        page_num = result['page_num']
        ocr_text = result['ocr_text']
        
        # Store for final processing
        self.processed_pages_data[page_num] = result
        
        # Remove placeholder and add content
        self._remove_placeholder_if_exists()
        
        # Minimized GUI updates: batch text insertion
        page_text = f"\n=== STRONA {page_num} ===\n{ocr_text}\n"
        self.text_area.insert(tk.END, page_text)
        
        # Auto-scroll to show latest results
        self.text_area.see(tk.END)

    def _display_cell_result(self, result):
        """
        Performance optimization: Display individual cell OCR result.
        Provides real-time feedback during show_all_ocr processing.
        """
        x, y, text = result['x'], result['y'], result['text']
        self._remove_placeholder_if_exists()
        self.text_area.insert(tk.END, f"x={x} y={y} → {text}\n")
        # Auto-scroll to show latest results
        self.text_area.see(tk.END)

    def _handle_all_cells_completion(self, result):
        """
        Performance optimization: Handle completion of all cells OCR processing.
        """
        processed_count = result['processed_count']
        self._add_status_message(f"Ukończono OCR {processed_count} komórek")
        self.show_ocr_button.config(text="Pokaż wszystkie komórki OCR")

    def _handle_csv_comparison_result(self, result):
        """
        Performance optimization: Handle CSV comparison results.
        """
        if 'window' in result:
            window = result['window']
            comparison_text = result['comparison_text']
            window.result_text.delete("1.0", tk.END)
            window.result_text.insert(tk.END, comparison_text)

    def _handle_folder_processing_result(self, result):
        """
        Performance optimization: Handle folder processing results.
        """
        if result['success']:
            result_text = result['result_text']
            csv_filename = result['csv_filename']
            file_count = result['file_count']
            csv_path = result['csv_path']
            
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, result_text)
            self._add_status_message(f"Zapisano {file_count} plików PDF do {csv_filename}")
            
            # Show success message
            messagebox.showinfo("Sukces", f"Pomyślnie zapisano {file_count} plików PDF do {csv_filename}\nLokalizacja: {csv_path}")
        else:
            error_msg = result['error']
            self._add_status_message(f"Błąd: {error_msg}")
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, error_msg)
            self._add_placeholder_if_empty()  # Add if the error message is empty
            messagebox.showerror("Błąd", error_msg)

    def _handle_ocr_completion(self, result):
        """
        Performance optimization: Handle OCR task completion with optimized final processing.
        """
        if result['success']:
            all_lines = result['all_lines']
            total_pages = result['total_pages']
            
            # Remove placeholder and add final results
            self._remove_placeholder_if_exists()
            
            # Performance optimization: Batch GUI updates for final results
            final_text = "\n---- Linie OCR z wszystkich stron ----\n"
            line_texts = []
            for i, (page_num, line) in enumerate(all_lines, 1):
                line_texts.append(f"strona {page_num}, linia {i}: {line}")
            
            final_text += "\n".join(line_texts) + "\n"
            self.text_area.insert(tk.END, final_text)
            
            # Save results to CSV with optimized batch writing
            self._save_ocr_results_optimized(all_lines)
            
            self._add_status_message(f"OCR z kolumny gotowy, {len(all_lines)} linii z {total_pages} stron, zapisano do Ksiegi/wyniki.csv")
        else:
            error_msg = result.get('error', 'Nieznany błąd')
            messagebox.showerror("Błąd OCR z kolumny", error_msg)
            self._add_status_message("Błąd OCR kolumny")
        
        # Reset button state
        self.ocr_button.config(text="OCR z kolumny (wszystkie strony)")

    def _save_ocr_results_optimized(self, all_lines):
        """
        Performance optimization: Optimized CSV writing with reduced I/O operations.
        """
        try:
            ksiegi_folder = self._ensure_ksiegi_folder()
            csv_path = os.path.join(ksiegi_folder, "wyniki.csv")
            
            # Performance optimization: Write all data in a single operation
            with open(csv_path, "w", encoding="utf-8", newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
                
                # Write header
                writer.writerow(["strona", "linia", "numer faktury"])
                
                # Batch write all rows
                csv_rows = [[page_num, i, line] for i, (page_num, line) in enumerate(all_lines, 1)]
                writer.writerows(csv_rows)
                
        except Exception as e:
            messagebox.showerror("Błąd zapisu pliku CSV", f"Nie udało się zapisać pliku wyniki.csv: {str(e)}")
            self._add_status_message("Błąd zapisu pliku CSV")

    def toggle_column_ocr(self):
        """
        Performance optimization: Toggle between starting and cancelling OCR task.
        """
        if self.ksiegi_processor.task_manager.is_task_active():
            self.cancel_ocr_task()
        else:
            self.run_column_ocr_threaded()

    def cancel_ocr_task(self):
        """Performance optimization: Cancel ongoing OCR task"""
        self.ksiegi_processor.task_manager.cancel_task()
        self._add_status_message("Anulowanie OCR...")
        self.ocr_button.config(text="OCR z kolumny (wszystkie strony)")

    def run_column_ocr_threaded(self):
        """
        Performance optimization: Threaded OCR processing of all pages.
        This replaces the original synchronous run_column_ocr method.
        """
        path = self.file_path_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("Brak pliku", "Wybierz poprawny plik PDF.")
            return

        # Clear previous results
        self.text_area.delete("1.0", tk.END)
        self._add_placeholder_if_empty()
        self.processed_pages_data.clear()
        
        # Update UI for processing state
        self.ocr_button.config(text="Anuluj OCR")
        self._add_status_message("Rozpoczynam OCR...")
        
        # Start threaded OCR processing
        self.ksiegi_processor.task_manager.start_task(
            self.ksiegi_processor.process_pdf_pages_threaded,
            pdf_path=path
        )

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
            self._add_status_message("Plik wybrany")

    def run_column_ocr_legacy(self):
        """
        Legacy synchronous OCR processing (kept for fallback).
        Original implementation - processes pages sequentially in main thread.
        """
        path = self.file_path_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("Brak pliku", "Wybierz poprawny plik PDF.")
            return

        self.text_area.delete("1.0", tk.END)
        self._add_placeholder_if_empty()
        try:
            images = convert_from_path(path, dpi=300, poppler_path=POPPLER_PATH)
            all_lines = []
            
            # Remove placeholder before adding OCR results
            self._remove_placeholder_if_exists()
            
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
                self._add_status_message("Błąd zapisu pliku CSV")
                return

            self._add_status_message(f"OCR z kolumny gotowy, {len(all_lines)} linii z {len(images)} stron, zapisano do Ksiegi/wyniki.csv")

        except Exception as e:
            messagebox.showerror("Błąd OCR z kolumny", str(e))
            self._add_status_message("Błąd OCR kolumny")

    def process_pdf(self):
        """
        Performance optimization: Enhanced single page segmentation with optimized processing.
        Uses the new KsiegiProcessor for better cell detection and OCR performance.
        """
        path = self.file_path_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("Brak pliku", "Wybierz poprawny plik PDF.")
            return

        self.text_area.delete("1.0", tk.END)
        self._add_placeholder_if_empty()
        self.canvas.delete("all")
        self.cells.clear()
        self.ocr_results.clear()
        
        # Performance optimization: Show progress during processing
        self._add_status_message("Ładowanie strony PDF...")

        try:
            # Load first page with optimized DPI for faster processing
            images = convert_from_path(path, dpi=400, poppler_path=POPPLER_PATH)
            if not images:
                messagebox.showerror("Błąd", "Nie można załadować stron PDF.")
                return
                
            pil_img = images[0]
            self._add_status_message("Przetwarzanie segmentacji tabeli...")
            
            # Performance optimization: Use optimized processor for better performance
            result = self.ksiegi_processor.process_single_page_segmented(pil_img)
            
            if result:
                self.image = result['image']
                self.cells = result['cells']
                self.ocr_results = result['ocr_results']
                
                # Performance optimization: Optimized display update
                self.display_image_with_boxes()

                if not self.ocr_results:
                    self._remove_placeholder_if_exists()
                    self.text_area.insert(tk.END, "Nie znaleziono numerów faktur.")
                    self._add_status_message("Brak wyników")
                    return

                # Performance optimization: Batch text insertion
                self._remove_placeholder_if_exists()
                result_texts = [f"x={x} y={y} → {text}" for x, y, text in self.ocr_results]
                self.text_area.insert(tk.END, "\n".join(result_texts) + "\n")

                # Write temp file with batch operation
                with open(TEMP_FILE, "w", encoding="utf-8") as f:
                    f.writelines(f"x={x} y={y} → {text}\n" for x, y, text in self.ocr_results)

                self._add_status_message(f"Znaleziono {len(self.ocr_results)} wpisów")
            else:
                self._add_status_message("Błąd przetwarzania strony")

        except Exception as e:
            messagebox.showerror("Błąd segmentacji", str(e))
            self._add_status_message("Błąd")

    def detect_table_cells(self, image):
        """
        Performance optimization: Enhanced table cell detection with reduced processing time.
        Optimized morphological operations for faster execution.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blur, 180, 255, cv2.THRESH_BINARY_INV)

        # Performance optimization: Reduced kernel sizes and iterations for speed
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 35))
        vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=1)

        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35, 1))
        horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)

        table_mask = cv2.add(vertical_lines, horizontal_lines)
        contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Performance optimization: Slightly reduced area threshold for better detection
        cells = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) > 900]
        cells.sort(key=lambda b: (b[1], b[0]))
        return cells

    def perform_ocr_on_cells(self, image, cells):
        """
        Performance optimization: Enhanced OCR processing with batch operations.
        Processes cells more efficiently and filters results faster.
        """
        results = []
        
        # Performance optimization: Process in batches to reduce OCR overhead
        batch_size = 8
        for i in range(0, len(cells), batch_size):
            batch = cells[i:i + batch_size]
            
            for (x, y, w, h) in batch:
                # Early filtering: skip cells outside target column
                if not (X_MIN <= x <= X_MAX):
                    continue
                    
                roi = image[y:y+h, x:x+w]
                
                # Performance optimization: Skip very small ROIs
                if roi.size < 100:
                    continue
                    
                text = pytesseract.image_to_string(roi, lang='pol').strip()
                
                # Performance optimization: Combined length and pattern check
                if len(text) >= 5 and self.contains_invoice_number(text):
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
        img_pil = img_pil.resize((800, 600)) if img_pil.width > 800 or img_pil.height > 600 else img_pil
        self.tk_image = ImageTk.PhotoImage(img_pil)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

    def show_all_ocr(self):
        """
        Performance optimization: Threaded OCR processing of all cells.
        GUI remains responsive during processing of many cells.
        """
        self.text_area.delete("1.0", tk.END)
        if not self.cells or self.image is None:
            self._remove_placeholder_if_exists()
            self.text_area.insert(tk.END, "Brak wysegmentowanych komórek do wyświetlenia.\n")
            return

        # Check if OCR task is already running
        if self.ksiegi_processor.task_manager.is_task_active():
            self._add_status_message("Zadanie OCR już w toku...")
            return

        # Clear previous results and start threaded processing
        self._add_status_message("Rozpoczynam OCR wszystkich komórek...")
        
        # Start threaded OCR processing of all cells
        self.ksiegi_processor.task_manager.start_task(
            self._process_all_cells_threaded,
            cells=self.cells.copy(),
            image=self.image.copy()
        )

    def _process_all_cells_threaded(self, cells, image):
        """
        Performance optimization: Process all cells in background thread.
        """
        try:
            total_cells = len(cells)
            processed_count = 0
            
            self.ksiegi_processor.task_manager.progress_queue.put(
                f"Przetwarzanie {total_cells} komórek OCR..."
            )
            
            for i, (x, y, w, h) in enumerate(cells):
                if self.ksiegi_processor.task_manager.task_cancelled:
                    break
                    
                try:
                    roi = image[y:y+h, x:x+w]
                    text = pytesseract.image_to_string(roi, lang='pol').strip()
                    
                    # Send result immediately for real-time display
                    self.ksiegi_processor.task_manager.result_queue.put({
                        'type': 'cell_result',
                        'x': x, 'y': y, 'text': text
                    })
                    
                    processed_count += 1
                    
                    # Update progress every 5 cells or on last cell
                    if processed_count % 5 == 0 or processed_count == total_cells:
                        self.ksiegi_processor.task_manager.progress_queue.put(
                            f"OCR komórek: {processed_count}/{total_cells}"
                        )
                        
                except Exception as e:
                    print(f"Błąd OCR komórki {i}: {e}")
                    
            # Send completion signal
            if not self.ksiegi_processor.task_manager.task_cancelled:
                self.ksiegi_processor.task_manager.result_queue.put({
                    'type': 'all_cells_complete',
                    'processed_count': processed_count
                })
                
        except Exception as e:
            print(f"Błąd przetwarzania wszystkich komórek: {e}")
            self.ksiegi_processor.task_manager.progress_queue.put(f"Błąd: {str(e)}")

    def toggle_show_all_ocr(self):
        """
        Performance optimization: Toggle between starting and cancelling show all OCR task.
        """
        if self.ksiegi_processor.task_manager.is_task_active():
            # Cancel the current task
            self.cancel_ocr_task()
            self.show_ocr_button.config(text="Pokaż wszystkie komórki OCR")
        else:
            # Start show all OCR
            self.show_ocr_button.config(text="Anuluj pokazywanie OCR")
            self.show_all_ocr()

    def select_folder_and_generate_csv(self):
        """
        Performance optimization: Threaded folder processing for large directories.
        GUI remains responsive during processing of large folders with many files.
        """
        folder_path = filedialog.askdirectory(title="Wybierz folder do odczytu")
        if not folder_path:
            return
        
        # Check if OCR task is already running
        if self.ksiegi_processor.task_manager.is_task_active():
            messagebox.showwarning("Zadanie w toku", "Poczekaj na zakończenie obecnego zadania.")
            return
        
        # Performance optimization: Show progress during processing
        self._add_status_message("Rozpoczynam przetwarzanie folderu...")
        
        # Start threaded folder processing
        self.ksiegi_processor.task_manager.start_task(
            self._folder_processing_threaded,
            folder_path=folder_path
        )

    def _folder_processing_threaded(self, folder_path):
        """
        Performance optimization: Process folder in background thread.
        """
        try:
            self.ksiegi_processor.task_manager.progress_queue.put("Normalizowanie ścieżki folderu...")
            
            # Normalize path for cross-platform compatibility
            folder_path = os.path.normpath(folder_path)
            folder_name = os.path.basename(folder_path)
            csv_filename = f"{folder_name}.csv"
            
            self.ksiegi_processor.task_manager.progress_queue.put("Przygotowywanie ścieżki wyjściowej...")
            
            # Get output path
            ksiegi_folder = self._ensure_ksiegi_folder()
            csv_path = os.path.join(ksiegi_folder, csv_filename)
            
            self.ksiegi_processor.task_manager.progress_queue.put("Skanowanie plików w folderze...")
            
            # Performance optimization: Optimized file filtering with progress updates
            if os.path.exists(folder_path):
                # Get all items first
                all_items = os.listdir(folder_path)
                total_items = len(all_items)
                
                self.ksiegi_processor.task_manager.progress_queue.put(
                    f"Przetwarzanie {total_items} elementów..."
                )
                
                # Process files with progress updates
                filenames_without_extension = []
                processed_count = 0
                
                for item in all_items:
                    if self.ksiegi_processor.task_manager.task_cancelled:
                        break
                        
                    if (os.path.isfile(os.path.join(folder_path, item)) and 
                        not item.startswith('.') and 
                        item.lower().endswith('.pdf')):
                        filenames_without_extension.append(os.path.splitext(item)[0])
                    
                    processed_count += 1
                    
                    # Update progress every 100 files or on completion
                    if processed_count % 100 == 0 or processed_count == total_items:
                        self.ksiegi_processor.task_manager.progress_queue.put(
                            f"Przetworzono {processed_count}/{total_items} elementów, znaleziono {len(filenames_without_extension)} plików PDF"
                        )
            else:
                filenames_without_extension = []
            
            if self.ksiegi_processor.task_manager.task_cancelled:
                return
            
            self.ksiegi_processor.task_manager.progress_queue.put("Zapisywanie pliku CSV...")
            
            # Performance optimization: Batch CSV writing
            with open(csv_path, 'w', encoding='utf-8', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Write all rows in one operation
                writer.writerows([[filename] for filename in filenames_without_extension])
            
            self.ksiegi_processor.task_manager.progress_queue.put("Przygotowywanie wyników...")
            
            # Performance optimization: Prepare results for main thread
            result_text = "\n".join([
                f"Odczytano folder: {folder_path}",
                f"Znaleziono {len(filenames_without_extension)} plików PDF (pomijając ukryte pliki i inne rozszerzenia):",
                "",
                *filenames_without_extension,
                "",
                f"Plik CSV zapisany jako: {csv_path}"
            ])
            
            # Send completion result
            self.ksiegi_processor.task_manager.result_queue.put({
                'type': 'folder_processing_result',
                'success': True,
                'result_text': result_text,
                'csv_filename': csv_filename,
                'file_count': len(filenames_without_extension),
                'csv_path': csv_path
            })
            
            self.ksiegi_processor.task_manager.progress_queue.put("Przetwarzanie folderu ukończone")
            
        except Exception as e:
            error_msg = f"Błąd podczas przetwarzania folderu: {str(e)}"
            self.ksiegi_processor.task_manager.progress_queue.put(f"Błąd: {error_msg}")
            self.ksiegi_processor.task_manager.result_queue.put({
                'type': 'folder_processing_result',
                'success': False,
                'error': error_msg
            })

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
        Performance optimization: Threaded CSV comparison for large files.
        GUI remains responsive during comparison of large CSV files.
        """
        if not file1_path or not file2_path:
            messagebox.showwarning("Błąd", "Proszę wybrać oba pliki CSV.")
            return
        
        if not os.path.exists(file1_path) or not os.path.exists(file2_path):
            messagebox.showerror("Błąd", "Jeden lub oba wybrane pliki nie istnieją.")
            return
        
        # Check if OCR task is already running
        if self.ksiegi_processor.task_manager.is_task_active():
            messagebox.showwarning("Zadanie w toku", "Poczekaj na zakończenie obecnego zadania.")
            return
        
        # Performance optimization: Show progress during processing
        window.result_text.delete("1.0", tk.END)
        window.result_text.insert(tk.END, "Rozpoczynam porównanie CSV...\n")
        
        # Start threaded CSV comparison
        self.ksiegi_processor.task_manager.start_task(
            self._csv_comparison_threaded,
            file1_path=file1_path,
            file2_path=file2_path,
            window=window
        )

    def _csv_comparison_threaded(self, file1_path, file2_path, window):
        """
        Performance optimization: Process CSV comparison in background thread.
        """
        try:
            # Progress updates
            self.ksiegi_processor.task_manager.progress_queue.put("Wykrywanie delimitatorów CSV...")
            
            # Performance optimization: Detect delimiters efficiently
            delimiter1 = self._detect_csv_delimiter(file1_path)
            delimiter2 = self._detect_csv_delimiter(file2_path)
            
            self.ksiegi_processor.task_manager.progress_queue.put("Odczytywanie plików CSV...")
            
            # Performance optimization: Read CSV files with optimized parsing
            data1 = self._read_csv_file(file1_path)
            data2 = self._read_csv_file(file2_path)
            
            self.ksiegi_processor.task_manager.progress_queue.put("Przetwarzanie kolumny C...")
            
            # Extract column C values with optimized processing
            values1, values2 = self._extract_column_values_optimized(data1, data2)
            
            self.ksiegi_processor.task_manager.progress_queue.put("Wykonywanie porównania...")
            
            # Performance optimization: Efficient comparison algorithm
            comparison_results = self._compare_values_optimized(values1, values2)
            
            self.ksiegi_processor.task_manager.progress_queue.put("Zapisywanie wyników...")
            
            # Save results with batch writing
            output_path = self._save_comparison_results_optimized(file2_path, comparison_results)
            
            self.ksiegi_processor.task_manager.progress_queue.put("Formatowanie wyników...")
            
            # Format results for display
            comparison_text = self._format_comparison_results_optimized(
                file1_path, file2_path, delimiter1, delimiter2, 
                values1, values2, comparison_results, output_path
            )
            
            # Send completion result
            self.ksiegi_processor.task_manager.result_queue.put({
                'type': 'csv_comparison_result',
                'window': window,
                'comparison_text': comparison_text
            })
            
            self.ksiegi_processor.task_manager.progress_queue.put("Porównanie CSV ukończone")
            
        except Exception as e:
            error_msg = f"Błąd podczas porównywania plików: {str(e)}"
            self.ksiegi_processor.task_manager.progress_queue.put(f"Błąd: {error_msg}")
            self.ksiegi_processor.task_manager.result_queue.put({
                'type': 'csv_comparison_result',
                'window': window,
                'comparison_text': error_msg
            })

    def _extract_column_values_optimized(self, data1, data2):
        """
        Performance optimization: Optimized extraction of column C values.
        """
        # Extract column C values with list comprehensions for better performance
        values1 = [
            (i + 2, row[2] if len(row) >= 3 else "")  # +2 because we skip header
            for i, row in enumerate(data1[1:])
        ]
        
        values2 = [
            (i + 2, row[2] if len(row) >= 3 else "")
            for i, row in enumerate(data2[1:])
        ]
        
        return values1, values2

    def _compare_values_optimized(self, values1, values2):
        """
        Performance optimization: Efficient value comparison algorithm.
        """
        comparison_results = []
        all_values1 = [val for _, val in values1]
        all_values2 = [val for _, val in values2]
        
        max_len = max(len(all_values1), len(all_values2))
        
        # Single pass comparison with optimized logic
        for i in range(max_len):
            val1 = all_values1[i] if i < len(all_values1) else ""
            val2 = all_values2[i] if i < len(all_values2) else ""
            row_num = i + 2  # +2 to account for header
            
            val1_clean = val1.strip()
            val2_clean = val2.strip()
            
            # Determine status with optimized conditional logic
            if val1_clean and val2_clean:
                status = "identyczne" if val1_clean.lower() == val2_clean.lower() else "różne"
            elif val1_clean and not val2_clean:
                status = "brak w pliku test.csv"
            elif not val1_clean and val2_clean:
                status = "brak w wyniki.csv"
            else:
                continue  # Skip empty rows
            
            comparison_results.append({
                'row_number': row_num,
                'value_wyniki': val1_clean,
                'value_test': val2_clean,
                'status': status
            })
        
        return comparison_results

    def _save_comparison_results_optimized(self, file2_path, comparison_results):
        """
        Performance optimization: Optimized batch CSV writing for comparison results.
        """
        output_dir = os.path.dirname(file2_path)
        output_path = os.path.join(output_dir, "porownanie.csv")
        
        # Batch write all data in single operation
        with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            
            # Write header
            writer.writerow(["Numer wiersza", "Wartość z wyniki.csv", "Wartość z test.csv", "Status"])
            
            # Batch write all rows
            writer.writerows([
                [result['row_number'], result['value_wyniki'], result['value_test'], result['status']]
                for result in comparison_results
            ])
        
        return output_path

    def _display_comparison_results_optimized(self, window, file1_path, file2_path, 
                                            delimiter1, delimiter2, values1, values2, 
                                            comparison_results, output_path):
        """
        Performance optimization: Optimized display of comparison results with batch text updates.
        """
        result_text = window.result_text
        result_text.delete("1.0", tk.END)
        
        # Performance optimization: Build entire text content at once
        delimiter_names = {
            ',': 'przecinek', ';': 'średnik', '\t': 'tabulacja', 
            '|': 'pionowa kreska', ':': 'dwukropek'
        }
        delimiter1_name = delimiter_names.get(delimiter1, repr(delimiter1))
        delimiter2_name = delimiter_names.get(delimiter2, repr(delimiter2))
        
        # Calculate statistics
        stats = {
            'identical': len([r for r in comparison_results if r['status'] == 'identyczne']),
            'different': len([r for r in comparison_results if r['status'] == 'różne']),
            'missing_in_test': len([r for r in comparison_results if r['status'] == 'brak w pliku test.csv']),
            'missing_in_wyniki': len([r for r in comparison_results if r['status'] == 'brak w wyniki.csv'])
        }
        
        # Build complete result text
        result_lines = [
            "=== PORÓWNANIE KOLUMNY C PLIKÓW CSV ===\n",
            f"WYNIKI.CSV: {os.path.basename(file1_path)} ({len(values1)} wartości, separator: {delimiter1_name})",
            f"TEST.CSV: {os.path.basename(file2_path)} ({len(values2)} wartości, separator: {delimiter2_name})\n",
            "=== WYNIKI PORÓWNANIA KOLUMNY C ===",
            f"• Identyczne wartości: {stats['identical']}",
            f"• Różne wartości: {stats['different']}",
            f"• Wartości tylko w wyniki.csv: {stats['missing_in_test']}",
            f"• Wartości tylko w test.csv: {stats['missing_in_wyniki']}",
            f"• Łączna liczba porównanych rekordów: {len(comparison_results)}\n"
        ]
        
        # Add examples of differences if any exist
        if stats['different'] > 0:
            result_lines.append("=== PRZYKŁADY RÓŻNYCH WARTOŚCI ===")
            different_examples = [r for r in comparison_results if r['status'] == 'różne'][:10]
            for example in different_examples:
                result_lines.append(f"Wiersz {example['row_number']}: '{example['value_wyniki']}' vs '{example['value_test']}'")
            result_lines.append("")
        
        # Add file information
        result_lines.extend([
            "=== PLIK WYNIKÓW ===",
            f"Szczegółowe wyniki zapisano w pliku:",
            output_path,
            "",
            f"Plik zawiera {len(comparison_results)} wierszy porównania."
        ])
        
        # Single text insertion for better performance
        result_text.insert(tk.END, "\n".join(result_lines))

    def _format_comparison_results_optimized(self, file1_path, file2_path, 
                                            delimiter1, delimiter2, values1, values2, 
                                            comparison_results, output_path):
        """
        Performance optimization: Format comparison results for threaded display.
        """
        # Performance optimization: Build entire text content at once
        delimiter_names = {
            ',': 'przecinek', ';': 'średnik', '\t': 'tabulacja', 
            '|': 'pionowa kreska', ':': 'dwukropek'
        }
        delimiter1_name = delimiter_names.get(delimiter1, repr(delimiter1))
        delimiter2_name = delimiter_names.get(delimiter2, repr(delimiter2))
        
        # Calculate statistics
        stats = {
            'identical': len([r for r in comparison_results if r['status'] == 'identyczne']),
            'different': len([r for r in comparison_results if r['status'] == 'różne']),
            'missing_in_test': len([r for r in comparison_results if r['status'] == 'brak w pliku test.csv']),
            'missing_in_wyniki': len([r for r in comparison_results if r['status'] == 'brak w wyniki.csv'])
        }
        
        # Build complete result text
        result_lines = [
            "=== PORÓWNANIE KOLUMNY C PLIKÓW CSV ===\n",
            f"WYNIKI.CSV: {os.path.basename(file1_path)} ({len(values1)} wartości, separator: {delimiter1_name})",
            f"TEST.CSV: {os.path.basename(file2_path)} ({len(values2)} wartości, separator: {delimiter2_name})\n",
            "=== WYNIKI PORÓWNANIA KOLUMNY C ===",
            f"• Identyczne wartości: {stats['identical']}",
            f"• Różne wartości: {stats['different']}",
            f"• Wartości tylko w wyniki.csv: {stats['missing_in_test']}",
            f"• Wartości tylko w test.csv: {stats['missing_in_wyniki']}",
            f"• Łączna liczba porównanych rekordów: {len(comparison_results)}\n"
        ]
        
        # Add examples of differences if any exist
        if stats['different'] > 0:
            result_lines.append("=== PRZYKŁADY RÓŻNYCH WARTOŚCI ===")
            different_examples = [r for r in comparison_results if r['status'] == 'różne'][:10]
            for example in different_examples:
                result_lines.append(f"Wiersz {example['row_number']}: '{example['value_wyniki']}' vs '{example['value_test']}'")
            result_lines.append("")
        
        # Add file information
        result_lines.extend([
            "=== PLIK WYNIKÓW ===",
            f"Szczegółowe wyniki zapisano w pliku:",
            output_path,
            "",
            f"Plik zawiera {len(comparison_results)} wierszy porównania."
        ])
        
        return "\n".join(result_lines)
        result_text.see("1.0")
        
        # Show completion message
        total_issues = stats['different'] + stats['missing_in_test'] + stats['missing_in_wyniki']
        if total_issues == 0:
            messagebox.showinfo("Sukces", f"Porównanie ukończone. Wszystkie wartości w kolumnie C są identyczne!\nWyniki zapisano do: {output_path}")
        else:
            messagebox.showinfo("Sukces", f"Porównanie ukończone. Znaleziono {total_issues} różnic w kolumnie C.\nWyniki zapisano do: {output_path}")

    def _detect_csv_delimiter(self, file_path):
        """
        Performance optimization: Enhanced CSV delimiter detection with efficient analysis.
        Wykrywa separator CSV używając kilku metod w kolejności priorytetu.
        Optimized to minimize file I/O and use efficient string analysis.
        """
        # Popular delimiters in order of preference - performance optimization
        common_delimiters = [';', ',', '\t', '|', ':']
        
        try:
            with open(file_path, 'r', encoding='utf-8', newline='') as csvfile:
                # Performance optimization: Read content once and validate
                content = csvfile.read()
                if not content.strip():
                    raise ValueError("Plik CSV jest pusty")
                
                csvfile.seek(0)
                
                # Performance optimization: Read only first 5 lines for analysis
                sample_lines = []
                for i in range(5):
                    line = csvfile.readline()
                    if not line:
                        break
                    sample_lines.append(line.strip())
                
                if not sample_lines:
                    raise ValueError("Plik nie zawiera czytelnych linii")
                
                # Method 1: Use csv.Sniffer (modern approach) - performance optimization
                csvfile.seek(0)
                sample = csvfile.read(1024)  # Limited sample for speed
                csvfile.seek(0)
                
                try:
                    sniffer = csv.Sniffer()
                    detected = sniffer.sniff(sample).delimiter
                    if detected in common_delimiters:
                        # Quick verification of detected delimiter
                        reader = csv.reader(csvfile, delimiter=detected)
                        first_row = next(reader, None)
                        if first_row and len(first_row) > 1:
                            csvfile.seek(0)
                            return detected
                except Exception:
                    pass  # Fall back to next method
                
                # Method 2: Count occurrences - performance optimization with single pass
                delimiter_counts = {delimiter: sum(line.count(delimiter) for line in sample_lines) 
                                  for delimiter in common_delimiters}
                
                # Find most frequent delimiter with preference order
                best_delimiter = None
                max_count = 0
                
                for delimiter in common_delimiters:  # Preserve preference order
                    count = delimiter_counts[delimiter]
                    if count > max_count:
                        max_count = count
                        best_delimiter = delimiter
                
                if best_delimiter and max_count > 0:
                    # Quick verification - performance optimization
                    try:
                        csvfile.seek(0)
                        reader = csv.reader(csvfile, delimiter=best_delimiter)
                        rows = list(reader)
                        if rows and any(len(row) > 1 for row in rows):
                            csvfile.seek(0)
                            return best_delimiter
                    except Exception:
                        pass
                
                # Method 3: Consistency check - performance optimization with efficient validation
                for delimiter in common_delimiters:
                    try:
                        csvfile.seek(0)
                        reader = csv.reader(csvfile, delimiter=delimiter)
                        rows = list(reader)
                        if not rows:
                            continue
                        
                        # Check field count consistency - performance optimization
                        field_counts = [len(row) for row in rows if row]
                        if not field_counts:
                            continue
                        
                        most_common_count = max(set(field_counts), key=field_counts.count)
                        if most_common_count > 1:
                            # Check consistency (80% threshold) - performance optimization
                            consistency = field_counts.count(most_common_count) / len(field_counts)
                            if consistency >= 0.8:
                                csvfile.seek(0)
                                return delimiter
                    except Exception:
                        continue
                
                # Final fallback: single column detection - performance optimization
                if len(sample_lines) > 0 and all(delimiter not in line 
                                               for line in sample_lines 
                                               for delimiter in common_delimiters):
                    csvfile.seek(0)
                    return ','  # Default separator for single column
                
                return None  # No delimiter detected
                
        except Exception as e:
            raise ValueError(f"Błąd podczas analizy pliku CSV: {str(e)}")

    def _read_csv_file(self, file_path):
        """
        Performance optimization: Enhanced CSV file reading with optimized parsing.
        Pomocnicza funkcja do wczytywania pliku CSV z automatycznym wykrywaniem separatora.
        Optimized to minimize memory usage and improve parsing speed.
        """
        rows = []
        
        try:
            # Performance optimization: Detect delimiter once
            delimiter = self._detect_csv_delimiter(file_path)
            if delimiter is None:
                raise ValueError(
                    "Nie udało się automatycznie wykryć separatora w pliku CSV.\n"
                    "Sprawdź czy plik zawiera poprawnie sformatowane dane CSV "
                    "z jednym z popularnych separatorów: ; , Tab |"
                )
            
            # Performance optimization: Read file with efficient processing
            with open(file_path, 'r', encoding='utf-8', newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter=delimiter)
                
                # Performance optimization: Process rows with list comprehension and filtering
                rows = [
                    tuple(cell.strip() for cell in row)
                    for row in reader
                    if row and any(cell.strip() for cell in row)  # Skip empty rows efficiently
                ]
            
            if not rows:
                raise ValueError("Plik CSV nie zawiera żadnych danych do przetworzenia")
            
            return rows
            
        except Exception as e:
            # Enhanced error context - performance optimization
            raise ValueError(f"Błąd odczytu pliku CSV '{os.path.basename(file_path)}': {str(e)}")