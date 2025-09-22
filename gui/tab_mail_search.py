import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import json
import queue
import threading
from datetime import datetime, timedelta, timezone
from exchangelib import Credentials, Account, Configuration, DELEGATE, Q
from exchangelib.folders import Inbox
from exchangelib.properties import Mailbox

from gui.mail_search_components.exchange_connection import ExchangeConnection
from gui.mail_search_components.search_engine import EmailSearchEngine
from gui.mail_search_components.results_display import ResultsDisplay

CONFIG_FILE = "exchange_config.json"

class MailSearchTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Initialize search variables
        self.folder_path_var = tk.StringVar(value="Skrzynka odbiorcza")
        self.subject_search_var = tk.StringVar()
        self.sender_var = tk.StringVar()
        self.unread_only_var = tk.BooleanVar()
        self.attachments_required_var = tk.BooleanVar()
        self.attachment_name_var = tk.StringVar()
        self.attachment_extension_var = tk.StringVar()
        
        # Date period selection variables
        self.selected_period = tk.StringVar(value="wszystkie")  # Default: no date filter
        
        # Threading support variables
        self.result_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        
        # Initialize components
        self.connection = ExchangeConnection()
        self.search_engine = EmailSearchEngine(self._add_progress, self._add_result)
        
        self.create_widgets()
        
        # Start processing queues
        self._process_result_queue()
        self._process_progress_queue()
        
    def create_widgets(self):
        # Title label
        title_label = ttk.Label(
            self, 
            text="Przeszukiwanie Poczty", 
            font=("Arial", 12),
            foreground="blue"
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Search criteria fields
        ttk.Label(self, text="Folder przeszukiwania:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self, textvariable=self.folder_path_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self, text="Co ma szukać w temacie maila:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self, textvariable=self.subject_search_var, width=40).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(self, text="Nadawca maila:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self, textvariable=self.sender_var, width=40).grid(row=3, column=1, padx=5, pady=5)
        
        # Checkboxes
        ttk.Checkbutton(self, text="Tylko nieprzeczytane", variable=self.unread_only_var).grid(row=4, column=0, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(self, text="Tylko z załącznikami", variable=self.attachments_required_var).grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        # Attachment filters
        ttk.Label(self, text="Nazwa załącznika (zawiera):").grid(row=5, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self, textvariable=self.attachment_name_var, width=40).grid(row=5, column=1, padx=5, pady=5)
        
        ttk.Label(self, text="Rozszerzenie załącznika:").grid(row=6, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self, textvariable=self.attachment_extension_var, width=40).grid(row=6, column=1, padx=5, pady=5)
        
        # Date period selection
        ttk.Label(self, text="Okres wiadomości:", font=("Arial", 10, "bold")).grid(row=7, column=0, sticky="w", padx=5, pady=(15, 5))
        
        # Create frame for period buttons
        period_frame = ttk.Frame(self)
        period_frame.grid(row=7, column=1, columnspan=2, sticky="w", padx=5, pady=(15, 5))
        
        # Period selection buttons
        periods = [
            ("wszystkie", "Wszystkie"),
            ("ostatni_miesiac", "Ostatni miesiąc"),
            ("ostatnie_3_miesiace", "Ostatnie 3 miesiące"),
            ("ostatnie_6_miesiecy", "Ostatnie 6 miesięcy"),
            ("ostatni_rok", "Ostatni rok")
        ]
        
        for i, (value, text) in enumerate(periods):
            ttk.Radiobutton(
                period_frame, 
                text=text, 
                variable=self.selected_period, 
                value=value
            ).grid(row=0, column=i, padx=5, sticky="w")
        
        # Search button and status
        search_frame = ttk.Frame(self)
        search_frame.grid(row=8, column=0, columnspan=3, pady=20)
        
        self.search_button = ttk.Button(search_frame, text="Rozpocznij wyszukiwanie", command=self.toggle_search)
        self.search_button.pack(side="left", padx=5)
        
        self.status_label = ttk.Label(search_frame, text="Gotowy", foreground="green")
        self.status_label.pack(side="left", padx=10)
        
        # Results area
        self.results_area = ScrolledText(self, wrap="word", width=120, height=25)
        self.results_area.grid(row=9, column=0, columnspan=3, padx=10, pady=10)
        
        # Initialize results display
        self.results_display = ResultsDisplay(self.results_area)
        
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
        """Start the threaded search"""
        # Clear previous results
        self.results_display.clear_results()
        
        # Update UI
        self.search_button.config(text="Anuluj wyszukiwanie")
        self.status_label.config(text="Nawiązywanie połączenia...", foreground="blue")

        # Start search in background thread
        search_thread = threading.Thread(
            target=self._perform_search,
            daemon=True
        )
        search_thread.start()
    
    def _perform_search(self):
        """Perform search operation in background thread"""
        try:
            # Get account connection
            account = self.connection.get_account()
            if not account:
                self._add_result({
                    'type': 'search_error',
                    'error': "Nie można nawiązać połączenia z serwerem poczty"
                })
                return
                
            # Get target folder
            folder = self.connection.get_folder_by_path(account, self.folder_path_var.get().strip())
            if not folder:
                self._add_result({
                    'type': 'search_error',
                    'error': "Nie można uzyskać dostępu do folderu"
                })
                return
                
            # Prepare search criteria
            criteria = {
                'subject': self.subject_search_var.get().strip(),
                'sender': self.sender_var.get().strip(),
                'unread_only': self.unread_only_var.get(),
                'attachments_required': self.attachments_required_var.get(),
                'attachment_name': self.attachment_name_var.get().strip(),
                'attachment_extension': self.attachment_extension_var.get().strip(),
                'date_period': self.selected_period.get()
            }
            
            # Start search
            self.search_engine.search_emails_threaded(self.connection, folder, criteria)
            
        except Exception as e:
            self._add_result({
                'type': 'search_error',
                'error': str(e)
            })
    
    def _add_progress(self, message):
        """Add progress message to queue"""
        self.progress_queue.put(message)
    
    def _add_result(self, result):
        """Add result to queue"""
        self.result_queue.put(result)
    
    def _process_result_queue(self):
        """Process results from worker thread"""
        try:
            while True:
                try:
                    result = self.result_queue.get_nowait()
                    
                    if result['type'] == 'search_complete':
                        results = result['results']
                        count = result['count']
                        self.results_display.display_results(results)
                        self.status_label.config(text=f"Znaleziono {count} wiadomości", foreground="green")
                        self.search_button.config(text="Rozpocznij wyszukiwanie")
                        
                    elif result['type'] == 'search_cancelled':
                        self.status_label.config(text="Wyszukiwanie anulowane", foreground="orange")
                        self.search_button.config(text="Rozpocznij wyszukiwanie")
                        
                    elif result['type'] == 'search_error':
                        error_msg = result['error']
                        messagebox.showerror("Błąd wyszukiwania", f"Błąd podczas wyszukiwania: {error_msg}")
                        self.status_label.config(text="Błąd wyszukiwania", foreground="red")
                        self.search_button.config(text="Rozpocznij wyszukiwanie")
                        
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Błąd przetwarzania kolejki wyników: {e}")
        
        # Schedule next check
        self.after(100, self._process_result_queue)
    
    def _process_progress_queue(self):
        """Process progress updates from worker thread"""
        try:
            while True:
                try:
                    progress = self.progress_queue.get_nowait()
                    self.status_label.config(text=progress, foreground="blue")
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Błąd przetwarzania kolejki postępu: {e}")
        
        # Schedule next check
        self.after(100, self._process_progress_queue)

    def search_emails(self):
        """Legacy method for backward compatibility"""
        self.start_search()
    
    def destroy(self):
        """Cleanup when widget is destroyed"""
        if self.search_engine.search_thread and self.search_engine.search_thread.is_alive():
            self.search_engine.cancel_search()
        super().destroy()