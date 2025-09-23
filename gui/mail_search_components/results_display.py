"""
Results display handler for mail search functionality
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading


class ResultsDisplay:
    """Handles display of search results with interactive capabilities"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.results_data = []
        self.current_page = 0
        self.per_page = 20
        self.total_pages = 0
        self.total_count = 0
        
        # Create temp directory in the main application folder
        self.temp_dir = os.path.join(os.getcwd(), 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create the results display widgets"""
        # Results frame
        self.results_frame = ttk.Frame(self.parent_frame)
        self.results_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        
        # Configure grid weights for dynamic resizing
        self.parent_frame.grid_rowconfigure(0, weight=1)
        self.parent_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_rowconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(0, weight=1)
        
        # Treeview with scrollbars
        self.tree = ttk.Treeview(self.results_frame, columns=("Date", "Sender", "Subject", "Status", "Attachments"), show="headings", height=15)
        
        # Configure column headings and widths
        self.tree.heading("Date", text="Data")
        self.tree.heading("Sender", text="Nadawca")
        self.tree.heading("Subject", text="Temat")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Attachments", text="Załączniki")
        
        self.tree.column("Date", width=150, minwidth=100)
        self.tree.column("Sender", width=200, minwidth=150)
        self.tree.column("Subject", width=300, minwidth=200)
        self.tree.column("Status", width=100, minwidth=80)
        self.tree.column("Attachments", width=100, minwidth=80)
        
        # Scrollbars
        h_scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        v_scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # Grid the treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Action buttons frame
        self.action_frame = ttk.Frame(self.parent_frame)
        self.action_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Buttons
        self.open_email_btn = ttk.Button(self.action_frame, text="Otwórz email", command=self.open_selected_email)
        self.open_email_btn.pack(side="left", padx=5)
        
        self.download_attachments_btn = ttk.Button(self.action_frame, text="Pobierz załączniki", command=self.download_attachments)
        self.download_attachments_btn.pack(side="left", padx=5)
        
        # Pagination frame
        self.pagination_frame = ttk.Frame(self.parent_frame)
        self.pagination_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        # Pagination controls
        self.prev_btn = ttk.Button(self.pagination_frame, text="< Poprzednia", command=self.prev_page)
        self.prev_btn.pack(side="left", padx=5)
        
        self.page_label = ttk.Label(self.pagination_frame, text="Strona 0 z 0")
        self.page_label.pack(side="left", padx=10)
        
        self.next_btn = ttk.Button(self.pagination_frame, text="Następna >", command=self.next_page)
        self.next_btn.pack(side="left", padx=5)
        
        # Results per page
        ttk.Label(self.pagination_frame, text="Wyników na stronę:").pack(side="left", padx=(20, 5))
        self.per_page_var = tk.StringVar(value="20")
        self.per_page_combo = ttk.Combobox(self.pagination_frame, textvariable=self.per_page_var, 
                                          values=["10", "20", "50", "100"], width=5, state="readonly")
        self.per_page_combo.pack(side="left", padx=5)
        self.per_page_combo.bind("<<ComboboxSelected>>", self.per_page_changed)
        
        # Results count
        self.count_label = ttk.Label(self.pagination_frame, text="Znaleziono: 0 wyników")
        self.count_label.pack(side="right", padx=10)
        
        # Double-click binding
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Initially disable buttons
        self.update_button_states()
    
    def display_results(self, results, page=0, per_page=20, total_count=0, total_pages=0):
        """Display search results in the tree"""
        self.results_data = results
        self.current_page = page
        self.per_page = per_page
        self.total_pages = total_pages
        self.total_count = total_count
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not results:
            # Insert placeholder item for no results
            self.tree.insert("", "end", values=("", "", "Nie znaleziono wiadomości spełniających kryteria", "", ""))
            self.update_button_states()
            self.update_pagination_display()
            return
        
        # Insert results
        for i, result in enumerate(results):
            date_str = result['datetime_received'].strftime('%Y-%m-%d %H:%M') if result['datetime_received'] else 'Brak daty'
            sender = result['sender'][:40] if len(result['sender']) > 40 else result['sender']
            subject = result['subject'][:60] if len(result['subject']) > 60 else result['subject']
            status = "Nieprzeczyt." if not result['is_read'] else "Przeczytane"
            attachments = f"{result['attachment_count']}" if result['has_attachments'] else "Brak"
            
            self.tree.insert("", "end", values=(date_str, sender, subject, status, attachments))
        
        self.update_button_states()
        self.update_pagination_display()
    
    def update_button_states(self):
        """Update button states based on selection and data"""
        selected_items = self.tree.selection()
        has_selection = len(selected_items) > 0 and len(self.results_data) > 0
        
        # Enable/disable action buttons based on selection
        state = "normal" if has_selection else "disabled"
        self.open_email_btn.config(state=state)
        self.download_attachments_btn.config(state=state)
        
        # Update pagination buttons
        self.prev_btn.config(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.config(state="normal" if self.current_page < self.total_pages - 1 else "disabled")
    
    def update_pagination_display(self):
        """Update pagination display"""
        self.page_label.config(text=f"Strona {self.current_page + 1} z {max(1, self.total_pages)}")
        self.count_label.config(text=f"Znaleziono: {self.total_count} wyników")
    
    def get_selected_result(self):
        """Get the selected result data"""
        selected_items = self.tree.selection()
        if not selected_items or not self.results_data:
            return None
        
        # Get the index of the selected item
        item = selected_items[0]
        index = self.tree.index(item)
        
        if index < len(self.results_data):
            return self.results_data[index]
        return None
    
    def on_double_click(self, event):
        """Handle double-click to open email"""
        self.open_selected_email()
    
    def open_selected_email(self):
        """Open the selected email in default email client"""
        result = self.get_selected_result()
        if not result:
            messagebox.showwarning("Brak zaznaczenia", "Proszę wybrać email do otwarcia.")
            return
        
        try:
            message = result.get('message_obj')
            if not message:
                messagebox.showerror("Błąd", "Nie można otworzyć wiadomości - brak danych.")
                return
            
            # Create EML format content
            eml_content = self._create_eml_content(message, result)
            
            # Create EML file
            temp_file = os.path.join(self.temp_dir, f"email_{result.get('message_id', 'unknown')}.eml")
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(eml_content)
            
            # Open in default application
            if os.name == 'nt':  # Windows
                os.startfile(temp_file)
            else:  # Unix/Linux
                os.system(f'xdg-open "{temp_file}"')
                
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć wiadomości: {str(e)}")
    
    def _create_eml_content(self, message, result):
        """Create proper EML format content for email"""
        # Start with basic headers
        eml_lines = []
        
        # Required headers
        eml_lines.append(f"From: {result['sender']}")
        eml_lines.append(f"Subject: {result['subject']}")
        eml_lines.append(f"Date: {result['datetime_received']}")
        
        # Additional headers if available
        if hasattr(message, 'to_recipients') and message.to_recipients:
            to_emails = []
            for recipient in message.to_recipients:
                if hasattr(recipient, 'email_address'):
                    to_emails.append(recipient.email_address)
                else:
                    to_emails.append(str(recipient))
            if to_emails:
                eml_lines.append(f"To: {', '.join(to_emails)}")
        
        if hasattr(message, 'cc_recipients') and message.cc_recipients:
            cc_emails = []
            for recipient in message.cc_recipients:
                if hasattr(recipient, 'email_address'):
                    cc_emails.append(recipient.email_address)
                else:
                    cc_emails.append(str(recipient))
            if cc_emails:
                eml_lines.append(f"Cc: {', '.join(cc_emails)}")
        
        # Message ID if available
        if hasattr(message, 'message_id') and message.message_id:
            eml_lines.append(f"Message-ID: {message.message_id}")
        
        # Content type
        eml_lines.append("Content-Type: text/plain; charset=utf-8")
        eml_lines.append("Content-Transfer-Encoding: 8bit")
        
        # Empty line separating headers from body
        eml_lines.append("")
        
        # Body content
        if hasattr(message, 'text_body') and message.text_body:
            eml_lines.append(message.text_body)
        else:
            eml_lines.append('Brak zawartości tekstowej')
        
        return '\n'.join(eml_lines)
    
    def download_attachments(self):
        """Download and open attachments for selected email"""
        result = self.get_selected_result()
        if not result:
            messagebox.showwarning("Brak zaznaczenia", "Proszę wybrać email z załącznikami.")
            return
        
        if not result.get('has_attachments'):
            messagebox.showinfo("Brak załączników", "Wybrany email nie ma załączników.")
            return
        
        try:
            # Clear temp directory of old attachments
            for file in os.listdir(self.temp_dir):
                if file.startswith('attachment_') or file.endswith('.eml'):
                    try:
                        os.remove(os.path.join(self.temp_dir, file))
                    except:
                        pass  # Ignore if file can't be removed
            
            attachments = result.get('attachments', [])
            if not attachments:
                messagebox.showinfo("Brak załączników", "Nie można pobrać załączników.")
                return
            
            downloaded_files = []
            used_filenames = set()  # Track used filenames to avoid conflicts
            
            for i, attachment in enumerate(attachments):
                try:
                    if hasattr(attachment, 'name') and hasattr(attachment, 'content'):
                        # Use original filename, preserve extension
                        original_filename = attachment.name or f"attachment_{i}.bin"
                        
                        # Create safe filename while preserving original name and extension
                        safe_filename = "".join(c for c in original_filename if c.isalnum() or c in (' ', '.', '_', '-', '(', ')'))
                        
                        # Handle duplicate filenames
                        if safe_filename in used_filenames:
                            name, ext = os.path.splitext(safe_filename)
                            counter = 1
                            while f"{name}_{counter}{ext}" in used_filenames:
                                counter += 1
                            safe_filename = f"{name}_{counter}{ext}"
                        
                        used_filenames.add(safe_filename)
                        filepath = os.path.join(self.temp_dir, safe_filename)
                        
                        # Write attachment content
                        with open(filepath, 'wb') as f:
                            f.write(attachment.content)
                        
                        downloaded_files.append(filepath)
                        
                except Exception as e:
                    print(f"Error downloading attachment: {e}")
                    continue
            
            if downloaded_files:
                # Open the temp directory
                if os.name == 'nt':  # Windows
                    os.startfile(self.temp_dir)
                else:  # Unix/Linux
                    os.system(f'xdg-open "{self.temp_dir}"')
                
                messagebox.showinfo("Załączniki pobrane", 
                                  f"Pobrano {len(downloaded_files)} załącznik(ów) do folderu tymczasowego.")
            else:
                messagebox.showerror("Błąd", "Nie udało się pobrać żadnych załączników.")
                
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas pobierania załączników: {str(e)}")
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            if hasattr(self, 'page_callback'):
                self.page_callback(self.current_page - 1)
    
    def next_page(self):
        """Go to next page"""
        if self.current_page < self.total_pages - 1:
            if hasattr(self, 'page_callback'):
                self.page_callback(self.current_page + 1)
    
    def per_page_changed(self, event=None):
        """Handle change in results per page"""
        try:
            new_per_page = int(self.per_page_var.get())
            if new_per_page != self.per_page and hasattr(self, 'per_page_callback'):
                self.per_page_callback(new_per_page)
        except ValueError:
            pass
    
    def set_page_callback(self, callback):
        """Set callback for page changes"""
        self.page_callback = callback
    
    def set_per_page_callback(self, callback):
        """Set callback for per page changes"""
        self.per_page_callback = callback
    
    def clear_results(self):
        """Clear all results"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results_data = []
        self.current_page = 0
        self.total_pages = 0
        self.total_count = 0
        self.update_button_states()
        self.update_pagination_display()
    
    def show_status(self, message):
        """Show status message in results area"""
        self.clear_results()
        self.tree.insert("", "end", values=("", "", message, "", ""))
        
    def bind_selection_change(self):
        """Bind selection change event"""
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.update_button_states())