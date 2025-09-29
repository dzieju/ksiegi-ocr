"""
Multi-account mail configuration widget supporting both Exchange and IMAP/SMTP
"""
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    HAVE_TKINTER = True
except ImportError:
    HAVE_TKINTER = False
    # This widget requires tkinter
    raise ImportError("MailConfigWidget requires tkinter")

import json
import threading
import queue
from imapclient import IMAPClient
import smtplib
import poplib
import ssl
from exchangelib import Credentials, Account, Configuration, DELEGATE
from tools.logger import log

CONFIG_FILE = "mail_config.json"

class MailConfigWidget(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Threading support variables
        self.testing_cancelled = False
        self.testing_thread = None
        self.result_queue = queue.Queue()
        
        # Account management
        self.accounts = []
        self.main_account_index = 0
        self.selected_account_index = 0
        
        self.create_widgets()
        self.load_config()
        
        # Start processing queue
        self._process_result_queue()
    
    def create_widgets(self):
        """Create the UI widgets"""
        # Main container with two columns
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Account list
        left_frame = ttk.LabelFrame(main_frame, text="Konta pocztowe", padding=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Account listbox with scrollbar
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.pack(fill="both", expand=True)
        
        self.account_listbox = tk.Listbox(listbox_frame, height=8)
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.account_listbox.yview)
        self.account_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.account_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.account_listbox.bind("<<ListboxSelect>>", self.on_account_select)
        
        # Account management buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="Dodaj konto", command=self.add_account).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Usuń konto", command=self.remove_account).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Ustaw jako główne", command=self.set_main_account).pack(side="left")
        
        # Right side - Account configuration
        right_frame = ttk.LabelFrame(main_frame, text="Konfiguracja konta", padding=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Configure grid weights
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Account configuration form
        self.create_account_form(right_frame)
    
    def create_account_form(self, parent):
        """Create the account configuration form"""
        # Account type selection
        ttk.Label(parent, text="Typ konta:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.account_type_var = tk.StringVar(value="exchange")
        type_frame = ttk.Frame(parent)
        type_frame.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Radiobutton(type_frame, text="Exchange", variable=self.account_type_var, 
                       value="exchange", command=self.on_account_type_change).pack(side="left", padx=(0, 10))
        ttk.Radiobutton(type_frame, text="IMAP/SMTP", variable=self.account_type_var, 
                       value="imap_smtp", command=self.on_account_type_change).pack(side="left", padx=(0, 10))
        ttk.Radiobutton(type_frame, text="POP3/SMTP", variable=self.account_type_var, 
                       value="pop3_smtp", command=self.on_account_type_change).pack(side="left")
        
        # Common fields
        ttk.Label(parent, text="Nazwa konta:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.account_name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.account_name_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(parent, text="Adres e-mail:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.email_var, width=40).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(parent, text="Login:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.username_var, width=40).grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(parent, text="Hasło:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.password_var, show="*", width=40).grid(row=4, column=1, padx=5, pady=5)
        
        # Authentication method
        ttk.Label(parent, text="Metoda uwierzytelniania:").grid(row=5, column=0, sticky="e", padx=5, pady=5)
        self.auth_method_var = tk.StringVar(value="password")
        auth_frame = ttk.Frame(parent)
        auth_frame.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Radiobutton(auth_frame, text="Hasło", variable=self.auth_method_var, 
                       value="password").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(auth_frame, text="OAuth2", variable=self.auth_method_var, 
                       value="oauth2").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(auth_frame, text="App Password", variable=self.auth_method_var, 
                       value="app_password").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(auth_frame, text="PLAIN/Plain Text", variable=self.auth_method_var, 
                       value="plain").pack(side="left")
        
        # Exchange specific fields
        self.exchange_frame = ttk.LabelFrame(parent, text="Ustawienia Exchange", padding=5)
        self.exchange_frame.grid(row=6, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        
        ttk.Label(self.exchange_frame, text="Serwer Exchange:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.exchange_server_var = tk.StringVar()
        ttk.Entry(self.exchange_frame, textvariable=self.exchange_server_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.exchange_frame, text="Domena (opcjonalnie):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.domain_var = tk.StringVar()
        ttk.Entry(self.exchange_frame, textvariable=self.domain_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        
        # IMAP/SMTP specific fields
        self.imap_smtp_frame = ttk.LabelFrame(parent, text="Ustawienia IMAP/SMTP", padding=5)
        self.imap_smtp_frame.grid(row=7, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        
        # IMAP settings
        imap_frame = ttk.LabelFrame(self.imap_smtp_frame, text="IMAP (odbiór)", padding=5)
        imap_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(imap_frame, text="Serwer IMAP:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.imap_server_var = tk.StringVar()
        ttk.Entry(imap_frame, textvariable=self.imap_server_var, width=30).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(imap_frame, text="Port IMAP:").grid(row=0, column=2, sticky="e", padx=5, pady=2)
        self.imap_port_var = tk.StringVar(value="993")
        ttk.Entry(imap_frame, textvariable=self.imap_port_var, width=10).grid(row=0, column=3, padx=5, pady=2)
        
        self.imap_ssl_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(imap_frame, text="SSL/TLS", variable=self.imap_ssl_var).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        # SMTP settings
        smtp_frame = ttk.LabelFrame(self.imap_smtp_frame, text="SMTP (wysyłanie)", padding=5)
        smtp_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(smtp_frame, text="Serwer SMTP:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.smtp_server_var = tk.StringVar()
        ttk.Entry(smtp_frame, textvariable=self.smtp_server_var, width=30).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(smtp_frame, text="Port SMTP:").grid(row=0, column=2, sticky="e", padx=5, pady=2)
        self.smtp_port_var = tk.StringVar(value="587")
        ttk.Entry(smtp_frame, textvariable=self.smtp_port_var, width=10).grid(row=0, column=3, padx=5, pady=2)
        
        self.smtp_ssl_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(smtp_frame, text="SSL/TLS", variable=self.smtp_ssl_var).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        # POP3/SMTP specific fields
        self.pop3_smtp_frame = ttk.LabelFrame(parent, text="Ustawienia POP3/SMTP", padding=5)
        self.pop3_smtp_frame.grid(row=8, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        
        # POP3 settings
        pop3_frame = ttk.LabelFrame(self.pop3_smtp_frame, text="POP3 (odbiór)", padding=5)
        pop3_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(pop3_frame, text="Serwer POP3:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.pop3_server_var = tk.StringVar()
        ttk.Entry(pop3_frame, textvariable=self.pop3_server_var, width=30).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(pop3_frame, text="Port POP3:").grid(row=0, column=2, sticky="e", padx=5, pady=2)
        self.pop3_port_var = tk.StringVar(value="995")
        ttk.Entry(pop3_frame, textvariable=self.pop3_port_var, width=10).grid(row=0, column=3, padx=5, pady=2)
        
        self.pop3_ssl_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(pop3_frame, text="SSL/TLS", variable=self.pop3_ssl_var).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        # SMTP settings for POP3 (reusing same frame layout)
        smtp_pop3_frame = ttk.LabelFrame(self.pop3_smtp_frame, text="SMTP (wysyłanie)", padding=5)
        smtp_pop3_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(smtp_pop3_frame, text="Serwer SMTP:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.smtp_server_pop3_var = tk.StringVar()
        ttk.Entry(smtp_pop3_frame, textvariable=self.smtp_server_pop3_var, width=30).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(smtp_pop3_frame, text="Port SMTP:").grid(row=0, column=2, sticky="e", padx=5, pady=2)
        self.smtp_port_pop3_var = tk.StringVar(value="587")
        ttk.Entry(smtp_pop3_frame, textvariable=self.smtp_port_pop3_var, width=10).grid(row=0, column=3, padx=5, pady=2)
        
        self.smtp_ssl_pop3_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(smtp_pop3_frame, text="SSL/TLS", variable=self.smtp_ssl_pop3_var).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        # Configure grid weights for frames
        self.exchange_frame.grid_columnconfigure(1, weight=1)
        self.imap_smtp_frame.grid_columnconfigure(1, weight=1)
        self.pop3_smtp_frame.grid_columnconfigure(1, weight=1)
        imap_frame.grid_columnconfigure(1, weight=1)
        smtp_frame.grid_columnconfigure(1, weight=1)
        pop3_frame.grid_columnconfigure(1, weight=1)
        smtp_pop3_frame.grid_columnconfigure(1, weight=1)
        
        # Action buttons
        action_frame = ttk.Frame(parent)
        action_frame.grid(row=9, column=0, columnspan=2, pady=20)
        
        self.test_button = ttk.Button(action_frame, text="Testuj połączenie", command=self.toggle_test_connection)
        self.test_button.pack(side="left", padx=5)
        
        ttk.Button(action_frame, text="Zapisz ustawienia", command=self.save_config).pack(side="left", padx=5)
        
        self.status_label = ttk.Label(action_frame, text="Gotowy", foreground="green")
        self.status_label.pack(side="left", padx=10)
        
        # Initially show appropriate fields
        self.on_account_type_change()
    
    def on_account_type_change(self):
        """Handle account type change"""
        account_type = self.account_type_var.get()
        if account_type == "exchange":
            self.exchange_frame.grid()
            self.imap_smtp_frame.grid_remove()
            self.pop3_smtp_frame.grid_remove()
        elif account_type == "imap_smtp":
            self.exchange_frame.grid_remove()
            self.imap_smtp_frame.grid()
            self.pop3_smtp_frame.grid_remove()
        elif account_type == "pop3_smtp":
            self.exchange_frame.grid_remove()
            self.imap_smtp_frame.grid_remove()
            self.pop3_smtp_frame.grid()
    
    def add_account(self):
        """Add a new account"""
        account = {
            "name": f"Nowe konto {len(self.accounts) + 1}",
            "type": "exchange",
            "email": "",
            "username": "",
            "password": "",
            "auth_method": "password",
            "exchange_server": "",
            "domain": "",
            "imap_server": "",
            "imap_port": 993,
            "imap_ssl": True,
            "smtp_server": "",
            "smtp_port": 587,
            "smtp_ssl": True,
            "pop3_server": "",
            "pop3_port": 995,
            "pop3_ssl": True,
            "smtp_server_pop3": "",
            "smtp_port_pop3": 587,
            "smtp_ssl_pop3": True
        }
        self.accounts.append(account)
        self.refresh_account_list()
        self.account_listbox.selection_set(len(self.accounts) - 1)
        self.load_account_to_form(len(self.accounts) - 1)
    
    def remove_account(self):
        """Remove selected account"""
        if not self.accounts or self.selected_account_index < 0:
            messagebox.showwarning("Ostrzeżenie", "Wybierz konto do usunięcia.")
            return
        
        if len(self.accounts) == 1:
            messagebox.showwarning("Ostrzeżenie", "Nie można usunąć ostatniego konta.")
            return
        
        account_name = self.accounts[self.selected_account_index]["name"]
        if messagebox.askyesno("Potwierdzenie", f"Czy na pewno chcesz usunąć konto '{account_name}'?"):
            # Adjust main account index if necessary
            if self.main_account_index == self.selected_account_index:
                self.main_account_index = 0
            elif self.main_account_index > self.selected_account_index:
                self.main_account_index -= 1
            
            del self.accounts[self.selected_account_index]
            self.refresh_account_list()
            
            # Select first account if available
            if self.accounts:
                self.selected_account_index = 0
                self.account_listbox.selection_set(0)
                self.load_account_to_form(0)
            else:
                self.clear_form()
    
    def set_main_account(self):
        """Set selected account as main"""
        if self.accounts and self.selected_account_index >= 0:
            self.main_account_index = self.selected_account_index
            self.refresh_account_list()
            
            # Immediately save configuration to make the change persistent
            config = {
                "accounts": self.accounts,
                "main_account_index": self.main_account_index
            }
            
            try:
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Informacja", f"Konto '{self.accounts[self.main_account_index]['name']}' zostało ustawione jako główne.")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zapisać konfiguracji: {str(e)}")
    
    def on_account_select(self, event):
        """Handle account selection"""
        selection = self.account_listbox.curselection()
        if selection:
            self.selected_account_index = selection[0]
            self.load_account_to_form(self.selected_account_index)
    
    def load_account_to_form(self, index):
        """Load account data to form"""
        if 0 <= index < len(self.accounts):
            account = self.accounts[index]
            
            self.account_name_var.set(account.get("name", ""))
            self.account_type_var.set(account.get("type", "exchange"))
            self.email_var.set(account.get("email", ""))
            self.username_var.set(account.get("username", ""))
            self.password_var.set(account.get("password", ""))
            self.auth_method_var.set(account.get("auth_method", "password"))
            
            # Exchange fields
            self.exchange_server_var.set(account.get("exchange_server", ""))
            self.domain_var.set(account.get("domain", ""))
            
            # IMAP/SMTP fields
            self.imap_server_var.set(account.get("imap_server", ""))
            self.imap_port_var.set(str(account.get("imap_port", 993)))
            self.imap_ssl_var.set(account.get("imap_ssl", True))
            self.smtp_server_var.set(account.get("smtp_server", ""))
            self.smtp_port_var.set(str(account.get("smtp_port", 587)))
            self.smtp_ssl_var.set(account.get("smtp_ssl", True))
            
            # POP3/SMTP fields
            self.pop3_server_var.set(account.get("pop3_server", ""))
            self.pop3_port_var.set(str(account.get("pop3_port", 995)))
            self.pop3_ssl_var.set(account.get("pop3_ssl", True))
            self.smtp_server_pop3_var.set(account.get("smtp_server_pop3", ""))
            self.smtp_port_pop3_var.set(str(account.get("smtp_port_pop3", 587)))
            self.smtp_ssl_pop3_var.set(account.get("smtp_ssl_pop3", True))
            
            self.on_account_type_change()
    
    def clear_form(self):
        """Clear the form"""
        self.account_name_var.set("")
        self.email_var.set("")
        self.username_var.set("")
        self.password_var.set("")
        self.auth_method_var.set("password")
        self.exchange_server_var.set("")
        self.domain_var.set("")
        self.imap_server_var.set("")
        self.imap_port_var.set("993")
        self.imap_ssl_var.set(True)
        self.smtp_server_var.set("")
        self.smtp_port_var.set("587")
        self.smtp_ssl_var.set(True)
        self.pop3_server_var.set("")
        self.pop3_port_var.set("995")
        self.pop3_ssl_var.set(True)
        self.smtp_server_pop3_var.set("")
        self.smtp_port_pop3_var.set("587")
        self.smtp_ssl_pop3_var.set(True)
    
    def refresh_account_list(self):
        """Refresh the account list display"""
        self.account_listbox.delete(0, tk.END)
        for i, account in enumerate(self.accounts):
            display_name = account["name"]
            if i == self.main_account_index:
                display_name += " (główne)"
            self.account_listbox.insert(tk.END, display_name)
    
    def save_config(self):
        """Save current form data to selected account and all accounts to config file"""
        if not self.accounts:
            messagebox.showwarning("Ostrzeżenie", "Brak kont do zapisania.")
            return
        
        # First, save current form data to selected account if we have one selected
        if self.selected_account_index >= 0:
            # Validation
            if not self.account_name_var.get().strip():
                messagebox.showerror("Błąd", "Nazwa konta nie może być pusta.")
                return
            
            if not self.email_var.get().strip():
                messagebox.showerror("Błąd", "Adres e-mail nie może być pusty.")
                return
            
            # Update the selected account with current form data
            account = self.accounts[self.selected_account_index]
            account.update({
                "name": self.account_name_var.get().strip(),
                "type": self.account_type_var.get(),
                "email": self.email_var.get().strip(),
                "username": self.username_var.get().strip(),
                "password": self.password_var.get(),
                "auth_method": self.auth_method_var.get(),
                "exchange_server": self.exchange_server_var.get().strip(),
                "domain": self.domain_var.get().strip(),
                "imap_server": self.imap_server_var.get().strip(),
                "imap_port": int(self.imap_port_var.get()) if self.imap_port_var.get().isdigit() else 993,
                "imap_ssl": self.imap_ssl_var.get(),
                "smtp_server": self.smtp_server_var.get().strip(),
                "smtp_port": int(self.smtp_port_var.get()) if self.smtp_port_var.get().isdigit() else 587,
                "smtp_ssl": self.smtp_ssl_var.get(),
                "pop3_server": self.pop3_server_var.get().strip(),
                "pop3_port": int(self.pop3_port_var.get()) if self.pop3_port_var.get().isdigit() else 995,
                "pop3_ssl": self.pop3_ssl_var.get(),
                "smtp_server_pop3": self.smtp_server_pop3_var.get().strip(),
                "smtp_port_pop3": int(self.smtp_port_pop3_var.get()) if self.smtp_port_pop3_var.get().isdigit() else 587,
                "smtp_ssl_pop3": self.smtp_ssl_pop3_var.get()
            })
            
            # Refresh the account list to show any name changes
            self.refresh_account_list()
        
        # Now save all accounts to config file
        config = {
            "accounts": self.accounts,
            "main_account_index": self.main_account_index
        }
        
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Zapisano", "Konfiguracja została zapisana.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać konfiguracji: {str(e)}")
    
    def load_config(self):
        """Load configuration from file"""
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            self.accounts = config.get("accounts", [])
            self.main_account_index = config.get("main_account_index", 0)
            
            # Validate main_account_index
            if self.main_account_index >= len(self.accounts):
                self.main_account_index = 0
            
            self.refresh_account_list()
            
            # Load first account if available
            if self.accounts:
                self.selected_account_index = 0
                self.account_listbox.selection_set(0)
                self.load_account_to_form(0)
                
        except FileNotFoundError:
            # Try to migrate from old Exchange config
            self.migrate_from_exchange_config()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można wczytać konfiguracji: {str(e)}")
            # Create default account
            self.add_account()
    
    def migrate_from_exchange_config(self):
        """Migrate from old Exchange configuration format"""
        try:
            with open("exchange_config.json", "r") as f:
                old_config = json.load(f)
            
            # Create account from old config
            account = {
                "name": f"Exchange ({old_config.get('email', 'Konto')})",
                "type": "exchange",
                "email": old_config.get("email", ""),
                "username": old_config.get("username", ""),
                "password": old_config.get("password", ""),
                "auth_method": "password",
                "exchange_server": old_config.get("server", ""),
                "domain": old_config.get("domain", ""),
                "imap_server": "",
                "imap_port": 993,
                "imap_ssl": True,
                "smtp_server": "",
                "smtp_port": 587,
                "smtp_ssl": True,
                "pop3_server": "",
                "pop3_port": 995,
                "pop3_ssl": True,
                "smtp_server_pop3": "",
                "smtp_port_pop3": 587,
                "smtp_ssl_pop3": True
            }
            
            self.accounts = [account]
            self.main_account_index = 0
            self.refresh_account_list()
            
            if self.accounts:
                self.selected_account_index = 0
                self.account_listbox.selection_set(0)
                self.load_account_to_form(0)
            
            messagebox.showinfo("Migracja", "Konfiguracja Exchange została zmigrowana do nowego formatu.")
            
        except FileNotFoundError:
            # No old config, create default account
            self.add_account()
    
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
        if self.selected_account_index < 0 or not self.accounts:
            messagebox.showwarning("Ostrzeżenie", "Wybierz konto do testowania.")
            return
        
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
            
            # Create a temporary account object with current form data for testing
            test_account = {
                "name": self.account_name_var.get().strip(),
                "type": self.account_type_var.get(),
                "email": self.email_var.get().strip(),
                "username": self.username_var.get().strip(),
                "password": self.password_var.get(),
                "auth_method": self.auth_method_var.get(),
                "exchange_server": self.exchange_server_var.get().strip(),
                "domain": self.domain_var.get().strip(),
                "imap_server": self.imap_server_var.get().strip(),
                "imap_port": int(self.imap_port_var.get()) if self.imap_port_var.get().isdigit() else 993,
                "imap_ssl": self.imap_ssl_var.get(),
                "smtp_server": self.smtp_server_var.get().strip(),
                "smtp_port": int(self.smtp_port_var.get()) if self.smtp_port_var.get().isdigit() else 587,
                "smtp_ssl": self.smtp_ssl_var.get(),
                "pop3_server": self.pop3_server_var.get().strip(),
                "pop3_port": int(self.pop3_port_var.get()) if self.pop3_port_var.get().isdigit() else 995,
                "pop3_ssl": self.pop3_ssl_var.get(),
                "smtp_server_pop3": self.smtp_server_pop3_var.get().strip(),
                "smtp_port_pop3": int(self.smtp_port_pop3_var.get()) if self.smtp_port_pop3_var.get().isdigit() else 587,
                "smtp_ssl_pop3": self.smtp_ssl_pop3_var.get()
            }
            
            account_type = test_account["type"]
            
            if account_type == "exchange":
                self._test_exchange_connection(test_account)
            elif account_type == "imap_smtp":
                self._test_imap_smtp_connection(test_account)
            elif account_type == "pop3_smtp":
                self._test_pop3_smtp_connection(test_account)
                
        except Exception as e:
            self.result_queue.put({
                'type': 'test_error',
                'error': str(e)
            })
    
    def _test_exchange_connection(self, account):
        """Test Exchange connection"""
        try:
            creds = Credentials(username=account["username"], password=account["password"])
            config = Configuration(server=account["exchange_server"], credentials=creds)
            ex_account = Account(primary_smtp_address=account["email"], config=config, autodiscover=False, access_type=DELEGATE)
            
            if self.testing_cancelled:
                self.result_queue.put({'type': 'test_cancelled'})
                return
            
            # Try to access inbox to verify connection
            folders = ex_account.inbox.children
            
            self.result_queue.put({
                'type': 'test_success',
                'message': f"Połączono z kontem Exchange: {ex_account.primary_smtp_address}"
            })
        except Exception as e:
            self.result_queue.put({
                'type': 'test_error',
                'error': f"Błąd połączenia Exchange: {str(e)}"
            })
    
    def _test_imap_smtp_connection(self, account):
        """Test IMAP/SMTP connection"""
        try:
            # Test IMAP connection
            if self.testing_cancelled:
                self.result_queue.put({'type': 'test_cancelled'})
                return
            
            # Create IMAPClient connection
            imap = IMAPClient(
                account["imap_server"], 
                port=account["imap_port"],
                ssl=account["imap_ssl"]
            )
            
            imap.login(account["username"], account["password"])
            imap.select_folder("INBOX")
            imap.logout()
            
            if self.testing_cancelled:
                self.result_queue.put({'type': 'test_cancelled'})
                return
            
            # Test SMTP connection
            if account["smtp_ssl"]:
                smtp = smtplib.SMTP_SSL(account["smtp_server"], account["smtp_port"])
            else:
                smtp = smtplib.SMTP(account["smtp_server"], account["smtp_port"])
                smtp.starttls()
            
            smtp.login(account["username"], account["password"])
            smtp.quit()
            
            self.result_queue.put({
                'type': 'test_success',
                'message': f"Połączono z kontem IMAP/SMTP: {account['email']}"
            })
            
        except Exception as e:
            self.result_queue.put({
                'type': 'test_error',
                'error': f"Błąd połączenia IMAP/SMTP: {str(e)}"
            })
    
    def _test_pop3_smtp_connection(self, account):
        """Test POP3/SMTP connection"""
        log(f"[MAIL CONFIG] Rozpoczęcie testu połączenia POP3/SMTP dla konta: {account.get('email', 'nieznane')}")
        log(f"[MAIL CONFIG] Parametry POP3: serwer={account.get('pop3_server', '')}, port={account.get('pop3_port', 995)}, SSL={account.get('pop3_ssl', True)}")
        log(f"[MAIL CONFIG] Parametry SMTP: serwer={account.get('smtp_server_pop3', '')}, port={account.get('smtp_port_pop3', 587)}, SSL={account.get('smtp_ssl_pop3', True)}")
        log(f"[MAIL CONFIG] Metoda uwierzytelniania: {account.get('auth_method', 'password')}")
        
        try:
            # Test POP3 connection
            if self.testing_cancelled:
                log("[MAIL CONFIG] Test POP3/SMTP anulowany przez użytkownika")
                self.result_queue.put({'type': 'test_cancelled'})
                return
            
            log("[MAIL CONFIG] Próba nawiązania połączenia POP3...")
            if account["pop3_ssl"]:
                log("[MAIL CONFIG] Używanie POP3_SSL")
                pop3 = poplib.POP3_SSL(account["pop3_server"], account["pop3_port"])
            else:
                log("[MAIL CONFIG] Używanie POP3 bez SSL")
                pop3 = poplib.POP3(account["pop3_server"], account["pop3_port"])
            
            log("[MAIL CONFIG] POP3 połączenie nawiązane, próba logowania...")
            pop3.user(account["username"])
            pop3.pass_(account["password"])
            log("[MAIL CONFIG] POP3 logowanie pomyślne")
            
            # Get message count to verify connection
            log("[MAIL CONFIG] Pobieranie liczby wiadomości z POP3...")
            msg_count = len(pop3.list()[1])
            log(f"[MAIL CONFIG] POP3 - znaleziono {msg_count} wiadomości")
            pop3.quit()
            log("[MAIL CONFIG] POP3 połączenie zamknięte")
            
            if self.testing_cancelled:
                log("[MAIL CONFIG] Test POP3/SMTP anulowany przez użytkownika po POP3")
                self.result_queue.put({'type': 'test_cancelled'})
                return
            
            # Test SMTP connection (using POP3 SMTP settings)
            smtp_server = account.get("smtp_server_pop3", account.get("smtp_server", ""))
            smtp_port = account.get("smtp_port_pop3", account.get("smtp_port", 587))
            smtp_ssl = account.get("smtp_ssl_pop3", account.get("smtp_ssl", True))
            
            log(f"[MAIL CONFIG] Próba nawiązania połączenia SMTP: {smtp_server}:{smtp_port}, SSL={smtp_ssl}")
            
            if smtp_ssl:
                log("[MAIL CONFIG] Używanie SMTP_SSL")
                smtp = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                log("[MAIL CONFIG] Używanie SMTP z STARTTLS")
                smtp = smtplib.SMTP(smtp_server, smtp_port)
                smtp.starttls()
            
            log("[MAIL CONFIG] SMTP połączenie nawiązane, próba logowania...")
            smtp.login(account["username"], account["password"])
            log("[MAIL CONFIG] SMTP logowanie pomyślne")
            smtp.quit()
            log("[MAIL CONFIG] SMTP połączenie zamknięte")
            
            success_message = f"Połączono z kontem POP3/SMTP: {account['email']} ({msg_count} wiadomości)"
            log(f"[MAIL CONFIG] Test POP3/SMTP zakończony pomyślnie: {success_message}")
            
            self.result_queue.put({
                'type': 'test_success',
                'message': success_message
            })
            
        except Exception as e:
            error_message = f"Błąd połączenia POP3/SMTP: {str(e)}"
            log(f"[MAIL CONFIG] Test POP3/SMTP zakończony błędem: {error_message}")
            log(f"[MAIL CONFIG] Szczegóły błędu: {type(e).__name__}: {str(e)}")
            self.result_queue.put({
                'type': 'test_error',
                'error': error_message
            })
    
    def _process_result_queue(self):
        """Process results from worker thread"""
        try:
            while True:
                try:
                    result = self.result_queue.get_nowait()
                    
                    if result['type'] == 'test_success':
                        message = result['message']
                        messagebox.showinfo("Połączenie OK", message)
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
    
    def get_main_account(self):
        """Get the main account configuration"""
        if self.accounts and 0 <= self.main_account_index < len(self.accounts):
            return self.accounts[self.main_account_index]
        return None
    
    def get_account_by_index(self, index):
        """Get account by index"""
        if 0 <= index < len(self.accounts):
            return self.accounts[index]
        return None
    
    def get_all_accounts(self):
        """Get all accounts"""
        return self.accounts.copy()
    
    def destroy(self):
        """Cleanup when widget is destroyed"""
        if self.testing_thread and self.testing_thread.is_alive():
            self.testing_cancelled = True
        super().destroy()