import tkinter as tk
from tkinter import ttk, messagebox
import queue
from tools import logger, i18n, darkmode
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
    
    def destroy(self):
        """Cleanup when widget is destroyed"""
        if self.backup_handler.operation_thread and self.backup_handler.operation_thread.is_alive():
            self.backup_handler.cancel_operation()
        if self.system_ops.operation_thread and self.system_ops.operation_thread.is_alive():
            self.system_ops.cancel_operation()
        super().destroy()