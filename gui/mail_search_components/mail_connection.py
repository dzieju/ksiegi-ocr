"""
Multi-account mail connection manager supporting both Exchange and IMAP/SMTP
"""
import json
import imaplib
import poplib
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
        self.pop3_connection = None
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
                            "auth_method": "password",
                            "exchange_server": legacy_config.get("server", ""),
                            "domain": legacy_config.get("domain", ""),
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
        # Close any existing connections before creating new ones
        self.close_connections()
        
        self.current_account_config = account_config
        account_type = account_config.get("type", "exchange")
        account_name = account_config.get("name", "Unknown Account")
        account_email = account_config.get("email", "Unknown Email")
        
        log(f"[MAIL CONNECTION] Connecting to account: '{account_name}' ({account_email})")
        log(f"[MAIL CONNECTION] Account type: {account_type}")
        
        # Log account configuration details (without sensitive data)
        if account_type == "exchange":
            server = account_config.get("exchange_server", "")
            domain = account_config.get("domain", "")
            log(f"[MAIL CONNECTION] Exchange server: {server}, domain: {domain}")
        elif account_type == "imap_smtp":
            imap_server = account_config.get("imap_server", "")
            smtp_server = account_config.get("smtp_server", "")
            log(f"[MAIL CONNECTION] IMAP server: {imap_server}, SMTP server: {smtp_server}")
        elif account_type == "pop3_smtp":
            pop3_server = account_config.get("pop3_server", "")
            smtp_server = account_config.get("smtp_server_pop3", "")
            log(f"[MAIL CONNECTION] POP3 server: {pop3_server}, SMTP server: {smtp_server}")
        
        try:
            if account_type == "exchange":
                return self._get_exchange_connection(account_config)
            elif account_type == "imap_smtp":
                return self._get_imap_connection(account_config)
            elif account_type == "pop3_smtp":
                return self._get_pop3_connection(account_config)
            else:
                log(f"[MAIL CONNECTION] WARNING: Unknown account type '{account_type}', defaulting to IMAP")
                # Default to IMAP for backward compatibility
                return self._get_imap_connection(account_config)
        except Exception as e:
            log(f"[MAIL CONNECTION] Connection failed for account '{account_name}' ({account_type}): {str(e)}")
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
    
    def _get_pop3_connection(self, account_config):
        """Get POP3 connection"""
        if account_config.get("pop3_ssl", True):
            pop3 = poplib.POP3_SSL(
                account_config.get("pop3_server", ""),
                account_config.get("pop3_port", 995)
            )
        else:
            pop3 = poplib.POP3(
                account_config.get("pop3_server", ""),
                account_config.get("pop3_port", 995)
            )
        
        pop3.user(account_config.get("username", ""))
        pop3.pass_(account_config.get("password", ""))
        self.pop3_connection = pop3
        return pop3
    
    def get_folder_by_path(self, account, folder_path):
        """Get folder by path - works for Exchange, IMAP, and POP3"""
        if not self.current_account_config:
            log("[MAIL CONNECTION] ERROR: No account configuration available for get_folder_by_path")
            return None
        
        account_type = self.current_account_config.get("type", "unknown")
        log(f"[MAIL CONNECTION] Getting folder by path for account type: {account_type}, path: {folder_path}")
        
        if account_type == "exchange":
            return self._get_exchange_folder_by_path(account, folder_path)
        elif account_type == "pop3_smtp":
            return self._get_pop3_folder_by_path(account, folder_path)
        elif account_type == "imap_smtp":
            return self._get_imap_folder_by_path(account, folder_path)
        else:
            log(f"[MAIL CONNECTION] WARNING: Unknown account type '{account_type}', defaulting to IMAP folder behavior")
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
    
    def _get_pop3_folder_by_path(self, pop3, folder_path):
        """Get POP3 folder by path - POP3 only supports inbox"""
        # POP3 only supports the main mailbox (inbox)
        # All folder paths are treated as the main mailbox
        return "INBOX"
    
    def get_folder_with_subfolders(self, account, folder_path, excluded_folders=None):
        """Get folder and all its subfolders recursively"""
        if not self.current_account_config:
            log("[MAIL CONNECTION] ERROR: No account configuration available for get_folder_with_subfolders")
            return []
        
        account_type = self.current_account_config.get("type", "unknown")
        log(f"[MAIL CONNECTION] Getting folder with subfolders for account type: {account_type}, path: {folder_path}")
        
        if account_type == "exchange":
            return self._get_exchange_folder_with_subfolders(account, folder_path, excluded_folders)
        elif account_type == "pop3_smtp":
            log("[MAIL CONNECTION] POP3 only supports single mailbox")
            # For POP3, this is simplified as POP3 only has one mailbox
            return ["INBOX"]
        elif account_type == "imap_smtp":
            log("[MAIL CONNECTION] IMAP simplified folder handling")
            # For IMAP, this is simplified as most IMAP operations work on single folders
            folder = self.get_folder_by_path(account, folder_path)
            return [folder] if folder else []
        else:
            log(f"[MAIL CONNECTION] WARNING: Unknown account type '{account_type}', defaulting to IMAP behavior")
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
    
    def _validate_account_config_for_folder_discovery(self, account_type):
        """Validate that account configuration is complete for folder discovery"""
        if not self.current_account_config:
            return False
        
        config = self.current_account_config
        
        # Basic validation for all account types
        required_basic = ["email", "username", "password"]
        for field in required_basic:
            if not config.get(field):
                log(f"[MAIL CONNECTION] Missing required field '{field}' for account type {account_type}")
                return False
        
        # Type-specific validation
        if account_type == "exchange":
            required_exchange = ["exchange_server", "domain"]
            for field in required_exchange:
                if not config.get(field):
                    log(f"[MAIL CONNECTION] Missing Exchange field '{field}'")
                    return False
        elif account_type == "imap_smtp":
            required_imap = ["imap_server", "smtp_server"]
            for field in required_imap:
                if not config.get(field):
                    log(f"[MAIL CONNECTION] Missing IMAP/SMTP field '{field}'")
                    return False
        elif account_type == "pop3_smtp":
            required_pop3 = ["pop3_server", "smtp_server_pop3"]
            for field in required_pop3:
                if not config.get(field):
                    log(f"[MAIL CONNECTION] Missing POP3/SMTP field '{field}'")
                    return False
        
        log(f"[MAIL CONNECTION] Account configuration validation passed for type: {account_type}")
        return True

    def get_available_folders_for_exclusion(self, account, folder_path):
        """Get list of available folders that can be excluded from search"""
        # Enhanced validation and logging
        if not self.current_account_config:
            log("[MAIL CONNECTION] ERROR: No account configuration available for folder discovery")
            return []
        
        account_type = self.current_account_config.get("type", "unknown")
        account_name = self.current_account_config.get("name", "Unknown Account")
        
        log(f"[MAIL CONNECTION] Getting available folders for account: '{account_name}' (type: {account_type})")
        log(f"[MAIL CONNECTION] Folder path: {folder_path}")
        
        # Validate account configuration before proceeding
        if not self._validate_account_config_for_folder_discovery(account_type):
            log(f"[MAIL CONNECTION] ERROR: Invalid or incomplete configuration for account type: {account_type}")
            return []
        
        if account_type == "exchange":
            log("[MAIL CONNECTION] Using Exchange folder detection")
            return self._get_exchange_available_folders(account, folder_path)
        elif account_type == "pop3_smtp":
            log("[MAIL CONNECTION] Using POP3 folder detection")
            # For POP3, only INBOX is available
            return ["INBOX"]
        elif account_type == "imap_smtp":
            log("[MAIL CONNECTION] Using IMAP folder detection")
            # For IMAP, return a simplified list
            return ["INBOX", "SENT", "DRAFTS", "SPAM"]
        else:
            log(f"[MAIL CONNECTION] WARNING: Unknown account type '{account_type}', defaulting to IMAP folder detection")
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
        log("[MAIL CONNECTION] Closing all connections")
        
        if self.imap_connection:
            try:
                self.imap_connection.logout()
                log("[MAIL CONNECTION] IMAP connection closed")
            except:
                pass
            self.imap_connection = None
        
        if self.pop3_connection:
            try:
                self.pop3_connection.quit()
                log("[MAIL CONNECTION] POP3 connection closed")
            except:
                pass
            self.pop3_connection = None
        
        self.account = None
        if self.current_account_config:
            account_name = self.current_account_config.get("name", "Unknown")
            log(f"[MAIL CONNECTION] Cleared account configuration for: {account_name}")
        self.current_account_config = None
    
    def get_current_account_info(self):
        """Get information about the currently configured account (for debugging)"""
        if not self.current_account_config:
            return "No account configured"
        
        account_type = self.current_account_config.get("type", "unknown")
        account_name = self.current_account_config.get("name", "Unknown")
        account_email = self.current_account_config.get("email", "Unknown")
        
        return f"Account: '{account_name}' ({account_email}) - Type: {account_type}"