#!/usr/bin/env python3
"""
Test for the fix of 'list object has no attribute filter' error
Tests that _get_exchange_messages can handle both list and single folder
"""
import unittest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock exchangelib before importing the search engine
sys.modules['exchangelib'] = MagicMock()

from gui.mail_search_components.search_engine import EmailSearchEngine


class TestSearchEngineFolderHandling(unittest.TestCase):
    """Test cases for search engine folder handling"""
    
    def setUp(self):
        """Set up test environment"""
        # Create mock callbacks
        self.progress_callback = Mock()
        self.result_callback = Mock()
        
        # Create search engine instance
        self.search_engine = EmailSearchEngine(
            progress_callback=self.progress_callback,
            result_callback=self.result_callback
        )
        
        # Mock the Q object from exchangelib
        self.mock_q = Mock()
        self.mock_q.return_value = Mock()
    
    def test_single_folder_handling(self):
        """Test that _get_exchange_messages works with a single folder object"""
        # Create mock folder object
        mock_folder = Mock()
        mock_messages = [Mock(), Mock()]
        
        # Mock the filter chain
        mock_filter_result = Mock()
        mock_filter_result.order_by.return_value.__getitem__ = Mock(return_value=mock_messages)
        mock_folder.filter.return_value = mock_filter_result
        
        # Test criteria
        criteria = {
            'selected_period': 'wszystkie',
            'subject_search': '',
            'sender': '',
            'body_search': '',
            'unread_only': False,
            'attachments_required': False,
            'no_attachments_only': False
        }
        
        # Call the method with single folder
        result = self.search_engine._get_exchange_messages(mock_folder, criteria, per_page=10)
        
        # Verify folder.filter was called
        self.assertTrue(mock_folder.filter.called)
        
        # Verify we got results
        self.assertEqual(len(result), len(mock_messages))
    
    def test_folder_list_handling(self):
        """Test that _get_exchange_messages works with a list of folder objects"""
        # Create mock folder objects
        mock_folder1 = Mock()
        mock_folder1.name = "Folder1"
        mock_folder2 = Mock()
        mock_folder2.name = "Folder2"
        
        mock_messages1 = [Mock(), Mock()]
        mock_messages2 = [Mock()]
        
        # Mock the filter chain for folder1
        mock_filter_result1 = Mock()
        mock_filter_result1.order_by.return_value.__getitem__ = Mock(return_value=mock_messages1)
        mock_folder1.filter.return_value = mock_filter_result1
        
        # Mock the filter chain for folder2
        mock_filter_result2 = Mock()
        mock_filter_result2.order_by.return_value.__getitem__ = Mock(return_value=mock_messages2)
        mock_folder2.filter.return_value = mock_filter_result2
        
        # Test criteria
        criteria = {
            'selected_period': 'wszystkie',
            'subject_search': '',
            'sender': '',
            'body_search': '',
            'unread_only': False,
            'attachments_required': False,
            'no_attachments_only': False
        }
        
        # Call the method with list of folders
        folder_list = [mock_folder1, mock_folder2]
        result = self.search_engine._get_exchange_messages(folder_list, criteria, per_page=10)
        
        # Verify both folders were searched
        self.assertTrue(mock_folder1.filter.called)
        self.assertTrue(mock_folder2.filter.called)
        
        # Verify we got results from both folders (3 total messages)
        self.assertEqual(len(result), 3)
    
    def test_empty_folder_list_handling(self):
        """Test that _get_exchange_messages handles empty folder list gracefully"""
        # Test criteria
        criteria = {
            'selected_period': 'wszystkie',
            'subject_search': '',
            'sender': '',
            'body_search': '',
            'unread_only': False,
            'attachments_required': False,
            'no_attachments_only': False
        }
        
        # Call the method with empty list
        folder_list = []
        result = self.search_engine._get_exchange_messages(folder_list, criteria, per_page=10)
        
        # Verify we got empty results
        self.assertEqual(len(result), 0)
    
    def test_folder_list_with_error_continues(self):
        """Test that if one folder fails, the others are still searched"""
        # Create mock folder objects
        mock_folder1 = Mock()
        mock_folder1.name = "FailingFolder"
        mock_folder1.filter.side_effect = Exception("Test error")
        
        mock_folder2 = Mock()
        mock_folder2.name = "WorkingFolder"
        mock_messages2 = [Mock()]
        
        # Mock the filter chain for folder2
        mock_filter_result2 = Mock()
        mock_filter_result2.order_by.return_value.__getitem__ = Mock(return_value=mock_messages2)
        mock_folder2.filter.return_value = mock_filter_result2
        
        # Test criteria
        criteria = {
            'selected_period': 'wszystkie',
            'subject_search': '',
            'sender': '',
            'body_search': '',
            'unread_only': False,
            'attachments_required': False,
            'no_attachments_only': False
        }
        
        # Call the method with list containing a failing folder
        folder_list = [mock_folder1, mock_folder2]
        result = self.search_engine._get_exchange_messages(folder_list, criteria, per_page=10)
        
        # Verify folder2 was still searched even though folder1 failed
        self.assertTrue(mock_folder2.filter.called)
        
        # Verify we got results from the working folder
        self.assertEqual(len(result), 1)
    
    def test_folder_with_search_criteria(self):
        """Test that search criteria are properly applied to filter query"""
        # Create mock folder object
        mock_folder = Mock()
        mock_messages = [Mock()]
        
        # Mock the filter chain
        mock_filter_result = Mock()
        mock_filter_result.order_by.return_value.__getitem__ = Mock(return_value=mock_messages)
        mock_folder.filter.return_value = mock_filter_result
        
        # Test criteria with various filters
        criteria = {
            'selected_period': 'wszystkie',
            'subject_search': 'test subject',
            'sender': 'test@example.com',
            'body_search': 'test body',
            'unread_only': True,
            'attachments_required': True,
            'no_attachments_only': False
        }
        
        # Call the method
        result = self.search_engine._get_exchange_messages(mock_folder, criteria, per_page=10)
        
        # Verify filter was called (the query would contain all criteria)
        self.assertTrue(mock_folder.filter.called)
        
        # Get the query object that was passed to filter
        call_args = mock_folder.filter.call_args
        query = call_args[0][0] if call_args[0] else None
        
        # We can't directly test the Q object contents easily, but we can verify
        # that filter was called which means the query was constructed
        self.assertIsNotNone(query)


if __name__ == "__main__":
    unittest.main()
