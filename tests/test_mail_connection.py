#!/usr/bin/env python3
"""
Regression tests for mail connection and folder detection functionality.
Tests the fix for the issue where folder detection always used Exchange logic.
"""
import unittest
import sys
import os
import json
import tempfile
import shutil

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.mail_search_components.mail_connection import MailConnection


class TestMailConnectionFolderDetection(unittest.TestCase):
    """Test cases for mail connection folder detection logic"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for test config files
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Store original config file paths
        self.original_config_file = None
        if os.path.exists(os.path.join(self.original_cwd, "mail_config.json")):
            self.original_config_file = os.path.join(self.original_cwd, "mail_config.json")
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def create_test_config(self, account_type, account_name="Test Account"):
        """Create a test configuration for the specified account type"""
        config = {
            "accounts": [{
                "name": account_name,
                "type": account_type,
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpass",
                "auth_method": "password",
                "exchange_server": "exchange.example.com" if account_type == "exchange" else "",
                "domain": "example.com" if account_type == "exchange" else "",
                "imap_server": "imap.example.com" if account_type == "imap_smtp" else "",
                "imap_port": 993,
                "imap_ssl": True,
                "smtp_server": "smtp.example.com" if account_type in ["imap_smtp", "pop3_smtp"] else "",
                "smtp_port": 587,
                "smtp_ssl": True,
                "pop3_server": "pop3.example.com" if account_type == "pop3_smtp" else "",
                "pop3_port": 995,
                "pop3_ssl": True,
                "smtp_server_pop3": "smtp.example.com" if account_type == "pop3_smtp" else "",
                "smtp_port_pop3": 587,
                "smtp_ssl_pop3": True
            }],
            "main_account_index": 0
        }
        
        with open("mail_config.json", "w") as f:
            json.dump(config, f, indent=2)
            
        return config
    
    def test_exchange_folder_detection(self):
        """Test that Exchange account type uses Exchange folder detection"""
        # Create Exchange config
        self.create_test_config("exchange")
        
        # Create connection and test folder detection
        conn = MailConnection()
        
        # Load config to set current_account_config
        try:
            account = conn.get_main_account()  # Will fail due to fake server, but sets config
        except:
            pass  # Expected to fail with fake server
        
        # Verify account type is set correctly
        self.assertIsNotNone(conn.current_account_config)
        self.assertEqual(conn.current_account_config.get("type"), "exchange")
        
        # Test folder detection (will return empty list due to connection failure, but uses right logic)
        folders = conn.get_available_folders_for_exclusion(None, "INBOX")
        # For Exchange with connection failure, should return empty list
        self.assertEqual(folders, [])
    
    def test_imap_folder_detection(self):
        """Test that IMAP/SMTP account type uses IMAP folder detection"""
        # Create IMAP config
        self.create_test_config("imap_smtp")
        
        # Create connection and test folder detection
        conn = MailConnection()
        
        # Load config to set current_account_config
        try:
            account = conn.get_main_account()  # Will fail due to fake server, but sets config
        except:
            pass  # Expected to fail with fake server
        
        # Verify account type is set correctly
        self.assertIsNotNone(conn.current_account_config)
        self.assertEqual(conn.current_account_config.get("type"), "imap_smtp")
        
        # Test folder detection
        folders = conn.get_available_folders_for_exclusion(None, "INBOX")
        # For IMAP, should return standard IMAP folders
        expected_folders = ["INBOX", "SENT", "DRAFTS", "SPAM"]
        self.assertEqual(folders, expected_folders)
    
    def test_pop3_folder_detection(self):
        """Test that POP3/SMTP account type uses POP3 folder detection"""
        # Create POP3 config
        self.create_test_config("pop3_smtp")
        
        # Create connection and test folder detection
        conn = MailConnection()
        
        # Load config to set current_account_config
        try:
            account = conn.get_main_account()  # Will fail due to fake server, but sets config
        except:
            pass  # Expected to fail with fake server
        
        # Verify account type is set correctly
        self.assertIsNotNone(conn.current_account_config)
        self.assertEqual(conn.current_account_config.get("type"), "pop3_smtp")
        
        # Test folder detection
        folders = conn.get_available_folders_for_exclusion(None, "INBOX")
        # For POP3, should return only INBOX
        expected_folders = ["INBOX"]
        self.assertEqual(folders, expected_folders)
    
    def test_account_type_switching(self):
        """Test that switching account types updates folder detection correctly"""
        # Start with Exchange
        self.create_test_config("exchange", "Exchange Account")
        conn = MailConnection()
        
        try:
            conn.get_main_account()
        except:
            pass
        
        self.assertEqual(conn.current_account_config.get("type"), "exchange")
        folders = conn.get_available_folders_for_exclusion(None, "INBOX")
        self.assertEqual(folders, [])  # Exchange with connection failure
        
        # Switch to IMAP
        self.create_test_config("imap_smtp", "IMAP Account")
        
        try:
            conn.get_main_account()  # This should reload config and update current_account_config
        except:
            pass
        
        self.assertEqual(conn.current_account_config.get("type"), "imap_smtp")
        folders = conn.get_available_folders_for_exclusion(None, "INBOX")
        self.assertEqual(folders, ["INBOX", "SENT", "DRAFTS", "SPAM"])
        
        # Switch to POP3
        self.create_test_config("pop3_smtp", "POP3 Account")
        
        try:
            conn.get_main_account()  # This should reload config and update current_account_config
        except:
            pass
        
        self.assertEqual(conn.current_account_config.get("type"), "pop3_smtp")
        folders = conn.get_available_folders_for_exclusion(None, "INBOX")
        self.assertEqual(folders, ["INBOX"])
    
    def test_connection_cleanup(self):
        """Test that old connections are properly cleaned up when switching account types"""
        conn = MailConnection()
        
        # Start with Exchange
        self.create_test_config("exchange")
        try:
            conn.get_main_account()
        except:
            pass
        
        # Verify Exchange connection was attempted (even if it failed)
        self.assertEqual(conn.current_account_config.get("type"), "exchange")
        
        # Switch to IMAP - old connections should be cleaned up
        self.create_test_config("imap_smtp")
        try:
            conn.get_main_account()
        except:
            pass
        
        # Verify IMAP connection was attempted and old state was cleared
        self.assertEqual(conn.current_account_config.get("type"), "imap_smtp")
        # The account should be None due to connection failure
        self.assertIsNone(conn.account)
        
        # Switch to POP3 - old connections should be cleaned up
        self.create_test_config("pop3_smtp")
        try:
            conn.get_main_account()
        except:
            pass
        
        # Verify POP3 connection was attempted and old state was cleared
        self.assertEqual(conn.current_account_config.get("type"), "pop3_smtp")
        # The connections should be None due to connection failure
        self.assertIsNone(conn.imap_connection)
        self.assertIsNone(conn.pop3_connection)
    
    def test_edge_cases_and_validation(self):
        """Test edge cases with incomplete configurations and validation"""
        conn = MailConnection()
        
        # Test with no account configuration
        folders = conn.get_available_folders_for_exclusion(None, "INBOX")
        self.assertEqual(folders, [])  # Should return empty list
        
        # Test with incomplete Exchange config (missing exchange_server)
        incomplete_config = {
            "accounts": [{
                "name": "Incomplete Exchange",
                "type": "exchange",
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpass",
                "auth_method": "password",
                "exchange_server": "",  # Missing server
                "domain": "example.com",
                "imap_server": "",
                "imap_port": 993,
                "imap_ssl": True
            }],
            "main_account_index": 0
        }
        
        with open("mail_config.json", "w") as f:
            json.dump(incomplete_config, f, indent=2)
        
        try:
            conn.get_main_account()
        except:
            pass
        
        # Should still have account config set but validation should fail
        self.assertIsNotNone(conn.current_account_config)
        self.assertEqual(conn.current_account_config.get("type"), "exchange")
        
        # Folder discovery should return empty due to validation failure
        folders = conn.get_available_folders_for_exclusion(None, "INBOX")
        self.assertEqual(folders, [])
        
        # Test with incomplete IMAP config (missing imap_server)
        incomplete_imap_config = {
            "accounts": [{
                "name": "Incomplete IMAP",
                "type": "imap_smtp",
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpass",
                "auth_method": "password",
                "imap_server": "",  # Missing server
                "smtp_server": "smtp.example.com"
            }],
            "main_account_index": 0
        }
        
        with open("mail_config.json", "w") as f:
            json.dump(incomplete_imap_config, f, indent=2)
        
        try:
            conn.get_main_account()
        except:
            pass
        
        # Folder discovery should return empty due to validation failure
        folders = conn.get_available_folders_for_exclusion(None, "INBOX")
        self.assertEqual(folders, [])
        
    def test_account_info_debugging(self):
        """Test account info debugging functionality"""
        conn = MailConnection()
        
        # Test with no account
        info = conn.get_current_account_info()
        self.assertEqual(info, "No account configured")
        
        # Test with configured account
        self.create_test_config("imap_smtp", "Debug Test Account")
        try:
            conn.get_main_account()
        except:
            pass
        
        info = conn.get_current_account_info()
        self.assertIn("Debug Test Account", info)
        self.assertIn("imap_smtp", info)
        self.assertIn("test@example.com", info)


if __name__ == "__main__":
    unittest.main()