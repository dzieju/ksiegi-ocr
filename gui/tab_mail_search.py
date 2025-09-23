import tkinter as tk
from tkinter import ttk, messagebox
import queue
import threading

from gui.mail_search_components.exchange_connection import ExchangeConnection
from gui.mail_search_components.search_engine import EmailSearchEngine
from gui.mail_search_components.results_display import ResultsDisplay
from gui.mail_search_components.ui_builder import MailSearchUI


class MailSearchTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Initialize search variables
        self.vars = {
            'folder_path': tk.StringVar(value="Skrzynka odbiorcza"),
            'subject_search': tk.StringVar(),
            'sender': tk.StringVar(),
            'unread_only': tk.BooleanVar(),
            'attachments_required': tk.BooleanVar(),
            'attachment_name': tk.StringVar(),
            'attachment_extension': tk.StringVar(),
            'selected_period': tk.StringVar(value="wszystkie")
        }
        
        # Pagination state
        self.current_page = 0
        self.per_page = 500
        
        # Threading support
        self.result_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        
        # Initialize components
        self.connection = ExchangeConnection()
        self.search_engine = EmailSearchEngine(self._add_progress, self._add_result)
        self.ui_builder = MailSearchUI(self, self.vars)
        
        self.create_widgets()
        
        # Start processing queues
        self._process_queues()
        
    def create_widgets(self):
        """Create all widgets using UI builder"""
        self.ui_builder.create_search_criteria_widgets()
        self.ui_builder.create_date_period_widgets()
        
        self.search_button, self.status_label = self.ui_builder.create_control_widgets(self.toggle_search)
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
    
    def start_search(self):
        """Start threaded search"""
        self.results_display.clear_results()
        self.search_button.config(text="Anuluj wyszukiwanie")
        self.status_label.config(text="Nawiązywanie połączenia...", foreground="blue")
        
        # Reset pagination
        self.current_page = 0

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

    def search_emails(self):
        """Legacy compatibility method"""
        self.start_search()
    
    def destroy(self):
        """Cleanup on destroy"""
        if self.search_engine.search_thread and self.search_engine.search_thread.is_alive():
            self.search_engine.cancel_search()
        super().destroy()