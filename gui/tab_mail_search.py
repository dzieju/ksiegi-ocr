import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import json
from exchangelib import Credentials, Account, Configuration, DELEGATE, Q
from exchangelib.folders import Inbox
from exchangelib.properties import Mailbox

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
        
        self.create_widgets()
        
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
        ttk.Checkbutton(self, text="Tylko nieprzeczytane", variable=self.unread_only_var).grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        ttk.Checkbutton(self, text="Wymagane załączniki", variable=self.attachments_required_var).grid(row=5, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # Attachment filters
        ttk.Label(self, text="Nazwa załącznika ma zawierać:").grid(row=6, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self, textvariable=self.attachment_name_var, width=40).grid(row=6, column=1, padx=5, pady=5)
        
        ttk.Label(self, text="Rozszerzenie załącznika:").grid(row=7, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self, textvariable=self.attachment_extension_var, width=40).grid(row=7, column=1, padx=5, pady=5)
        
        # Search button
        ttk.Button(self, text="Przeszukaj pocztę", command=self.search_emails).grid(row=8, column=1, pady=20)
        
        # Status label
        self.status_label = ttk.Label(self, text="Gotowy do wyszukiwania", foreground="blue")
        self.status_label.grid(row=9, column=1, pady=5)
        
        # Results area
        self.results_area = ScrolledText(self, wrap="word", width=120, height=25)
        self.results_area.grid(row=10, column=0, columnspan=3, padx=10, pady=10)
        
    def load_exchange_config(self):
        """Load Exchange configuration from config file"""
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config
        except FileNotFoundError:
            messagebox.showerror("Błąd konfiguracji", "Brak konfiguracji poczty. Skonfiguruj połączenie w zakładce 'Konfiguracja poczty'.")
            return None
        except Exception as e:
            messagebox.showerror("Błąd konfiguracji", f"Błąd odczytu konfiguracji: {str(e)}")
            return None
    
    def get_account(self):
        """Get Exchange account connection"""
        config = self.load_exchange_config()
        if not config:
            return None
            
        try:
            creds = Credentials(
                username=config.get("username", ""),
                password=config.get("password", "")
            )
            account_config = Configuration(
                server=config.get("server", ""),
                credentials=creds
            )
            account = Account(
                primary_smtp_address=config.get("email", ""),
                config=account_config,
                autodiscover=False,
                access_type=DELEGATE
            )
            return account
        except Exception as e:
            messagebox.showerror("Błąd połączenia", f"Nie można połączyć z serwerem poczty: {str(e)}")
            return None
    
    def get_folder_by_path(self, account, folder_path):
        """Get folder by path like 'Skrzynka odbiorcza/Kompensaty Quadra'"""
        try:
            if not folder_path or folder_path.lower() in ["skrzynka odbiorcza", "inbox"]:
                return account.inbox
                
            # Split path and navigate to folder
            path_parts = folder_path.split('/')
            current_folder = account.inbox
            
            for part in path_parts:
                part = part.strip()
                if part.lower() in ["skrzynka odbiorcza", "inbox"]:
                    continue
                    
                # Search for subfolder
                found = False
                for child in current_folder.children:
                    if child.name.lower() == part.lower():
                        current_folder = child
                        found = True
                        break
                
                if not found:
                    messagebox.showwarning("Błąd folderu", f"Nie znaleziono folderu: {part}")
                    return account.inbox
                    
            return current_folder
        except Exception as e:
            messagebox.showerror("Błąd folderu", f"Błąd dostępu do folderu: {str(e)}")
            return account.inbox
    
    def search_emails(self):
        """Perform email search based on criteria"""
        self.status_label.config(text="Wyszukiwanie w toku...")
        self.results_area.delete("1.0", tk.END)
        
        # Get account connection
        account = self.get_account()
        if not account:
            self.status_label.config(text="Błąd połączenia")
            return
            
        # Get target folder
        folder = self.get_folder_by_path(account, self.folder_path_var.get().strip())
        if not folder:
            self.status_label.config(text="Błąd folderu")
            return
            
        try:
            # Build search query
            query_filters = []
            
            # Subject filter
            subject_text = self.subject_search_var.get().strip()
            if subject_text:
                query_filters.append(Q(subject__icontains=subject_text))
            
            # Sender filter
            sender_email = self.sender_var.get().strip()
            if sender_email:
                query_filters.append(Q(sender=sender_email))
            
            # Unread filter
            if self.unread_only_var.get():
                query_filters.append(Q(is_read=False))
            
            # Attachments filter
            if self.attachments_required_var.get():
                query_filters.append(Q(has_attachments=True))
            
            # Combine all filters
            if query_filters:
                combined_query = query_filters[0]
                for q in query_filters[1:]:
                    combined_query &= q
                messages = folder.filter(combined_query)
            else:
                messages = folder.all()
            
            # Process results
            results = []
            processed_count = 0
            max_results = 100  # Limit results to prevent UI freeze
            
            for message in messages:
                if processed_count >= max_results:
                    break
                    
                try:
                    # Check attachment filters if needed
                    if self.attachments_required_var.get() or self.attachment_name_var.get().strip() or self.attachment_extension_var.get().strip():
                        if not self.check_attachment_filters(message):
                            continue
                    
                    # Format result
                    result_info = {
                        'datetime_received': message.datetime_received,
                        'subject': message.subject or '(brak tematu)',
                        'sender': str(message.sender) if message.sender else '(nieznany nadawca)',
                        'is_read': message.is_read,
                        'has_attachments': message.has_attachments,
                        'attachment_count': len(message.attachments) if message.attachments else 0
                    }
                    results.append(result_info)
                    processed_count += 1
                    
                except Exception as e:
                    # Skip messages that cause errors
                    continue
            
            # Display results
            self.display_results(results, processed_count >= max_results)
            self.status_label.config(text=f"Znaleziono {len(results)} wiadomości")
            
        except Exception as e:
            messagebox.showerror("Błąd wyszukiwania", f"Błąd podczas wyszukiwania: {str(e)}")
            self.status_label.config(text="Błąd wyszukiwania")
    
    def check_attachment_filters(self, message):
        """Check if message meets attachment criteria"""
        if not message.has_attachments and self.attachments_required_var.get():
            return False
            
        attachment_name_filter = self.attachment_name_var.get().strip().lower()
        attachment_ext_filter = self.attachment_extension_var.get().strip().lower()
        
        if not attachment_name_filter and not attachment_ext_filter:
            return True
            
        if not message.attachments:
            return False
            
        for attachment in message.attachments:
            if hasattr(attachment, 'name') and attachment.name:
                attachment_name = attachment.name.lower()
                
                # Check name filter
                if attachment_name_filter and attachment_name_filter not in attachment_name:
                    continue
                    
                # Check extension filter
                if attachment_ext_filter:
                    if not attachment_name.endswith(f'.{attachment_ext_filter}'):
                        continue
                
                # If we get here, attachment matches filters
                return True
        
        return False
    
    def display_results(self, results, more_available=False):
        """Display search results in the text area"""
        if not results:
            self.results_area.insert(tk.END, "Nie znaleziono żadnych wiadomości spełniających kryteria.\n")
            return
            
        # Header
        header = f"{'Data':<20} | {'Nadawca':<30} | {'Temat':<50} | {'Status':<12} | {'Załączniki':<10}"
        self.results_area.insert(tk.END, header + "\n")
        self.results_area.insert(tk.END, "-" * len(header) + "\n")
        
        # Results
        for result in results:
            date_str = result['datetime_received'].strftime('%Y-%m-%d %H:%M') if result['datetime_received'] else 'Brak daty'
            sender = result['sender'][:28] if len(result['sender']) > 28 else result['sender']
            subject = result['subject'][:48] if len(result['subject']) > 48 else result['subject']
            status = "Nieprzeczyt." if not result['is_read'] else "Przeczytane"
            attachments = f"{result['attachment_count']}" if result['has_attachments'] else "Brak"
            
            line = f"{date_str:<20} | {sender:<30} | {subject:<50} | {status:<12} | {attachments:<10}"
            self.results_area.insert(tk.END, line + "\n")
        
        if more_available:
            self.results_area.insert(tk.END, f"\n*** Wyświetlono pierwszych 100 wyników. Zawęź kryteria wyszukiwania aby zobaczyć więcej. ***\n")