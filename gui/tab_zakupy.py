import customtkinter as ctk
from tkinter import filedialog, messagebox
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

# Configuration paths
POPPLER_PATH = r"C:\poppler\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Crop coordinates for invoice numbers column
CROP_LEFT, CROP_RIGHT = 499, 771
CROP_TOP, CROP_BOTTOM = 332, 2377

# OCR log file
OCR_LOG_FILE = "ocr_log.txt"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

class ZakupiTab(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Initialize file path variable
        self.file_path_var = ctk.StringVar()
        
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
        Enhanced invoice number detection with improved blacklist filtering
        Returns True if text contains an invoice number pattern
        """
        if not text or len(text.strip()) == 0:
            return False
        
        text_clean = text.strip()
        
        # Enhanced blacklist of phrases that should NOT be considered invoice numbers
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
        
        # Enhanced blacklist of words that should NOT be considered invoice numbers
        blacklist_words = [
            "usług", "zakupu", "naturze", "sprzedaż", "towarów", "zakup", "spółka",
            "materiałów", "artykułów", "przeznaczone"
        ]
        
        # Check if text contains any blacklisted phrases
        text_lower = text_clean.lower()
        for phrase in blacklist_phrases:
            if phrase in text_lower:
                return False
        
        # Check if text contains only blacklisted words
        words = text_lower.split()
        if all(word in blacklist_words for word in words if word):
            return False
        
        # Pattern for invoice numbers
        invoice_patterns = [
            r'\b\d+/\d+/\d+\b',          # 123/456/789
            r'\b\d+/\d+\b',              # 123/456  
            r'\b[A-Z]+/\d+/\d+/\d+\b',   # ABC/123/456/789
            r'\b[A-Z]+\d+/\d+\b',        # ABC123/456
            r'\b\d+/[A-Z]+/\d+\b',       # 123/ABC/456
            r'\b[A-Z]\d+\b',             # A123
        ]
        
        for pattern in invoice_patterns:
            if re.search(pattern, text_clean):
                return True
        
        return False

    def browse_file(self):
        """Open file dialog to select PDF file"""
        file_path = filedialog.askopenfilename(
            title="Wybierz plik PDF z księgą",
            filetypes=[("PDF files", "*.pdf")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.file_label.configure(text=f"✓ {os.path.basename(file_path)}")
            self.status_label.configure(text="Plik wybrany")

    def start_processing(self):
        """Start OCR processing in separate thread"""
        if not self.file_path_var.get():
            messagebox.showerror("Błąd", "Najpierw wybierz plik PDF")
            return
        
        if self.processing_thread and self.processing_thread.is_alive():
            messagebox.showwarning("Ostrzeżenie", "Przetwarzanie już trwa")
            return
        
        # Clear previous results
        self.text_area.delete("1.0", "end")
        self.processing_cancelled = False
        
        # Update UI
        self.process_button.configure(text="Anuluj przetwarzanie")
        self.status_label.configure(text="Rozpoczynam przetwarzanie...")
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._process_pdf_threaded,
            args=(self.file_path_var.get(),),
            daemon=True
        )
        self.processing_thread.start()

    def cancel_processing(self):
        """Cancel current processing"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_cancelled = True
            self.result_queue.put({'type': 'processing_cancelled'})

    def toggle_processing(self):
        """Toggle between start and cancel processing"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.cancel_processing()
        else:
            self.start_processing()

    def save_ocr_log(self, ocr_log_data):
        """Save OCR log data to file"""
        try:
            with open(OCR_LOG_FILE, "w", encoding="utf-8") as f:
                f.write("OCR Log\n")
                f.write("=" * 50 + "\n\n")
                for entry in ocr_log_data:
                    f.write(f"Strona {entry['page']}, Linia {entry['line_num']}: {entry['line']}\n")
        except Exception as e:
            print(f"Błąd zapisywania loga: {e}")

    def save_invoice_numbers_to_csv(self, invoice_numbers):
        """Save invoice numbers to CSV file"""
        try:
            # Create the directory if it doesn't exist
            directory = "odczyty"
            if not os.path.exists(directory):
                os.makedirs(directory)
            
            csv_file_path = os.path.join(directory, "zakupy.csv")
            
            with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Numer faktury"])  # Header
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
                messagebox.showinfo("Podgląd logów", "Brak pliku loga. Najpierw wykonaj odczyt OCR.")
                return
                
            with open(OCR_LOG_FILE, "r", encoding="utf-8") as f:
                log_content = f.read()
            
            # Create new window
            log_window = ctk.CTkToplevel(self)
            log_window.title("Podgląd loga OCR")
            log_window.geometry("800x700")
            log_window.transient(self)
            log_window.grab_set()
            
            # Create text widget
            text_widget = ScrolledText(log_window, wrap="word", width=57, height=35)
            text_widget.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Insert log content
            text_widget.insert("1.0", log_content)
            
            # Add close button
            close_btn = ctk.CTkButton(log_window, text="Zamknij", command=log_window.destroy)
            close_btn.pack(pady=10)
            
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
                        self.text_area.insert("end", f"{cleaned_line}\n")
                    elif result['type'] == 'csv_export_success':
                        # Show CSV export success messagebox
                        messagebox.showinfo("Eksport zakończony", f"Wyeksportowano {result['invoice_count']} numerów do odczyty/zakupy.csv")
                    elif result['type'] == 'csv_export_error':
                        # Show CSV export error
                        messagebox.showerror("Błąd eksportu CSV", f"Błąd podczas zapisywania CSV: {result['error']}")
                    elif result['type'] == 'processing_complete':
                        # Restore button state and show final results
                        self.process_button.configure(text="Odczytaj numery faktur")
                        
                        # Updated summary format: show total lines and detected invoice numbers separately
                        invoice_info = f" (wykryto {result['invoice_count']} numerów faktur)" if result['invoice_count'] > 0 else " (wykryto 0 numerów faktur)"
                        csv_info = " → zapisano do CSV" if result.get('csv_saved', False) else ""
                        self.status_label.configure(
                            text=f"OCR z kolumny gotowy, {result['total_lines']} linii z {result['total_pages']} stron{invoice_info}{csv_info}"
                        )
                    elif result['type'] == 'processing_error':
                        # Show error and restore button
                        self.process_button.configure(text="Odczytaj numery faktur")
                        messagebox.showerror("Błąd OCR z kolumny", result['error'])
                        self.status_label.configure(text="Błąd OCR kolumny")
                    elif result['type'] == 'processing_cancelled':
                        # Processing was cancelled
                        self.process_button.configure(text="Odczytaj numery faktur")
                        self.status_label.configure(text="Przetwarzanie anulowane")
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
                    self.status_label.configure(text=progress)
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Błąd przetwarzania kolejki postępu: {e}")
        
        # Schedule next check
        self.after(100, self._process_progress_queue)

    def _process_pdf_threaded(self, file_path):
        """Process PDF in background thread with multiprocessing OCR"""
        try:
            self.progress_queue.put("Konwertowanie PDF na obrazy...")
            
            # Convert PDF to images  
            images = convert_from_path(file_path, poppler_path=POPPLER_PATH)
            total_pages = len(images)
            
            if self.processing_cancelled:
                return
                
            # Prepare crops for batch processing
            crops = []
            for page_num, image in enumerate(images, 1):
                if self.processing_cancelled:
                    return
                    
                self.progress_queue.put(f"Przygotowuję obraz strony {page_num}/{total_pages}...")
                
                # Crop the image to invoice column area
                crop = image.crop((CROP_LEFT, CROP_TOP, CROP_RIGHT, CROP_BOTTOM))
                crops.append((crop, page_num))
            
            if self.processing_cancelled:
                return
            
            # Process all crops with multiprocessing OCR
            self.progress_queue.put("Wykonuję OCR z wieloprocesowością...")
            
            # Use OCR manager for batch processing
            ocr_results = ocr_manager.perform_ocr_batch(
                [crop for crop, _ in crops], 
                language='pol+eng'
            )
            
            # Process results
            all_lines = []
            invoice_numbers = []
            invoice_count = 0
            ocr_log_data = []
            
            for i, (ocr_text, (crop, page_num)) in enumerate(zip(ocr_results, crops)):
                if self.processing_cancelled:
                    return
                    
                if not ocr_text:
                    # Fallback to single processing if batch failed
                    ocr_text = ocr_manager.perform_ocr_single(crop, 'pol+eng')
                
                # Process OCR text line by line
                lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
                
                line_counter = 0
                for line in lines:
                    if self.processing_cancelled:
                        return
                        
                    line_counter += 1
                    all_lines.append(line)
                    
                    # Add to log data
                    ocr_log_data.append({
                        'page': page_num,
                        'line_num': line_counter,
                        'line': line
                    })
                    
                    # Check if line contains invoice number
                    if self.contains_invoice_number(line):
                        invoice_count += 1
                        invoice_numbers.append(line)
                        
                        # Send line to UI for display
                        self.result_queue.put({
                            'type': 'ocr_line',
                            'page': page_num,
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
                self.result_queue.put({
                    'type': 'processing_complete',
                    'total_lines': len(all_lines),
                    'total_pages': total_pages,
                    'invoice_count': invoice_count,
                    'csv_saved': csv_saved
                })

        except Exception as e:
            if not self.processing_cancelled:
                self.result_queue.put({
                    'type': 'processing_error',
                    'error': str(e)
                })
        
    def create_widgets(self):
        """Create CustomTkinter widgets for the purchases tab"""
        
        # Title section
        title_label = ctk.CTkLabel(self, text="🛒 Odczyt Numerów Faktur", font=("Arial", 20, "bold"))
        title_label.pack(pady=(0, 20), anchor="w")

        # File selection section
        file_frame = ctk.CTkFrame(self)
        file_frame.pack(fill="x", pady=(0, 10))
        
        file_title = ctk.CTkLabel(file_frame, text="📄 Wybór pliku PDF", font=("Arial", 14, "bold"))
        file_title.pack(pady=(15, 10), anchor="w", padx=15)
        
        # File selection controls
        file_controls_frame = ctk.CTkFrame(file_frame)
        file_controls_frame.pack(fill="x", pady=(0, 15), padx=15)
        
        self.browse_button = ctk.CTkButton(file_controls_frame, text="Wybierz plik PDF", command=self.browse_file)
        self.browse_button.pack(side="left", padx=(0, 10))
        
        self.file_label = ctk.CTkLabel(file_controls_frame, text="Brak wybranego pliku")
        self.file_label.pack(side="left")

        # Action buttons section
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", pady=(0, 10))
        
        action_title = ctk.CTkLabel(action_frame, text="⚡ Akcje", font=("Arial", 14, "bold"))
        action_title.pack(pady=(15, 10), anchor="w", padx=15)
        
        button_controls_frame = ctk.CTkFrame(action_frame)
        button_controls_frame.pack(fill="x", pady=(0, 15), padx=15)
        
        self.process_button = ctk.CTkButton(button_controls_frame, text="Odczytaj numery faktur", command=self.toggle_processing)
        self.process_button.pack(side="left", padx=(0, 10))
        
        self.log_button = ctk.CTkButton(button_controls_frame, text="Podgląd logów", command=self.show_ocr_log_preview)
        self.log_button.pack(side="left")
        
        # Status
        self.status_label = ctk.CTkLabel(button_controls_frame, text="● Plik nie wybrany")
        self.status_label.pack(side="left", padx=(15, 0))

        # Results section
        results_frame = ctk.CTkFrame(self)
        results_frame.pack(fill="both", expand=True)
        
        results_title = ctk.CTkLabel(results_frame, text="📊 Wyniki OCR", font=("Arial", 14, "bold"))
        results_title.pack(pady=(15, 10), anchor="w", padx=15)
        
        # Create text area with fixed width (47 characters = ~10cm)
        self.text_area = ScrolledText(results_frame, wrap="word", width=47, height=25)
        self.text_area.pack(fill="both", expand=True, padx=15, pady=(0, 15))