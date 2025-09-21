"""
Search Criteria model for managing search parameters and configurations.
Handles saving, loading, and managing search criteria for the application.
"""

import json
import os
from datetime import datetime, date
from typing import Dict, Any, List, Optional


class SearchCriteria:
    """Model for managing search criteria parameters."""
    
    def __init__(self):
        self.text_query = ""
        self.date_from = None
        self.date_to = None
        self.category = ""
        self.amount_min = None
        self.amount_max = None
        self.include_attachments = True
        self.case_sensitive = False
        self.whole_words_only = False
        self.search_in_subject = True
        self.search_in_body = True
        self.search_in_attachments = True
        self.exclude_folders = set()
        self.include_folders = set()
        self.file_extensions = set()
        self.custom_filters = {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert search criteria to dictionary format for saving."""
        return {
            'text_query': self.text_query,
            'date_from': self.date_from.isoformat() if self.date_from else None,
            'date_to': self.date_to.isoformat() if self.date_to else None,
            'category': self.category,
            'amount_min': self.amount_min,
            'amount_max': self.amount_max,
            'include_attachments': self.include_attachments,
            'case_sensitive': self.case_sensitive,
            'whole_words_only': self.whole_words_only,
            'search_in_subject': self.search_in_subject,
            'search_in_body': self.search_in_body,
            'search_in_attachments': self.search_in_attachments,
            'exclude_folders': list(self.exclude_folders),
            'include_folders': list(self.include_folders),
            'file_extensions': list(self.file_extensions),
            'custom_filters': self.custom_filters
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load search criteria from dictionary format."""
        self.text_query = data.get('text_query', '')
        
        # Handle date parsing
        date_from_str = data.get('date_from')
        if date_from_str:
            try:
                self.date_from = datetime.fromisoformat(date_from_str).date()
            except (ValueError, TypeError):
                self.date_from = None
                
        date_to_str = data.get('date_to')
        if date_to_str:
            try:
                self.date_to = datetime.fromisoformat(date_to_str).date()
            except (ValueError, TypeError):
                self.date_to = None
        
        self.category = data.get('category', '')
        self.amount_min = data.get('amount_min')
        self.amount_max = data.get('amount_max')
        self.include_attachments = data.get('include_attachments', True)
        self.case_sensitive = data.get('case_sensitive', False)
        self.whole_words_only = data.get('whole_words_only', False)
        self.search_in_subject = data.get('search_in_subject', True)
        self.search_in_body = data.get('search_in_body', True)
        self.search_in_attachments = data.get('search_in_attachments', True)
        self.exclude_folders = set(data.get('exclude_folders', []))
        self.include_folders = set(data.get('include_folders', []))
        self.file_extensions = set(data.get('file_extensions', []))
        self.custom_filters = data.get('custom_filters', {})
    
    def save_to_file(self, filepath: str) -> bool:
        """Save search criteria to a JSON file."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving search criteria: {e}")
            return False
    
    def load_from_file(self, filepath: str) -> bool:
        """Load search criteria from a JSON file."""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.from_dict(data)
                return True
        except Exception as e:
            print(f"Error loading search criteria: {e}")
        return False
    
    def reset(self) -> None:
        """Reset all search criteria to default values."""
        self.__init__()
    
    def is_empty(self) -> bool:
        """Check if search criteria is empty (no search parameters set)."""
        return (
            not self.text_query.strip() and
            not self.date_from and
            not self.date_to and
            not self.category.strip() and
            self.amount_min is None and
            self.amount_max is None and
            not self.exclude_folders and
            not self.include_folders and
            not self.file_extensions and
            not self.custom_filters
        )
    
    def validate(self) -> List[str]:
        """Validate search criteria and return list of validation errors."""
        errors = []
        
        if self.date_from and self.date_to and self.date_from > self.date_to:
            errors.append("Data 'od' nie może być późniejsza niż data 'do'")
        
        if self.amount_min is not None and self.amount_max is not None:
            if self.amount_min > self.amount_max:
                errors.append("Minimalna kwota nie może być większa niż maksymalna")
        
        if self.amount_min is not None and self.amount_min < 0:
            errors.append("Minimalna kwota nie może być ujemna")
            
        if self.amount_max is not None and self.amount_max < 0:
            errors.append("Maksymalna kwota nie może być ujemna")
        
        return errors


class SearchCriteriaManager:
    """Manager for handling multiple saved search criteria."""
    
    def __init__(self, base_dir: str = "search_criteria"):
        self.base_dir = base_dir
        self.ensure_directory()
    
    def ensure_directory(self) -> None:
        """Ensure the search criteria directory exists."""
        os.makedirs(self.base_dir, exist_ok=True)
    
    def list_saved_criteria(self) -> List[str]:
        """List all saved search criteria files."""
        try:
            files = []
            for filename in os.listdir(self.base_dir):
                if filename.endswith('.json'):
                    files.append(filename[:-5])  # Remove .json extension
            return sorted(files)
        except OSError:
            return []
    
    def save_criteria(self, name: str, criteria: SearchCriteria) -> bool:
        """Save search criteria with a given name."""
        if not name.strip():
            return False
        
        # Sanitize filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_name:
            return False
            
        filepath = os.path.join(self.base_dir, f"{safe_name}.json")
        return criteria.save_to_file(filepath)
    
    def load_criteria(self, name: str) -> Optional[SearchCriteria]:
        """Load search criteria by name."""
        filepath = os.path.join(self.base_dir, f"{name}.json")
        criteria = SearchCriteria()
        if criteria.load_from_file(filepath):
            return criteria
        return None
    
    def delete_criteria(self, name: str) -> bool:
        """Delete saved search criteria by name."""
        try:
            filepath = os.path.join(self.base_dir, f"{name}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except OSError:
            pass
        return False
    
    def export_criteria(self, name: str, export_path: str) -> bool:
        """Export search criteria to a specified path."""
        criteria = self.load_criteria(name)
        if criteria:
            return criteria.save_to_file(export_path)
        return False
    
    def import_criteria(self, import_path: str, name: str) -> bool:
        """Import search criteria from a file."""
        criteria = SearchCriteria()
        if criteria.load_from_file(import_path):
            return self.save_criteria(name, criteria)
        return False