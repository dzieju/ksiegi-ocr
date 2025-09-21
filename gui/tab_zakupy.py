import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import os
import pytesseract
from pdf2image import convert_from_path
from PIL import ImageEnhance
import threading
import queue
import time
import re

# Configuration paths (same as in tab_ksiegi.py)
POPPLER_PATH = r"C:\poppler\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Crop coordinates for invoice numbers column (same as in tab_ksiegi.py)
CROP_LEFT, CROP_RIGHT = 503, 771
CROP_TOP, CROP_BOTTOM = 332, 2377

# OCR enhancement settings
# Contrast enhancement factor - higher values increase contrast
# To change contrast: modify CONTRAST_FACTOR value (recommended range: 1.0-3.0)
# 1.0 = no enhancement, 2.0 = double contrast, 3.0 = triple contrast
CONTRAST_FACTOR = 2.0

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

    def contains_invoice_number(self, text):
        """
        Check if text contains invoice number using fuzzy matching.
        Uses regex pattern allowing missing 'F' at the beginning: r'(F?/?\\d{5}/\\d{2}/\\d{2}/M1)'
        """
        # Primary pattern with optional F prefix - handles all variations:
        # F/12345/01/25/M1, /12345/01/25/M1, 12345/01/25/M1
        pattern = r'(?:F/|/|^|\s)?\d{5}/\d{2}/\d{2}/M1'
        
        if re.search(pattern, text):
            return True
            
        # Additional patterns for other invoice formats (from tab_ksiegi.py)
        additional_patterns = [
            r"\b\d{5}/\d{2}/\d{4}/UP\b",
            r"\b\d{5}/\d{2}\b",
            r"\b\d{3}/\d{4}\b",
            r"\bF/M\d{2}/\d{7}/\d{2}/\d{2}\b",
            r"\b\d{2}/\d{2}/\d{4}\b",
            r"\b\d{1,2}/\d{2}/\d{4}\b"
        ]
        
        for pattern in additional_patterns:
            if re.search(pattern, text):
                return True
                
        return False

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
            
            # Create text widget with scrollbar
            text_widget = ScrolledText(log_window, wrap="word", width=100, height=35)
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
                        # Add OCR line to text area
                        self.text_area.insert(tk.END, f"strona {result['page_num']}, linia {result['line_num']}: {result['line']}\n")
                    elif result['type'] == 'processing_complete':
                        # Restore button state and show final results
                        self.process_button.config(text="Odczytaj numery faktur")
                        
                        # Resize text area to 50% width
                        current_width = self.text_area.cget("width")
                        new_width = int(current_width * 0.5)
                        self.text_area.config(width=new_width)
                        
                        invoice_info = f" (znaleziono {result['invoice_count']} faktur)" if result['invoice_count'] > 0 else ""
                        self.status_label.config(
                            text=f"OCR z kolumny gotowy, {result['total_lines']} linii z {result['total_pages']} stron{invoice_info}", 
                            foreground="green"
                        )
                    elif result['type'] == 'processing_error':
                        # Show error and restore button
                        self.process_button.config(text="Odczytaj numery faktur")
                        messagebox.showerror("Błąd OCR z kolumny", result['error'])
                        self.status_label.config(text="Błąd OCR kolumny", foreground="red")
                    elif result['type'] == 'processing_cancelled':
                        # Processing was cancelled
                        self.process_button.config(text="Odczytaj numery faktur")
                        self.status_label.config(text="Przetwarzanie anulowane", foreground="orange")
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
        self.text_area.delete("1.0", tk.END)
        
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
        try:
            self.progress_queue.put("Konwertowanie PDF na obrazy...")
            
            # Convert PDF to images
            images = convert_from_path(filepath, dpi=300, poppler_path=POPPLER_PATH)
            total_pages = len(images)
            
            if self.processing_cancelled:
                self.result_queue.put({'type': 'processing_cancelled'})
                return
            
            self.result_queue.put({'type': 'ocr_line', 'page_num': 0, 'line_num': 0, 'line': "----- Linie OCR -----"})
            
            all_lines = []
            ocr_log_data = []  # Store raw OCR data for logging
            line_counter = 0
            invoice_count = 0  # Count detected invoice numbers
            
            for page_num, pil_img in enumerate(images, 1):
                if self.processing_cancelled:
                    self.result_queue.put({'type': 'processing_cancelled'})
                    return
                
                self.progress_queue.put(f"Przetwarzanie strony {page_num} z {total_pages}...")
                
                # Crop the image to the specified region
                crop = pil_img.crop((CROP_LEFT, CROP_TOP, CROP_RIGHT, CROP_BOTTOM))
                
                # Enhance contrast to improve OCR accuracy
                # To modify contrast: change CONTRAST_FACTOR constant at the top of the file
                enhancer = ImageEnhance.Contrast(crop)
                crop_enhanced = enhancer.enhance(CONTRAST_FACTOR)
                
                # Perform OCR on the enhanced image
                ocr_text = pytesseract.image_to_string(crop_enhanced, lang='pol+eng')
                
                # Process lines
                lines = [l.strip() for l in ocr_text.split('\n') if l.strip()]
                
                for line in lines:
                    if self.processing_cancelled:
                        self.result_queue.put({'type': 'processing_cancelled'})
                        return
                    
                    line_counter += 1
                    all_lines.append((page_num, line))
                    ocr_log_data.append((page_num, line))  # Add to log data
                    
                    # Check if line contains invoice number
                    if self.contains_invoice_number(line):
                        invoice_count += 1
                        # Highlight invoice numbers in display
                        display_line = f"[FAKTURA] {line}"
                    else:
                        display_line = line
                    
                    # Send line to GUI
                    self.result_queue.put({
                        'type': 'ocr_line',
                        'page_num': page_num,
                        'line_num': line_counter,
                        'line': display_line
                    })
                
                # Small delay to allow GUI updates and cancellation
                time.sleep(0.01)

            # Save OCR log (always overwrite)
            if not self.processing_cancelled:
                self.save_ocr_log(ocr_log_data)

            # Processing complete
            if not self.processing_cancelled:
                self.result_queue.put({
                    'type': 'processing_complete',
                    'total_lines': len(all_lines),
                    'total_pages': total_pages,
                    'invoice_count': invoice_count
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
            
    def odczytaj_numery_faktur_old(self):
        """OCR funkcja odczytu numerów faktur z kolumny - oparta na run_column_ocr z tab_ksiegi.py
        
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
                
                # Enhance contrast to improve OCR accuracy
                # To modify contrast: change CONTRAST_FACTOR constant at the top of the file
                enhancer = ImageEnhance.Contrast(crop)
                crop_enhanced = enhancer.enhance(CONTRAST_FACTOR)
                
                ocr_text = pytesseract.image_to_string(crop_enhanced, lang='pol+eng')
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