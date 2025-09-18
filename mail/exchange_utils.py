"""
Exchange connection and mail/folder handling utilities.
"""
import json
import os
from exchangelib import Credentials, Account, Configuration, DELEGATE

CONFIG_FILE = "exchange_config.json"
FOLDER_NAMES = ["inbox", "sent", "drafts", "junk", "deleted_items", "archive"]


class ExchangeConnection:
    """Manages Exchange server connection and folder operations."""
    
    def __init__(self):
        self.account = None
    
    def connect(self):
        """Establish connection to Exchange server."""
        if not os.path.exists(CONFIG_FILE):
            raise FileNotFoundError("Nie znaleziono pliku exchange_config.json.")
        
        with open(CONFIG_FILE, "r") as f:
            cfg = json.load(f)

        creds = Credentials(username=cfg["username"], password=cfg["password"])
        config = Configuration(server=cfg["server"], credentials=creds)
        self.account = Account(primary_smtp_address=cfg["email"], config=config, 
                             autodiscover=False, access_type=DELEGATE)
        return self.account
    
    def get_folder_path(self, folder):
        """Get full path of a folder."""
        names = []
        while folder and hasattr(folder, "name") and folder.name:
            names.append(folder.name)
            folder = folder.parent
        return "/".join(reversed(names))
    
    def get_user_folders(self, root_folder, prefix=""):
        """
        Recursively build list of user folder names (paths like 'Odebrane/Faktury').
        """
        folders = []
        display_name = f"{prefix}{root_folder.name}"
        folders.append(display_name)
        # children may be empty, need to check
        try:
            for child in root_folder.children:
                folders.extend(self.get_user_folders(child, prefix=display_name + "/"))
        except Exception:
            pass
        return folders
    
    def load_all_folders(self):
        """Load all available folders from Exchange."""
        if not self.account:
            self.connect()
        
        user_folders = []
        for folder_name in FOLDER_NAMES:
            folder = getattr(self.account, folder_name, None)
            if folder is not None:
                print(f"Znaleziono root folder: {folder.name}")
                user_folders.extend(self.get_user_folders(folder))
        
        return user_folders
    
    def find_folder_by_display_name(self, display_name):
        """
        Find exchangelib folder based on text path, e.g. 'Odebrane/Faktury'
        """
        if not self.account:
            self.connect()
            
        try:
            path_parts = display_name.split("/")
            folder = None
            root_map = {
                "Odebrane": getattr(self.account, "inbox", None),
                "Sent Items": getattr(self.account, "sent", None),
                "Wersje robocze": getattr(self.account, "drafts", None),
                "Archiwum": getattr(self.account, "archive", None),
                "Wiadomości-śmieci": getattr(self.account, "junk", None),
                "Kosz": getattr(self.account, "deleted_items", None),
            }
            first = path_parts[0]
            folder = root_map.get(first)
            if not folder:
                print(f"Nie znaleziono root folderu dla: {first}")
                return None
            for part in path_parts[1:]:
                folder = next((child for child in folder.children if child.name == part), None)
                if folder is None:
                    print(f"Nie znaleziono podfolderu: {part}")
                    return None
            return folder
        except Exception as e:
            print(f"Błąd znajdowania folderu: {display_name}, wyjątek: {e}")
            return None