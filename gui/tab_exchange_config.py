import tkinter as tk
from tkinter import ttk, messagebox
import json
from exchangelib import Credentials, Account, Configuration, DELEGATE

CONFIG_FILE = "exchange_config.json"

class ExchangeConfigTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

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

        # Przyciski
        ttk.Button(self, text="Zapisz ustawienia", command=self.save_config).grid(row=5, column=0, pady=10)
        ttk.Button(self, text="Testuj połączenie", command=self.test_connection).grid(row=5, column=1, pady=10)

        self.load_config()

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

    def test_connection(self):
        try:
            creds = Credentials(username=self.username_var.get(), password=self.password_var.get())
            config = Configuration(server=self.server_var.get(), credentials=creds)
            account = Account(primary_smtp_address=self.email_var.get(), config=config, autodiscover=False, access_type=DELEGATE)
            folders = account.inbox.children
            messagebox.showinfo("Połączenie OK", f"Połączono z kontem: {account.primary_smtp_address}")
        except Exception as e:
            messagebox.showerror("Błąd połączenia", str(e))
