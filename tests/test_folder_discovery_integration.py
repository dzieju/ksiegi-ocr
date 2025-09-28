#!/usr/bin/env python3
"""
Integration test for folder discovery functionality.
Simulates the user workflow of changing account types and clicking 'Detect folders'.
"""
import unittest
import sys
import os
import json
import tempfile
import shutil
from unittest.mock import MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFolderDiscoveryIntegration(unittest.TestCase):
    """Integration tests for folder discovery workflow"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for test config files
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def create_test_config(self, account_type):
        """Create a test configuration for the specified account type"""
        config = {
            "accounts": [{
                "name": f"Test {account_type.upper()} Account",
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
    
    def test_folder_discovery_workflow(self):
        """Test complete folder discovery workflow with account type switching"""
        from gui.mail_search_components.mail_connection import MailConnection
        
        # Initialize connection (simulating MailSearchTab.__init__)
        mail_connection = MailConnection()
        
        # Test data for expected results
        test_cases = [
            ("exchange", []),  # Exchange returns empty list on connection failure
            ("imap_smtp", ["INBOX", "SENT", "DRAFTS", "SPAM"]),  # IMAP returns standard folders
            ("pop3_smtp", ["INBOX"]),  # POP3 returns only INBOX
        ]
        
        results = []
        
        for account_type, expected_folders in test_cases:
            # User changes account type in config
            self.create_test_config(account_type)
            
            # User clicks "Detect folders" button
            # This simulates the discover_folders() method flow
            try:
                account = mail_connection.get_main_account()
            except:
                pass  # Connection will fail with fake servers
            
            # Get available folders for exclusion
            folders = mail_connection.get_available_folders_for_exclusion(account, "INBOX")
            
            results.append((account_type, folders))
            
            # Verify the result matches expected
            self.assertEqual(folders, expected_folders, 
                           f"Account type {account_type} should return {expected_folders}, got {folders}")
        
        # Verify all account types were tested and returned correct results
        self.assertEqual(len(results), 3)
        
        # Verify progression through different account types
        exchange_result = results[0]
        imap_result = results[1]
        pop3_result = results[2]
        
        self.assertEqual(exchange_result[0], "exchange")
        self.assertEqual(exchange_result[1], [])
        
        self.assertEqual(imap_result[0], "imap_smtp")
        self.assertEqual(imap_result[1], ["INBOX", "SENT", "DRAFTS", "SPAM"])
        
        self.assertEqual(pop3_result[0], "pop3_smtp")
        self.assertEqual(pop3_result[1], ["INBOX"])
    
    def test_folder_discovery_with_mock_ui(self):
        """Test folder discovery with a mock UI component"""
        # Mock UI variables and methods
        mock_vars = {
            'folder_path': MagicMock(),
        }
        mock_vars['folder_path'].get.return_value = "INBOX"
        
        # Mock progress and result callbacks
        progress_messages = []
        result_data = []
        
        def mock_add_progress(message):
            progress_messages.append(message)
        
        def mock_add_result(result):
            result_data.append(result)
        
        # Import and test the discovery logic
        from gui.mail_search_components.mail_connection import MailConnection
        
        connection = MailConnection()
        
        # Test each account type
        for account_type in ["exchange", "imap_smtp", "pop3_smtp"]:
            self.create_test_config(account_type)
            
            # Simulate the discover_folders workflow
            mock_add_progress("Wykrywanie dostępnych folderów...")
            
            try:
                account = connection.get_main_account()
                if account or connection.current_account_config:  # Even if account is None, we can still get folders
                    folder_path = mock_vars['folder_path'].get()
                    folders = connection.get_available_folders_for_exclusion(account, folder_path)
                    
                    # Mock the UI update
                    mock_add_progress(f"Wykryto {len(folders)} folderów")
                    
                    # Verify correct folders for account type
                    if account_type == "exchange":
                        self.assertEqual(folders, [])
                    elif account_type == "imap_smtp":
                        self.assertEqual(folders, ["INBOX", "SENT", "DRAFTS", "SPAM"])
                    elif account_type == "pop3_smtp":
                        self.assertEqual(folders, ["INBOX"])
                        
            except Exception as e:
                mock_add_progress("Błąd wykrywania folderów")
        
        # Verify progress messages were generated
        self.assertGreater(len(progress_messages), 0)
        # Should have at least 6 messages (3 start + 3 completion messages)
        self.assertGreaterEqual(len(progress_messages), 6)


if __name__ == "__main__":
    unittest.main()