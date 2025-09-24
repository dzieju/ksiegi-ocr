import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import queue
import threading
import json
import os
from gui.modern_theme import ModernTheme
from gui.tooltip_utils import add_tooltip, TOOLTIPS

from gui.mail_search_components.exchange_connection import ExchangeConnection
from gui.mail_search_components.search_engine import EmailSearchEngine
from gui.mail_search_components.results_display import ResultsDisplay
from gui.mail_search_components.ui_builder import MailSearchUI

MAIL_SEARCH_CONFIG_FILE = "mail_search_config.json"


class MailSearchTab(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        print("DEBUG: MailSearchTab.__init__() started")
        print(f"DEBUG: MailSearchTab parent: {parent}")
        try:
            super().__init__(parent, **ModernTheme.get_frame_style('section'))
            print("DEBUG: MailSearchTab super().__init__() completed")
        except Exception as e:
            print(f"DEBUG: MailSearchTab super().__init__() failed: {e}")
            super().__init__(parent)
        
        # Add test widget immediately
        print("DEBUG: Adding test widget to MailSearchTab...")
        try:
            test_label = ctk.CTkLabel(self, text="📧 TEST: Mail Search Tab Loaded!", 
                                    font=("Arial", 16, "bold"), 
                                    text_color="darkblue")
            test_label.pack(pady=10)
            
            test_button = ctk.CTkButton(self, text="Test Mail Search Button", 
                                      command=lambda: print("DEBUG: Mail Search test button clicked!"))
            test_button.pack(pady=5)
            print("DEBUG: Test widgets added to MailSearchTab successfully")
        except Exception as e:
            print(f"DEBUG: Failed to add test widgets to MailSearchTab: {e}")
        
        # Create a main container frame within the scrollable frame to handle grid layout
        try:
            self.main_container = ctk.CTkFrame(self, fg_color="transparent")
            self.main_container.pack(fill="both", expand=True, padx=ModernTheme.SPACING['medium'], pady=ModernTheme.SPACING['medium'])
            print("DEBUG: MailSearchTab main_container created")
        except Exception as e:
            print(f"DEBUG: MailSearchTab main_container creation failed: {e}")
            self.main_container = ctk.CTkFrame(self, fg_color="transparent")
            self.main_container.pack(fill="both", expand=True, padx=16, pady=16)
        
        # Configure the container frame to support grid layout
        try:
            self.main_container.grid_columnconfigure(0, weight=1)
            self.main_container.grid_columnconfigure(1, weight=1)  
            self.main_container.grid_columnconfigure(2, weight=1)
            print("DEBUG: MailSearchTab grid configuration completed")
        except Exception as e:
            print(f"DEBUG: MailSearchTab grid configuration failed: {e}")
        
        # Initialize search variables
        self.vars = {
            'folder_path': ctk.StringVar(value="Skrzynka odbiorcza"),
            'excluded_folders': ctk.StringVar(),
            'subject_search': ctk.StringVar(),
            'body_search': ctk.StringVar(),
            'pdf_search_text': ctk.StringVar(),
            'sender': ctk.StringVar(),
            'unread_only': ctk.BooleanVar(),
            'attachments_required': ctk.BooleanVar(),
            'no_attachments_only': ctk.BooleanVar(),
            'attachment_name': tk.StringVar(),
            'attachment_extension': tk.StringVar(),
            'selected_period': tk.StringVar(value="wszystkie")
        }
        
        # Folder exclusion support
        self.available_folders = []
        self.folder_exclusion_vars = {}  # Will hold BooleanVar for each discovered folder
        self.folder_checkboxes_frame = None
        self.folder_section_widgets = None  # Will hold toggle button, save button, check all button, uncheck all button and checkboxes frame
        self.exclusion_section_visible = True  # Track visibility state
        
        # Pagination state
        self.current_page = 0
        self.per_page = 500
        
        # Threading support
        self.result_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        
        # Initialize components
        try:
            self.connection = ExchangeConnection()
            self.search_engine = EmailSearchEngine(self._add_progress, self._add_result)
            # Pass the main_container to UI builder instead of self
            self.ui_builder = MailSearchUI(self.main_container, self.vars, self.discover_folders)
            print("DEBUG: MailSearchTab components initialized")
        except Exception as e:
            print(f"DEBUG: MailSearchTab components initialization failed: {e}")

        print("DEBUG: MailSearchTab calling create_widgets()...")
        try:
            self.create_widgets()
            print("DEBUG: MailSearchTab create_widgets() completed")
        except Exception as e:
            print(f"DEBUG: MailSearchTab create_widgets() failed: {e}")
        
        # Load saved settings
        try:
            self.load_mail_search_config()
            print("DEBUG: MailSearchTab config loaded")
        except Exception as e:
            print(f"DEBUG: MailSearchTab config loading failed: {e}")
        
        # Start processing queues
        try:
            self._process_queues()
            print("DEBUG: MailSearchTab queue processing started")
        except Exception as e:
            print(f"DEBUG: MailSearchTab queue processing failed: {e}")
        
        print("DEBUG: MailSearchTab.__init__() completed")
        
    def create_widgets(self):
        """Create all widgets using UI builder"""
        print("DEBUG: MailSearchTab.create_widgets() started")
        
        # Add another test widget
        try:
            test_label2 = ctk.CTkLabel(self, text="🎯 TEST: Mail Search create_widgets() executed!", 
                                     font=("Arial", 14), text_color="teal")
            test_label2.pack(pady=5)
            print("DEBUG: Additional test widget added in MailSearchTab create_widgets()")
        except Exception as e:
            print(f"DEBUG: Failed to add additional test widget to MailSearchTab: {e}")
        
        try:
            self.ui_builder.create_search_criteria_widgets()
            print("DEBUG: MailSearchTab search criteria widgets created")
        except Exception as e:
            print(f"DEBUG: MailSearchTab search criteria widgets creation failed: {e}")
            
        try:
            self.ui_builder.create_date_period_widgets()
            print("DEBUG: MailSearchTab date period widgets created")
        except Exception as e:
            print(f"DEBUG: MailSearchTab date period widgets creation failed: {e}")
        
        try:
            self.search_button, self.status_label = self.ui_builder.create_control_widgets(self.toggle_search)
            print("DEBUG: MailSearchTab control widgets created")
        except Exception as e:
            print(f"DEBUG: MailSearchTab control widgets creation failed: {e}")
            
        try:
            self.results_frame = self.ui_builder.create_results_widget()
            print("DEBUG: MailSearchTab results widget created")
        except Exception as e:
            print(f"DEBUG: MailSearchTab results widget creation failed: {e}")
        
        # Initialize results display with the frame
        try:
            self.results_display = ResultsDisplay(self.results_frame)
            self.results_display.set_page_callback(self.go_to_page)
            self.results_display.set_per_page_callback(self.change_per_page)
            self.results_display.bind_selection_change()
            print("DEBUG: MailSearchTab results display initialized")
        except Exception as e:
            print(f"DEBUG: MailSearchTab results display initialization failed: {e}")
        
        print("DEBUG: MailSearchTab.create_widgets() completed")
        
    def toggle_search(self):
        """Toggle between starting and cancelling search"""
        if self.search_engine.search_thread and self.search_engine.search_thread.is_alive():
            self.cancel_search()
        else:
            self.start_search()
    
    def cancel_search(self):
        """Cancel ongoing search"""
        self.search_engine.cancel_search()
        self.status_label.config(text="Anulowanie...", foreground="orange")
        self.search_button.config(text="Rozpocznij wyszukiwanie")
    
    def discover_folders(self):
        """Discover available folders for exclusion in background thread"""
        def _discover():
            try:
                self._add_progress("Wykrywanie dostępnych folderów...")
                account = self.connection.get_account()
                if account:
                    folder_path = self.vars['folder_path'].get()
                    folders = self.connection.get_available_folders_for_exclusion(account, folder_path)
                    self.after_idle(lambda: self._update_folder_checkboxes(folders))
            except Exception as e:
                print(f"Błąd wykrywania folderów: {e}")
                self._add_progress("Błąd wykrywania folderów")
        
        threading.Thread(target=_discover, daemon=True).start()
    
    def _update_folder_checkboxes(self, folders):
        """Update folder checkboxes in the UI thread"""
        self.available_folders = folders
        self.folder_exclusion_vars = {}
        
        # Clear existing checkboxes
        if self.folder_checkboxes_frame:
            self.folder_checkboxes_frame.destroy()
        
        # Create new checkboxes frame if we have folders
        if folders:
            self.folder_checkboxes_frame, self.folder_section_widgets = self.ui_builder.create_folder_exclusion_checkboxes(
                folders, 
                self.folder_exclusion_vars, 
                hide_callback=self.toggle_folder_exclusion_section,
                uncheck_all_callback=self.uncheck_all_exclusions,
                check_all_callback=self.check_all_exclusions,
                is_visible=self.exclusion_section_visible
            )
            
            # Set up save button callback
            if self.folder_section_widgets:
                toggle_button, save_button, check_all_button, uncheck_all_button, checkboxes_frame = self.folder_section_widgets
                save_button.config(command=self.save_mail_search_config)
                
            # Load saved excluded folders
            self._load_saved_exclusions()
        
        self._add_progress(f"Wykryto {len(folders)} folderów")
    
    def _get_excluded_folders_from_checkboxes(self):
        """Get list of excluded folders from checkboxes"""
        excluded = []
        for folder_name, var in self.folder_exclusion_vars.items():
            if var.get():
                excluded.append(folder_name)
        return ','.join(excluded)  # Convert back to comma-separated format for backend compatibility
    
    def start_search(self):
        """Start threaded search"""
        self.results_display.clear_results()
        self.search_button.config(text="Anuluj wyszukiwanie")
        self.status_label.config(text="Nawiązywanie połączenia...", foreground="blue")
        
        # Reset pagination
        self.current_page = 0
        
        # Update excluded_folders from checkboxes before search
        self.vars['excluded_folders'].set(self._get_excluded_folders_from_checkboxes())

        threading.Thread(target=self._perform_search, daemon=True).start()
    
    def _perform_search(self):
        """Perform search in background thread"""
        try:
            criteria = {key: var.get() if hasattr(var, 'get') else var for key, var in self.vars.items()}
            self.search_engine.search_emails_threaded(self.connection, criteria, self.current_page, self.per_page)
            
        except Exception as e:
            self._add_result({'type': 'search_error', 'error': str(e)})
    
    def _add_progress(self, message):
        """Add progress to queue"""
        # Also print to console for debugging
        print(f"[MAIL SEARCH] {message}")
        self.progress_queue.put(message)
    
    def _add_result(self, result):
        """Add result to queue"""
        self.result_queue.put(result)
    
    def _process_queues(self):
        """Process both result and progress queues"""
        # Process results
        try:
            while True:
                try:
                    result = self.result_queue.get_nowait()
                    self._handle_result(result)
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Błąd przetwarzania wyników: {e}")
        
        # Process progress
        try:
            while True:
                try:
                    progress = self.progress_queue.get_nowait()
                    self.status_label.config(text=progress, foreground="blue")
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Błąd przetwarzania postępu: {e}")
        
        self.after(100, self._process_queues)
    
    def _handle_result(self, result):
        """Handle search result"""
        if result['type'] == 'search_complete':
            self.results_display.display_results(
                result['results'], 
                result.get('page', 0), 
                result.get('per_page', 500),
                result.get('total_count', result['count']),
                result.get('total_pages', 1)
            )
            self.status_label.config(text=f"Znaleziono {result.get('total_count', result['count'])} wiadomości", foreground="green")
            self.search_button.config(text="Rozpocznij wyszukiwanie")
            
        elif result['type'] == 'search_cancelled':
            self.status_label.config(text="Wyszukiwanie anulowane", foreground="orange")
            self.search_button.config(text="Rozpocznij wyszukiwanie")
            
        elif result['type'] == 'search_error':
            messagebox.showerror("Błąd wyszukiwania", f"Błąd: {result['error']}")
            self.status_label.config(text="Błąd wyszukiwania", foreground="red")
            self.search_button.config(text="Rozpocznij wyszukiwanie")
    
    def go_to_page(self, page):
        """Go to specific page"""
        self.current_page = page
        self.status_label.config(text="Ładowanie strony...", foreground="blue")
        threading.Thread(target=self._perform_search, daemon=True).start()
    
    def change_per_page(self, per_page):
        """Change results per page"""
        self.per_page = per_page
        self.current_page = 0  # Reset to first page
        self.status_label.config(text="Ładowanie wyników...", foreground="blue")
        threading.Thread(target=self._perform_search, daemon=True).start()

    def _load_saved_exclusions(self):
        """Load saved folder exclusions and apply them to checkboxes"""
        try:
            if os.path.exists(MAIL_SEARCH_CONFIG_FILE):
                with open(MAIL_SEARCH_CONFIG_FILE, "r", encoding='utf-8') as f:
                    config = json.load(f)
                    excluded_folders = config.get("excluded_folders", [])
                    
                    # Apply saved exclusions to checkboxes
                    for folder_name in excluded_folders:
                        if folder_name in self.folder_exclusion_vars:
                            self.folder_exclusion_vars[folder_name].set(True)
        except Exception as e:
            print(f"Błąd ładowania wykluczeń folderów: {e}")

    def load_mail_search_config(self):
        """Load mail search configuration from config file"""
        try:
            if os.path.exists(MAIL_SEARCH_CONFIG_FILE):
                with open(MAIL_SEARCH_CONFIG_FILE, "r", encoding='utf-8') as f:
                    config = json.load(f)
                    self.exclusion_section_visible = config.get("exclusion_section_visible", True)
                    # Excluded folders will be loaded when folders are discovered
        except Exception as e:
            print(f"Błąd ładowania konfiguracji wyszukiwania: {e}")

    def save_mail_search_config(self):
        """Save mail search configuration to config file"""
        try:
            # Get currently excluded folders
            excluded_folders = []
            for folder_name, var in self.folder_exclusion_vars.items():
                if var.get():
                    excluded_folders.append(folder_name)
            
            config = {
                "excluded_folders": excluded_folders,
                "exclusion_section_visible": self.exclusion_section_visible
            }
            
            with open(MAIL_SEARCH_CONFIG_FILE, "w", encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("Zapisano", "Ustawienia zostały zapisane.")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd zapisywania ustawień: {e}")
    
    def uncheck_all_exclusions(self):
        """Uncheck all folder exclusion checkboxes"""
        try:
            for folder_name, var in self.folder_exclusion_vars.items():
                var.set(False)
        except Exception as e:
            print(f"Błąd odznaczania wykluczeń: {e}")
    
    def check_all_exclusions(self):
        """Check all folder exclusion checkboxes"""
        try:
            for folder_name, var in self.folder_exclusion_vars.items():
                var.set(True)
        except Exception as e:
            print(f"Błąd zaznaczania wykluczeń: {e}")

    def toggle_folder_exclusion_section(self, toggle_button):
        """Toggle visibility of folder exclusion section"""
        if self.folder_section_widgets:
            toggle_button_widget, save_button, check_all_button, uncheck_all_button, checkboxes_frame = self.folder_section_widgets
            
            if self.exclusion_section_visible:
                # Hide the checkboxes
                checkboxes_frame.grid_remove()
                toggle_button.config(text="Pokaż")
                self.exclusion_section_visible = False
            else:
                # Show the checkboxes
                checkboxes_frame.grid()
                toggle_button.config(text="Ukryj")
                self.exclusion_section_visible = True

    def search_emails(self):
        """Legacy compatibility method"""
        self.start_search()
    
    def destroy(self):
        """Cleanup on destroy"""
        if self.search_engine.search_thread and self.search_engine.search_thread.is_alive():
            self.search_engine.cancel_search()
        super().destroy()