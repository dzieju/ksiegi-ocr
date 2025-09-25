import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import os
import pytesseract
from pdf2image import convert_from_path
import threading
import queue
import time
import re
import csv
from tools.ocr_engines import ocr_manager

# Import poppler utilities for automatic path detection
try:
    from tools.poppler_utils import get_poppler_path, check_pdf_file_exists
    POPPLER_PATH = get_poppler_path()
    if POPPLER_PATH:
        print(f"Zakupy tab: Poppler detected at: {POPPLER_PATH}")
    else:
        print("Zakupy tab: Warning: Poppler not detected, using fallback path")
        POPPLER_PATH = r"C:\poppler\Library\bin"  # Fallback
except ImportError as e:
    print(f"Zakupy tab: Failed to import poppler_utils, using fallback path: {e}")
    POPPLER_PATH = r"C:\poppler\Library\bin"  # Fallback

# Import tesseract utilities for automatic path detection
try:
    from tools.tesseract_utils import get_tesseract_path
    TESSERACT_PATH = get_tesseract_path()
    if TESSERACT_PATH:
        print(f"Zakupy tab: Tesseract detected at: {TESSERACT_PATH}")
    else:
        print("Zakupy tab: Warning: Tesseract not detected, using fallback path")
        TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Fallback
except ImportError as e:
    print(f"Zakupy tab: Failed to import tesseract_utils, using fallback path: {e}")
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Fallback

# Crop coordinates for invoice numbers column
CROP_LEFT, CROP_RIGHT = 499, 771
CROP_TOP, CROP_BOTTOM = 332, 2377

# OCR log file
OCR_LOG_FILE = "ocr_log.txt"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


class ZakupiTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Initialize file path variable
        self.file_path_var = tk.StringVar()
        
        # Threading support variables
        self.processing_cancelled = False
        self.processing_thread = None
        self.result_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        
        # Create UI elements
        self.create_widgets()
        
        # Start processing queues
        self._process_result_queue()
        self._process_progress_queue()

    def clean_invoice_name(self, text):
        """
        Clean invoice name by removing leading '|' symbol and spaces.
        
        Args:
            text: Raw invoice name from OCR
            
        Returns:
            Cleaned invoice name with leading '|' and spaces removed
        """
        if not text:
            return text
            
        # First remove leading whitespace, then remove leading '|', then remove any remaining leading whitespace
        cleaned = text.lstrip()  # Remove leading whitespace
        if cleaned.startswith('|'):
            cleaned = cleaned[1:]  # Remove the first '|' character
        cleaned = cleaned.lstrip()  # Remove any remaining leading whitespace
        return cleaned

    def contains_invoice_number(self, text):
        """
        Check if text contains invoice number.
        Now accepts ANY line that looks like an invoice number (not just specific patterns):
        - Contains at least one digit
        - Contains "/" or "-" separator
        - Minimum 5 characters length
        - Not on blacklist
        """
        # Blacklist of specific problematic phrases to exclude from invoice detection
        blacklist_phrases = [
            "py dla sprzedaży wyłącznie",
            "dla sprzedaży wyłącznie", 
            "dla sprzedaży",
            "sprzedaży wyłącznie",
            "wyłącznie dla sprzedaży",
            "materiały do sprzedaży",
            "przeznaczone do sprzedaży",
            "artykuły do sprzedaży"
        ]
        
        # Blacklist of individual words that should cause exclusion if they appear in the text
        blacklist_words = [
            "usług",
            "zakupu", 
            "naturze",
            "sprzedaż",
            "towarów",
            "zakup",
            "spółka",
            "materiałów",
            "artykułów",
            "przeznaczone"
        ]
        
        text_lower = text.lower().strip()
        
        # Check if text contains any blacklisted phrase (substring match)
        for phrase in blacklist_phrases:
            if phrase.lower() in text_lower:
                return False
        
        # Check if text contains any blacklisted word (using word boundaries for precision)
        for word in blacklist_words:
            if re.search(r'\b' + re.escape(word.lower()) + r'\b', text_lower):
                return False
        
        # NEW LOGIC: Accept ANY line that looks like an invoice number
        # Requirements: at least one digit, contains "/" or "-", minimum 5 characters
        text_stripped = text.strip()
        if len(text_stripped) < 5:
            return False
            
        # Must contain at least one digit
        if not re.search(r'\d', text_stripped):
            return False
            
        # Must contain "/" or "-"  
        if not re.search(r'[/-]', text_stripped):
            return False
            
        return True

    def save_ocr_log(self, ocr_data):
        """
        Save original OCR results to log file (overwrite, not append).
        Args:
            ocr_data: List of tuples (page_num, line_text)
        """
        try:
            with open(OCR_LOG_FILE, "w", encoding="utf-8") as f:
                f.write("=== OCR LOG ===\n")
                f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total pages processed: {max([page_num for page_num, _ in ocr_data], default=0)}\n")
                f.write(f"Total lines: {len(ocr_data)}\n")
                f.write("\n--- RAW OCR OUTPUT ---\n")
                
                for page_num, line in ocr_data:
                    f.write(f"Page {page_num}: {line}\n")
        except Exception as e:
            print(f"Error saving OCR log: {e}")

    def save_invoice_numbers_to_csv(self, invoice_numbers):
        """
        Zapisuje rozpoznane numery faktur do pliku zakupy.csv w folderze /odczyty
        """
        try:
            # Ścieżka do pliku CSV względem katalogu głównego projektu
            csv_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "odczyty", "zakupy.csv")
            
            # Upewnij się, że katalog istnieje
            os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
            
            # Zapisz do pliku CSV (nadpisuje poprzedni plik)
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Zapisz każdy numer faktury w osobnej kolumnie A
                # Wyczyść każdy numer faktury usuwając znak "|" z początku
                for invoice_number in invoice_numbers:
                    cleaned_invoice_number = self.clean_invoice_name(invoice_number)
                    writer.writerow([cleaned_invoice_number])
            
            return csv_file_path
        except Exception as e:
            raise Exception(f"Błąd podczas zapisywania CSV: {str(e)}")

    def show_ocr_log_preview(self):
        """Open new window with current OCR log content"""
        try:
            if not os.path.exists(OCR_LOG_FILE):
                messagebox.showinfo("Podgląd loga", "Brak pliku loga. Najpierw wykonaj odczyt OCR.")
                return
                
            with open(OCR_LOG_FILE, "r", encoding="utf-8") as f:
                log_content = f.read()
            
            # Create new window
            log_window = tk.Toplevel(self)
            log_window.title("Podgląd loga OCR")
            log_window.geometry("800x600")
            log_window.transient(self)
            log_window.grab_set()
            
            # Create text widget with scrollbar (consistent with main report width)
            text_widget = ScrolledText(log_window, wrap="word", width=57, height=35)
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Insert log content
            text_widget.insert("1.0", log_content)
            text_widget.config(state="disabled")  # Make read-only
            
            # Add close button
            close_btn = ttk.Button(log_window, text="Zamknij", command=log_window.destroy)
            close_btn.pack(pady=5)
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć loga: {str(e)}")

    def destroy(self):
        """Cleanup when widget is destroyed"""
        self.cancel_processing()
        super().destroy()

    def _process_result_queue(self):
        """Process results from worker thread"""
        try:
            while True:
                try:
                    result = self.result_queue.get_nowait()
                    if result['type'] == 'ocr_line':
                        # Add only the recognized invoice name to text area (single column)
                        # Clean the invoice name by removing leading '|' and spaces
                        cleaned_line = self.clean_invoice_name(result['line'])
                        self.text_area.insert(tk.END, f"{cleaned_line}\n")
                    elif result['type'] == 'csv_export_success':
                        # Show CSV export success messagebox
                        messagebox.showinfo("Eksport zakończony", f"Wyeksportowano {result['invoice_count']} numerów do odczyty/zakupy.csv")
                    elif result['type'] == 'csv_export_error':
                        # Show CSV export error
                        messagebox.showerror("Błąd eksportu CSV", f"Błąd podczas zapisywania CSV: {result['error']}")
                    elif result['type'] == 'processing_complete':
                        # Restore button state and show final results
                        self.process_button.config(text="Odczytaj numery faktur")
                        
                        # Updated summary format: show total lines and detected invoice numbers separately
                        invoice_info = f" (wykryto {result['invoice_count']} numerów faktur)" if result['invoice_count'] > 0 else " (wykryto 0 numerów faktur)"
                        csv_info = " → zapisano do CSV" if result.get('csv_saved', False) else ""
                        self.status_label.config(
                            text=f"OCR z kolumny gotowy, {result['total_lines']} linii z {result['total_pages']} stron{invoice_info}{csv_info}", 
                            foreground="green"
                        )
                        
                        # Display timing information
                        if 'duration' in result:
                            duration_text = f"Czas wykonania: {result['duration']:.2f} s"
                            self.timing_label.config(text=duration_text, foreground="green")
                    elif result['type'] == 'processing_error':
                        # Show error and restore button
                        self.process_button.config(text="Odczytaj numery faktur")
                        messagebox.showerror("Błąd OCR z kolumny", result['error'])
                        self.status_label.config(text="Błąd OCR kolumny", foreground="red")
                        self.timing_label.config(text="")  # Clear timing on error
                    elif result['type'] == 'processing_cancelled':
                        # Processing was cancelled
                        self.process_button.config(text="Odczytaj numery faktur")
                        self.status_label.config(text="Przetwarzanie anulowane", foreground="orange")
                        self.timing_label.config(text="")  # Clear timing on cancellation
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Błąd przetwarzania kolejki wyników: {e}")
        
        # Schedule next check
        self.after(100, self._process_result_queue)

    def _process_progress_queue(self):
        """Process progress updates from worker thread"""
        try:
            while True:
                try:
                    progress = self.progress_queue.get_nowait()
                    self.status_label.config(text=progress, foreground="blue")
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Błąd przetwarzania kolejki postępu: {e}")
        
        # Schedule next check
        self.after(100, self._process_progress_queue)

    def toggle_processing(self):
        """Toggle between starting and cancelling OCR processing"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.cancel_processing()
        else:
            self.start_processing()

    def cancel_processing(self):
        """Cancel ongoing OCR processing"""
        self.processing_cancelled = True
        self.status_label.config(text="Anulowanie...", foreground="orange")
        self.process_button.config(text="Odczytaj numery faktur")
        self.timing_label.config(text="")  # Clear timing on manual cancel

    def start_processing(self):
        """Start the threaded OCR processing"""
        filepath = self.file_path_var.get().strip()
        
        if not filepath:
            messagebox.showwarning("Brak pliku", "Proszę najpierw wybrać plik PDF.")
            return
            
        # Use improved PDF file validation
        try:
            pdf_exists, pdf_message = check_pdf_file_exists(filepath)
            if not pdf_exists:
                messagebox.showwarning("Problem z plikiem PDF", pdf_message)
                return
        except NameError:
            # Fallback to basic existence check if check_pdf_file_exists is not available
            if not os.path.exists(filepath):
                messagebox.showwarning("Brak pliku", "Wybierz poprawny plik PDF.")
                return

        # Clear previous results and timing
        self.text_area.delete("1.0", tk.END)
        self.timing_label.config(text="")  # Clear previous timing display
        
        # Reset cancellation flag
        self.processing_cancelled = False
        
        # Update UI
        self.process_button.config(text="Anuluj przetwarzanie")
        self.status_label.config(text="Rozpoczynam przetwarzanie...", foreground="blue")

        # Start processing in background thread
        self.processing_thread = threading.Thread(
            target=self._threaded_ocr_processing,
            args=(filepath,),
            daemon=True
        )
        self.processing_thread.start()

    def _threaded_ocr_processing(self, filepath):
        """Main OCR processing logic running in background thread"""
        start_time = time.time()  # Record start time for duration calculation
        try:
            self.progress_queue.put("Konwertowanie PDF na obrazy...")
            
            # Convert PDF to images
            images = convert_from_path(filepath, dpi=300, poppler_path=POPPLER_PATH)
            total_pages = len(images)
            
            if self.processing_cancelled:
                self.result_queue.put({'type': 'processing_cancelled'})
                return
            
            self.result_queue.put({'type': 'ocr_line', 'page_num': 0, 'line_num': 0, 'line': "----- Rozpoznane numery faktur -----"})
            
            all_lines = []
            ocr_log_data = []  # Store raw OCR data for logging
            line_counter = 0
            invoice_count = 0  # Count detected invoice numbers
            invoice_numbers = []  # Store detected invoice numbers for CSV export
            
            # Prepare cropped images for batch OCR processing
            self.progress_queue.put("Przygotowywanie obrazów do OCR...")
            cropped_images = []
            for page_num, pil_img in enumerate(images, 1):
                if self.processing_cancelled:
                    self.result_queue.put({'type': 'processing_cancelled'})
                    return
                
                # Crop the image to the specified region
                crop = pil_img.crop((CROP_LEFT, CROP_TOP, CROP_RIGHT, CROP_BOTTOM))
                cropped_images.append((page_num, crop))
            
            self.progress_queue.put("Uruchamianie OCR...")
            
            # Perform batch OCR with progress callback
            def ocr_progress_callback(processed, total):
                if not self.processing_cancelled:
                    self.progress_queue.put(f"OCR: {processed + 1}/{total} stron...")
            
            # Extract just the images for OCR processing
            images_for_ocr = [crop for page_num, crop in cropped_images]
            
            try:
                # Perform batch OCR using the configured engine
                ocr_results = ocr_manager.perform_ocr_batch(
                    images_for_ocr, 
                    language='pol+eng',
                    progress_callback=ocr_progress_callback
                )
            except Exception as e:
                # Fallback to single-threaded processing if batch fails
                self.progress_queue.put("Błąd batch OCR, przełączam na tryb pojedynczy...")
                ocr_results = []
                for i, (page_num, crop) in enumerate(cropped_images):
                    if self.processing_cancelled:
                        self.result_queue.put({'type': 'processing_cancelled'})
                        return
                    
                    self.progress_queue.put(f"OCR (fallback): {i + 1}/{len(cropped_images)} stron...")
                    try:
                        ocr_text = ocr_manager.perform_ocr_single(crop, 'pol+eng')
                        ocr_results.append(ocr_text)
                    except Exception as ocr_error:
                        # Final fallback to tesseract
                        ocr_text = pytesseract.image_to_string(crop, lang='pol+eng')
                        ocr_results.append(ocr_text)
            
            # Process OCR results
            for i, (page_num, crop) in enumerate(cropped_images):
                if self.processing_cancelled:
                    self.result_queue.put({'type': 'processing_cancelled'})
                    return
                
                self.progress_queue.put(f"Przetwarzanie wyników: {i + 1}/{len(cropped_images)}...")
                
                ocr_text = ocr_results[i] if i < len(ocr_results) else ""
                
                # Process lines
                lines = [l.strip() for l in ocr_text.split('\n') if l.strip()]
                
                for line in lines:
                    if self.processing_cancelled:
                        self.result_queue.put({'type': 'processing_cancelled'})
                        return
                    
                    line_counter += 1
                    all_lines.append((page_num, line))
                    ocr_log_data.append((page_num, line))  # Add to log data
                    
                    # Check if line contains invoice number and send only those to the report
                    if self.contains_invoice_number(line):
                        invoice_count += 1
                        invoice_numbers.append(line.strip())  # Add to CSV export list
                        # Send only the recognized invoice number to GUI (single column)
                        self.result_queue.put({
                            'type': 'ocr_line',
                            'page_num': page_num,
                            'line_num': line_counter,
                            'line': line
                        })
                
                # Small delay to allow GUI updates and cancellation
                time.sleep(0.01)

            # Save OCR log (always overwrite)
            if not self.processing_cancelled:
                self.save_ocr_log(ocr_log_data)

            # Export invoice numbers to CSV and show messagebox if any were found
            csv_saved = False
            csv_path = ""
            if not self.processing_cancelled and invoice_numbers:
                try:
                    csv_path = self.save_invoice_numbers_to_csv(invoice_numbers)
                    csv_saved = True
                    
                    # Schedule messagebox to be shown in main thread
                    self.result_queue.put({
                        'type': 'csv_export_success',
                        'invoice_count': len(invoice_numbers),
                        'csv_path': csv_path
                    })
                except Exception as csv_error:
                    self.result_queue.put({
                        'type': 'csv_export_error',
                        'error': str(csv_error)
                    })

            # Processing complete
            if not self.processing_cancelled:
                end_time = time.time()
                duration = end_time - start_time
                self.result_queue.put({
                    'type': 'processing_complete',
                    'total_lines': len(all_lines),
                    'total_pages': total_pages,
                    'invoice_count': invoice_count,
                    'csv_saved': csv_saved,
                    'duration': duration
                })

        except Exception as e:
            if not self.processing_cancelled:
                self.result_queue.put({
                    'type': 'processing_error',
                    'error': str(e)
                })
        
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
        self.process_button = ttk.Button(self, text="Odczytaj numery faktur", command=self.toggle_processing)
        self.process_button.grid(row=2, column=1, pady=20)
        
        # Log preview button
        self.log_preview_button = ttk.Button(self, text="Podgląd loga w nowym oknie", command=self.show_ocr_log_preview)
        self.log_preview_button.grid(row=2, column=2, padx=10, pady=20)
        
        # Status label and timing label frame
        status_frame = ttk.Frame(self)
        status_frame.grid(row=3, column=1, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Brak wybranego pliku", foreground="blue")
        self.status_label.pack(side="left")
        
        # Timing label - initially empty, positioned next to status label
        self.timing_label = ttk.Label(status_frame, text="", foreground="gray")
        self.timing_label.pack(side="left", padx=(10, 0))
        
        # Text area for OCR results - fixed width of ~57 chars (~12 cm for monospace fonts)
        self.text_area = ScrolledText(self, wrap="word", width=57, height=25)
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
            
    def odczytaj_numery_faktur_old(self):
        """OCR funkcja odczytu numerów faktur z kolumny
        
        This is the old synchronous version, kept for reference.
        The new threaded version is implemented above.
        """
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

            # Wyświetl tylko rozpoznane numery faktur (pojedyncza kolumna)
            self.text_area.insert(tk.END, "----- Rozpoznane numery faktur -----\n")
            invoice_count = 0
            for i, (page_num, line) in enumerate(all_lines, 1):
                if self.contains_invoice_number(line):
                    invoice_count += 1
                    # Clean the invoice name by removing leading '|' and spaces
                    cleaned_line = self.clean_invoice_name(line)
                    self.text_area.insert(tk.END, f"{cleaned_line}\n")

            self.status_label.config(text=f"OCR z kolumny gotowy, {len(all_lines)} linii z {len(images)} stron (wykryto {invoice_count} numerów faktur)", foreground="green")

        except Exception as e:
            messagebox.showerror("Błąd OCR z kolumny", str(e))
            self.status_label.config(text="Błąd OCR kolumny", foreground="red")