import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
from tools import backup, logger, update_checker, email_report, i18n, darkmode

class SystemTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Threading support variables
        self.operation_cancelled = False
        self.operation_thread = None
        self.result_queue = queue.Queue()
        self.progress_queue = queue.Queue()

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
        path = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("Backup", "*.zip")])
        if path:
            self.status_label.config(text="Tworzenie backup...", foreground="blue")
            self.backup_btn.config(state="disabled")
            
            self.operation_thread = threading.Thread(
                target=self._threaded_create_backup,
                args=(path,),
                daemon=True
            )
            self.operation_thread.start()
    
    def _threaded_create_backup(self, path):
        """Create backup in background thread"""
        try:
            backup.create_backup(path)
            self.result_queue.put({
                'type': 'backup_success',
                'message': "Backup utworzony!"
            })
        except Exception as e:
            self.result_queue.put({
                'type': 'backup_error',
                'error': str(e)
            })

    def restore_backup(self):
        path = filedialog.askopenfilename(filetypes=[("Backup", "*.zip")])
        if path:
            self.status_label.config(text="Przywracanie backup...", foreground="blue")
            self.restore_btn.config(state="disabled")
            
            self.operation_thread = threading.Thread(
                target=self._threaded_restore_backup,
                args=(path,),
                daemon=True
            )
            self.operation_thread.start()
    
    def _threaded_restore_backup(self, path):
        """Restore backup in background thread"""
        try:
            backup.restore_backup(path)
            self.result_queue.put({
                'type': 'restore_success',
                'message': "Backup przywrócony!"
            })
        except Exception as e:
            self.result_queue.put({
                'type': 'restore_error',
                'error': str(e)
            })

    def show_logs(self):
        logs = logger.read_logs()
        win = tk.Toplevel(self)
        win.title("Logi/historia")
        txt = tk.Text(win, wrap="word")
        txt.insert("1.0", logs)
        txt.pack(expand=True, fill="both")

    def check_update(self):
        self.status_label.config(text="Sprawdzanie aktualizacji...", foreground="blue")
        self.update_btn.config(state="disabled")
        
        self.operation_thread = threading.Thread(
            target=self._threaded_check_update,
            daemon=True
        )
        self.operation_thread.start()
    
    def _threaded_check_update(self):
        """Check for updates in background thread"""
        try:
            result = update_checker.check_for_update()
            self.result_queue.put({
                'type': 'update_result',
                'message': result
            })
        except Exception as e:
            self.result_queue.put({
                'type': 'update_error',
                'error': str(e)
            })

    def send_report(self):
        self.status_label.config(text="Wysyłanie raportu...", foreground="blue")
        self.report_btn.config(state="disabled")
        
        self.operation_thread = threading.Thread(
            target=self._threaded_send_report,
            daemon=True
        )
        self.operation_thread.start()
    
    def _threaded_send_report(self):
        """Send report in background thread"""
        try:
            email_report.send_report()
            self.result_queue.put({
                'type': 'report_success',
                'message': "Raport wysłany!"
            })
        except Exception as e:
            self.result_queue.put({
                'type': 'report_error',
                'error': str(e)
            })

    def restart_app(self):
        import os, sys
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    def _process_result_queue(self):
        """Process results from worker thread"""
        try:
            while True:
                try:
                    result = self.result_queue.get_nowait()
                    
                    if result['type'] == 'backup_success':
                        messagebox.showinfo("Backup", result['message'])
                        self.status_label.config(text="Backup utworzony", foreground="green")
                        self.backup_btn.config(state="normal")
                        
                    elif result['type'] == 'backup_error':
                        messagebox.showerror("Błąd backupu", result['error'])
                        self.status_label.config(text="Błąd backup", foreground="red")
                        self.backup_btn.config(state="normal")
                        
                    elif result['type'] == 'restore_success':
                        messagebox.showinfo("Backup", result['message'])
                        self.status_label.config(text="Backup przywrócony", foreground="green")
                        self.restore_btn.config(state="normal")
                        
                    elif result['type'] == 'restore_error':
                        messagebox.showerror("Błąd backupu", result['error'])
                        self.status_label.config(text="Błąd przywracania", foreground="red")
                        self.restore_btn.config(state="normal")
                        
                    elif result['type'] == 'update_result':
                        messagebox.showinfo("Aktualizacje", result['message'])
                        self.status_label.config(text="Sprawdzono aktualizacje", foreground="green")
                        self.update_btn.config(state="normal")
                        
                    elif result['type'] == 'update_error':
                        messagebox.showerror("Błąd aktualizacji", result['error'])
                        self.status_label.config(text="Błąd aktualizacji", foreground="red")
                        self.update_btn.config(state="normal")
                        
                    elif result['type'] == 'report_success':
                        messagebox.showinfo("Raport", result['message'])
                        self.status_label.config(text="Raport wysłany", foreground="green")
                        self.report_btn.config(state="normal")
                        
                    elif result['type'] == 'report_error':
                        messagebox.showerror("Błąd raportu", result['error'])
                        self.status_label.config(text="Błąd raportu", foreground="red")
                        self.report_btn.config(state="normal")
                        
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
    
    def destroy(self):
        """Cleanup when widget is destroyed"""
        if self.operation_thread and self.operation_thread.is_alive():
            self.operation_cancelled = True
        super().destroy()