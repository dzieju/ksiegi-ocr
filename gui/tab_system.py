import tkinter as tk
from tkinter import ttk, messagebox
import queue
import multiprocessing
from tools import logger, i18n, darkmode
from tools.ocr_config import ocr_config


class SystemTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Threading support variables
        self.result_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        
        # OCR configuration variables
        self.ocr_engine_var = tk.StringVar(value=ocr_config.get_engine())
        self.gpu_enabled_var = tk.BooleanVar(value=ocr_config.get_use_gpu())
        self.multiprocessing_var = tk.BooleanVar(value=ocr_config.get_multiprocessing())
        self.max_workers_var = tk.StringVar(value=str(ocr_config.get_max_workers() or "Auto"))

        self.create_widgets()
        
        # Start processing queues
        self._process_result_queue()
        self._process_progress_queue()
    
    def create_widgets(self):
        # Status label
        self.status_label = ttk.Label(self, text="Gotowy", foreground="green")
        self.status_label.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        # Backup
        self.backup_btn = ttk.Button(self, text=i18n.translate("Utwórz backup"), command=self.create_backup)
        self.backup_btn.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.restore_btn = ttk.Button(self, text=i18n.translate("Przywróć backup"), command=self.restore_backup)
        self.restore_btn.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Logi/historia
        log_btn = ttk.Button(self, text=i18n.translate("Pokaż logi"), command=self.show_logs)
        log_btn.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        # Aktualizacje
        self.update_btn = ttk.Button(self, text=i18n.translate("Sprawdź aktualizacje"), command=self.check_update)
        self.update_btn.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        # Raportowanie
        self.report_btn = ttk.Button(self, text=i18n.translate("Wyślij raport"), command=self.send_report)
        self.report_btn.grid(row=4, column=0, padx=10, pady=10, sticky="w")

        # Dark mode
        theme_btn = ttk.Button(self, text=i18n.translate("Przełącz tryb ciemny/jasny"), command=darkmode.toggle_theme)
        theme_btn.grid(row=5, column=0, padx=10, pady=10, sticky="w")

        # Restart
        restart_btn = ttk.Button(self, text=i18n.translate("Restartuj aplikację"), command=self.restart_app)
        restart_btn.grid(row=6, column=0, padx=10, pady=10, sticky="w")
        
        # OCR Configuration Section
        ocr_label = ttk.Label(self, text="Konfiguracja OCR:", font=("Arial", 10, "bold"))
        ocr_label.grid(row=7, column=0, columnspan=3, padx=10, pady=(20, 5), sticky="w")
        
        # OCR Engine selection
        ttk.Label(self, text="Silnik OCR:").grid(row=8, column=0, padx=10, pady=5, sticky="w")
        ocr_engine_combo = ttk.Combobox(self, textvariable=self.ocr_engine_var, width=15, state="readonly")
        ocr_engine_combo['values'] = ("tesseract", "easyocr", "paddleocr")
        ocr_engine_combo.grid(row=8, column=1, padx=10, pady=5, sticky="w")
        ocr_engine_combo.bind('<<ComboboxSelected>>', self._on_engine_change)
        
        # GPU/CPU selection
        ttk.Label(self, text="Tryb GPU:").grid(row=9, column=0, padx=10, pady=5, sticky="w")
        gpu_checkbox = ttk.Checkbutton(self, text="Użyj GPU (jeśli dostępny)", variable=self.gpu_enabled_var, command=self._on_gpu_change)
        gpu_checkbox.grid(row=9, column=1, padx=10, pady=5, sticky="w")
        
        # Multiprocessing
        ttk.Label(self, text="Wieloprocesowość:").grid(row=10, column=0, padx=10, pady=5, sticky="w")
        mp_checkbox = ttk.Checkbutton(self, text="Włącz wieloprocesowość OCR", variable=self.multiprocessing_var, command=self._on_multiprocessing_change)
        mp_checkbox.grid(row=10, column=1, padx=10, pady=5, sticky="w")
        
        # Max workers
        ttk.Label(self, text="Maks. procesów:").grid(row=11, column=0, padx=10, pady=5, sticky="w")
        workers_frame = ttk.Frame(self)
        workers_frame.grid(row=11, column=1, padx=10, pady=5, sticky="w")
        
        self.workers_entry = ttk.Entry(workers_frame, textvariable=self.max_workers_var, width=10)
        self.workers_entry.pack(side="left")
        self.workers_entry.bind('<KeyRelease>', self._on_workers_change)
        
        ttk.Label(workers_frame, text=f"(Auto = {multiprocessing.cpu_count()})").pack(side="left", padx=(5, 0))
        
        # Save OCR config button
        save_ocr_btn = ttk.Button(self, text="Zapisz konfigurację OCR", command=self._save_ocr_config)
        save_ocr_btn.grid(row=12, column=0, padx=10, pady=10, sticky="w")

    def create_backup(self):
        """Create backup"""
        try:
            from tools.backup import create_backup
            success, message = create_backup()
            if success:
                self.status_label.config(text="Backup utworzony", foreground="green")
                messagebox.showinfo("Backup", message)
            else:
                self.status_label.config(text="Błąd tworzenia backup", foreground="red")
                messagebox.showerror("Błąd", message)
        except Exception as e:
            logger.log(f"Błąd podczas tworzenia backup: {e}")
            self.status_label.config(text="Błąd tworzenia backup", foreground="red")
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas tworzenia backup: {e}")

    def restore_backup(self):
        """Restore backup"""
        try:
            from tools.backup import restore_backup
            success, message = restore_backup()
            if success:
                self.status_label.config(text="Backup przywrócony", foreground="green")
                messagebox.showinfo("Backup", message)
            else:
                self.status_label.config(text="Błąd przywracania backup", foreground="red")
                messagebox.showerror("Błąd", message)
        except Exception as e:
            logger.log(f"Błąd podczas przywracania backup: {e}")
            self.status_label.config(text="Błąd przywracania backup", foreground="red")
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas przywracania backup: {e}")

    def show_logs(self):
        """Show logs in new window"""
        logs = logger.read_logs()
        win = tk.Toplevel(self)
        win.title("Logi/historia")
        txt = tk.Text(win, wrap="word")
        txt.insert("1.0", logs)
        txt.pack(expand=True, fill="both")

    def check_update(self):
        """Check for updates"""
        try:
            from tools.update_checker import check_for_updates
            has_update, version_info = check_for_updates()
            if has_update:
                self.status_label.config(text=f"Dostępna aktualizacja: {version_info}", foreground="orange")
                messagebox.showinfo("Aktualizacja", f"Dostępna jest nowa wersja: {version_info}")
            else:
                self.status_label.config(text="Brak aktualizacji", foreground="green")
                messagebox.showinfo("Aktualizacja", "Aplikacja jest aktualna.")
        except Exception as e:
            logger.log(f"Błąd podczas sprawdzania aktualizacji: {e}")
            self.status_label.config(text="Błąd sprawdzania aktualizacji", foreground="red")
            messagebox.showerror("Błąd", f"Nie można sprawdzić aktualizacji: {e}")

    def send_report(self):
        """Send report"""
        try:
            from tools.email_report import send_report
            success, message = send_report()
            if success:
                self.status_label.config(text="Raport wysłany", foreground="green")
                messagebox.showinfo("Raport", message)
            else:
                self.status_label.config(text="Błąd wysyłania raportu", foreground="red")
                messagebox.showerror("Błąd", message)
        except Exception as e:
            logger.log(f"Błąd podczas wysyłania raportu: {e}")
            self.status_label.config(text="Błąd wysyłania raportu", foreground="red")
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas wysyłania raportu: {e}")

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
    
    def create_widgets(self):
        # Status label
        self.status_label = ttk.Label(self, text="Gotowy", foreground="green")
        self.status_label.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        # Backup
        self.backup_btn = ttk.Button(self, text=i18n.translate("Utwórz backup"), command=self.create_backup)
        self.backup_btn.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.restore_btn = ttk.Button(self, text=i18n.translate("Przywróć backup"), command=self.restore_backup)
        self.restore_btn.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Logi/historia
        log_btn = ttk.Button(self, text=i18n.translate("Pokaż logi"), command=self.show_logs)
        log_btn.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        # Aktualizacje
        self.update_btn = ttk.Button(self, text=i18n.translate("Sprawdź aktualizacje"), command=self.check_update)
        self.update_btn.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        # Raportowanie
        self.report_btn = ttk.Button(self, text=i18n.translate("Wyślij raport"), command=self.send_report)
        self.report_btn.grid(row=4, column=0, padx=10, pady=10, sticky="w")

        # Dark mode
        theme_btn = ttk.Button(self, text=i18n.translate("Przełącz tryb ciemny/jasny"), command=darkmode.toggle_theme)
        theme_btn.grid(row=5, column=0, padx=10, pady=10, sticky="w")

        # Restart
        restart_btn = ttk.Button(self, text=i18n.translate("Restartuj aplikację"), command=self.restart_app)
        restart_btn.grid(row=6, column=0, padx=10, pady=10, sticky="w")
        
        # OCR Configuration Section
        ocr_label = ttk.Label(self, text="Konfiguracja OCR:", font=("Arial", 10, "bold"))
        ocr_label.grid(row=7, column=0, columnspan=3, padx=10, pady=(20, 5), sticky="w")
        
        # OCR Engine selection
        ttk.Label(self, text="Silnik OCR:").grid(row=8, column=0, padx=10, pady=5, sticky="w")
        ocr_engine_combo = ttk.Combobox(self, textvariable=self.ocr_engine_var, width=15, state="readonly")
        ocr_engine_combo['values'] = ("tesseract", "easyocr", "paddleocr")
        ocr_engine_combo.grid(row=8, column=1, padx=10, pady=5, sticky="w")
        ocr_engine_combo.bind('<<ComboboxSelected>>', self._on_engine_change)
        
        # GPU/CPU selection
        ttk.Label(self, text="Tryb GPU:").grid(row=9, column=0, padx=10, pady=5, sticky="w")
        gpu_checkbox = ttk.Checkbutton(self, text="Użyj GPU (jeśli dostępny)", variable=self.gpu_enabled_var, command=self._on_gpu_change)
        gpu_checkbox.grid(row=9, column=1, padx=10, pady=5, sticky="w")
        
        # Multiprocessing
        ttk.Label(self, text="Wieloprocesowość:").grid(row=10, column=0, padx=10, pady=5, sticky="w")
        mp_checkbox = ttk.Checkbutton(self, text="Włącz wieloprocesowość OCR", variable=self.multiprocessing_var, command=self._on_multiprocessing_change)
        mp_checkbox.grid(row=10, column=1, padx=10, pady=5, sticky="w")
        
        # Max workers
        ttk.Label(self, text="Maks. procesów:").grid(row=11, column=0, padx=10, pady=5, sticky="w")
        workers_frame = ttk.Frame(self)
        workers_frame.grid(row=11, column=1, padx=10, pady=5, sticky="w")
        
        self.workers_entry = ttk.Entry(workers_frame, textvariable=self.max_workers_var, width=10)
        self.workers_entry.pack(side="left")
        self.workers_entry.bind('<KeyRelease>', self._on_workers_change)
        
        ttk.Label(workers_frame, text=f"(Auto = {multiprocessing.cpu_count()})").pack(side="left", padx=(5, 0))
        
        # Save OCR config button
        save_ocr_btn = ttk.Button(self, text="Zapisz konfigurację OCR", command=self._save_ocr_config)
        save_ocr_btn.grid(row=12, column=0, padx=10, pady=10, sticky="w")

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
        """Show logs in new window"""
        logs = logger.read_logs()
        win = tk.Toplevel(self)
        win.title("Logi/historia")
        txt = tk.Text(win, wrap="word")
        txt.insert("1.0", logs)
        txt.pack(expand=True, fill="both")

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
        super().destroy()