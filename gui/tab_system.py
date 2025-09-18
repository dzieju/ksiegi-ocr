import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tools import backup, logger, update_checker, email_report, i18n, darkmode

class SystemTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Backup
        backup_btn = ttk.Button(self, text=i18n.translate("Utwórz backup"), command=self.create_backup)
        backup_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        restore_btn = ttk.Button(self, text=i18n.translate("Przywróć backup"), command=self.restore_backup)
        restore_btn.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Logi/historia
        log_btn = ttk.Button(self, text=i18n.translate("Pokaż logi"), command=self.show_logs)
        log_btn.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        # Aktualizacje
        update_btn = ttk.Button(self, text=i18n.translate("Sprawdź aktualizacje"), command=self.check_update)
        update_btn.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        # Raportowanie
        report_btn = ttk.Button(self, text=i18n.translate("Wyślij raport"), command=self.send_report)
        report_btn.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        # Dark mode
        theme_btn = ttk.Button(self, text=i18n.translate("Przełącz tryb ciemny/jasny"), command=darkmode.toggle_theme)
        theme_btn.grid(row=4, column=0, padx=10, pady=10, sticky="w")

        # Restart
        restart_btn = ttk.Button(self, text=i18n.translate("Restartuj aplikację"), command=self.restart_app)
        restart_btn.grid(row=5, column=0, padx=10, pady=10, sticky="w")

    def create_backup(self):
        path = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("Backup", "*.zip")])
        if path:
            try:
                backup.create_backup(path)
                messagebox.showinfo("Backup", "Backup utworzony!")
            except Exception as e:
                messagebox.showerror("Błąd backupu", str(e))

    def restore_backup(self):
        path = filedialog.askopenfilename(filetypes=[("Backup", "*.zip")])
        if path:
            try:
                backup.restore_backup(path)
                messagebox.showinfo("Backup", "Backup przywrócony!")
            except Exception as e:
                messagebox.showerror("Błąd backupu", str(e))

    def show_logs(self):
        logs = logger.read_logs()
        win = tk.Toplevel(self)
        win.title("Logi/historia")
        txt = tk.Text(win, wrap="word")
        txt.insert("1.0", logs)
        txt.pack(expand=True, fill="both")

    def check_update(self):
        result = update_checker.check_for_update()
        messagebox.showinfo("Aktualizacje", result)

    def send_report(self):
        email_report.send_report()
        messagebox.showinfo("Raport", "Raport wysłany!")

    def restart_app(self):
        import os, sys
        os.execl(sys.executable, sys.executable, *sys.argv)