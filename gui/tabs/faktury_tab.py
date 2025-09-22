import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pdfplumber
import threading
import queue

class FakturyTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Threading support variables
        self.processing_cancelled = False
        self.processing_thread = None
        self.result_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        
        self.create_widgets()
        
        # Start processing queues
        self._process_result_queue()
        self._process_progress_queue()
    
    def create_widgets(self):
        # File path display
        self.file_path_var = tk.StringVar()
        file_frame = tk.Frame(self)
        file_frame.pack(pady=5, fill="x", padx=10)
        
        tk.Label(file_frame, text="Wybrany plik:").pack(side="left")
        tk.Entry(file_frame, textvariable=self.file_path_var, state="readonly", width=50).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(file_frame, text="Wybierz PDF", command=self.wybierz_pdf).pack(side="right")

        # Process button and status
        control_frame = tk.Frame(self)
        control_frame.pack(pady=10)
        
        self.process_button = tk.Button(control_frame, text="Wczytaj plik PDF", command=self.toggle_processing)
        self.process_button.pack(side="left", padx=5)
        
        self.status_label = tk.Label(control_frame, text="Gotowy", foreground="green")
        self.status_label.pack(side="left", padx=10)

        # Output text area
        self.text_output = tk.Text(self, width=100, height=25)
        self.text_output.pack(padx=10, pady=10, fill="both", expand=True)
    
    def wybierz_pdf(self):
        """Choose PDF file"""
        filepath = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if filepath:
            self.file_path_var.set(filepath)
            self.status_label.config(text="Plik wybrany", foreground="green")
    
    def toggle_processing(self):
        """Toggle between starting and cancelling PDF processing"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.cancel_processing()
        else:
            self.start_processing()
    
    def cancel_processing(self):
        """Cancel ongoing PDF processing"""
        self.processing_cancelled = True
        self.status_label.config(text="Anulowanie...", foreground="orange")
        self.process_button.config(text="Wczytaj plik PDF")
    
    def start_processing(self):
        """Start the threaded PDF processing"""
        filepath = self.file_path_var.get().strip()
        
        if not filepath:
            messagebox.showwarning("Brak pliku", "Proszę najpierw wybrać plik PDF.")
            return
            
        # Clear previous results
        self.text_output.delete("1.0", tk.END)
        
        # Reset cancellation flag
        self.processing_cancelled = False
        
        # Update UI
        self.process_button.config(text="Anuluj przetwarzanie")
        self.status_label.config(text="Rozpoczynam przetwarzanie...", foreground="blue")

        # Start processing in background thread
        self.processing_thread = threading.Thread(
            target=self._threaded_pdf_processing,
            args=(filepath,),
            daemon=True
        )
        self.processing_thread.start()
    
    def _threaded_pdf_processing(self, filepath):
        """Main PDF processing logic running in background thread"""
        try:
            wynik_linii = []
            
            with pdfplumber.open(filepath) as pdf:
                total_pages = len(pdf.pages)
                self.progress_queue.put(f"Przetwarzanie PDF z {total_pages} stronami...")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    if self.processing_cancelled:
                        self.result_queue.put({'type': 'processing_cancelled'})
                        return
                    
                    self.progress_queue.put(f"Przetwarzanie strony {page_num} z {total_pages}...")
                    
                    table = page.extract_table()
                    if table and len(table) > 3:
                        headers = table[0]
                        
                        try:
                            # Find column indices by names
                            idx_lp = next(i for i, h in enumerate(headers) if h and "l.p" in h.lower())
                            idx_nr = next(i for i, h in enumerate(headers) if h and "nr dowodu księgowego" in h.lower())
                            idx_koszty = next(i for i, h in enumerate(headers) if h and "koszty prowadzenia działalności" in h.lower())

                            for row in table[2:]:  # Skip first two rows
                                if self.processing_cancelled:
                                    self.result_queue.put({'type': 'processing_cancelled'})
                                    return
                                    
                                if len(row) <= max(idx_lp, idx_nr, idx_koszty):
                                    continue
                                lp = row[idx_lp]
                                nr_dowodu = row[idx_nr]
                                koszty = row[idx_koszty]
                                if lp and nr_dowodu and koszty:
                                    wynik_linii.append((lp, nr_dowodu, koszty))
                        except StopIteration:
                            continue
            
            # Send results to main thread
            self.result_queue.put({
                'type': 'processing_complete',
                'data': wynik_linii
            })
            
        except Exception as e:
            self.result_queue.put({
                'type': 'processing_error',
                'error': str(e)
            })
    
    def _process_result_queue(self):
        """Process results from worker thread"""
        try:
            while True:
                try:
                    result = self.result_queue.get_nowait()
                    
                    if result['type'] == 'processing_complete':
                        wynik_linii = result['data']
                        self._display_results(wynik_linii)
                        self.status_label.config(text=f"Zakończono - znaleziono {len(wynik_linii)} rekordów", foreground="green")
                        self.process_button.config(text="Wczytaj plik PDF")
                        
                    elif result['type'] == 'processing_cancelled':
                        self.status_label.config(text="Przetwarzanie anulowane", foreground="orange")
                        self.process_button.config(text="Wczytaj plik PDF")
                        
                    elif result['type'] == 'processing_error':
                        error_msg = result['error']
                        messagebox.showerror("Błąd", f"Nie udało się odczytać pliku:\n{error_msg}")
                        self.status_label.config(text="Błąd przetwarzania", foreground="red")
                        self.process_button.config(text="Wczytaj plik PDF")
                        
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
    
    def _display_results(self, wynik_linii):
        """Display processing results"""
        self.text_output.delete("1.0", tk.END)
        if wynik_linii:
            self.text_output.insert(tk.END, f"{'L.p.':<10} {'Nr dowodu księgowego':<30} {'Koszty działalności':<40}\n")
            self.text_output.insert(tk.END, "-" * 85 + "\n")
            for lp, nr_dowodu, koszty in wynik_linii:
                self.text_output.insert(tk.END, f"{lp:<10} {nr_dowodu:<30} {koszty:<40}\n")
        else:
            self.text_output.insert(tk.END, "Nie znaleziono danych w wymaganych kolumnach.")
    
    def destroy(self):
        """Cleanup when widget is destroyed"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_cancelled = True
        super().destroy()


