import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import queue
from exchangelib import Credentials, Account, Configuration, DELEGATE

CONFIG_FILE = "exchange_config.json"

class ExchangeConfigTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Threading support variables
        self.testing_cancelled = False
        self.testing_thread = None
        self.result_queue = queue.Queue()

        # Pola wejściowe
        self.server_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.domain_var = tk.StringVar()

        ttk.Label(self, text="Serwer Exchange:").grid(row=0, column=0, sticky="e")
        ttk.Entry(self, textvariable=self.server_var, width=40).grid(row=0, column=1)

        ttk.Label(self, text="Adres e-mail:").grid(row=1, column=0, sticky="e")
        ttk.Entry(self, textvariable=self.email_var, width=40).grid(row=1, column=1)

        ttk.Label(self, text="Login użytkownika:").grid(row=2, column=0, sticky="e")
        ttk.Entry(self, textvariable=self.username_var, width=40).grid(row=2, column=1)

        ttk.Label(self, text="Hasło:").grid(row=3, column=0, sticky="e")
        ttk.Entry(self, textvariable=self.password_var, show="*", width=40).grid(row=3, column=1)

        ttk.Label(self, text="Domena (opcjonalnie):").grid(row=4, column=0, sticky="e")
        ttk.Entry(self, textvariable=self.domain_var, width=40).grid(row=4, column=1)

        # Przyciski i status
        button_frame = ttk.Frame(self)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Zapisz ustawienia", command=self.save_config).pack(side="left", padx=5)
        
        self.test_button = ttk.Button(button_frame, text="Testuj połączenie", command=self.toggle_test_connection)
        self.test_button.pack(side="left", padx=5)
        
        self.status_label = ttk.Label(button_frame, text="Gotowy", foreground="green")
        self.status_label.pack(side="left", padx=10)

        self.load_config()
        
        # Start processing queue
        self._process_result_queue()

    def save_config(self):
        config = {
            "server": self.server_var.get(),
            "email": self.email_var.get(),
            "username": self.username_var.get(),
            "password": self.password_var.get(),
            "domain": self.domain_var.get()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        messagebox.showinfo("Zapisano", "Ustawienia zostały zapisane.")

    def load_config(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.server_var.set(config.get("server", ""))
                self.email_var.set(config.get("email", ""))
                self.username_var.set(config.get("username", ""))
                self.password_var.set(config.get("password", ""))
                self.domain_var.set(config.get("domain", ""))
        except FileNotFoundError:
            pass

    def toggle_test_connection(self):
        """Toggle between starting and cancelling connection test"""
        if self.testing_thread and self.testing_thread.is_alive():
            self.cancel_test_connection()
        else:
            self.start_test_connection()
    
    def cancel_test_connection(self):
        """Cancel ongoing connection test"""
        self.testing_cancelled = True
        self.status_label.config(text="Anulowanie...", foreground="orange")
        self.test_button.config(text="Testuj połączenie")
    
    def start_test_connection(self):
        """Start the threaded connection test"""
        # Reset cancellation flag
        self.testing_cancelled = False
        
        # Update UI
        self.test_button.config(text="Anuluj test")
        self.status_label.config(text="Testowanie połączenia...", foreground="blue")

        # Start testing in background thread
        self.testing_thread = threading.Thread(
            target=self._threaded_connection_test,
            daemon=True
        )
        self.testing_thread.start()
    
    def _threaded_connection_test(self):
        """Connection test logic running in background thread"""
        try:
            if self.testing_cancelled:
                self.result_queue.put({'type': 'test_cancelled'})
                return
                
            creds = Credentials(username=self.username_var.get(), password=self.password_var.get())
            config = Configuration(server=self.server_var.get(), credentials=creds)
            account = Account(primary_smtp_address=self.email_var.get(), config=config, autodiscover=False, access_type=DELEGATE)
            
            if self.testing_cancelled:
                self.result_queue.put({'type': 'test_cancelled'})
                return
                
            folders = account.inbox.children
            
            self.result_queue.put({
                'type': 'test_success',
                'email': account.primary_smtp_address
            })
        except Exception as e:
            self.result_queue.put({
                'type': 'test_error',
                'error': str(e)
            })
    
    def _process_result_queue(self):
        """Process results from worker thread"""
        try:
            while True:
                try:
                    result = self.result_queue.get_nowait()
                    
                    if result['type'] == 'test_success':
                        email = result['email']
                        messagebox.showinfo("Połączenie OK", f"Połączono z kontem: {email}")
                        self.status_label.config(text="Test połączenia udany", foreground="green")
                        self.test_button.config(text="Testuj połączenie")
                        
                    elif result['type'] == 'test_cancelled':
                        self.status_label.config(text="Test anulowany", foreground="orange")
                        self.test_button.config(text="Testuj połączenie")
                        
                    elif result['type'] == 'test_error':
                        error_msg = result['error']
                        messagebox.showerror("Błąd połączenia", error_msg)
                        self.status_label.config(text="Błąd połączenia", foreground="red")
                        self.test_button.config(text="Testuj połączenie")
                        
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Błąd przetwarzania kolejki wyników: {e}")
        
        # Schedule next check
        self.after(100, self._process_result_queue)

    def test_connection(self):
        """Legacy method for backward compatibility"""
        self.start_test_connection()
    
    def destroy(self):
        """Cleanup when widget is destroyed"""
        if self.testing_thread and self.testing_thread.is_alive():
            self.testing_cancelled = True
        super().destroy()
