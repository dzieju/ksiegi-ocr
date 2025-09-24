import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import pytesseract
from pdf2image import convert_from_path
import threading
import queue
import time
import re
import csv
from tools.ocr_engines import ocr_manager
from gui.modern_theme import ModernTheme
from gui.tooltip_utils import add_tooltip, TOOLTIPS

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
        super().__init__(parent, **ModernTheme.get_frame_style('section'))
        
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
            log_window = ctk.CTkToplevel(self)
            log_window.title("Podgląd loga OCR")
            log_window.geometry("800x700")
            log_window.transient(self)
            log_window.grab_set()
            
            # Create text widget (consistent with main report width)
            text_widget = ctk.CTkTextbox(log_window, **ModernTheme.get_textbox_style())
            text_widget.pack(fill="both", expand=True, padx=ModernTheme.SPACING['medium'], pady=ModernTheme.SPACING['medium'])
            
            # Insert log content
            text_widget.insert("1.0", log_content)
            
            # Add close button
            close_btn = ctk.CTkButton(
                log_window, 
                text="Zamknij", 
                command=log_window.destroy,
                **ModernTheme.get_button_style('secondary')
            )
            close_btn.pack(pady=ModernTheme.SPACING['small'])
            
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
                            text=f"OCR z kolumny gotowy, {result['total_lines']} linii z {result['total_pages']} stron{invoice_info}{csv_info}", 
                            text_color=ModernTheme.COLORS['success']
                        )
                    elif result['type'] == 'processing_error':
                        # Show error and restore button
                        self.process_button.configure(text="Odczytaj numery faktur")
                        messagebox.showerror("Błąd OCR z kolumny", result['error'])
                        self.status_label.configure(text="Błąd OCR kolumny", text_color=ModernTheme.COLORS['error'])
                    elif result['type'] == 'processing_cancelled':
                        # Processing was cancelled
                        self.process_button.configure(text="Odczytaj numery faktur")
                        self.status_label.configure(text="Przetwarzanie anulowane", text_color=ModernTheme.COLORS['warning'])
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
                    self.status_label.configure(text=progress, text_color=ModernTheme.COLORS['warning'])
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
        self.status_label.configure(text="Anulowanie...", text_color=ModernTheme.COLORS['warning'])
        self.process_button.configure(text="Odczytaj numery faktur")

    def start_processing(self):
        """Start the threaded OCR processing"""
        filepath = self.file_path_var.get().strip()
        
        if not filepath:
            messagebox.showwarning("Brak pliku", "Proszę najpierw wybrać plik PDF.")
            return
            
        if not os.path.exists(filepath):
            messagebox.showwarning("Brak pliku", "Wybierz poprawny plik PDF.")
            return

        # Clear previous results
        self.text_area.delete("1.0", "end")
        
        # Reset cancellation flag
        self.processing_cancelled = False
        
        # Update UI
        self.process_button.configure(text="Anuluj przetwarzanie")
        self.status_label.configure(text="Rozpoczynam przetwarzanie...", text_color=ModernTheme.COLORS['warning'])

        # Start processing in background thread
        self.processing_thread = threading.Thread(
            target=self._threaded_ocr_processing,
            args=(filepath,),
            daemon=True
        )
        self.processing_thread.start()

    def _threaded_ocr_processing(self, filepath):
        """Main OCR processing logic running in background thread"""
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
        """Create modern CustomTkinter widgets for the purchases tab"""
        
        # Title section
        title_label = ctk.CTkLabel(
            self,
            text="🛒 Odczyt Numerów Faktur",
            **ModernTheme.get_label_style('heading')
        )
        title_label.pack(pady=(0, ModernTheme.SPACING['large']), anchor="w")

        # File selection section
        file_frame = ctk.CTkFrame(self, **ModernTheme.get_frame_style('card'))
        file_frame.pack(fill="x", pady=(0, ModernTheme.SPACING['medium']))
        
        file_title = ctk.CTkLabel(
            file_frame,
            text="📄 Wybór pliku PDF",
            **ModernTheme.get_label_style('subheading')
        )
        file_title.pack(pady=(ModernTheme.SPACING['medium'], ModernTheme.SPACING['small']), anchor="w", padx=ModernTheme.SPACING['medium'])

        # File input row
        file_input_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_input_frame.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(0, ModernTheme.SPACING['medium']))

        self.file_path_entry = ctk.CTkEntry(
            file_input_frame,
            textvariable=self.file_path_var,
            placeholder_text="Wybierz plik PDF z fakturami...",
            **ModernTheme.get_entry_style()
        )
        self.file_path_entry.pack(side="left", fill="x", expand=True, padx=(0, ModernTheme.SPACING['small']))

        select_file_btn = ctk.CTkButton(
            file_input_frame,
            text="Wybierz plik",
            command=self.wybierz_plik_pdf,
            **ModernTheme.get_button_style('secondary')
        )
        select_file_btn.pack(side="right")
        add_tooltip(select_file_btn, TOOLTIPS['pdf_select'])

        # Processing section
        process_frame = ctk.CTkFrame(self, **ModernTheme.get_frame_style('card'))
        process_frame.pack(fill="x", pady=(0, ModernTheme.SPACING['medium']))
        
        process_title = ctk.CTkLabel(
            process_frame,
            text="⚡ Przetwarzanie OCR",
            **ModernTheme.get_label_style('subheading')
        )
        process_title.pack(pady=(ModernTheme.SPACING['medium'], ModernTheme.SPACING['small']), anchor="w", padx=ModernTheme.SPACING['medium'])

        # Process buttons row
        process_buttons_frame = ctk.CTkFrame(process_frame, fg_color="transparent")
        process_buttons_frame.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(0, ModernTheme.SPACING['small']))

        self.process_button = ctk.CTkButton(
            process_buttons_frame,
            text="Odczytaj numery faktur",
            command=self.toggle_processing,
            **ModernTheme.get_button_style('primary')
        )
        self.process_button.pack(side="left", padx=(0, ModernTheme.SPACING['small']))
        add_tooltip(self.process_button, TOOLTIPS['ocr_process'])

        self.log_preview_button = ctk.CTkButton(
            process_buttons_frame,
            text="Podgląd logów OCR",
            command=self.show_ocr_log_preview,
            **ModernTheme.get_button_style('secondary')
        )
        self.log_preview_button.pack(side="left")
        add_tooltip(self.log_preview_button, TOOLTIPS['ocr_preview'])

        # Status
        self.status_label = ctk.CTkLabel(
            process_frame,
            text="Brak wybranego pliku",
            **ModernTheme.get_label_style('secondary')
        )
        self.status_label.pack(pady=(0, ModernTheme.SPACING['medium']), anchor="w", padx=ModernTheme.SPACING['medium'])

        # Results section
        results_frame = ctk.CTkFrame(self, **ModernTheme.get_frame_style('card'))
        results_frame.pack(fill="both", expand=True)
        
        results_title = ctk.CTkLabel(
            results_frame,
            text="📊 Wyniki OCR",
            **ModernTheme.get_label_style('subheading')
        )
        results_title.pack(pady=(ModernTheme.SPACING['medium'], ModernTheme.SPACING['small']), anchor="w", padx=ModernTheme.SPACING['medium'])

        # Text area for OCR results
        self.text_area = ctk.CTkTextbox(
            results_frame,
            **ModernTheme.get_textbox_style()
        )
        self.text_area.pack(fill="both", expand=True, padx=ModernTheme.SPACING['medium'], pady=(0, ModernTheme.SPACING['medium']))
        
    def wybierz_plik_pdf(self):
        """Funkcja do wyboru pliku PDF"""
        filepath = filedialog.askopenfilename(
            title="Wybierz plik PDF", 
            filetypes=[("PDF files", "*.pdf")]
        )
        if filepath:
            self.file_path_var.set(filepath)
            self.status_label.configure(text="Plik wybrany", text_color=ModernTheme.COLORS['success'])
            
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
            self.text_area.insert("end", "----- Rozpoznane numery faktur -----\n")
            invoice_count = 0
            for i, (page_num, line) in enumerate(all_lines, 1):
                if self.contains_invoice_number(line):
                    invoice_count += 1
                    # Clean the invoice name by removing leading '|' and spaces
                    cleaned_line = self.clean_invoice_name(line)
                    self.text_area.insert("end", f"{cleaned_line}\n")

            self.status_label.configure(text=f"OCR z kolumny gotowy, {len(all_lines)} linii z {len(images)} stron (wykryto {invoice_count} numerów faktur)", text_color=ModernTheme.COLORS['success'])

        except Exception as e:
            messagebox.showerror("Błąd OCR z kolumny", str(e))
            self.status_label.configure(text="Błąd OCR kolumny", text_color=ModernTheme.COLORS['error'])