"""
Exchange email connection manager for mail search functionality
"""
import json
from tkinter import messagebox
from exchangelib import Credentials, Account, Configuration, DELEGATE
from tools.logger import log

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
    
    def get_folder_with_subfolders(self, account, folder_path, excluded_folders=None):
        """Get folder and all its subfolders recursively, excluding specified folders"""
        log(f"=== ODKRYWANIE FOLDERÓW ===")
        log(f"Szukanie folderu bazowego: '{folder_path}'")
        
        # Parse excluded folders
        excluded_folder_names = set()
        if excluded_folders:
            excluded_folder_names = {name.strip() for name in excluded_folders.split(',') if name.strip()}
            if excluded_folder_names:
                log(f"Foldery do wykluczenia: {list(excluded_folder_names)}")
        
        base_folder = self.get_folder_by_path(account, folder_path)
        if not base_folder:
            log(f"BŁĄD: Nie znaleziono folderu bazowego '{folder_path}'")
            return []
        
        log(f"Znaleziono folder bazowy: '{base_folder.name}'")
        folders = [base_folder]  # Include the base folder itself
        
        log("Rozpoczynanie rekursywnego wyszukiwania podfolderów...")
        subfolders = self._get_all_subfolders_recursive(base_folder, excluded_folder_names)
        folders.extend(subfolders)
        
        log(f"Odkrywanie folderów zakończone:")
        log(f"  - Folder bazowy: {base_folder.name}")
        log(f"  - Znalezione podfoldery: {len(subfolders)}")
        for i, subfolder in enumerate(subfolders, 1):
            log(f"    {i}. {subfolder.name}")
        log(f"  - Łącznie folderów do przeszukania: {len(folders)}")
        
        return folders
    
    def _get_all_subfolders_recursive(self, folder, excluded_folder_names=None):
        """Recursively get all subfolders of a given folder, excluding specified folders"""
        if excluded_folder_names is None:
            excluded_folder_names = set()
            
        all_subfolders = []
        try:
            log(f"Sprawdzanie podfolderów w: '{folder.name}'")
            children_count = 0
            excluded_count = 0
            
            for child in folder.children:
                children_count += 1
                
                # Check if this folder should be excluded
                if child.name in excluded_folder_names:
                    excluded_count += 1
                    log(f"  Pominięto wykluczony folder: '{child.name}'")
                    continue
                
                # Add the child folder
                all_subfolders.append(child)
                log(f"  Znaleziono podfolder: '{child.name}'")
                
                # Recursively get subfolders of this child
                sub_subfolders = self._get_all_subfolders_recursive(child, excluded_folder_names)
                all_subfolders.extend(sub_subfolders)
            
            if children_count == 0:
                log(f"  Folder '{folder.name}' nie ma podfolderów")
            else:
                log(f"  Folder '{folder.name}' ma {children_count} bezpośrednich podfolderów")
                if excluded_count > 0:
                    log(f"  Wykluczono {excluded_count} folderów z przeszukiwania")
                
        except Exception as e:
            # Some folders might not be accessible, continue with others
            log(f"BŁĄD dostępu do podfolderów '{folder.name}': {str(e)}")
            pass
        return all_subfolders
    
    def get_available_folders_for_exclusion(self, account, folder_path):
        """Get list of available folders that can be excluded from search"""
        log(f"=== ODKRYWANIE FOLDERÓW DO WYKLUCZENIA ===")
        log(f"Szukanie folderów w: '{folder_path}'")
        
        base_folder = self.get_folder_by_path(account, folder_path)
        if not base_folder:
            log(f"BŁĄD: Nie znaleziono folderu bazowego '{folder_path}'")
            return []
        
        log(f"Znaleziono folder bazowy: '{base_folder.name}'")
        
        # Get all subfolders without exclusions to show them as options
        all_subfolders = self._get_all_subfolders_recursive(base_folder, set())
        
        folder_names = [folder.name for folder in all_subfolders]
        folder_names.sort()  # Sort alphabetically for better UX
        
        log(f"Znalezione foldery do wykluczenia ({len(folder_names)}):")
        for i, name in enumerate(folder_names, 1):
            log(f"  {i}. {name}")
        
        return folder_names