import tkinter as tk
from tkinter import ttk, messagebox
import queue
import multiprocessing
from tools import logger, i18n, darkmode
from tools.ocr_config import ocr_config
from tools.system_requirements import SystemRequirementsChecker
from tools.live_logger import get_live_logger
from gui.system_components.backup_handler import BackupHandler
from gui.system_components.system_operations import SystemOperations


class SystemTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Threading support variables
        self.result_queue = queue.Queue()
        self.progress_queue = queue.Queue()

        # Initialize handlers
        self.backup_handler = BackupHandler(self._add_result)
        self.system_ops = SystemOperations(self._add_result)
        
        # OCR configuration variables
        self.ocr_engine_var = tk.StringVar(value=ocr_config.get_engine())
        self.gpu_enabled_var = tk.BooleanVar(value=ocr_config.get_use_gpu())
        self.multiprocessing_var = tk.BooleanVar(value=ocr_config.get_multiprocessing())
        self.max_workers_var = tk.StringVar(value=str(ocr_config.get_max_workers() or "Auto"))

        # System requirements checker
        self.requirements_checker = SystemRequirementsChecker()
        
        # Live logger setup
        self.live_logger = get_live_logger()
        self.live_logger.start_capture()
        self.live_logger.clear_logs()  # Start with fresh logs

        self.create_widgets()
        
        # Start processing queues
        self._process_result_queue()
        self._process_progress_queue()
        
        # Update requirements display
        self._update_requirements_display()
    
    def create_widgets(self):
        # Configure main grid weights for responsive layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Logs area gets extra space
        
        # === 1. SYSTEM REQUIREMENTS CHECKLIST (TOP) ===
        self._create_requirements_section()
        
        # === 2. DIAGNOSTIC/CONFIG CONTROLS (MIDDLE) ===
        self._create_controls_section()
        
        # === 3. LIVE LOGS DISPLAY (BOTTOM) ===
        self._create_logs_section()
    
    def _create_requirements_section(self):
        """Create the system requirements checklist at the top."""
        req_frame = ttk.LabelFrame(self, text="Wymagania systemowe", padding="10")
        req_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        req_frame.grid_columnconfigure(0, weight=1)
        
        # Requirements grid container
        self.req_grid = ttk.Frame(req_frame)
        self.req_grid.grid(row=0, column=0, sticky="ew")
        
        # Configure grid for 3 columns
        for i in range(3):
            self.req_grid.grid_columnconfigure(i, weight=1)
        
        # Will be populated by _update_requirements_display()
        self.requirement_labels = {}
    
    def _create_controls_section(self):
        """Create the grouped diagnostic and configuration controls."""
        controls_frame = ttk.Frame(self)
        controls_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=1) 
        controls_frame.grid_columnconfigure(2, weight=1)
        
        # === PDF/BACKUP GROUP ===
        pdf_group = ttk.LabelFrame(controls_frame, text="PDF & Backup", padding="5")
        pdf_group.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        # Backup buttons
        self.backup_btn = ttk.Button(pdf_group, text="Utwórz backup", command=self.create_backup)
        self.backup_btn.pack(fill="x", pady=2)
        
        self.restore_btn = ttk.Button(pdf_group, text="Przywróć backup", command=self.restore_backup)
        self.restore_btn.pack(fill="x", pady=2)
        
        # === OCR GROUP ===
        ocr_group = ttk.LabelFrame(controls_frame, text="Konfiguracja OCR", padding="5")
        ocr_group.grid(row=0, column=1, sticky="ew", padx=5)
        
        # OCR Engine selection
        engine_frame = ttk.Frame(ocr_group)
        engine_frame.pack(fill="x", pady=2)
        ttk.Label(engine_frame, text="Silnik:").pack(side="left")
        ocr_engine_combo = ttk.Combobox(engine_frame, textvariable=self.ocr_engine_var, 
                                       width=12, state="readonly")
        ocr_engine_combo['values'] = ("tesseract", "easyocr", "paddleocr")
        ocr_engine_combo.pack(side="right")
        ocr_engine_combo.bind('<<ComboboxSelected>>', self._on_engine_change)
        
        # GPU checkbox
        gpu_checkbox = ttk.Checkbutton(ocr_group, text="Użyj GPU", 
                                      variable=self.gpu_enabled_var, command=self._on_gpu_change)
        gpu_checkbox.pack(fill="x", pady=2)
        
        # Multiprocessing checkbox
        mp_checkbox = ttk.Checkbutton(ocr_group, text="Wieloprocesowość", 
                                     variable=self.multiprocessing_var, command=self._on_multiprocessing_change)
        mp_checkbox.pack(fill="x", pady=2)
        
        # Workers setting
        workers_frame = ttk.Frame(ocr_group)
        workers_frame.pack(fill="x", pady=2)
        ttk.Label(workers_frame, text="Procesy:").pack(side="left")
        self.workers_entry = ttk.Entry(workers_frame, textvariable=self.max_workers_var, width=8)
        self.workers_entry.pack(side="right")
        self.workers_entry.bind('<KeyRelease>', self._on_workers_change)
        
        # Save config button
        save_ocr_btn = ttk.Button(ocr_group, text="Zapisz konfigurację", command=self._save_ocr_config)
        save_ocr_btn.pack(fill="x", pady=2)
        
        # === SYSTEM GROUP ===
        system_group = ttk.LabelFrame(controls_frame, text="System & Diagnostyka", padding="5")
        system_group.grid(row=0, column=2, sticky="ew", padx=(5, 0))
        
        # Status label at top
        self.status_label = ttk.Label(system_group, text="Gotowy", foreground="green")
        self.status_label.pack(fill="x", pady=2)
        
        # Update check
        self.update_btn = ttk.Button(system_group, text="Sprawdź aktualizacje", command=self.check_update)
        self.update_btn.pack(fill="x", pady=2)
        
        # Report
        self.report_btn = ttk.Button(system_group, text="Wyślij raport", command=self.send_report)
        self.report_btn.pack(fill="x", pady=2)
        
        # Theme toggle
        theme_btn = ttk.Button(system_group, text="Przełącz motyw", command=darkmode.toggle_theme)
        theme_btn.pack(fill="x", pady=2)
        
        # Restart
        restart_btn = ttk.Button(system_group, text="Restart aplikacji", command=self.restart_app)
        restart_btn.pack(fill="x", pady=2)
        
        # Refresh requirements
        refresh_btn = ttk.Button(system_group, text="Odśwież wymagania", command=self._update_requirements_display)
        refresh_btn.pack(fill="x", pady=2)
    
    def _create_logs_section(self):
        """Create the live logs display area at the bottom."""
        logs_frame = ttk.LabelFrame(self, text="Logi bieżącej sesji", padding="5")
        logs_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        logs_frame.grid_columnconfigure(0, weight=1)
        logs_frame.grid_rowconfigure(1, weight=1)
        
        # Logs control buttons
        logs_controls = ttk.Frame(logs_frame)
        logs_controls.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        ttk.Button(logs_controls, text="Wyczyść logi", command=self._clear_logs).pack(side="left")
        ttk.Button(logs_controls, text="Odśwież", command=self._refresh_logs).pack(side="left", padx=(5, 0))
        
        # Logs text area with scrollbar
        logs_text_frame = ttk.Frame(logs_frame)
        logs_text_frame.grid(row=1, column=0, sticky="nsew")
        logs_text_frame.grid_columnconfigure(0, weight=1)
        logs_text_frame.grid_rowconfigure(0, weight=1)
        
        self.logs_text = tk.Text(logs_text_frame, wrap="word", height=10, font=("Consolas", 9))
        self.logs_text.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar for logs
        logs_scrollbar = ttk.Scrollbar(logs_text_frame, orient="vertical", command=self.logs_text.yview)
        logs_scrollbar.grid(row=0, column=1, sticky="ns")
        self.logs_text.configure(yscrollcommand=logs_scrollbar.set)
        
        # Initial logs display
        self._refresh_logs()
        
        # Auto-refresh logs every second
        self._schedule_logs_refresh()
    
    def _update_requirements_display(self):
        """Update the requirements checklist display."""
        # Clear existing labels
        for widget in self.req_grid.winfo_children():
            widget.destroy()
        self.requirement_labels.clear()
        
        # Get updated requirements
        requirements = self.requirements_checker.check_all_requirements()
        
        # Create labels in a 3-column grid
        row = 0
        col = 0
        for req_name, req_info in requirements.items():
            icon = "✅" if req_info['status'] else "❌"
            
            # Create frame for this requirement
            req_item = ttk.Frame(self.req_grid)
            req_item.grid(row=row, column=col, sticky="w", padx=5, pady=2)
            
            # Icon and name
            req_label = ttk.Label(req_item, text=f"{icon} {req_info['description']}")
            req_label.pack(side="left")
            
            # Store reference for potential updates
            self.requirement_labels[req_name] = req_label
            
            # Add tooltip with error if any
            if not req_info['status'] and req_info['error']:
                self._create_tooltip(req_label, req_info['error'])
            
            # Update grid position
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def create_backup(self):
        """Create backup using threaded handler"""
        if self.backup_handler.create_backup_threaded():
            self.status_label.config(text="Tworzenie backup...", foreground="blue")
            self.backup_btn.config(state="disabled")

    def restore_backup(self):
        """Restore backup using threaded handler"""
        if self.backup_handler.restore_backup_threaded():
            self.status_label.config(text="Przywracanie backup...", foreground="blue")
            self.restore_btn.config(state="disabled")

    def show_logs(self):
        """Show logs in new window - now shows current session logs"""
        logs = self.live_logger.get_logs_text()
        win = tk.Toplevel(self)
        win.title("Logi bieżącej sesji")
        win.geometry("800x600")
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(win)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        txt = tk.Text(text_frame, wrap="word", font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=scrollbar.set)
        
        txt.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        txt.insert("1.0", logs)
        txt.config(state="disabled")

    def check_update(self):
        """Check for updates using threaded handler"""
        self.status_label.config(text="Sprawdzanie aktualizacji...", foreground="blue")
        self.update_btn.config(state="disabled")
        self.system_ops.check_update_threaded()

    def send_report(self):
        """Send report using threaded handler"""
        self.status_label.config(text="Wysyłanie raportu...", foreground="blue")
        self.report_btn.config(state="disabled")
        self.system_ops.send_report_threaded()

    def restart_app(self):
        """Restart application"""
        import os, sys
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    def _add_result(self, result):
        """Add result to queue"""
        self.result_queue.put(result)
    
    def _process_result_queue(self):
        """Process results from worker threads"""
        try:
            while True:
                try:
                    result = self.result_queue.get_nowait()
                    self._handle_result(result)
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Błąd przetwarzania kolejki wyników: {e}")
        
        # Schedule next check
        self.after(100, self._process_result_queue)
    
    def _handle_result(self, result):
        """Handle individual result"""
        result_type = result['type']
        
        if result_type == 'backup_success':
            messagebox.showinfo("Backup", result['message'])
            self.status_label.config(text="Backup utworzony", foreground="green")
            self.backup_btn.config(state="normal")
            
        elif result_type == 'backup_error':
            messagebox.showerror("Błąd backupu", result['error'])
            self.status_label.config(text="Błąd backup", foreground="red")
            self.backup_btn.config(state="normal")
            
        elif result_type == 'restore_success':
            messagebox.showinfo("Backup", result['message'])
            self.status_label.config(text="Backup przywrócony", foreground="green")
            self.restore_btn.config(state="normal")
            
        elif result_type == 'restore_error':
            messagebox.showerror("Błąd backupu", result['error'])
            self.status_label.config(text="Błąd przywracania", foreground="red")
            self.restore_btn.config(state="normal")
            
        elif result_type == 'update_result':
            messagebox.showinfo("Aktualizacje", result['message'])
            self.status_label.config(text="Sprawdzono aktualizacje", foreground="green")
            self.update_btn.config(state="normal")
            
        elif result_type == 'update_error':
            messagebox.showerror("Błąd aktualizacji", result['error'])
            self.status_label.config(text="Błąd aktualizacji", foreground="red")
            self.update_btn.config(state="normal")
            
        elif result_type == 'report_success':
            messagebox.showinfo("Raport", result['message'])
            self.status_label.config(text="Raport wysłany", foreground="green")
            self.report_btn.config(state="normal")
            
        elif result_type == 'report_error':
            messagebox.showerror("Błąd raportu", result['error'])
            self.status_label.config(text="Błąd raportu", foreground="red")
            self.report_btn.config(state="normal")
    
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
    
    def _on_engine_change(self, event=None):
        """Handle OCR engine selection change"""
        engine = self.ocr_engine_var.get()
        ocr_config.set_engine(engine)
        
        # Update GPU availability hint based on engine
        if engine == "tesseract":
            # Tesseract is CPU-only
            self.gpu_enabled_var.set(False)
            self.status_label.config(text=f"Zmieniono silnik OCR na: {engine} (tylko CPU)", foreground="blue")
        else:
            self.status_label.config(text=f"Zmieniono silnik OCR na: {engine}", foreground="blue")
    
    def _on_gpu_change(self):
        """Handle GPU usage change"""
        use_gpu = self.gpu_enabled_var.get()
        engine = self.ocr_engine_var.get()
        
        if use_gpu and engine == "tesseract":
            messagebox.showwarning("GPU niedostępny", "Tesseract nie obsługuje GPU. Użyj EasyOCR lub PaddleOCR dla obsługi GPU.")
            self.gpu_enabled_var.set(False)
            return
            
        ocr_config.set_use_gpu(use_gpu)
        mode = "GPU" if use_gpu else "CPU"
        self.status_label.config(text=f"Tryb OCR zmieniony na: {mode}", foreground="blue")
    
    def _on_multiprocessing_change(self):
        """Handle multiprocessing setting change"""
        use_mp = self.multiprocessing_var.get()
        ocr_config.set_multiprocessing(use_mp)
        status = "włączona" if use_mp else "wyłączona"
        self.status_label.config(text=f"Wieloprocesowość OCR {status}", foreground="blue")
    
    def _on_workers_change(self, event=None):
        """Handle max workers change"""
        try:
            value = self.max_workers_var.get().strip()
            if value.lower() in ("auto", ""):
                ocr_config.set_max_workers(None)
            else:
                workers = int(value)
                if workers > 0:
                    ocr_config.set_max_workers(workers)
                else:
                    raise ValueError("Number must be positive")
        except ValueError:
            # Reset to current value on invalid input
            current = ocr_config.get_max_workers()
            self.max_workers_var.set(str(current) if current else "Auto")
    
    def _save_ocr_config(self):
        """Save OCR configuration to file"""
        if ocr_config.save_config():
            self.status_label.config(text="Konfiguracja OCR zapisana", foreground="green")
            messagebox.showinfo("Konfiguracja", "Konfiguracja OCR została zapisana. Zmiany będą aktywne przy następnym uruchomieniu OCR.")
        else:
            self.status_label.config(text="Błąd zapisywania konfiguracji OCR", foreground="red")
            messagebox.showerror("Błąd", "Nie udało się zapisać konfiguracji OCR.")
    
    def destroy(self):
        """Cleanup when widget is destroyed"""
        if self.backup_handler.operation_thread and self.backup_handler.operation_thread.is_alive():
            self.backup_handler.cancel_operation()
        if self.system_ops.operation_thread and self.system_ops.operation_thread.is_alive():
            self.system_ops.cancel_operation()
        
        # Stop live logging
        self.live_logger.stop_capture()
        
        super().destroy()
    
    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget (simple implementation)."""
        def on_enter(event):
            # Simple tooltip - could be enhanced with proper tooltip widget
            widget.configure(text=widget.cget("text") + f" ({text[:50]}{'...' if len(text) > 50 else ''})")
        
        def on_leave(event):
            # Reset to original text
            original_text = widget.cget("text").split(" (")[0]
            widget.configure(text=original_text)
        
        # Note: This is a simple implementation. For production, consider using a proper tooltip library
        pass  # Keeping simple for now
    
    def _clear_logs(self):
        """Clear the live logs display and buffer."""
        self.live_logger.clear_logs()
        self._refresh_logs()
    
    def _refresh_logs(self):
        """Refresh the logs display with current buffer content."""
        current_logs = self.live_logger.get_logs_text()
        
        # Update text widget
        self.logs_text.config(state="normal")
        self.logs_text.delete("1.0", "end")
        self.logs_text.insert("1.0", current_logs)
        self.logs_text.config(state="disabled")
        
        # Auto-scroll to bottom
        self.logs_text.see("end")
    
    def _schedule_logs_refresh(self):
        """Schedule periodic logs refresh."""
        self._refresh_logs()
        # Schedule next refresh in 1 second
        self.after(1000, self._schedule_logs_refresh)