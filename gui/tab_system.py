import customtkinter as ctk
from tkinter import messagebox, ttk
import queue
import multiprocessing
from tools import logger, i18n, darkmode
from tools.ocr_config import ocr_config
from gui.system_components.backup_handler import BackupHandler
from gui.system_components.system_operations import SystemOperations
from gui.modern_theme import ModernTheme
from gui.tooltip_utils import add_tooltip, TOOLTIPS


class SystemTab(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent, **ModernTheme.get_frame_style('section'))

        # Configure the scrollable frame to support potential grid layouts
        self.grid_columnconfigure(0, weight=1)

        # Threading support variables
        self.result_queue = queue.Queue()
        self.progress_queue = queue.Queue()

        # Initialize handlers
        self.backup_handler = BackupHandler(self._add_result)
        self.system_ops = SystemOperations(self._add_result)
        
        # OCR configuration variables
        self.ocr_engine_var = ctk.StringVar(value=ocr_config.get_engine())
        self.gpu_enabled_var = ctk.BooleanVar(value=ocr_config.get_use_gpu())
        self.multiprocessing_var = ctk.BooleanVar(value=ocr_config.get_multiprocessing())
        self.max_workers_var = ctk.StringVar(value=str(ocr_config.get_max_workers() or "Auto"))

        self.create_widgets()
        
        # Start processing queues
        self._process_result_queue()
        self._process_progress_queue()
    
    def create_widgets(self):
        """Create modern CustomTkinter widgets for the system tab"""
        
        # Title section
        title_label = ctk.CTkLabel(
            self, 
            text="🔧 Ustawienia Systemowe",
            **ModernTheme.get_label_style('heading')
        )
        title_label.pack(pady=(0, ModernTheme.SPACING['large']), anchor="w")

        # Status section
        status_frame = ctk.CTkFrame(self, **ModernTheme.get_frame_style('card'))
        status_frame.pack(fill="x", pady=(0, ModernTheme.SPACING['medium']))
        
        status_title = ctk.CTkLabel(
            status_frame,
            text="Status systemu:",
            **ModernTheme.get_label_style('subheading')
        )
        status_title.pack(pady=(ModernTheme.SPACING['small'], 0), anchor="w", padx=ModernTheme.SPACING['medium'])
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Gotowy",
            **ModernTheme.get_label_style('success')
        )
        self.status_label.pack(pady=(0, ModernTheme.SPACING['small']), anchor="w", padx=ModernTheme.SPACING['medium'])

        # Backup operations section
        backup_frame = ctk.CTkFrame(self, **ModernTheme.get_frame_style('card'))
        backup_frame.pack(fill="x", pady=(0, ModernTheme.SPACING['medium']))
        
        backup_title = ctk.CTkLabel(
            backup_frame,
            text="💾 Zarządzanie kopiami zapasowymi",
            **ModernTheme.get_label_style('subheading')
        )
        backup_title.pack(pady=(ModernTheme.SPACING['medium'], ModernTheme.SPACING['small']), anchor="w", padx=ModernTheme.SPACING['medium'])

        backup_buttons_frame = ctk.CTkFrame(backup_frame, fg_color="transparent")
        backup_buttons_frame.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(0, ModernTheme.SPACING['medium']))

        self.backup_btn = ctk.CTkButton(
            backup_buttons_frame,
            text=i18n.translate("Utwórz backup"),
            command=self.create_backup,
            **ModernTheme.get_button_style('primary')
        )
        self.backup_btn.pack(side="left", padx=(0, ModernTheme.SPACING['small']))
        add_tooltip(self.backup_btn, TOOLTIPS['backup_create'])

        self.restore_btn = ctk.CTkButton(
            backup_buttons_frame,
            text=i18n.translate("Przywróć backup"), 
            command=self.restore_backup,
            **ModernTheme.get_button_style('secondary')
        )
        self.restore_btn.pack(side="left")
        add_tooltip(self.restore_btn, TOOLTIPS['backup_restore'])

        # System operations section
        system_frame = ctk.CTkFrame(self, **ModernTheme.get_frame_style('card'))
        system_frame.pack(fill="x", pady=(0, ModernTheme.SPACING['medium']))
        
        system_title = ctk.CTkLabel(
            system_frame,
            text="🛠️ Operacje systemowe",
            **ModernTheme.get_label_style('subheading')
        )
        system_title.pack(pady=(ModernTheme.SPACING['medium'], ModernTheme.SPACING['small']), anchor="w", padx=ModernTheme.SPACING['medium'])

        # Row 1: Logs and Updates
        system_row1 = ctk.CTkFrame(system_frame, fg_color="transparent")
        system_row1.pack(fill="x", padx=ModernTheme.SPACING['medium'])
        
        log_btn = ctk.CTkButton(
            system_row1,
            text=i18n.translate("Pokaż logi"),
            command=self.show_logs,
            **ModernTheme.get_button_style('secondary')
        )
        log_btn.pack(side="left", padx=(0, ModernTheme.SPACING['small']))
        add_tooltip(log_btn, TOOLTIPS['logs_show'])

        self.update_btn = ctk.CTkButton(
            system_row1,
            text=i18n.translate("Sprawdź aktualizacje"),
            command=self.check_update,
            **ModernTheme.get_button_style('secondary')
        )
        self.update_btn.pack(side="left")
        add_tooltip(self.update_btn, TOOLTIPS['update_check'])

        # Row 2: Report and Theme
        system_row2 = ctk.CTkFrame(system_frame, fg_color="transparent") 
        system_row2.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(ModernTheme.SPACING['small'], 0))

        self.report_btn = ctk.CTkButton(
            system_row2,
            text=i18n.translate("Wyślij raport"),
            command=self.send_report,
            **ModernTheme.get_button_style('secondary')
        )
        self.report_btn.pack(side="left", padx=(0, ModernTheme.SPACING['small']))
        add_tooltip(self.report_btn, TOOLTIPS['report_send'])

        theme_btn = ctk.CTkButton(
            system_row2,
            text=i18n.translate("Przełącz tryb ciemny/jasny"),
            command=darkmode.toggle_theme,
            **ModernTheme.get_button_style('secondary')
        )
        theme_btn.pack(side="left")
        add_tooltip(theme_btn, TOOLTIPS['theme_toggle'])

        # Row 3: Restart
        system_row3 = ctk.CTkFrame(system_frame, fg_color="transparent")
        system_row3.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(ModernTheme.SPACING['small'], ModernTheme.SPACING['medium']))

        restart_btn = ctk.CTkButton(
            system_row3,
            text=i18n.translate("Restartuj aplikację"),
            command=self.restart_app,
            **ModernTheme.get_button_style('danger')
        )
        restart_btn.pack(side="left")
        add_tooltip(restart_btn, TOOLTIPS['app_restart'])

        # OCR Configuration section  
        self._create_ocr_section()

    def _create_ocr_section(self):
        """Create OCR configuration section with modern styling"""
        ocr_frame = ctk.CTkFrame(self, **ModernTheme.get_frame_style('card'))
        ocr_frame.pack(fill="x", pady=(0, ModernTheme.SPACING['medium']))
        
        ocr_title = ctk.CTkLabel(
            ocr_frame,
            text="⚡ Konfiguracja OCR",
            **ModernTheme.get_label_style('subheading')
        )
        ocr_title.pack(pady=(ModernTheme.SPACING['medium'], ModernTheme.SPACING['small']), anchor="w", padx=ModernTheme.SPACING['medium'])

        # OCR Engine selection
        engine_frame = ctk.CTkFrame(ocr_frame, fg_color="transparent")
        engine_frame.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(0, ModernTheme.SPACING['small']))

        engine_label = ctk.CTkLabel(
            engine_frame,
            text="Silnik OCR:",
            **ModernTheme.get_label_style('body')
        )
        engine_label.pack(side="left", padx=(0, ModernTheme.SPACING['small']))

        self.ocr_engine_combo = ctk.CTkComboBox(
            engine_frame,
            variable=self.ocr_engine_var,
            values=["tesseract", "easyocr", "paddleocr"],
            state="readonly",
            command=self._on_engine_change,
            **ModernTheme.get_entry_style()
        )
        self.ocr_engine_combo.pack(side="left")
        add_tooltip(self.ocr_engine_combo, TOOLTIPS['ocr_engine'])

        # GPU/CPU selection
        gpu_frame = ctk.CTkFrame(ocr_frame, fg_color="transparent")
        gpu_frame.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(0, ModernTheme.SPACING['small']))

        self.gpu_checkbox = ctk.CTkCheckBox(
            gpu_frame,
            text="Użyj GPU (jeśli dostępny)",
            variable=self.gpu_enabled_var,
            command=self._on_gpu_change,
            **ModernTheme.get_label_style('body')
        )
        self.gpu_checkbox.pack(side="left")

        # Multiprocessing
        mp_frame = ctk.CTkFrame(ocr_frame, fg_color="transparent")
        mp_frame.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(0, ModernTheme.SPACING['small']))

        self.mp_checkbox = ctk.CTkCheckBox(
            mp_frame,
            text="Włącz wieloprocesowość OCR",
            variable=self.multiprocessing_var,
            command=self._on_multiprocessing_change,
            **ModernTheme.get_label_style('body')
        )
        self.mp_checkbox.pack(side="left")

        # Max workers
        workers_frame = ctk.CTkFrame(ocr_frame, fg_color="transparent")
        workers_frame.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(0, ModernTheme.SPACING['small']))

        workers_label = ctk.CTkLabel(
            workers_frame,
            text="Maks. procesów:",
            **ModernTheme.get_label_style('body')
        )
        workers_label.pack(side="left", padx=(0, ModernTheme.SPACING['small']))

        self.workers_entry = ctk.CTkEntry(
            workers_frame,
            textvariable=self.max_workers_var,
            width=100,
            **ModernTheme.get_entry_style()
        )
        self.workers_entry.pack(side="left", padx=(0, ModernTheme.SPACING['small']))
        self.workers_entry.bind('<KeyRelease>', self._on_workers_change)

        workers_info = ctk.CTkLabel(
            workers_frame,
            text=f"(Auto = {multiprocessing.cpu_count()})",
            **ModernTheme.get_label_style('secondary')
        )
        workers_info.pack(side="left")

        # Save button
        save_frame = ctk.CTkFrame(ocr_frame, fg_color="transparent")
        save_frame.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(0, ModernTheme.SPACING['medium']))

        save_ocr_btn = ctk.CTkButton(
            save_frame,
            text="Zapisz konfigurację OCR",
            command=self._save_ocr_config,
            **ModernTheme.get_button_style('success')
        )
        save_ocr_btn.pack(side="left")

    def create_backup(self):
        """Create backup using threaded handler"""
        if self.backup_handler.create_backup_threaded():
            self.status_label.configure(text="Tworzenie backup...", text_color=ModernTheme.COLORS['warning'])
            self.backup_btn.configure(state="disabled")

    def restore_backup(self):
        """Restore backup using threaded handler"""
        if self.backup_handler.restore_backup_threaded():
            self.status_label.configure(text="Przywracanie backup...", text_color=ModernTheme.COLORS['warning'])
            self.restore_btn.configure(state="disabled")

    def show_logs(self):
        """Show logs in new window using CustomTkinter"""
        logs = logger.read_logs()
        win = ctk.CTkToplevel(self)
        win.title("Logi/historia")
        win.geometry("800x600")
        
        # Create text widget
        txt = ctk.CTkTextbox(win, **ModernTheme.get_textbox_style())
        txt.pack(expand=True, fill="both", padx=ModernTheme.SPACING['medium'], pady=ModernTheme.SPACING['medium'])
        txt.insert("1.0", logs)

    def check_update(self):
        """Check for updates using threaded handler"""
        self.status_label.configure(text="Sprawdzanie aktualizacji...", text_color=ModernTheme.COLORS['warning'])
        self.update_btn.configure(state="disabled")
        self.system_ops.check_update_threaded()

    def send_report(self):
        """Send report using threaded handler"""
        self.status_label.configure(text="Wysyłanie raportu...", text_color=ModernTheme.COLORS['warning'])
        self.report_btn.configure(state="disabled")
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
            self.status_label.configure(text="Backup utworzony", text_color=ModernTheme.COLORS['success'])
            self.backup_btn.configure(state="normal")
            
        elif result_type == 'backup_error':
            messagebox.showerror("Błąd backupu", result['error'])
            self.status_label.configure(text="Błąd backup", text_color=ModernTheme.COLORS['error'])
            self.backup_btn.configure(state="normal")
            
        elif result_type == 'restore_success':
            messagebox.showinfo("Backup", result['message'])
            self.status_label.configure(text="Backup przywrócony", text_color=ModernTheme.COLORS['success'])
            self.restore_btn.configure(state="normal")
            
        elif result_type == 'restore_error':
            messagebox.showerror("Błąd backupu", result['error'])
            self.status_label.configure(text="Błąd przywracania", text_color=ModernTheme.COLORS['error'])
            self.restore_btn.configure(state="normal")
            
        elif result_type == 'update_result':
            messagebox.showinfo("Aktualizacje", result['message'])
            self.status_label.configure(text="Sprawdzono aktualizacje", text_color=ModernTheme.COLORS['success'])
            self.update_btn.configure(state="normal")
            
        elif result_type == 'update_error':
            messagebox.showerror("Błąd aktualizacji", result['error'])
            self.status_label.configure(text="Błąd aktualizacji", text_color=ModernTheme.COLORS['error'])
            self.update_btn.configure(state="normal")
            
        elif result_type == 'report_success':
            messagebox.showinfo("Raport", result['message'])
            self.status_label.configure(text="Raport wysłany", text_color=ModernTheme.COLORS['success'])
            self.report_btn.configure(state="normal")
            
        elif result_type == 'report_error':
            messagebox.showerror("Błąd raportu", result['error'])
            self.status_label.configure(text="Błąd raportu", text_color=ModernTheme.COLORS['error'])
            self.report_btn.configure(state="normal")
    
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
    
    def _on_engine_change(self, event=None):
        """Handle OCR engine selection change"""
        engine = self.ocr_engine_var.get()
        ocr_config.set_engine(engine)
        
        # Update GPU availability hint based on engine
        if engine == "tesseract":
            # Tesseract is CPU-only
            self.gpu_enabled_var.set(False)
            self.status_label.configure(text=f"Zmieniono silnik OCR na: {engine} (tylko CPU)", text_color=ModernTheme.COLORS['primary'])
        else:
            self.status_label.configure(text=f"Zmieniono silnik OCR na: {engine}", text_color=ModernTheme.COLORS['primary'])
    
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
        self.status_label.configure(text=f"Tryb OCR zmieniony na: {mode}", text_color=ModernTheme.COLORS['primary'])
    
    def _on_multiprocessing_change(self):
        """Handle multiprocessing setting change"""
        use_mp = self.multiprocessing_var.get()
        ocr_config.set_multiprocessing(use_mp)
        status = "włączona" if use_mp else "wyłączona"
        self.status_label.configure(text=f"Wieloprocesowość OCR {status}", text_color=ModernTheme.COLORS['primary'])
    
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
            self.status_label.configure(text="Konfiguracja OCR zapisana", text_color=ModernTheme.COLORS['success'])
            messagebox.showinfo("Konfiguracja", "Konfiguracja OCR została zapisana. Zmiany będą aktywne przy następnym uruchomieniu OCR.")
        else:
            self.status_label.configure(text="Błąd zapisywania konfiguracji OCR", text_color=ModernTheme.COLORS['error'])
            messagebox.showerror("Błąd", "Nie udało się zapisać konfiguracji OCR.")
    
    def destroy(self):
        """Cleanup when widget is destroyed"""
        if self.backup_handler.operation_thread and self.backup_handler.operation_thread.is_alive():
            self.backup_handler.cancel_operation()
        if self.system_ops.operation_thread and self.system_ops.operation_thread.is_alive():
            self.system_ops.cancel_operation()
        super().destroy()