"""
Application state management utilities for saving/loading settings.
"""
import json
import os

STATE_FILE = "invoice_search_state.json"


class StateManager:
    """Manages application state persistence."""
    
    def __init__(self, state_file=None):
        self.state_file = state_file or STATE_FILE
    
    def load_state(self):
        """Load application state from file."""
        print("Ładowanie poprzedniego stanu aplikacji...")
        if not os.path.exists(self.state_file):
            return self._get_default_state()
        
        try:
            with open(self.state_file, "r") as f:
                state = json.load(f)
                # Ensure all required keys exist with defaults
                default_state = self._get_default_state()
                for key, default_value in default_state.items():
                    if key not in state:
                        state[key] = default_value
                return state
        except Exception as e:
            print(f"Błąd ładowania stanu: {e}")
            return self._get_default_state()
    
    def save_state(self, state_data):
        """Save application state to file."""
        print("Zapisuję stan aplikacji...")
        try:
            with open(self.state_file, "w") as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Błąd zapisywania stanu: {e}")
            return False
    
    def _get_default_state(self):
        """Get default application state."""
        return {
            "last_folder": "Inbox",
            "last_nip": "",
            "date_from": "",
            "date_to": "",
            "target_folder": "Archiwum",
            "search_all_folders": False,
            "excluded_folders": [],
            "exclude_mode": False
        }
    
    def update_state_field(self, field_name, value):
        """Update a single field in the saved state."""
        state = self.load_state()
        state[field_name] = value
        return self.save_state(state)
    
    def get_state_field(self, field_name, default_value=None):
        """Get a single field from the saved state."""
        state = self.load_state()
        return state.get(field_name, default_value)


class ApplicationStateManager:
    """Higher-level state management for the invoice search application."""
    
    def __init__(self, state_file=None):
        self.state_manager = StateManager(state_file)
        self.current_state = self.state_manager.load_state()
    
    def get_folder_settings(self):
        """Get folder-related settings."""
        return {
            'last_folder': self.current_state.get('last_folder', 'Inbox'),
            'target_folder': self.current_state.get('target_folder', 'Archiwum'),
            'search_all_folders': self.current_state.get('search_all_folders', False),
            'excluded_folders': set(self.current_state.get('excluded_folders', [])),
            'exclude_mode': self.current_state.get('exclude_mode', False)
        }
    
    def get_search_settings(self):
        """Get search-related settings."""
        return {
            'last_nip': self.current_state.get('last_nip', ''),
            'date_from': self.current_state.get('date_from', ''),
            'date_to': self.current_state.get('date_to', '')
        }
    
    def update_folder_settings(self, folder_var, target_folder_var, search_all_folders_var, 
                             excluded_folders, exclude_mode_var):
        """Update folder settings in current state."""
        self.current_state.update({
            'last_folder': folder_var.get() if hasattr(folder_var, 'get') else folder_var,
            'target_folder': target_folder_var.get() if hasattr(target_folder_var, 'get') else target_folder_var,
            'search_all_folders': search_all_folders_var.get() if hasattr(search_all_folders_var, 'get') else search_all_folders_var,
            'excluded_folders': list(excluded_folders),
            'exclude_mode': exclude_mode_var.get() if hasattr(exclude_mode_var, 'get') else exclude_mode_var
        })
    
    def update_search_settings(self, nip_var, date_from_var, date_to_var):
        """Update search settings in current state."""
        self.current_state.update({
            'last_nip': nip_var.get().strip() if hasattr(nip_var, 'get') else str(nip_var).strip(),
            'date_from': date_from_var.get() if hasattr(date_from_var, 'get') else date_from_var,
            'date_to': date_to_var.get() if hasattr(date_to_var, 'get') else date_to_var
        })
    
    def save_current_state(self):
        """Save the current state to file."""
        return self.state_manager.save_state(self.current_state)
    
    def apply_state_to_widgets(self, widgets_dict):
        """Apply saved state to GUI widgets."""
        try:
            # Apply folder settings
            if 'folder_var' in widgets_dict:
                widgets_dict['folder_var'].set(self.current_state.get('last_folder', 'Inbox'))
            if 'target_folder_var' in widgets_dict:
                widgets_dict['target_folder_var'].set(self.current_state.get('target_folder', 'Archiwum'))
            if 'search_all_folders_var' in widgets_dict:
                widgets_dict['search_all_folders_var'].set(self.current_state.get('search_all_folders', False))
            if 'exclude_mode_var' in widgets_dict:
                widgets_dict['exclude_mode_var'].set(self.current_state.get('exclude_mode', False))
            
            # Apply search settings
            if 'nip_var' in widgets_dict:
                widgets_dict['nip_var'].set(self.current_state.get('last_nip', ''))
            if 'date_from_var' in widgets_dict:
                widgets_dict['date_from_var'].set(self.current_state.get('date_from', ''))
            if 'date_to_var' in widgets_dict:
                widgets_dict['date_to_var'].set(self.current_state.get('date_to', ''))
            
            return True
        except Exception as e:
            print(f"Błąd aplikowania stanu do widgetów: {e}")
            return False