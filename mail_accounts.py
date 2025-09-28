"""
Persistent multi-account configuration for mail settings.

Supports IMAP/SMTP, POP3/SMTP, and Exchange accounts with JSON-based storage.
Provides centralized account management including loading, saving, adding, editing, and removing accounts.
"""

import json
import os
from typing import Dict, List, Optional, Union
from tools.logger import log


class MailAccountManager:
    """
    Manages persistent multi-account mail configuration with JSON-based storage.
    
    Supports:
    - Exchange accounts
    - IMAP/SMTP accounts  
    - POP3/SMTP accounts
    - Loading and saving configuration
    - Adding, editing, and removing accounts
    - Account validation
    - Legacy configuration migration
    """
    
    # Configuration file paths
    CONFIG_FILE = "mail_config.json"
    LEGACY_CONFIG_FILE = "exchange_config.json"
    
    # Default account template for new accounts
    DEFAULT_ACCOUNT_TEMPLATE = {
        "name": "",
        "type": "exchange",  # exchange, imap_smtp, pop3_smtp
        "email": "",
        "username": "",
        "password": "",
        "auth_method": "password",  # password, oauth2, app_password
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
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the mail account manager.
        
        Args:
            config_file: Optional custom config file path (defaults to mail_config.json)
        """
        self.config_file = config_file or self.CONFIG_FILE
        self.accounts: List[Dict] = []
        self.main_account_index: int = 0
        
        # Load existing configuration on initialization
        self.load_config()
    
    def load_config(self) -> bool:
        """
        Load mail configuration from file with fallback to legacy format.
        
        Returns:
            bool: True if configuration was loaded successfully, False otherwise
        """
        try:
            # Try new format first
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                self.accounts = config.get("accounts", [])
                self.main_account_index = config.get("main_account_index", 0)
                
                # Validate main_account_index
                if self.main_account_index >= len(self.accounts):
                    self.main_account_index = 0
                
                log(f"Loaded {len(self.accounts)} accounts from {self.config_file}")
                return True
            
            # Try to migrate from legacy Exchange config
            elif os.path.exists(self.LEGACY_CONFIG_FILE):
                return self._migrate_from_legacy()
            
            else:
                # No config files found, start with empty configuration
                log("No configuration file found, starting with empty configuration")
                self.accounts = []
                self.main_account_index = 0
                return True
                
        except Exception as e:
            log(f"ERROR: Error loading mail configuration: {str(e)}")
            # Reset to empty configuration on error
            self.accounts = []
            self.main_account_index = 0
            return False
    
    def save_config(self) -> bool:
        """
        Save current account configuration to JSON file.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not self.accounts:
            log(f"WARNING: Attempting to save empty account configuration")
        
        config = {
            "accounts": self.accounts,
            "main_account_index": self.main_account_index
        }
        
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            log(f"Saved {len(self.accounts)} accounts to {self.config_file}")
            return True
            
        except Exception as e:
            log(f"ERROR: Error saving mail configuration: {str(e)}")
            return False
    
    def add_account(self, account_data: Optional[Dict] = None) -> int:
        """
        Add a new mail account.
        
        Args:
            account_data: Optional account data dictionary. If None, creates default account.
        
        Returns:
            int: Index of the newly added account
        """
        if account_data is None:
            # Create default account with minimal required fields
            account = self.DEFAULT_ACCOUNT_TEMPLATE.copy()
            account["name"] = f"Nowe konto {len(self.accounts) + 1}"
            account["email"] = "user@example.com"  # Placeholder email for validation
            account["username"] = "user"  # Placeholder username for validation
        else:
            # Use provided data, but ensure all required fields are present
            account = self.DEFAULT_ACCOUNT_TEMPLATE.copy()
            account.update(account_data)
        
        # Only validate if this is not a default empty account
        if account_data is not None and not self._validate_account(account):
            raise ValueError("Invalid account data provided")
        
        self.accounts.append(account)
        new_index = len(self.accounts) - 1
        
        log(f"Added new account: {account['name']} (index: {new_index})")
        return new_index
    
    def edit_account(self, index: int, account_data: Dict) -> bool:
        """
        Edit an existing account at the specified index.
        
        Args:
            index: Index of the account to edit
            account_data: Updated account data
        
        Returns:
            bool: True if edited successfully, False otherwise
        """
        if not self._is_valid_index(index):
            log(f"Invalid account index: {index}")
            return False
        
        # Merge with existing account data to preserve all fields
        updated_account = self.accounts[index].copy()
        updated_account.update(account_data)
        
        # Validate the updated account
        if not self._validate_account(updated_account):
            log(f"ERROR: Invalid account data for account at index {index}")
            return False
        
        old_name = self.accounts[index].get("name", "Unknown")
        self.accounts[index] = updated_account
        
        log(f"Updated account at index {index}: {old_name} -> {updated_account['name']}")
        return True
    
    def remove_account(self, index: int) -> bool:
        """
        Remove an account at the specified index.
        
        Args:
            index: Index of the account to remove
        
        Returns:
            bool: True if removed successfully, False otherwise
        """
        if not self._is_valid_index(index):
            log(f"ERROR: Invalid account index: {index}")
            return False
        
        if len(self.accounts) <= 1:
            log("ERROR: Cannot remove the last remaining account")
            return False
        
        account_name = self.accounts[index].get("name", "Unknown")
        
        # Adjust main account index if necessary
        if self.main_account_index == index:
            self.main_account_index = 0  # Set to first account
        elif self.main_account_index > index:
            self.main_account_index -= 1  # Shift down
        
        del self.accounts[index]
        
        log(f"Removed account: {account_name} (was at index {index})")
        return True
    
    def get_account(self, index: int) -> Optional[Dict]:
        """
        Get account data by index.
        
        Args:
            index: Index of the account to retrieve
        
        Returns:
            Dict: Account data if found, None otherwise
        """
        if self._is_valid_index(index):
            return self.accounts[index].copy()  # Return copy to prevent external modification
        return None
    
    def get_main_account(self) -> Optional[Dict]:
        """
        Get the main account configuration.
        
        Returns:
            Dict: Main account data if available, None otherwise
        """
        if self.accounts and 0 <= self.main_account_index < len(self.accounts):
            return self.accounts[self.main_account_index].copy()
        return None
    
    def get_all_accounts(self) -> List[Dict]:
        """
        Get all account configurations.
        
        Returns:
            List[Dict]: List of all account data (copies to prevent external modification)
        """
        return [account.copy() for account in self.accounts]
    
    def set_main_account(self, index: int) -> bool:
        """
        Set the main account by index.
        
        Args:
            index: Index of the account to set as main
        
        Returns:
            bool: True if set successfully, False otherwise
        """
        if not self._is_valid_index(index):
            log(f"ERROR: Invalid account index: {index}")
            return False
        
        old_main = self.main_account_index
        self.main_account_index = index
        
        old_name = self.accounts[old_main].get("name", "Unknown") if self._is_valid_index(old_main) else "None"
        new_name = self.accounts[index].get("name", "Unknown")
        
        log(f"Changed main account from {old_name} to {new_name}")
        return True
    
    def get_account_count(self) -> int:
        """
        Get the total number of accounts.
        
        Returns:
            int: Number of configured accounts
        """
        return len(self.accounts)
    
    def get_accounts_by_type(self, account_type: str) -> List[Dict]:
        """
        Get all accounts of a specific type.
        
        Args:
            account_type: Type of accounts to retrieve (exchange, imap_smtp, pop3_smtp)
        
        Returns:
            List[Dict]: List of accounts matching the specified type
        """
        return [account.copy() for account in self.accounts if account.get("type") == account_type]
    
    def validate_account_credentials(self, account_data: Dict) -> bool:
        """
        Validate that account has required credentials based on its type.
        
        Args:
            account_data: Account data to validate
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        account_type = account_data.get("type", "")
        email = account_data.get("email", "").strip()
        username = account_data.get("username", "").strip()
        password = account_data.get("password", "").strip()
        
        # Basic validation - email and credentials required
        if not email or not username:
            return False
        
        # Type-specific validation
        if account_type == "exchange":
            return bool(password and account_data.get("exchange_server", "").strip())
        
        elif account_type == "imap_smtp":
            return bool(password and 
                       account_data.get("imap_server", "").strip() and
                       account_data.get("smtp_server", "").strip())
        
        elif account_type == "pop3_smtp":
            return bool(password and 
                       account_data.get("pop3_server", "").strip() and
                       account_data.get("smtp_server_pop3", "").strip())
        
        return False
    
    def _migrate_from_legacy(self) -> bool:
        """
        Migrate from legacy Exchange configuration format.
        
        Returns:
            bool: True if migration was successful, False otherwise
        """
        try:
            with open(self.LEGACY_CONFIG_FILE, "r", encoding="utf-8") as f:
                legacy_config = json.load(f)
            
            # Create account from legacy config
            account = self.DEFAULT_ACCOUNT_TEMPLATE.copy()
            account.update({
                "name": f"Exchange ({legacy_config.get('email', 'Migrated Account')})",
                "type": "exchange",
                "email": legacy_config.get("email", ""),
                "username": legacy_config.get("username", ""),
                "password": legacy_config.get("password", ""),
                "exchange_server": legacy_config.get("server", ""),
                "domain": legacy_config.get("domain", "")
            })
            
            self.accounts = [account]
            self.main_account_index = 0
            
            log(f"Successfully migrated legacy Exchange configuration")
            
            # Save in new format
            if self.save_config():
                log("Migrated configuration saved in new format")
                return True
            
        except Exception as e:
            log(f"ERROR: Error migrating legacy configuration: {str(e)}")
        
        return False
    
    def _validate_account(self, account: Dict) -> bool:
        """
        Validate account data structure and required fields.
        
        Args:
            account: Account data to validate
        
        Returns:
            bool: True if account data is valid, False otherwise
        """
        # Check required fields
        required_fields = ["name", "type", "email"]
        for field in required_fields:
            if field not in account or not account[field].strip():
                log(f"ERROR: Account validation failed: missing or empty field '{field}'")
                return False
        
        # Validate account type
        valid_types = ["exchange", "imap_smtp", "pop3_smtp"]
        if account["type"] not in valid_types:
            log(f"ERROR: Account validation failed: invalid type '{account['type']}'")
            return False
        
        # Validate email format (basic check)
        email = account["email"].strip()
        if "@" not in email or "." not in email:
            log(f"ERROR: Account validation failed: invalid email format '{email}'")
            return False
        
        return True
    
    def _is_valid_index(self, index: int) -> bool:
        """
        Check if the given index is valid for the accounts list.
        
        Args:
            index: Index to validate
        
        Returns:
            bool: True if index is valid, False otherwise
        """
        return 0 <= index < len(self.accounts)


# Convenience functions for backward compatibility and easy integration
def get_mail_account_manager(config_file: Optional[str] = None) -> MailAccountManager:
    """
    Get a shared instance of MailAccountManager.
    
    Args:
        config_file: Optional custom config file path
    
    Returns:
        MailAccountManager: Configured account manager instance
    """
    return MailAccountManager(config_file)


def load_mail_accounts(config_file: Optional[str] = None) -> List[Dict]:
    """
    Load all mail accounts from configuration.
    
    Args:
        config_file: Optional custom config file path
    
    Returns:
        List[Dict]: List of all configured accounts
    """
    manager = get_mail_account_manager(config_file)
    return manager.get_all_accounts()


def get_main_mail_account(config_file: Optional[str] = None) -> Optional[Dict]:
    """
    Get the main mail account configuration.
    
    Args:
        config_file: Optional custom config file path
    
    Returns:
        Dict: Main account data if available, None otherwise
    """
    manager = get_mail_account_manager(config_file)
    return manager.get_main_account()