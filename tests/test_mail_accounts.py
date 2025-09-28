#!/usr/bin/env python3
"""
Tests for mail_accounts.py - persistent multi-account configuration management.
"""

import unittest
import sys
import os
import json
import tempfile
import shutil
from unittest.mock import patch, mock_open

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mail_accounts import MailAccountManager, get_mail_account_manager, load_mail_accounts, get_main_mail_account


class TestMailAccountManager(unittest.TestCase):
    """Test cases for MailAccountManager class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for test config files
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Test config file paths
        self.config_file = "test_mail_config.json"
        self.legacy_config_file = "exchange_config.json"
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def create_test_config(self, accounts=None, main_index=0):
        """Create a test configuration file"""
        if accounts is None:
            accounts = [
                {
                    "name": "Test Exchange",
                    "type": "exchange",
                    "email": "test@exchange.com",
                    "username": "testuser",
                    "password": "testpass",
                    "auth_method": "password",
                    "exchange_server": "exchange.test.com",
                    "domain": "test.com",
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
            ]
        
        config = {
            "accounts": accounts,
            "main_account_index": main_index
        }
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        
        return config
    
    def create_legacy_config(self):
        """Create a legacy Exchange configuration file"""
        legacy_config = {
            "server": "legacy.exchange.com",
            "email": "legacy@test.com",
            "username": "legacyuser",
            "password": "legacypass",
            "domain": "test.com"
        }
        
        with open(self.legacy_config_file, "w", encoding="utf-8") as f:
            json.dump(legacy_config, f)
        
        return legacy_config
    
    def test_init_empty_config(self):
        """Test initialization with no config file"""
        manager = MailAccountManager(self.config_file)
        
        self.assertEqual(len(manager.accounts), 0)
        self.assertEqual(manager.main_account_index, 0)
        self.assertEqual(manager.config_file, self.config_file)
    
    def test_init_with_existing_config(self):
        """Test initialization with existing config file"""
        test_config = self.create_test_config()
        manager = MailAccountManager(self.config_file)
        
        self.assertEqual(len(manager.accounts), 1)
        self.assertEqual(manager.accounts[0]["name"], "Test Exchange")
        self.assertEqual(manager.main_account_index, 0)
    
    def test_load_config_success(self):
        """Test successful config loading"""
        test_config = self.create_test_config([
            {
                "name": "IMAP Account",
                "type": "imap_smtp",
                "email": "test@imap.com",
                "username": "imapuser",
                "password": "imappass",
                "auth_method": "password",
                "exchange_server": "",
                "domain": "",
                "imap_server": "imap.test.com",
                "imap_port": 993,
                "imap_ssl": True,
                "smtp_server": "smtp.test.com",
                "smtp_port": 587,
                "smtp_ssl": True,
                "pop3_server": "",
                "pop3_port": 995,
                "pop3_ssl": True,
                "smtp_server_pop3": "",
                "smtp_port_pop3": 587,
                "smtp_ssl_pop3": True
            }
        ])
        
        manager = MailAccountManager(self.config_file)
        result = manager.load_config()
        
        self.assertTrue(result)
        self.assertEqual(len(manager.accounts), 1)
        self.assertEqual(manager.accounts[0]["type"], "imap_smtp")
    
    def test_load_config_invalid_main_index(self):
        """Test config loading with invalid main account index"""
        test_config = self.create_test_config(main_index=5)  # Invalid index
        manager = MailAccountManager(self.config_file)
        
        self.assertEqual(manager.main_account_index, 0)  # Should be corrected to 0
    
    def test_save_config_success(self):
        """Test successful config saving"""
        manager = MailAccountManager(self.config_file)
        manager.add_account({
            "name": "Test Save Account",
            "type": "exchange",
            "email": "save@test.com",
            "username": "saveuser",
            "password": "savepass",
            "exchange_server": "save.exchange.com"
        })
        
        result = manager.save_config()
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.config_file))
        
        # Verify saved content
        with open(self.config_file, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        
        self.assertEqual(len(saved_config["accounts"]), 1)
        self.assertEqual(saved_config["accounts"][0]["name"], "Test Save Account")
    
    def test_add_account_default(self):
        """Test adding account with default data"""
        manager = MailAccountManager(self.config_file)
        
        index = manager.add_account()
        
        self.assertEqual(index, 0)
        self.assertEqual(len(manager.accounts), 1)
        self.assertEqual(manager.accounts[0]["name"], "Nowe konto 1")
        self.assertEqual(manager.accounts[0]["type"], "exchange")
    
    def test_add_account_custom_data(self):
        """Test adding account with custom data"""
        manager = MailAccountManager(self.config_file)
        
        custom_account = {
            "name": "Custom Account",
            "type": "imap_smtp",
            "email": "custom@test.com",
            "username": "customuser",
            "password": "custompass",
            "imap_server": "imap.custom.com",
            "smtp_server": "smtp.custom.com"
        }
        
        index = manager.add_account(custom_account)
        
        self.assertEqual(index, 0)
        self.assertEqual(len(manager.accounts), 1)
        self.assertEqual(manager.accounts[0]["name"], "Custom Account")
        self.assertEqual(manager.accounts[0]["type"], "imap_smtp")
        self.assertEqual(manager.accounts[0]["imap_server"], "imap.custom.com")
    
    def test_add_account_invalid_data(self):
        """Test adding account with invalid data"""
        manager = MailAccountManager(self.config_file)
        
        invalid_account = {
            "name": "",  # Empty name
            "type": "invalid_type",  # Invalid type
            "email": "invalid-email"  # Invalid email format
        }
        
        with self.assertRaises(ValueError):
            manager.add_account(invalid_account)
    
    def test_edit_account_success(self):
        """Test successful account editing"""
        manager = MailAccountManager(self.config_file)
        manager.add_account()
        
        updated_data = {
            "name": "Updated Account",
            "email": "updated@test.com"
        }
        
        result = manager.edit_account(0, updated_data)
        
        self.assertTrue(result)
        self.assertEqual(manager.accounts[0]["name"], "Updated Account")
        self.assertEqual(manager.accounts[0]["email"], "updated@test.com")
        # Other fields should remain unchanged
        self.assertEqual(manager.accounts[0]["type"], "exchange")
    
    def test_edit_account_invalid_index(self):
        """Test editing account with invalid index"""
        manager = MailAccountManager(self.config_file)
        
        result = manager.edit_account(5, {"name": "Test"})
        
        self.assertFalse(result)
    
    def test_edit_account_invalid_data(self):
        """Test editing account with invalid data"""
        manager = MailAccountManager(self.config_file)
        manager.add_account()
        
        invalid_data = {
            "email": "invalid-email"  # Invalid email format
        }
        
        result = manager.edit_account(0, invalid_data)
        
        self.assertFalse(result)
    
    def test_remove_account_success(self):
        """Test successful account removal"""
        manager = MailAccountManager(self.config_file)
        manager.add_account({"name": "Account 1", "email": "acc1@test.com", "username": "user1", "password": "pass1"})
        manager.add_account({"name": "Account 2", "email": "acc2@test.com", "username": "user2", "password": "pass2"})
        
        result = manager.remove_account(0)
        
        self.assertTrue(result)
        self.assertEqual(len(manager.accounts), 1)
        self.assertEqual(manager.accounts[0]["name"], "Account 2")
    
    def test_remove_account_adjust_main_index(self):
        """Test removing account adjusts main account index"""
        manager = MailAccountManager(self.config_file)
        manager.add_account({"name": "Account 1", "email": "acc1@test.com", "username": "user1", "password": "pass1"})
        manager.add_account({"name": "Account 2", "email": "acc2@test.com", "username": "user2", "password": "pass2"})
        manager.add_account({"name": "Account 3", "email": "acc3@test.com", "username": "user3", "password": "pass3"})
        
        manager.set_main_account(2)  # Set third account as main
        self.assertEqual(manager.main_account_index, 2)
        
        # Remove first account
        manager.remove_account(0)
        
        # Main index should be adjusted
        self.assertEqual(manager.main_account_index, 1)  # Was 2, now 1
    
    def test_remove_account_last_account(self):
        """Test removing last account should fail"""
        manager = MailAccountManager(self.config_file)
        manager.add_account()
        
        result = manager.remove_account(0)
        
        self.assertFalse(result)
        self.assertEqual(len(manager.accounts), 1)
    
    def test_remove_account_invalid_index(self):
        """Test removing account with invalid index"""
        manager = MailAccountManager(self.config_file)
        
        result = manager.remove_account(5)
        
        self.assertFalse(result)
    
    def test_get_account_success(self):
        """Test getting account by index"""
        manager = MailAccountManager(self.config_file)
        manager.add_account({"name": "Test Account", "email": "test@test.com", "username": "testuser", "password": "testpass"})
        
        account = manager.get_account(0)
        
        self.assertIsNotNone(account)
        self.assertEqual(account["name"], "Test Account")
        
        # Should return a copy, not the original
        account["name"] = "Modified"
        self.assertEqual(manager.accounts[0]["name"], "Test Account")
    
    def test_get_account_invalid_index(self):
        """Test getting account with invalid index"""
        manager = MailAccountManager(self.config_file)
        
        account = manager.get_account(5)
        
        self.assertIsNone(account)
    
    def test_get_main_account_success(self):
        """Test getting main account"""
        manager = MailAccountManager(self.config_file)
        manager.add_account({"name": "Main Account", "email": "main@test.com", "username": "mainuser", "password": "mainpass"})
        manager.add_account({"name": "Secondary Account", "email": "sec@test.com", "username": "secuser", "password": "secpass"})
        manager.set_main_account(1)
        
        main_account = manager.get_main_account()
        
        self.assertIsNotNone(main_account)
        self.assertEqual(main_account["name"], "Secondary Account")
    
    def test_get_main_account_no_accounts(self):
        """Test getting main account when no accounts exist"""
        manager = MailAccountManager(self.config_file)
        
        main_account = manager.get_main_account()
        
        self.assertIsNone(main_account)
    
    def test_get_all_accounts(self):
        """Test getting all accounts"""
        manager = MailAccountManager(self.config_file)
        manager.add_account({"name": "Account 1", "email": "acc1@test.com", "username": "user1", "password": "pass1"})
        manager.add_account({"name": "Account 2", "email": "acc2@test.com", "username": "user2", "password": "pass2"})
        
        all_accounts = manager.get_all_accounts()
        
        self.assertEqual(len(all_accounts), 2)
        self.assertEqual(all_accounts[0]["name"], "Account 1")
        self.assertEqual(all_accounts[1]["name"], "Account 2")
        
        # Should return copies, not originals
        all_accounts[0]["name"] = "Modified"
        self.assertEqual(manager.accounts[0]["name"], "Account 1")
    
    def test_set_main_account_success(self):
        """Test setting main account"""
        manager = MailAccountManager(self.config_file)
        manager.add_account({"name": "Account 1", "email": "acc1@test.com", "username": "user1", "password": "pass1"})
        manager.add_account({"name": "Account 2", "email": "acc2@test.com", "username": "user2", "password": "pass2"})
        
        result = manager.set_main_account(1)
        
        self.assertTrue(result)
        self.assertEqual(manager.main_account_index, 1)
    
    def test_set_main_account_invalid_index(self):
        """Test setting main account with invalid index"""
        manager = MailAccountManager(self.config_file)
        
        result = manager.set_main_account(5)
        
        self.assertFalse(result)
        self.assertEqual(manager.main_account_index, 0)
    
    def test_get_account_count(self):
        """Test getting account count"""
        manager = MailAccountManager(self.config_file)
        
        self.assertEqual(manager.get_account_count(), 0)
        
        manager.add_account()
        self.assertEqual(manager.get_account_count(), 1)
        
        manager.add_account()
        self.assertEqual(manager.get_account_count(), 2)
    
    def test_get_accounts_by_type(self):
        """Test getting accounts by type"""
        manager = MailAccountManager(self.config_file)
        manager.add_account({"name": "Exchange", "type": "exchange", "email": "ex@test.com", "username": "user1", "password": "pass1"})
        manager.add_account({"name": "IMAP", "type": "imap_smtp", "email": "imap@test.com", "username": "user2", "password": "pass2"})
        manager.add_account({"name": "POP3", "type": "pop3_smtp", "email": "pop3@test.com", "username": "user3", "password": "pass3"})
        manager.add_account({"name": "Another IMAP", "type": "imap_smtp", "email": "imap2@test.com", "username": "user4", "password": "pass4"})
        
        exchange_accounts = manager.get_accounts_by_type("exchange")
        imap_accounts = manager.get_accounts_by_type("imap_smtp")
        pop3_accounts = manager.get_accounts_by_type("pop3_smtp")
        
        self.assertEqual(len(exchange_accounts), 1)
        self.assertEqual(len(imap_accounts), 2)
        self.assertEqual(len(pop3_accounts), 1)
        
        self.assertEqual(exchange_accounts[0]["name"], "Exchange")
        self.assertEqual(imap_accounts[0]["name"], "IMAP")
        self.assertEqual(imap_accounts[1]["name"], "Another IMAP")
    
    def test_validate_account_credentials_exchange(self):
        """Test validating Exchange account credentials"""
        manager = MailAccountManager(self.config_file)
        
        valid_exchange = {
            "type": "exchange",
            "email": "test@exchange.com",
            "username": "testuser",
            "password": "testpass",
            "exchange_server": "exchange.test.com"
        }
        
        invalid_exchange = {
            "type": "exchange",
            "email": "test@exchange.com",
            "username": "testuser",
            "password": "testpass",
            "exchange_server": ""  # Missing server
        }
        
        self.assertTrue(manager.validate_account_credentials(valid_exchange))
        self.assertFalse(manager.validate_account_credentials(invalid_exchange))
    
    def test_validate_account_credentials_imap(self):
        """Test validating IMAP account credentials"""
        manager = MailAccountManager(self.config_file)
        
        valid_imap = {
            "type": "imap_smtp",
            "email": "test@imap.com",
            "username": "testuser",
            "password": "testpass",
            "imap_server": "imap.test.com",
            "smtp_server": "smtp.test.com"
        }
        
        invalid_imap = {
            "type": "imap_smtp",
            "email": "test@imap.com",
            "username": "testuser",
            "password": "testpass",
            "imap_server": "",  # Missing IMAP server
            "smtp_server": "smtp.test.com"
        }
        
        self.assertTrue(manager.validate_account_credentials(valid_imap))
        self.assertFalse(manager.validate_account_credentials(invalid_imap))
    
    def test_validate_account_credentials_pop3(self):
        """Test validating POP3 account credentials"""
        manager = MailAccountManager(self.config_file)
        
        valid_pop3 = {
            "type": "pop3_smtp",
            "email": "test@pop3.com",
            "username": "testuser",
            "password": "testpass",
            "pop3_server": "pop3.test.com",
            "smtp_server_pop3": "smtp.test.com"
        }
        
        invalid_pop3 = {
            "type": "pop3_smtp",
            "email": "test@pop3.com",
            "username": "testuser",
            "password": "testpass",
            "pop3_server": "pop3.test.com",
            "smtp_server_pop3": ""  # Missing SMTP server
        }
        
        self.assertTrue(manager.validate_account_credentials(valid_pop3))
        self.assertFalse(manager.validate_account_credentials(invalid_pop3))
    
    def test_migrate_from_legacy_success(self):
        """Test successful migration from legacy config"""
        self.create_legacy_config()
        
        manager = MailAccountManager(self.config_file)
        
        self.assertEqual(len(manager.accounts), 1)
        self.assertEqual(manager.accounts[0]["type"], "exchange")
        self.assertEqual(manager.accounts[0]["email"], "legacy@test.com")
        self.assertEqual(manager.accounts[0]["exchange_server"], "legacy.exchange.com")
        self.assertTrue(manager.accounts[0]["name"].startswith("Exchange ("))
    
    def test_migrate_from_legacy_saves_new_format(self):
        """Test that legacy migration saves in new format"""
        self.create_legacy_config()
        
        manager = MailAccountManager(self.config_file)
        
        # Config file should have been created
        self.assertTrue(os.path.exists(self.config_file))
        
        # Verify new format
        with open(self.config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        self.assertIn("accounts", config)
        self.assertIn("main_account_index", config)
        self.assertEqual(len(config["accounts"]), 1)
    
    @patch('mail_accounts.log')  # Mock the log function to prevent file I/O during test
    @patch('builtins.open', side_effect=IOError("File not found"))
    def test_load_config_file_error(self, mock_open, mock_log):
        """Test config loading with file I/O error falls back to empty config"""
        manager = MailAccountManager(self.config_file)
        result = manager.load_config()
        
        # Should return True because it falls back to empty configuration
        self.assertTrue(result)
        self.assertEqual(len(manager.accounts), 0)
    
    @patch('mail_accounts.log')  # Mock the log function to prevent file I/O during test  
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_save_config_file_error(self, mock_open, mock_log):
        """Test config saving with file I/O error"""
        manager = MailAccountManager(self.config_file)
        manager.add_account()
        
        result = manager.save_config()
        
        self.assertFalse(result)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        self.config_file = "test_mail_config.json"
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def test_get_mail_account_manager(self):
        """Test getting mail account manager instance"""
        manager = get_mail_account_manager(self.config_file)
        
        self.assertIsInstance(manager, MailAccountManager)
        self.assertEqual(manager.config_file, self.config_file)
    
    def test_load_mail_accounts(self):
        """Test loading mail accounts convenience function"""
        # Create test config
        config = {
            "accounts": [
                {"name": "Test 1", "type": "exchange", "email": "test1@test.com", "username": "user1", "password": "pass1"},
                {"name": "Test 2", "type": "imap_smtp", "email": "test2@test.com", "username": "user2", "password": "pass2"}
            ],
            "main_account_index": 0
        }
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f)
        
        accounts = load_mail_accounts(self.config_file)
        
        self.assertEqual(len(accounts), 2)
        self.assertEqual(accounts[0]["name"], "Test 1")
        self.assertEqual(accounts[1]["name"], "Test 2")
    
    def test_get_main_mail_account(self):
        """Test getting main mail account convenience function"""
        # Create test config
        config = {
            "accounts": [
                {"name": "Test 1", "type": "exchange", "email": "test1@test.com", "username": "user1", "password": "pass1"},
                {"name": "Test 2", "type": "imap_smtp", "email": "test2@test.com", "username": "user2", "password": "pass2"}
            ],
            "main_account_index": 1
        }
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f)
        
        main_account = get_main_mail_account(self.config_file)
        
        self.assertIsNotNone(main_account)
        self.assertEqual(main_account["name"], "Test 2")


if __name__ == "__main__":
    unittest.main()