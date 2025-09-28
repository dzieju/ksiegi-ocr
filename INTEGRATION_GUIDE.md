# Integration Guide for mail_accounts.py

This document shows how existing components can be updated to use the new `mail_accounts.py` module for persistent multi-account configuration.

## Overview

The `mail_accounts.py` module provides a centralized, GUI-independent way to manage mail account configurations. It replaces the scattered account management logic in various components with a single, well-tested API.

## Key Benefits

- **Centralized Configuration**: Single source of truth for account data
- **Reusable API**: Can be used from GUI, CLI, and automated scripts  
- **Robust Validation**: Comprehensive validation for all account types
- **Error Handling**: Graceful handling of configuration errors
- **Legacy Support**: Automatic migration from old configurations
- **Thread Safe**: No shared state issues between components

## Basic Usage

### Simple Operations

```python
from mail_accounts import MailAccountManager

# Create manager instance
manager = MailAccountManager()

# Add different account types
exchange_account = {
    "name": "Company Exchange",
    "type": "exchange", 
    "email": "user@company.com",
    "username": "user@company.com",
    "password": "password",
    "exchange_server": "exchange.company.com"
}
manager.add_account(exchange_account)

# Get main account
main_account = manager.get_main_account()

# Save configuration
manager.save_config()
```

### Convenience Functions

```python
from mail_accounts import get_mail_account_manager, load_mail_accounts, get_main_mail_account

# Quick access to shared manager
manager = get_mail_account_manager()

# Load all accounts
accounts = load_mail_accounts()

# Get main account directly  
main = get_main_mail_account()
```

## Integration Examples

### 1. Updating MailConfigWidget

The existing `MailConfigWidget` can be simplified by delegating account management to `MailAccountManager`:

```python
# OLD: Direct account management in widget
class MailConfigWidget(ttk.Frame):
    def __init__(self, parent):
        self.accounts = []
        self.main_account_index = 0
        self.load_config()  # Custom JSON loading logic
    
    def save_config(self):
        # Custom JSON saving logic
        config = {"accounts": self.accounts, "main_account_index": self.main_account_index}
        with open("mail_config.json", "w") as f:
            json.dump(config, f)

# NEW: Using MailAccountManager
class MailConfigWidget(ttk.Frame):
    def __init__(self, parent):
        from mail_accounts import MailAccountManager
        self.account_manager = MailAccountManager()
        self.refresh_account_list()
    
    def save_config(self):
        return self.account_manager.save_config()
    
    def add_account(self):
        index = self.account_manager.add_account()
        self.refresh_account_list()
        return index
    
    def remove_account(self, index):
        success = self.account_manager.remove_account(index)
        if success:
            self.refresh_account_list()
        return success
```

### 2. Updating MailConnection

The existing `MailConnection` can use the centralized configuration:

```python
# OLD: Direct config loading in connection class
class MailConnection:
    def load_mail_config(self):
        try:
            with open("mail_config.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback to legacy config...
            pass

# NEW: Using MailAccountManager
class MailConnection:
    def __init__(self):
        from mail_accounts import MailAccountManager
        self.account_manager = MailAccountManager()
        
    def load_mail_config(self):
        # MailAccountManager handles loading, legacy migration, error handling
        return {
            "accounts": self.account_manager.get_all_accounts(),
            "main_account_index": self.account_manager.main_account_index
        }
    
    def get_main_account(self):
        account_config = self.account_manager.get_main_account()
        if not account_config:
            return None
        return self._get_account_connection(account_config)
```

### 3. Command Line Interface

Create CLI tools for account management:

```python
#!/usr/bin/env python3
"""Command line tool for managing mail accounts"""

import sys
from mail_accounts import MailAccountManager

def main():
    manager = MailAccountManager()
    
    if len(sys.argv) < 2:
        print("Usage: mail_accounts.py [list|add|remove|main] [options]")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        accounts = manager.get_all_accounts()
        for i, account in enumerate(accounts):
            main_indicator = " (MAIN)" if i == manager.main_account_index else ""
            print(f"[{i}] {account['name']} ({account['type']}) - {account['email']}{main_indicator}")
    
    elif command == "add":
        # Interactive account creation
        name = input("Account name: ")
        email = input("Email: ")
        # ... collect other fields
        
        account_data = {"name": name, "email": email, "username": email, "password": password}
        index = manager.add_account(account_data) 
        manager.save_config()
        print(f"Added account at index {index}")
    
    elif command == "main":
        if len(sys.argv) > 2:
            index = int(sys.argv[2])
            if manager.set_main_account(index):
                manager.save_config()
                print(f"Set account {index} as main")
            else:
                print("Invalid account index")
        else:
            main = manager.get_main_account()
            if main:
                print(f"Main account: {main['name']} - {main['email']}")
            else:
                print("No main account configured")

if __name__ == "__main__":
    main()
```

## Migration Strategy

### Phase 1: Parallel Integration
- Keep existing code working
- Add `MailAccountManager` usage alongside existing logic
- Validate that both approaches produce same results

### Phase 2: Gradual Replacement  
- Replace account management methods one by one
- Update tests to use new API
- Remove redundant configuration loading code

### Phase 3: Cleanup
- Remove old account management code
- Simplify components that no longer need to handle configuration
- Update documentation

## Configuration Compatibility

The new module maintains 100% backward compatibility:

```json
{
  "accounts": [
    {
      "name": "Exchange Account",
      "type": "exchange",
      "email": "user@company.com",
      "username": "user@company.com", 
      "password": "password",
      "auth_method": "password",
      "exchange_server": "exchange.company.com",
      "domain": "company.com",
      "imap_server": "",
      "imap_port": 993,
      "imap_ssl": true,
      "smtp_server": "",
      "smtp_port": 587,
      "smtp_ssl": true,
      "pop3_server": "",
      "pop3_port": 995,
      "pop3_ssl": true,
      "smtp_server_pop3": "",
      "smtp_port_pop3": 587,
      "smtp_ssl_pop3": true
    }
  ],
  "main_account_index": 0
}
```

## Testing Integration

When updating components, maintain existing tests and add new ones:

```python
def test_widget_uses_account_manager(self):
    """Test that widget properly uses MailAccountManager"""
    widget = MailConfigWidget(parent)
    
    # Verify manager is initialized
    self.assertIsNotNone(widget.account_manager)
    
    # Test account operations work through manager
    initial_count = widget.account_manager.get_account_count()
    widget.add_account()
    self.assertEqual(widget.account_manager.get_account_count(), initial_count + 1)
```

## Error Handling

The module provides robust error handling that components can rely on:

```python
# Operations return success/failure status
success = manager.add_account(invalid_data)
if not success:
    # Handle error - manager already logged details
    show_error_message("Failed to add account")

# Configuration loading always succeeds (falls back to empty config)
manager = MailAccountManager()  # Never throws for missing config

# Validation prevents invalid data
try:
    manager.add_account({"name": "", "email": "invalid"})  # Raises ValueError
except ValueError as e:
    show_error_message(f"Invalid account data: {e}")
```

## Summary

The `mail_accounts.py` module provides a robust foundation for mail account management that can simplify existing components while improving reliability and maintainability. The integration can be done gradually without breaking existing functionality.