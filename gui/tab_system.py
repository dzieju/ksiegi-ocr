import tkinter as tk
from tkinter import ttk, messagebox
import queue
import multiprocessing
import webbrowser
from tools import logger, i18n, darkmode
from tools.ocr_config import ocr_config
from tools.version_info import format_system_info
from gui.system_components.backup_handler import BackupHandler
from gui.system_components.system_operations import SystemOperations
from gui.system_components.dependency_widget import DependencyWidget


class SystemTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        logger.log("Inicjalizacja SystemTab")

        # Threading support variables
        self.result_queue = queue.Queue()
        self.progress_queue = queue.Queue()

        # Initialize handlers
        self.backup_handler = BackupHandler(self._add_result)
        self.system_ops = SystemOperations(self._add_result)
        logger.log("Komponenty systemowe zainicjalizowane")
        
        # OCR configuration variables
        self.ocr_engine_var = tk.StringVar(value=ocr_config.get_engine())
        self.gpu_enabled_var = tk.BooleanVar(value=ocr_config.get_use_gpu())
        self.multiprocessing_var = tk.BooleanVar(value=ocr_config.get_multiprocessing())
        self.max_workers_var = tk.StringVar(value=str(ocr_config.get_max_workers() or "Auto"))
        logger.log("Konfiguracja OCR załadowana")

        self.create_widgets()
        
        # Start processing queues
        self._process_result_queue()
        self._process_progress_queue()
        logger.log("SystemTab - inicjalizacja zakończona")
    
    def create_widgets(self):
        # Main container with notebook for organization
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        logger.log("Tworzenie zakładek SystemTab")
        
        # System Operations Tab
        self.system_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.system_frame, text="Operacje systemowe")
        self._create_system_operations_widgets()
        logger.log("Podzakładka 'Operacje systemowe' utworzona")
        
        # Dependencies Tab
        self.deps_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.deps_frame, text="Zależności środowiskowe")
        self._create_dependencies_widgets()
        logger.log("Podzakładka 'Zależności środowiskowe' utworzona")
        
        # OCR Configuration Tab
        self.ocr_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ocr_frame, text="Konfiguracja OCR")
        self._create_ocr_config_widgets()
        logger.log("Podzakładka 'Konfiguracja OCR' utworzona")
        
        # Logs Tab - NEW
        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text="Logi")
        self._create_logs_widgets()
        logger.log("Podzakładka 'Logi' utworzona")
    
    def _create_system_operations_widgets(self):
        """Create system operations widgets."""
        parent = self.system_frame
        
        # Version Information Section
        version_frame = ttk.LabelFrame(parent, text="Informacje o wersji", padding=10)
        version_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.version_info_label = ttk.Label(version_frame, text="", font=("Consolas", 9))
        self.version_info_label.pack(anchor="w")
        
        # Refresh version info button
        refresh_version_btn = ttk.Button(version_frame, text="Odśwież informacje o wersji", 
                                        command=self.refresh_version_info)
        refresh_version_btn.pack(anchor="w", pady=(5, 0))
        
        # Status label
        self.status_label = ttk.Label(parent, text="Gotowy", foreground="green")
        self.status_label.grid(row=1, column=2, padx=10, pady=10, sticky="w")

        # Backup
        self.backup_btn = ttk.Button(parent, text=i18n.translate("Utwórz backup"), command=self.create_backup)
        self.backup_btn.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.restore_btn = ttk.Button(parent, text=i18n.translate("Przywróć backup"), command=self.restore_backup)
        self.restore_btn.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # Logi/historia
        log_btn = ttk.Button(parent, text=i18n.translate("Pokaż logi"), command=self.show_logs)
        log_btn.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        # Aktualizacje
        self.update_btn = ttk.Button(parent, text=i18n.translate("Sprawdź aktualizacje"), command=self.check_update)
        self.update_btn.grid(row=4, column=0, padx=10, pady=10, sticky="w")

        # Raportowanie
        self.report_btn = ttk.Button(parent, text=i18n.translate("Wyślij raport"), command=self.send_report)
        self.report_btn.grid(row=5, column=0, padx=10, pady=10, sticky="w")

        # Dark mode
        theme_btn = ttk.Button(parent, text=i18n.translate("Przełącz tryb ciemny/jasny"), command=darkmode.toggle_theme)
        theme_btn.grid(row=6, column=0, padx=10, pady=10, sticky="w")

        # Restart
        restart_btn = ttk.Button(parent, text=i18n.translate("Restartuj aplikację"), command=self.restart_app)
        restart_btn.grid(row=7, column=0, padx=10, pady=10, sticky="w")
        
        # Configure column weights for proper stretching
        parent.columnconfigure(0, weight=1)
        
        # Load initial version info
        self.refresh_version_info()
    
    def _create_dependencies_widgets(self):
        """Create dependencies checklist widgets."""
        parent = self.deps_frame
        
        # Create dependency widget
        self.dependency_widget = DependencyWidget(parent)
        self.dependency_widget.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _create_ocr_config_widgets(self):
        """Create OCR configuration widgets."""
        parent = self.ocr_frame
        
        # OCR Configuration Section
        ocr_label = ttk.Label(parent, text="Konfiguracja OCR:", font=("Arial", 10, "bold"))
        ocr_label.grid(row=0, column=0, columnspan=4, padx=10, pady=(10, 5), sticky="w")
        
        # Validation status label
        self.ocr_status_label = ttk.Label(parent, text="", foreground="blue", font=("Arial", 8))
        self.ocr_status_label.grid(row=1, column=0, columnspan=4, padx=10, pady=(0, 5), sticky="w")
        
        # OCR Engine selection with availability indicators
        ttk.Label(parent, text="Silnik OCR:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        engine_frame = ttk.Frame(parent)
        engine_frame.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="w")
        
        self.ocr_engine_combo = ttk.Combobox(engine_frame, textvariable=self.ocr_engine_var, width=15, state="readonly")
        self.ocr_engine_combo.pack(side="left")
        self.ocr_engine_combo.bind('<<ComboboxSelected>>', self._on_engine_change)
        
        # Engine status indicator
        self.engine_status_label = ttk.Label(engine_frame, text="", foreground="gray", font=("Arial", 8))
        self.engine_status_label.pack(side="left", padx=(5, 0))
        
        # GPU/CPU selection with compatibility indicator
        ttk.Label(parent, text="Tryb GPU:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        gpu_frame = ttk.Frame(parent)
        gpu_frame.grid(row=3, column=1, columnspan=2, padx=10, pady=5, sticky="w")
        
        self.gpu_checkbox = ttk.Checkbutton(gpu_frame, text="Użyj GPU (jeśli dostępny)", 
                                          variable=self.gpu_enabled_var, command=self._on_gpu_change)
        self.gpu_checkbox.pack(side="left")
        
        # GPU compatibility indicator
        self.gpu_status_label = ttk.Label(gpu_frame, text="", foreground="gray", font=("Arial", 8))
        self.gpu_status_label.pack(side="left", padx=(5, 0))
        
        # Multiprocessing
        ttk.Label(parent, text="Wieloprocesowość:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        
        mp_frame = ttk.Frame(parent)
        mp_frame.grid(row=4, column=1, columnspan=2, padx=10, pady=5, sticky="w")
        
        self.mp_checkbox = ttk.Checkbutton(mp_frame, text="Włącz wieloprocesowość OCR", 
                                         variable=self.multiprocessing_var, command=self._on_multiprocessing_change)
        self.mp_checkbox.pack(side="left")
        
        # MP info label
        self.mp_info_label = ttk.Label(mp_frame, text=f"(Zalecane dla > 5 obrazów)", 
                                     foreground="gray", font=("Arial", 8))
        self.mp_info_label.pack(side="left", padx=(5, 0))
        
        # Max workers
        ttk.Label(parent, text="Maks. procesów:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        workers_frame = ttk.Frame(parent)
        workers_frame.grid(row=5, column=1, padx=10, pady=5, sticky="w")
        
        self.workers_entry = ttk.Entry(workers_frame, textvariable=self.max_workers_var, width=10)
        self.workers_entry.pack(side="left")
        self.workers_entry.bind('<KeyRelease>', self._on_workers_change)
        
        ttk.Label(workers_frame, text=f"(Auto = {multiprocessing.cpu_count()})").pack(side="left", padx=(5, 0))
        
        # Engine information panel
        info_frame = ttk.LabelFrame(parent, text="Informacje o silniku", padding=10)
        info_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=10, sticky="ew")
        
        self.engine_info_label = ttk.Label(info_frame, text="", font=("Arial", 9), justify="left")
        self.engine_info_label.pack(anchor="w")
        
        # Save OCR config button
        save_ocr_btn = ttk.Button(parent, text="Zapisz konfigurację OCR", command=self._save_ocr_config)
        save_ocr_btn.grid(row=7, column=0, padx=10, pady=10, sticky="w")
        
        # Refresh engines button  
        refresh_btn = ttk.Button(parent, text="Odśwież silniki", command=self._refresh_ocr_engines)
        refresh_btn.grid(row=7, column=1, padx=10, pady=10, sticky="w")
        
        # GPU Test button
        gpu_test_btn = ttk.Button(parent, text="Testuj dostępność GPU", command=self._test_gpu_availability)
        gpu_test_btn.grid(row=7, column=2, padx=10, pady=10, sticky="w")
        
        # Initialize the interface
        self._refresh_ocr_engines()

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
    
    def _refresh_ocr_engines(self):
        """Refresh OCR engines list and update interface"""
        try:
            # Get available engines
            available_engines = ocr_config.get_available_engines()
            all_engines = ["tesseract", "easyocr", "paddleocr"]
            
            # Update combobox values with availability indicators
            engine_values = []
            for engine in all_engines:
                if engine in available_engines:
                    engine_values.append(engine)
                else:
                    engine_values.append(f"{engine} (niedostępny)")
            
            self.ocr_engine_combo['values'] = engine_values
            
            # Validate current configuration
            issues = ocr_config.validate_configuration()
            
            # Update validation status
            if issues:
                issue_messages = [issue['message'] for issue in issues]
                self.ocr_status_label.config(text="⚠️ " + "; ".join(issue_messages), foreground="orange")
                
                # Auto-fix if possible
                for issue in issues:
                    if issue['type'] == 'engine_unavailable' and available_engines:
                        # Switch to first available engine
                        new_engine = available_engines[0]
                        self.ocr_engine_var.set(new_engine)
                        ocr_config.set_engine(new_engine)
                        logger.log(f"Auto-switched OCR engine to {new_engine}")
                    elif issue['type'] == 'gpu_incompatible':
                        # Disable GPU
                        self.gpu_enabled_var.set(False)
                        ocr_config.set_use_gpu(False)
                        logger.log("Auto-disabled GPU for incompatible engine")
            else:
                self.ocr_status_label.config(text="✅ Konfiguracja prawidłowa", foreground="green")
            
            # Update interface based on current engine
            self._update_engine_interface()
            
        except Exception as e:
            logger.log(f"Error refreshing OCR engines: {e}")
            self.ocr_status_label.config(text=f"❌ Błąd: {e}", foreground="red")
    
    def _update_engine_interface(self):
        """Update interface elements based on selected engine"""
        current_engine = self.ocr_engine_var.get()
        
        # Clean engine name (remove availability indicators)
        clean_engine = current_engine.split(" (")[0]
        
        # Update engine status
        is_available = ocr_config.is_engine_available(clean_engine)
        if is_available:
            self.engine_status_label.config(text="✅ Dostępny", foreground="green")
        else:
            self.engine_status_label.config(text="❌ Niedostępny", foreground="red")
        
        # Update GPU compatibility
        gpu_supported = ocr_config.is_gpu_supported(clean_engine)
        if gpu_supported and is_available:
            self.gpu_checkbox.config(state="normal")
            self.gpu_status_label.config(text="✅ Obsługiwane", foreground="green")
        else:
            self.gpu_checkbox.config(state="disabled")
            if not gpu_supported:
                self.gpu_status_label.config(text="❌ Nieobsługiwane", foreground="red")
                # Auto-disable GPU if not supported
                if self.gpu_enabled_var.get():
                    self.gpu_enabled_var.set(False)
                    ocr_config.set_use_gpu(False)
            else:
                self.gpu_status_label.config(text="⚠️ Silnik niedostępny", foreground="orange")
        
        # Update multiprocessing availability
        if is_available:
            self.mp_checkbox.config(state="normal")
        else:
            self.mp_checkbox.config(state="disabled")
        
        # Update workers entry
        if is_available and self.multiprocessing_var.get():
            self.workers_entry.config(state="normal")
        else:
            self.workers_entry.config(state="disabled")
        
        # Update engine information
        self._update_engine_info(clean_engine, is_available)
    
    def _update_engine_info(self, engine, is_available):
        """Update engine information panel"""
        info_texts = {
            "tesseract": {
                "available": "• Najstarszy i najbardziej stabilny silnik OCR\n• Tylko tryb CPU\n• Najlepszy dla dokumentów tekstowych\n• Wymaga instalacji zewnętrznej",
                "unavailable": "• Tesseract nie jest zainstalowany\n• Zainstaluj: apt-get install tesseract-ocr (Linux)\n• Windows: pobierz z UB-Mannheim/tesseract\n• pip install pytesseract"
            },
            "easyocr": {
                "available": "• Nowoczesny silnik AI\n• Obsługuje GPU i CPU\n• Dobry dla obrazów naturalnych\n• Automatyczna detekcja orientacji\n• Instalacja: pip install easyocr",
                "unavailable": "• EasyOCR nie jest zainstalowany\n• Instalacja: pip install easyocr\n• Wymaga PyTorch\n• Obsługuje GPU CUDA"
            },
            "paddleocr": {
                "available": "• Najnowszy silnik AI od Baidu\n• Obsługuje GPU i CPU\n• Bardzo dokładny dla tekstu azjatyckiego\n• Dobre wyniki dla dokumentów\n• Instalacja: pip install paddlepaddle paddleocr",
                "unavailable": "• PaddleOCR nie jest zainstalowany\n• Instalacja: pip install paddlepaddle paddleocr\n• Obsługuje GPU CUDA\n• Wymaga więcej pamięci RAM"
            }
        }
        
        if engine in info_texts:
            status_key = "available" if is_available else "unavailable"
            info_text = info_texts[engine][status_key]
            self.engine_info_label.config(text=info_text)
        else:
            self.engine_info_label.config(text="Nieznany silnik OCR")
    
    def _on_engine_change(self, event=None):
        """Handle OCR engine selection change"""
        selected = self.ocr_engine_combo.get()
        engine = selected.split(" (")[0]  # Remove availability indicator
        
        # Only allow selection of available engines
        if not ocr_config.is_engine_available(engine):
            messagebox.showwarning("Silnik niedostępny", 
                                 f"Silnik {engine} nie jest dostępny. Zainstaluj go lub wybierz inny silnik.")
            # Revert to current engine
            self.ocr_engine_var.set(ocr_config.get_engine())
            return
        
        # Set the engine
        ocr_config.set_engine(engine)
        self.status_label.config(text=f"Zmieniono silnik OCR na: {engine}", foreground="blue")
        
        # Update interface
        self._update_engine_interface()
        
        # Re-validate configuration
        self._refresh_ocr_engines()
    
    def _on_gpu_change(self):
        """Handle GPU usage change"""
        use_gpu = self.gpu_enabled_var.get()
        engine = self.ocr_engine_var.get().split(" (")[0]  # Remove availability indicator
        
        # Check GPU support
        if use_gpu and not ocr_config.is_gpu_supported(engine):
            messagebox.showwarning("GPU nieobsługiwane", 
                                 f"Silnik {engine} nie obsługuje GPU. Wybierz EasyOCR lub PaddleOCR dla obsługi GPU.")
            self.gpu_enabled_var.set(False)
            return
        
        # Check engine availability
        if use_gpu and not ocr_config.is_engine_available(engine):
            messagebox.showwarning("Silnik niedostępny", 
                                 f"Silnik {engine} nie jest dostępny. Zainstaluj go aby używać GPU.")
            self.gpu_enabled_var.set(False)
            return
        
        # Additional GPU capability check when enabling GPU
        if use_gpu:
            try:
                from tools.gpu_utils import test_gpu_availability
                gpu_test = test_gpu_availability()
                
                if gpu_test['overall_status'] == 'unavailable':
                    response = messagebox.askyesno(
                        "GPU/CUDA niedostępne",
                        "GPU lub CUDA nie zostały wykryte w systemie.\n\n"
                        "Czy chcesz otworzyć instrukcje instalacji CUDA?\n\n"
                        "Uwaga: OCR będzie działać w trybie CPU.",
                        icon="warning"
                    )
                    if response:
                        self._show_cuda_installation_help()
                    # Allow proceeding but warn it will use CPU
                    self.status_label.config(text="Uwaga: GPU niedostępne, używam CPU", foreground="orange")
                elif gpu_test['overall_status'] in ['cuda_only', 'framework_only']:
                    messagebox.showwarning(
                        "Problemy z konfiguracją GPU",
                        f"Wykryto problemy z konfiguracją GPU:\n\n" +
                        "\n".join(gpu_test['recommendations']) +
                        "\n\nUżyj przycisku 'Testuj dostępność GPU' aby uzyskać szczegóły."
                    )
            except Exception as e:
                logger.log(f"Error testing GPU during configuration: {e}")
                
        ocr_config.set_use_gpu(use_gpu)
        mode = "GPU" if use_gpu else "CPU"
        self.status_label.config(text=f"Tryb OCR zmieniony na: {mode}", foreground="blue")
    
    def _on_multiprocessing_change(self):
        """Handle multiprocessing setting change"""
        use_mp = self.multiprocessing_var.get()
        engine = self.ocr_engine_var.get().split(" (")[0]
        
        # Check if engine is available
        if use_mp and not ocr_config.is_engine_available(engine):
            messagebox.showwarning("Silnik niedostępny", 
                                 f"Silnik {engine} nie jest dostępny. Zainstaluj go aby używać wieloprocesowości.")
            self.multiprocessing_var.set(False)
            return
        
        ocr_config.set_multiprocessing(use_mp)
        status = "włączona" if use_mp else "wyłączona"
        self.status_label.config(text=f"Wieloprocesowość OCR {status}", foreground="blue")
        
        # Update workers entry state
        if use_mp:
            self.workers_entry.config(state="normal")
        else:
            self.workers_entry.config(state="disabled")
    
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
    
    def _create_logs_widgets(self):
        """Create logs viewing widgets."""
        parent = self.logs_frame
        
        # Top frame with refresh and clear buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        # Refresh button
        self.refresh_logs_btn = ttk.Button(button_frame, text=i18n.translate("Odśwież logi"), command=self.refresh_logs)
        self.refresh_logs_btn.pack(side="left")
        
        # Clear logs button
        self.clear_logs_btn = ttk.Button(button_frame, text=i18n.translate("Wyczyść logi"), 
                                        command=self.clear_logs, style="Toolbutton")
        self.clear_logs_btn.pack(side="left", padx=(10, 0))
        
        # Log info label
        self.log_info_label = ttk.Label(button_frame, text="", foreground="gray")
        self.log_info_label.pack(side="left", padx=(10, 0))
        
        # Text widget with scrollbar for logs
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create text widget
        self.logs_text = tk.Text(text_frame, wrap="word", state="disabled", 
                                font=("Consolas", 9), bg="white", fg="black")
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.logs_text.yview)
        self.logs_text.configure(yscrollcommand=scrollbar.set)
        
        # Pack text widget and scrollbar
        self.logs_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Load logs initially
        self.refresh_logs()
    
    def refresh_logs(self):
        """Refresh and display logs from app.log"""
        try:
            logs_content = logger.read_logs()
            
            # Update text widget
            self.logs_text.config(state="normal")
            self.logs_text.delete(1.0, tk.END)
            self.logs_text.insert(1.0, logs_content)
            self.logs_text.config(state="disabled")
            
            # Scroll to bottom to show latest logs
            self.logs_text.see(tk.END)
            
            # Update info label
            if logs_content == "Brak logów.":
                self.log_info_label.config(text="Brak logów do wyświetlenia")
            else:
                lines_count = len(logs_content.split('\n')) - 1  # -1 for empty last line
                self.log_info_label.config(text=f"Załadowano {lines_count} linii logów")
                
            # Log the refresh action (this will appear in next refresh)
            logger.log("Logi odświeżone przez użytkownika")
            
        except Exception as e:
            self.logs_text.config(state="normal")
            self.logs_text.delete(1.0, tk.END)
            self.logs_text.insert(1.0, f"Błąd podczas ładowania logów: {str(e)}")
            self.logs_text.config(state="disabled")
            self.log_info_label.config(text="Błąd ładowania logów")
    
    def clear_logs(self):
        """Clear all application log files."""
        try:
            # Ask for confirmation
            result = messagebox.askyesno(
                "Potwierdzenie", 
                "Czy na pewno chcesz usunąć wszystkie pliki logów?\n\nTa operacja jest nieodwracalna.",
                icon="warning"
            )
            
            if result:
                # Clear the log file by calling logger's clear function
                if hasattr(logger, 'clear_logs'):
                    logger.clear_logs()
                else:
                    # If clear_logs doesn't exist, manually clear the log file
                    import os
                    if os.path.exists(logger.LOG_FILE):
                        os.remove(logger.LOG_FILE)
                
                # Log the clear action (this will create a new log file)
                logger.log("Wszystkie logi zostały wyczyszczone przez użytkownika")
                
                # Refresh the display
                self.refresh_logs()
                
                messagebox.showinfo("Sukces", "Wszystkie logi zostały pomyślnie wyczyszczone.")
                
        except Exception as e:
            logger.log(f"Błąd podczas czyszczenia logów: {str(e)}")
            messagebox.showerror("Błąd", f"Nie udało się wyczyścić logów:\n{str(e)}")
    
    def refresh_version_info(self):
        """Refresh version information display."""
        try:
            version_text = format_system_info()
            self.version_info_label.config(text=version_text)
            logger.log("Informacje o wersji zostały odświeżone")
        except Exception as e:
            error_text = f"Błąd podczas ładowania informacji o wersji: {str(e)}"
            self.version_info_label.config(text=error_text)
            logger.log(f"Błąd odświeżania informacji o wersji: {str(e)}")
    
    def _test_gpu_availability(self):
        """Test GPU availability and show detailed results"""
        try:
            from tools.gpu_utils import test_gpu_availability
            
            self.status_label.config(text="Testowanie dostępności GPU...", foreground="blue")
            self.update()  # Update GUI immediately
            
            # Run comprehensive GPU test
            results = test_gpu_availability()
            
            # Create results window
            self._show_gpu_test_results(results)
            
            self.status_label.config(text=f"Test GPU: {results['overall_status']}", foreground="green")
            
        except Exception as e:
            logger.log(f"Error during GPU test: {e}")
            messagebox.showerror("Błąd testu GPU", f"Nie udało się przetestować GPU:\n{str(e)}")
            self.status_label.config(text="Błąd testu GPU", foreground="red")
    
    def _show_gpu_test_results(self, results):
        """Show detailed GPU test results in a popup window"""
        # Create popup window
        popup = tk.Toplevel(self)
        popup.title("Wyniki testu dostępności GPU")
        popup.geometry("600x500")
        popup.resizable(True, True)
        
        # Main frame with scrollbar
        main_frame = ttk.Frame(popup)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollable text widget
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill="both", expand=True)
        
        text_widget = tk.Text(text_frame, wrap="word", font=("Consolas", 10), 
                             state="normal", bg="white", fg="black")
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Format and insert results
        result_text = self._format_gpu_test_results(results)
        text_widget.insert("1.0", result_text)
        text_widget.config(state="disabled")
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Close button
        close_btn = ttk.Button(button_frame, text="Zamknij", command=popup.destroy)
        close_btn.pack(side="right")
        
        # CUDA installation help button (if needed)
        if results['overall_status'] in ['unavailable', 'cuda_only']:
            help_btn = ttk.Button(button_frame, text="Instrukcje instalacji CUDA", 
                                command=self._show_cuda_installation_help)
            help_btn.pack(side="right", padx=(0, 10))
    
    def _format_gpu_test_results(self, results):
        """Format GPU test results for display"""
        lines = []
        
        # Overall status
        status_emojis = {
            'available': '✅',
            'cuda_only': '⚠️', 
            'framework_only': '⚠️',
            'unavailable': '❌'
        }
        
        emoji = status_emojis.get(results['overall_status'], '❓')
        lines.append(f"{emoji} OGÓLNY STATUS GPU: {results['overall_status'].upper()}")
        lines.append("=" * 50)
        lines.append("")
        
        # CUDA System Info
        cuda = results['cuda_system']
        lines.append("🔧 SYSTEM CUDA:")
        if cuda['available']:
            lines.append(f"   ✅ Status: Dostępna")
            if cuda['driver_version']:
                lines.append(f"   📝 Sterownik NVIDIA: {cuda['driver_version']}")
            if cuda['cuda_version']:
                lines.append(f"   🏗️  CUDA Version: {cuda['cuda_version']}")
            lines.append(f"   🔍 Metoda wykrywania: {cuda['method']}")
        else:
            lines.append("   ❌ Status: Niedostępna")
            lines.append("   💡 Sterowniki NVIDIA lub CUDA nie zostały wykryte")
        lines.append("")
        
        # PyTorch Info
        torch = results['torch']
        lines.append("🔥 PYTORCH:")
        if torch['available']:
            lines.append(f"   ✅ Status: Zainstalowany")
            lines.append(f"   📦 Wersja: {torch['version']}")
            if torch['cuda_available']:
                lines.append(f"   🚀 CUDA: Dostępna (v{torch['cuda_version']})")
                lines.append(f"   📱 Liczba GPU: {torch['device_count']}")
                for i, device in enumerate(torch['device_names']):
                    lines.append(f"      GPU {i}: {device}")
            else:
                lines.append("   ❌ CUDA: Niedostępna")
        else:
            lines.append("   ❌ Status: Nie zainstalowany")
            lines.append("   💡 Instalacja: pip install torch")
        
        if 'error' in torch:
            lines.append(f"   ⚠️  Błąd: {torch['error']}")
        lines.append("")
        
        # PaddlePaddle Info
        paddle = results['paddle']
        lines.append("🚀 PADDLEPADDLE:")
        if paddle['available']:
            lines.append(f"   ✅ Status: Zainstalowany")
            lines.append(f"   📦 Wersja: {paddle['version']}")
            if paddle['gpu_available']:
                lines.append(f"   🚀 GPU: Dostępna")
                lines.append(f"   📱 Liczba GPU: {paddle['device_count']}")
                for device in paddle['device_info']:
                    lines.append(f"      📱 {device}")
            else:
                lines.append("   ❌ GPU: Niedostępna")
        else:
            lines.append("   ❌ Status: Nie zainstalowany")
            lines.append("   💡 Instalacja: pip install paddlepaddle paddleocr")
        
        if 'error' in paddle:
            lines.append(f"   ⚠️  Błąd: {paddle['error']}")
        lines.append("")
        
        # Recommendations
        lines.append("💡 REKOMENDACJE:")
        for i, rec in enumerate(results['recommendations'], 1):
            lines.append(f"   {i}. {rec}")
        
        return "\n".join(lines)
    
    def _show_cuda_installation_help(self):
        """Show CUDA installation help with links"""
        try:
            from tools.gpu_utils import get_cuda_installation_links
            links = get_cuda_installation_links()
            
            # Create help popup
            help_popup = tk.Toplevel(self)
            help_popup.title("Instrukcje instalacji CUDA")
            help_popup.geometry("500x400")
            
            # Main frame
            main_frame = ttk.Frame(help_popup)
            main_frame.pack(fill="both", expand=True, padx=15, pady=15)
            
            # Title
            title_label = ttk.Label(main_frame, text="Instrukcje instalacji CUDA i GPU support", 
                                  font=("Arial", 12, "bold"))
            title_label.pack(anchor="w", pady=(0, 10))
            
            # Instructions
            instructions_frame = ttk.LabelFrame(main_frame, text="Kroki instalacji", padding=10)
            instructions_frame.pack(fill="both", expand=True, pady=(0, 10))
            
            for i, instruction in enumerate(links['instructions'], 1):
                instr_label = ttk.Label(instructions_frame, text=instruction, wraplength=450)
                instr_label.pack(anchor="w", pady=2)
            
            # Links frame
            links_frame = ttk.LabelFrame(main_frame, text="Przydatne linki", padding=10)
            links_frame.pack(fill="x", pady=(0, 10))
            
            # Create clickable links
            link_buttons = [
                ("CUDA Toolkit", links['cuda_toolkit']),
                ("Sterowniki NVIDIA", links['nvidia_drivers']),
                ("PyTorch CUDA", links['pytorch_cuda']),
                ("PaddlePaddle GPU", links['paddle_gpu'])
            ]
            
            for name, url in link_buttons:
                btn = ttk.Button(links_frame, text=f"🔗 {name}", 
                               command=lambda u=url: webbrowser.open(u))
                btn.pack(fill="x", pady=2)
            
            # Close button
            close_btn = ttk.Button(main_frame, text="Zamknij", command=help_popup.destroy)
            close_btn.pack(anchor="e")
            
        except Exception as e:
            logger.log(f"Error showing CUDA installation help: {e}")
            messagebox.showerror("Błąd", f"Nie udało się wyświetlić pomocy:\n{str(e)}")
    
    def destroy(self):
        """Cleanup when widget is destroyed"""
        if self.backup_handler.operation_thread and self.backup_handler.operation_thread.is_alive():
            self.backup_handler.cancel_operation()
        if self.system_ops.operation_thread and self.system_ops.operation_thread.is_alive():
            self.system_ops.cancel_operation()
        super().destroy()