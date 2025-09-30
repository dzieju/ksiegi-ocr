import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import queue
import threading
import json
import os

from gui.mail_search_components.mail_connection import MailConnection
from gui.mail_search_components.search_engine import EmailSearchEngine
from gui.mail_search_components.results_display import ResultsDisplay
from gui.mail_search_components.ui_builder import MailSearchUI

MAIL_SEARCH_CONFIG_FILE = "mail_search_config.json"


class MailSearchTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Initialize search variables
        self.vars = {
            'folder_path': tk.StringVar(value="Skrzynka odbiorcza"),
            'excluded_folders': tk.StringVar(),
            'subject_search': tk.StringVar(),
            'body_search': tk.StringVar(),
            'pdf_search_text': tk.StringVar(),
            'pdf_save_directory': tk.StringVar(value=os.path.join(os.getcwd(), "odczyty", "Faktury")),
            'sender': tk.StringVar(),
            'unread_only': tk.BooleanVar(),
            'attachments_required': tk.BooleanVar(),
            'no_attachments_only': tk.BooleanVar(),
            'attachment_name': tk.StringVar(),
            'attachment_extension': tk.StringVar(),
            'selected_period': tk.StringVar(value="wszystkie"),
            'skip_searched_pdfs': tk.BooleanVar()
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
        self.connection = MailConnection()
        self.search_engine = EmailSearchEngine(self._add_progress, self._add_result)
        self.ui_builder = MailSearchUI(self, self.vars, self.discover_folders, self.choose_pdf_save_folder, self.clear_pdf_history, self.show_pdf_history)
        
        # Initialize PDF history manager
        from gui.mail_search_components.pdf_history_manager import PDFHistoryManager
        self.pdf_history_manager = PDFHistoryManager()
        
        # Set PDF history manager in search engine
        self.search_engine.pdf_history_manager = self.pdf_history_manager
        
        self.create_widgets()
        
        # Add callback to update folder info when folder path changes
        self.vars['folder_path'].trace('w', self._on_folder_path_change)
        
        # Load saved settings
        self.load_mail_search_config()
        
        # Update account info display
        self.update_account_info_display()
        
        # Start processing queues
        self._process_queues()
        
    def create_widgets(self):
        """Create all widgets using UI builder"""
        self.ui_builder.create_search_criteria_widgets()
        self.ui_builder.create_date_period_widgets()
        
        self.search_button, self.status_label, self.account_info_label, self.folder_info_label = self.ui_builder.create_control_widgets(self.toggle_search)
        self.results_frame = self.ui_builder.create_results_widget()
        
        # Initialize results display with the frame
        self.results_display = ResultsDisplay(self.results_frame)
        self.results_display.set_page_callback(self.go_to_page)
        self.results_display.set_per_page_callback(self.change_per_page)
        self.results_display.bind_selection_change()
        
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
    
    def choose_pdf_save_folder(self):
        """Open folder selection dialog for PDF save directory"""
        try:
            current_directory = self.vars['pdf_save_directory'].get()
            
            # Open folder selection dialog
            selected_folder = filedialog.askdirectory(
                title="Wybierz folder do zapisu PDFów",
                initialdir=current_directory if os.path.exists(current_directory) else os.getcwd()
            )
            
            if selected_folder:  # User selected a folder (didn't cancel)
                self.vars['pdf_save_directory'].set(selected_folder)
                self._add_progress(f"Wybrano folder do zapisu PDFów: {selected_folder}")
                
                # Save to configuration
                self.save_mail_search_config()
                
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd wyboru folderu: {e}")
    
    def clear_pdf_history(self):
        """Clear PDF search history"""
        try:
            # Ask for confirmation
            result = messagebox.askyesno(
                "Potwierdzenie", 
                "Czy na pewno chcesz wyczyścić całą historię wyszukiwania PDF?\n\nTa operacja jest nieodwracalna.",
                icon="warning"
            )
            
            if result:
                if self.pdf_history_manager.clear_history():
                    messagebox.showinfo("Sukces", "Historia wyszukiwania PDF została wyczyszczona.")
                    self._add_progress("Historia PDF została wyczyszczona")
                else:
                    messagebox.showerror("Błąd", "Nie udało się wyczyścić historii PDF.")
                    
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd czyszczenia historii: {e}")
    
    def show_pdf_history(self):
        """Show PDF search history in a modal window"""
        try:
            from gui.mail_search_components.pdf_history_display import PDFHistoryDisplayWindow
            
            # Create and show the history display window
            history_window = PDFHistoryDisplayWindow(self, self.pdf_history_manager)
            history_window.show()
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd wyświetlania historii: {e}")
    
    def update_account_info_display(self):
        """Update account and folder information display"""
        try:
            if hasattr(self, 'account_info_label') and hasattr(self, 'folder_info_label'):
                current_folder = self.vars['folder_path'].get()
                account_info, folder_info = self.connection.get_account_and_folder_info(current_folder)
                
                # Update account info with color coding
                if "Exchange" in account_info:
                    color = "green"
                elif "IMAP" in account_info:
                    color = "blue"
                elif "POP3" in account_info:
                    color = "purple"
                elif "Nieskonfigurowane" in account_info:
                    color = "red"
                else:
                    color = "orange"
                
                self.account_info_label.config(text=account_info, foreground=color)
                
                # Update folder info with enhanced information
                if "→" in folder_info:  # Translation shown
                    self.folder_info_label.config(text=folder_info, foreground="blue")
                elif "Brak" in folder_info:
                    self.folder_info_label.config(text=folder_info, foreground="gray")
                else:
                    self.folder_info_label.config(text=folder_info, foreground="green")
                
                # Add folder validation status if connection is available
                if self.connection.current_account_config:
                    account_type = self.connection.current_account_config.get("type", "unknown")
                    if account_type in ["imap_smtp", "pop3_smtp", "exchange"]:
                        # Show additional validation info for folder existence
                        from gui.mail_search_components.mail_connection import FolderNameMapper
                        server_folder = FolderNameMapper.polish_to_server(current_folder)
                        if server_folder != current_folder:
                            validation_info = f" (Mapowanie: {server_folder})"
                            current_text = self.folder_info_label.cget("text")
                            if "Mapowanie:" not in current_text:
                                self.folder_info_label.config(text=current_text + validation_info)
                        
        except Exception as e:
            if hasattr(self, 'account_info_label'):
                self.account_info_label.config(text="Konto: Błąd konfiguracji", foreground="red")
            if hasattr(self, 'folder_info_label'):
                self.folder_info_label.config(text="Folder: Błąd dostępu", foreground="red")
            from tools.logger import log
            log(f"[ACCOUNT INFO] Error updating display: {str(e)}")

    def _on_folder_path_change(self, *args):
        """Called when folder path is changed to update display"""
        self.update_account_info_display()

    def discover_folders(self):
        """Discover available folders for exclusion in background thread"""
        def _discover():
            try:
                self._add_progress("Wykrywanie dostępnych folderów...")
                
                # Add debug logging
                from tools.logger import log
                log("[FOLDER DISCOVERY] Starting folder discovery")
                
                account = self.connection.get_main_account()
                log(f"[FOLDER DISCOVERY] Got account: {account is not None}")
                
                # Update account info display after getting account
                self.after_idle(self.update_account_info_display)
                
                if account:
                    folder_path = self.vars['folder_path'].get()
                    log(f"[FOLDER DISCOVERY] Folder path: {folder_path}")
                    
                    folders = self.connection.get_available_folders_for_exclusion(account, folder_path)
                    log(f"[FOLDER DISCOVERY] Found {len(folders)} folders: {folders}")
                    
                    if folders:
                        self.after_idle(lambda: self._update_folder_checkboxes(folders))
                        self._add_progress(f"Wykryto {len(folders)} folderów")
                    else:
                        # Show user-friendly message when no folders are discovered
                        self._add_progress("Nie udało się pobrać listy folderów z serwera")
                        # Still show fallback folders for user convenience
                        fallback_folders = ["SENT", "Sent", "DRAFTS", "Drafts", "SPAM", "Junk", "TRASH", "Trash"]
                        self.after_idle(lambda: self._update_folder_checkboxes(fallback_folders))
                        log("[FOLDER DISCOVERY] Using fallback folders due to discovery failure")
                else:
                    log("[FOLDER DISCOVERY] No account available")
                    self._add_progress("Brak dostępnego konta pocztowego")
                    
            except Exception as e:
                from tools.logger import log
                log(f"[FOLDER DISCOVERY] Error: {str(e)}")
                print(f"Błąd wykrywania folderów: {e}")
                self._add_progress("Błąd wykrywania folderów - sprawdź konfigurację konta")
                # Provide fallback folders even on error
                fallback_folders = ["SENT", "Sent", "DRAFTS", "Drafts", "SPAM", "Junk", "TRASH", "Trash"] 
                self.after_idle(lambda: self._update_folder_checkboxes(fallback_folders))
        
        threading.Thread(target=_discover, daemon=True).start()
    
    def _update_folder_checkboxes(self, folders):
        """Update folder checkboxes in the UI thread"""
        from tools.logger import log
        log(f"[FOLDER UI] Updating folder checkboxes with {len(folders)} folders: {folders}")
        
        self.available_folders = folders
        self.folder_exclusion_vars = {}
        
        # Clear existing checkboxes
        if self.folder_checkboxes_frame:
            log("[FOLDER UI] Destroying existing checkboxes frame")
            self.folder_checkboxes_frame.destroy()
        
        # Create new checkboxes frame if we have folders
        if folders:
            log("[FOLDER UI] Creating new folder checkboxes")
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
            
            # Show success message with folder count
            self._add_progress(f"Pomyślnie załadowano {len(folders)} folderów")
        else:
            log("[FOLDER UI] No folders to display")
            self._add_progress("Brak folderów do wyświetlenia")
        
        # Update account display to show current status
        self.update_account_info_display()
    
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
                    # Load PDF save directory if available
                    pdf_save_dir = config.get("pdf_save_directory")
                    if pdf_save_dir:
                        self.vars['pdf_save_directory'].set(pdf_save_dir)
                    # Load skip searched PDFs setting
                    skip_searched = config.get("skip_searched_pdfs", False)
                    self.vars['skip_searched_pdfs'].set(skip_searched)
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
                "exclusion_section_visible": self.exclusion_section_visible,
                "pdf_save_directory": self.vars['pdf_save_directory'].get(),
                "skip_searched_pdfs": self.vars['skip_searched_pdfs'].get()
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