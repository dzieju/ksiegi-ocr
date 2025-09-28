"""
Multi-account mail connection manager supporting both Exchange and IMAP/SMTP
"""
import json
import imaplib
import email
from exchangelib import Credentials, Account, Configuration, DELEGATE
from tools.logger import log

# Handle optional tkinter import
try:
    from tkinter import messagebox
    HAVE_TKINTER = True
except ImportError:
    HAVE_TKINTER = False
    # Create dummy messagebox for environments without tkinter
    class DummyMessagebox:
        @staticmethod
        def showerror(title, message):
            print(f"ERROR [{title}]: {message}")
        
        @staticmethod
        def showinfo(title, message):
            print(f"INFO [{title}]: {message}")
        
        @staticmethod
        def showwarning(title, message):
            print(f"WARNING [{title}]: {message}")
    
    messagebox = DummyMessagebox()

# New multi-account config file
CONFIG_FILE = "mail_config.json"
# Legacy Exchange config file for backward compatibility
LEGACY_CONFIG_FILE = "exchange_config.json"


class MailConnection:
    """Manages mail server connections for both Exchange and IMAP/SMTP"""
    
    def __init__(self):
        self.account = None
        self.imap_connection = None
        self.current_account_config = None
    
    def load_mail_config(self):
        """Load mail configuration from config file with fallback to legacy"""
        try:
            # Try new format first
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config
        except FileNotFoundError:
            # Fallback to legacy Exchange config
            try:
                with open(LEGACY_CONFIG_FILE, "r") as f:
                    legacy_config = json.load(f)
                    # Convert to new format
                    return {
                        "accounts": [{
                            "name": f"Legacy Exchange ({legacy_config.get('email', 'Account')})",
                            "type": "exchange",
                            "email": legacy_config.get("email", ""),
                            "username": legacy_config.get("username", ""),
                            "password": legacy_config.get("password", ""),
                            "exchange_server": legacy_config.get("server", ""),
                            "domain": legacy_config.get("domain", ""),
                            "imap_server": "",
                            "imap_port": 993,
                            "imap_ssl": True,
                            "smtp_server": "",
                            "smtp_port": 587,
                            "smtp_ssl": True
                        }],
                        "main_account_index": 0
                    }
            except FileNotFoundError:
                messagebox.showerror("Błąd konfiguracji", "Brak konfiguracji poczty. Skonfiguruj połączenie w zakładce 'Konfiguracja poczty'.")
                return None
        except Exception as e:
            messagebox.showerror("Błąd konfiguracji", f"Błąd odczytu konfiguracji: {str(e)}")
            return None
    
    def get_main_account(self):
        """Get main account connection"""
        config = self.load_mail_config()
        if not config or not config.get("accounts"):
            return None
        
        main_index = config.get("main_account_index", 0)
        accounts = config.get("accounts", [])
        
        if main_index >= len(accounts):
            main_index = 0
        
        account_config = accounts[main_index]
        return self._get_account_connection(account_config)
    
    def get_account_by_index(self, index):
        """Get account connection by index"""
        config = self.load_mail_config()
        if not config or not config.get("accounts"):
            return None
        
        accounts = config.get("accounts", [])
        if index >= len(accounts):
            return None
        
        account_config = accounts[index]
        return self._get_account_connection(account_config)
    
    def _get_account_connection(self, account_config):
        """Get connection for specific account configuration"""
        self.current_account_config = account_config
        account_type = account_config.get("type", "exchange")
        
        try:
            if account_type == "exchange":
                return self._get_exchange_connection(account_config)
            else:
                return self._get_imap_connection(account_config)
        except Exception as e:
            log(f"Błąd połączenia z kontem {account_config.get('name', 'Unknown')}: {str(e)}")
            messagebox.showerror("Błąd połączenia", f"Nie można połączyć z kontem poczty: {str(e)}")
            return None
    
    def _get_exchange_connection(self, account_config):
        """Get Exchange connection"""
        creds = Credentials(
            username=account_config.get("username", ""),
            password=account_config.get("password", "")
        )
        config = Configuration(
            server=account_config.get("exchange_server", ""),
            credentials=creds
        )
        account = Account(
            primary_smtp_address=account_config.get("email", ""),
            config=config,
            autodiscover=False,
            access_type=DELEGATE
        )
        self.account = account
        return account
    
    def _get_imap_connection(self, account_config):
        """Get IMAP connection"""
        if account_config.get("imap_ssl", True):
            imap = imaplib.IMAP4_SSL(
                account_config.get("imap_server", ""),
                account_config.get("imap_port", 993)
            )
        else:
            imap = imaplib.IMAP4(
                account_config.get("imap_server", ""),
                account_config.get("imap_port", 993)
            )
        
        imap.login(
            account_config.get("username", ""),
            account_config.get("password", "")
        )
        self.imap_connection = imap
        return imap
    
    def get_folder_by_path(self, account, folder_path):
        """Get folder by path - works for both Exchange and IMAP"""
        if self.current_account_config and self.current_account_config.get("type") == "exchange":
            return self._get_exchange_folder_by_path(account, folder_path)
        else:
            return self._get_imap_folder_by_path(account, folder_path)
    
    def _get_exchange_folder_by_path(self, account, folder_path):
        """Get Exchange folder by path"""
        try:
            path_parts = folder_path.split("/")
            current_folder = account.inbox
            
            if path_parts[0].lower() in ["inbox", "skrzynka odbiorcza"]:
                path_parts = path_parts[1:]  # Skip inbox part
            
            for part in path_parts:
                if part:
                    found = False
                    for child in current_folder.children:
                        if child.name.lower() == part.lower():
                            current_folder = child
                            found = True
                            break
                    if not found:
                        log(f"Nie znaleziono folderu: {part} w ścieżce {folder_path}")
                        return account.inbox
            
            return current_folder
        except Exception as e:
            messagebox.showerror("Błąd folderu", f"Błąd dostępu do folderu: {str(e)}")
            return account.inbox
    
    def _get_imap_folder_by_path(self, imap, folder_path):
        """Get IMAP folder by path"""
        try:
            # For IMAP, we need to translate folder names
            # This is a simplified implementation
            if folder_path.lower() in ["inbox", "skrzynka odbiorcza"]:
                folder_name = "INBOX"
            else:
                # Try to use the folder path as-is, or map common names
                folder_mapping = {
                    "skrzynka odbiorcza": "INBOX",
                    "sent": "SENT",
                    "wysłane": "SENT",
                    "drafts": "DRAFTS",
                    "robocze": "DRAFTS",
                    "spam": "SPAM",
                    "junk": "SPAM"
                }
                folder_name = folder_mapping.get(folder_path.lower(), folder_path)
            
            # Select the folder
            status, messages = imap.select(folder_name)
            if status == 'OK':
                return folder_name
            else:
                # Fallback to INBOX
                imap.select("INBOX")
                return "INBOX"
                
        except Exception as e:
            log(f"Błąd dostępu do folderu IMAP {folder_path}: {str(e)}")
            imap.select("INBOX")
            return "INBOX"
    
    def get_folder_with_subfolders(self, account, folder_path, excluded_folders=None):
        """Get folder and all its subfolders recursively"""
        if self.current_account_config and self.current_account_config.get("type") == "exchange":
            return self._get_exchange_folder_with_subfolders(account, folder_path, excluded_folders)
        else:
            # For IMAP, this is simplified as most IMAP operations work on single folders
            folder = self.get_folder_by_path(account, folder_path)
            return [folder] if folder else []
    
    def _get_exchange_folder_with_subfolders(self, account, folder_path, excluded_folders=None):
        """Get Exchange folder and all its subfolders recursively"""
        try:
            folder = self.get_folder_by_path(account, folder_path)
            if not folder:
                return []
            
            all_folders = [folder]
            excluded_names = set(excluded_folders or [])
            
            subfolders = self._get_all_subfolders_recursive(folder, excluded_names)
            all_folders.extend(subfolders)
            
            log(f"Znaleziono łącznie {len(all_folders)} folderów do przeszukania")
            return all_folders
            
        except Exception as e:
            log(f"Błąd pobierania folderów: {str(e)}")
            messagebox.showerror("Błąd folderów", f"Błąd pobierania listy folderów: {str(e)}")
            return []
    
    def _get_all_subfolders_recursive(self, folder, excluded_folder_names=None):
        """Recursively get all subfolders of a given folder"""
        if excluded_folder_names is None:
            excluded_folder_names = set()
        
        subfolders = []
        try:
            for child in folder.children:
                if child.name not in excluded_folder_names:
                    subfolders.append(child)
                    # Recursively get subfolders
                    nested_subfolders = self._get_all_subfolders_recursive(child, excluded_folder_names)
                    subfolders.extend(nested_subfolders)
                else:
                    log(f"Wykluczono folder: {child.name}")
        except Exception as e:
            log(f"Błąd pobierania podfolderów dla {folder.name}: {str(e)}")
        
        return subfolders
    
    def get_available_folders_for_exclusion(self, account, folder_path):
        """Get list of available folders that can be excluded from search"""
        if self.current_account_config and self.current_account_config.get("type") == "exchange":
            return self._get_exchange_available_folders(account, folder_path)
        else:
            # For IMAP, return a simplified list
            return ["INBOX", "SENT", "DRAFTS", "SPAM"]
    
    def _get_exchange_available_folders(self, account, folder_path):
        """Get available Exchange folders for exclusion"""
        try:
            folder = self.get_folder_by_path(account, folder_path)
            if not folder:
                return []
            
            folder_names = []
            
            def collect_folder_names(f, prefix=""):
                for child in f.children:
                    full_name = f"{prefix}{child.name}" if prefix else child.name
                    folder_names.append(full_name)
                    collect_folder_names(child, f"{full_name}/")
            
            collect_folder_names(folder)
            
            log(f"Znalezione foldery do wykluczenia ({len(folder_names)}):")
            for i, name in enumerate(folder_names, 1):
                log(f"  {i}. {name}")
            
            return folder_names
            
        except Exception as e:
            log(f"Błąd pobierania listy folderów do wykluczenia: {str(e)}")
            return []
    
    def close_connections(self):
        """Close all active connections"""
        if self.imap_connection:
            try:
                self.imap_connection.logout()
            except:
                pass
            self.imap_connection = None
        
        self.account = None
        self.current_account_config = None