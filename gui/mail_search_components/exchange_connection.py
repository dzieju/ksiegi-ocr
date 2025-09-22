"""
Exchange email connection manager for mail search functionality
"""
import json
from tkinter import messagebox
from exchangelib import Credentials, Account, Configuration, DELEGATE

CONFIG_FILE = "exchange_config.json"


class ExchangeConnection:
    """Manages Exchange server connection and authentication"""
    
    def __init__(self):
        self.account = None
    
    def load_exchange_config(self):
        """Load Exchange configuration from config file"""
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config
        except FileNotFoundError:
            messagebox.showerror("Błąd konfiguracji", "Brak konfiguracji poczty. Skonfiguruj połączenie w zakładce 'Konfiguracja poczty'.")
            return None
        except Exception as e:
            messagebox.showerror("Błąd konfiguracji", f"Błąd odczytu konfiguracji: {str(e)}")
            return None
    
    def get_account(self):
        """Get Exchange account connection"""
        config = self.load_exchange_config()
        if not config:
            return None
            
        try:
            creds = Credentials(
                username=config.get("username", ""),
                password=config.get("password", "")
            )
            account_config = Configuration(
                server=config.get("server", ""),
                credentials=creds
            )
            account = Account(
                primary_smtp_address=config.get("email", ""),
                config=account_config,
                autodiscover=False,
                access_type=DELEGATE
            )
            self.account = account
            return account
        except Exception as e:
            messagebox.showerror("Błąd połączenia", f"Nie można połączyć z serwerem poczty: {str(e)}")
            return None
    
    def get_folder_by_path(self, account, folder_path):
        """Get folder by path like 'Skrzynka odbiorcza/Kompensaty Quadra'"""
        try:
            if not folder_path or folder_path.lower() in ["skrzynka odbiorcza", "inbox"]:
                return account.inbox
                
            # Split path and navigate to folder
            path_parts = folder_path.split('/')
            current_folder = account.inbox
            
            for part in path_parts:
                part = part.strip()
                if part.lower() in ["skrzynka odbiorcza", "inbox"]:
                    continue
                    
                # Search for subfolder
                found = False
                for child in current_folder.children:
                    if child.name.lower() == part.lower():
                        current_folder = child
                        found = True
                        break
                
                if not found:
                    messagebox.showwarning("Błąd folderu", f"Nie znaleziono folderu: {part}")
                    return account.inbox
                    
            return current_folder
        except Exception as e:
            messagebox.showerror("Błąd folderu", f"Błąd dostępu do folderu: {str(e)}")
            return account.inbox