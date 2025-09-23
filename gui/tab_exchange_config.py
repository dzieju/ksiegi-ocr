import customtkinter as ctk
from tkinter import messagebox
import json
import threading
import queue
from exchangelib import Credentials, Account, Configuration, DELEGATE
from gui.modern_theme import ModernTheme
from gui.tooltip_utils import add_tooltip, TOOLTIPS

CONFIG_FILE = "exchange_config.json"

class ExchangeConfigTab(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent, **ModernTheme.get_frame_style('section'))

        # Configure the scrollable frame to support potential grid layouts
        self.grid_columnconfigure(0, weight=1)

        # Threading support variables
        self.testing_cancelled = False
        self.testing_thread = None
        self.result_queue = queue.Queue()

        # Pola wejściowe
        self.server_var = ctk.StringVar()
        self.email_var = ctk.StringVar()
        self.username_var = ctk.StringVar()
        self.password_var = ctk.StringVar()
        self.domain_var = ctk.StringVar()

        self.create_widgets()
        self.load_config()
        self._process_result_queue()

    def create_widgets(self):
        """Create modern Exchange configuration widgets"""
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="⚙️ Konfiguracja Serwera Exchange",
            **ModernTheme.get_label_style('heading')
        )
        title_label.pack(pady=(0, ModernTheme.SPACING['large']), anchor="w")

        # Connection settings frame
        config_frame = ctk.CTkFrame(self, **ModernTheme.get_frame_style('card'))
        config_frame.pack(fill="x", pady=(0, ModernTheme.SPACING['medium']))
        
        config_title = ctk.CTkLabel(
            config_frame,
            text="🌐 Parametry połączenia",
            **ModernTheme.get_label_style('subheading')
        )
        config_title.pack(pady=(ModernTheme.SPACING['medium'], ModernTheme.SPACING['small']), anchor="w", padx=ModernTheme.SPACING['medium'])

        # Server field
        server_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        server_frame.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(0, ModernTheme.SPACING['small']))

        server_label = ctk.CTkLabel(server_frame, text="Serwer Exchange:", **ModernTheme.get_label_style('body'))
        server_label.pack(side="left", anchor="w")

        server_entry = ctk.CTkEntry(
            server_frame,
            textvariable=self.server_var,
            placeholder_text="np. outlook.office365.com",
            **ModernTheme.get_entry_style()
        )
        server_entry.pack(side="right", fill="x", expand=True, padx=(ModernTheme.SPACING['medium'], 0))
        add_tooltip(server_entry, TOOLTIPS['exchange_config'])

        # Email field
        email_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        email_frame.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(0, ModernTheme.SPACING['medium']))

        email_label = ctk.CTkLabel(email_frame, text="Adres e-mail:", **ModernTheme.get_label_style('body'))
        email_label.pack(side="left", anchor="w")

        email_entry = ctk.CTkEntry(
            email_frame,
            textvariable=self.email_var,
            placeholder_text="np. uzytkownik@firma.pl",
            **ModernTheme.get_entry_style()
        )
        email_entry.pack(side="right", fill="x", expand=True, padx=(ModernTheme.SPACING['medium'], 0))

        # Username field
        username_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        username_frame.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(0, ModernTheme.SPACING['small']))

        username_label = ctk.CTkLabel(username_frame, text="Login użytkownika:", **ModernTheme.get_label_style('body'))
        username_label.pack(side="left", anchor="w")

        username_entry = ctk.CTkEntry(
            username_frame,
            textvariable=self.username_var,
            **ModernTheme.get_entry_style()
        )
        username_entry.pack(side="right", fill="x", expand=True, padx=(ModernTheme.SPACING['medium'], 0))

        # Password field
        password_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        password_frame.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(0, ModernTheme.SPACING['small']))

        password_label = ctk.CTkLabel(password_frame, text="Hasło:", **ModernTheme.get_label_style('body'))
        password_label.pack(side="left", anchor="w")

        password_entry = ctk.CTkEntry(
            password_frame,
            textvariable=self.password_var,
            show="*",
            **ModernTheme.get_entry_style()
        )
        password_entry.pack(side="right", fill="x", expand=True, padx=(ModernTheme.SPACING['medium'], 0))

        # Domain field
        domain_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        domain_frame.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(0, ModernTheme.SPACING['medium']))

        domain_label = ctk.CTkLabel(domain_frame, text="Domena (opcjonalnie):", **ModernTheme.get_label_style('body'))
        domain_label.pack(side="left", anchor="w")

        domain_entry = ctk.CTkEntry(
            domain_frame,
            textvariable=self.domain_var,
            **ModernTheme.get_entry_style()
        )
        domain_entry.pack(side="right", fill="x", expand=True, padx=(ModernTheme.SPACING['medium'], 0))

        # Actions section
        actions_frame = ctk.CTkFrame(self, **ModernTheme.get_frame_style('card'))
        actions_frame.pack(fill="x", pady=(0, ModernTheme.SPACING['medium']))
        
        actions_title = ctk.CTkLabel(
            actions_frame,
            text="🔧 Operacje",
            **ModernTheme.get_label_style('subheading')
        )
        actions_title.pack(pady=(ModernTheme.SPACING['medium'], ModernTheme.SPACING['small']), anchor="w", padx=ModernTheme.SPACING['medium'])

        # Buttons and status
        button_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=ModernTheme.SPACING['medium'], pady=(0, ModernTheme.SPACING['small']))
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Zapisz ustawienia",
            command=self.save_config,
            **ModernTheme.get_button_style('success')
        )
        save_btn.pack(side="left", padx=(0, ModernTheme.SPACING['small']))
        
        self.test_button = ctk.CTkButton(
            button_frame,
            text="Testuj połączenie",
            command=self.toggle_test_connection,
            **ModernTheme.get_button_style('primary')
        )
        self.test_button.pack(side="left")
        
        # Status
        self.status_label = ctk.CTkLabel(
            actions_frame,
            text="Gotowy",
            **ModernTheme.get_label_style('success')
        )
        self.status_label.pack(pady=(0, ModernTheme.SPACING['medium']), anchor="w", padx=ModernTheme.SPACING['medium'])

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
        self.status_label.configure(text="Anulowanie...", text_color=ModernTheme.COLORS['warning'])
        self.test_button.configure(text="Testuj połączenie")
    
    def start_test_connection(self):
        """Start the threaded connection test"""
        # Reset cancellation flag
        self.testing_cancelled = False
        
        # Update UI
        self.test_button.configure(text="Anuluj test")
        self.status_label.configure(text="Testowanie połączenia...", text_color=ModernTheme.COLORS['warning'])

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
                        self.status_label.configure(text="Test połączenia udany", text_color=ModernTheme.COLORS['success'])
                        self.test_button.configure(text="Testuj połączenie")
                        
                    elif result['type'] == 'test_cancelled':
                        self.status_label.configure(text="Test anulowany", text_color=ModernTheme.COLORS['warning'])
                        self.test_button.configure(text="Testuj połączenie")
                        
                    elif result['type'] == 'test_error':
                        error_msg = result['error']
                        messagebox.showerror("Błąd połączenia", error_msg)
                        self.status_label.configure(text="Błąd połączenia", text_color=ModernTheme.COLORS['error'])
                        self.test_button.configure(text="Testuj połączenie")
                        
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
