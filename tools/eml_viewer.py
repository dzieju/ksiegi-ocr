"""
EML file viewer module for reading and displaying email files.
Supports headers, content (plain text/HTML), inline images, attachments,
and full MIME encoding.
"""
import os
import base64
import email
import email.utils
import email.header
import mimetypes
from email.message import EmailMessage
from typing import Dict, List, Tuple, Optional, Any
import tempfile
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk
import webbrowser


class EMLAttachment:
    """Represents an email attachment"""
    
    def __init__(self, filename: str, content: bytes, content_type: str, content_id: Optional[str] = None):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self.content_id = content_id  # For inline attachments
        self.size = len(content)
    
    def save_to_file(self, filepath: str) -> bool:
        """Save attachment to specified file path"""
        try:
            with open(filepath, 'wb') as f:
                f.write(self.content)
            return True
        except Exception as e:
            print(f"Error saving attachment {self.filename}: {e}")
            return False


class EMLReader:
    """EML file reader with full MIME support"""
    
    def __init__(self):
        self.raw_email = None
        self.parsed_email = None
        self.headers = {}
        self.plain_text_body = ""
        self.html_body = ""
        self.attachments = []
        self.inline_attachments = []
    
    def load_eml_file(self, filepath: str) -> bool:
        """Load and parse EML file"""
        try:
            with open(filepath, 'rb') as f:
                self.raw_email = f.read()
            
            # Parse the email
            self.parsed_email = email.message_from_bytes(self.raw_email)
            
            # Extract headers
            self._extract_headers()
            
            # Extract body content
            self._extract_body_content()
            
            # Extract attachments
            self._extract_attachments()
            
            return True
            
        except Exception as e:
            print(f"Error loading EML file {filepath}: {e}")
            return False
    
    def _extract_headers(self):
        """Extract email headers"""
        self.headers = {}
        
        # Common headers to extract
        header_fields = [
            'From', 'To', 'Cc', 'Bcc', 'Subject', 'Date', 
            'Message-ID', 'Reply-To', 'Return-Path', 'X-Mailer',
            'Content-Type', 'MIME-Version'
        ]
        
        for header in header_fields:
            value = self.parsed_email.get(header)
            if value:
                # Decode header if needed
                decoded_header = email.header.decode_header(value)
                decoded_value = ""
                for part, encoding in decoded_header:
                    if isinstance(part, bytes):
                        if encoding:
                            decoded_value += part.decode(encoding)
                        else:
                            decoded_value += part.decode('utf-8', errors='ignore')
                    else:
                        decoded_value += part
                self.headers[header] = decoded_value
        
        # Add any additional headers
        for key, value in self.parsed_email.items():
            if key not in self.headers:
                self.headers[key] = value
    
    def _extract_body_content(self):
        """Extract plain text and HTML body content"""
        self.plain_text_body = ""
        self.html_body = ""
        
        if self.parsed_email.is_multipart():
            for part in self.parsed_email.walk():
                content_type = part.get_content_type()
                content_disposition = part.get('Content-Disposition', '')
                
                # Skip attachments
                if 'attachment' in content_disposition:
                    continue
                
                if content_type == 'text/plain':
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            self.plain_text_body += payload.decode(charset)
                        except:
                            self.plain_text_body += payload.decode('utf-8', errors='ignore')
                
                elif content_type == 'text/html':
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            self.html_body += payload.decode(charset)
                        except:
                            self.html_body += payload.decode('utf-8', errors='ignore')
        else:
            # Single part message
            content_type = self.parsed_email.get_content_type()
            payload = self.parsed_email.get_payload(decode=True)
            
            if payload:
                charset = self.parsed_email.get_content_charset() or 'utf-8'
                try:
                    content = payload.decode(charset)
                except:
                    content = payload.decode('utf-8', errors='ignore')
                
                if content_type == 'text/plain':
                    self.plain_text_body = content
                elif content_type == 'text/html':
                    self.html_body = content
                else:
                    self.plain_text_body = content
    
    def _extract_attachments(self):
        """Extract attachments and inline content"""
        self.attachments = []
        self.inline_attachments = []
        
        if not self.parsed_email.is_multipart():
            return
        
        for part in self.parsed_email.walk():
            content_disposition = part.get('Content-Disposition', '')
            content_type = part.get_content_type()
            content_id = part.get('Content-ID')
            
            # Skip text parts that are not attachments
            if content_type.startswith('text/') and 'attachment' not in content_disposition:
                continue
            
            # Get filename
            filename = part.get_filename()
            if not filename and 'attachment' in content_disposition:
                # Try to extract filename from Content-Disposition
                import re
                match = re.search(r'filename[*]?=([^;]+)', content_disposition)
                if match:
                    filename = match.group(1).strip('"\'')
            
            if not filename:
                # Generate filename based on content type
                ext = mimetypes.guess_extension(content_type) or '.bin'
                filename = f'attachment{ext}'
            
            # Get content
            payload = part.get_payload(decode=True)
            if payload:
                attachment = EMLAttachment(filename, payload, content_type, content_id)
                
                # Determine if it's inline or regular attachment
                if content_id or ('inline' in content_disposition):
                    self.inline_attachments.append(attachment)
                else:
                    self.attachments.append(attachment)
    
    def get_preferred_body(self) -> str:
        """Get preferred body content (HTML if available, otherwise plain text)"""
        if self.html_body.strip():
            return self.html_body
        return self.plain_text_body
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of email content"""
        return {
            'subject': self.headers.get('Subject', 'No Subject'),
            'from': self.headers.get('From', 'Unknown Sender'),
            'to': self.headers.get('To', 'Unknown Recipient'),
            'date': self.headers.get('Date', 'Unknown Date'),
            'has_html': bool(self.html_body.strip()),
            'has_plain_text': bool(self.plain_text_body.strip()),
            'attachment_count': len(self.attachments),
            'inline_attachment_count': len(self.inline_attachments),
            'total_size': sum(att.size for att in self.attachments + self.inline_attachments)
        }


class EMLViewerGUI:
    """GUI for viewing EML files"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.eml_reader = EMLReader()
        self.current_file = None
        self.create_widgets()
    
    def create_widgets(self):
        """Create the EML viewer GUI widgets"""
        # Main container
        self.main_frame = ttk.Frame(self.parent_frame)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Title and open button
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill="x", pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="Czytnik plików EML", font=("Arial", 12, "bold"))
        title_label.pack(side="left")
        
        self.open_button = ttk.Button(title_frame, text="Otwórz plik EML", command=self.open_eml_file)
        self.open_button.pack(side="right")
        
        # Content notebook for organizing display
        self.content_notebook = ttk.Notebook(self.main_frame)
        self.content_notebook.pack(fill="both", expand=True)
        
        # Headers tab
        self.headers_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(self.headers_frame, text="Nagłówki")
        self._create_headers_widgets()
        
        # Content tab
        self.content_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(self.content_frame, text="Treść")
        self._create_content_widgets()
        
        # Attachments tab
        self.attachments_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(self.attachments_frame, text="Załączniki")
        self._create_attachments_widgets()
        
        # Initially disable tabs until file is loaded
        for i in range(self.content_notebook.index("end")):
            self.content_notebook.tab(i, state="disabled")
    
    def _create_headers_widgets(self):
        """Create headers display widgets"""
        # Scrollable text widget for headers
        headers_scroll_frame = ttk.Frame(self.headers_frame)
        headers_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.headers_text = tk.Text(headers_scroll_frame, wrap="word", height=20)
        headers_scrollbar = ttk.Scrollbar(headers_scroll_frame, orient="vertical", command=self.headers_text.yview)
        self.headers_text.configure(yscrollcommand=headers_scrollbar.set)
        
        self.headers_text.pack(side="left", fill="both", expand=True)
        headers_scrollbar.pack(side="right", fill="y")
    
    def _create_content_widgets(self):
        """Create content display widgets"""
        # Frame for content type selection
        content_type_frame = ttk.Frame(self.content_frame)
        content_type_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(content_type_frame, text="Typ wyświetlania:").pack(side="left")
        
        self.content_type_var = tk.StringVar(value="auto")
        content_type_combo = ttk.Combobox(content_type_frame, textvariable=self.content_type_var, 
                                         values=["auto", "html", "text"], state="readonly")
        content_type_combo.pack(side="left", padx=(5, 0))
        content_type_combo.bind("<<ComboboxSelected>>", self._on_content_type_change)
        
        # Button to open in external browser (for HTML)
        self.external_button = ttk.Button(content_type_frame, text="Otwórz w przeglądarce", 
                                         command=self.open_in_browser)
        self.external_button.pack(side="right")
        
        # Scrollable text widget for content
        content_scroll_frame = ttk.Frame(self.content_frame)
        content_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.content_text = tk.Text(content_scroll_frame, wrap="word", height=20)
        content_scrollbar = ttk.Scrollbar(content_scroll_frame, orient="vertical", command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=content_scrollbar.set)
        
        self.content_text.pack(side="left", fill="both", expand=True)
        content_scrollbar.pack(side="right", fill="y")
    
    def _create_attachments_widgets(self):
        """Create attachments display widgets"""
        # Attachments list
        attachments_list_frame = ttk.Frame(self.attachments_frame)
        attachments_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Treeview for attachments
        self.attachments_tree = ttk.Treeview(attachments_list_frame, 
                                           columns=("Name", "Type", "Size"), 
                                           show="headings", height=10)
        
        self.attachments_tree.heading("Name", text="Nazwa pliku")
        self.attachments_tree.heading("Type", text="Typ")
        self.attachments_tree.heading("Size", text="Rozmiar")
        
        self.attachments_tree.column("Name", width=300)
        self.attachments_tree.column("Type", width=150)
        self.attachments_tree.column("Size", width=100)
        
        attachments_scrollbar = ttk.Scrollbar(attachments_list_frame, orient="vertical", 
                                            command=self.attachments_tree.yview)
        self.attachments_tree.configure(yscrollcommand=attachments_scrollbar.set)
        
        self.attachments_tree.pack(side="left", fill="both", expand=True)
        attachments_scrollbar.pack(side="right", fill="y")
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.attachments_frame)
        buttons_frame.pack(fill="x", padx=5, pady=5)
        
        self.save_attachment_button = ttk.Button(buttons_frame, text="Zapisz zaznaczony", 
                                               command=self.save_selected_attachment)
        self.save_attachment_button.pack(side="left", padx=(0, 5))
        
        self.save_all_button = ttk.Button(buttons_frame, text="Zapisz wszystkie", 
                                        command=self.save_all_attachments)
        self.save_all_button.pack(side="left")
    
    def open_eml_file(self):
        """Open EML file with choice dialog"""
        # File selection dialog
        file_path = filedialog.askopenfilename(
            title="Wybierz plik EML",
            filetypes=[("Email files", "*.eml"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Choice dialog for opening method
        choice = messagebox.askyesnocancel(
            "Sposób otwarcia",
            "Jak chcesz otworzyć plik EML?\n\n"
            "TAK - Otwórz w zintegrowanym czytniku\n"
            "NIE - Otwórz w zewnętrznej aplikacji\n"
            "ANULUJ - Nie otwieraj"
        )
        
        if choice is None:  # Cancel
            return
        elif choice is False:  # External application
            self._open_in_external_app(file_path)
        else:  # Integrated viewer
            self._load_eml_in_viewer(file_path)
    
    def _open_in_external_app(self, file_path: str):
        """Open EML file in external application"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            else:  # Unix/Linux
                os.system(f'xdg-open "{file_path}"')
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć pliku w zewnętrznej aplikacji: {e}")
    
    def _load_eml_in_viewer(self, file_path: str):
        """Load EML file in integrated viewer"""
        if self.eml_reader.load_eml_file(file_path):
            self.current_file = file_path
            self._display_eml_content()
            
            # Enable tabs
            for i in range(self.content_notebook.index("end")):
                self.content_notebook.tab(i, state="normal")
            
            messagebox.showinfo("Sukces", f"Wczytano plik EML: {os.path.basename(file_path)}")
        else:
            messagebox.showerror("Błąd", f"Nie można wczytać pliku EML: {file_path}")
    
    def _display_eml_content(self):
        """Display EML content in GUI"""
        self._display_headers()
        self._display_content()
        self._display_attachments()
    
    def _display_headers(self):
        """Display email headers"""
        self.headers_text.delete(1.0, tk.END)
        
        # Display most important headers first
        priority_headers = ['Subject', 'From', 'To', 'Cc', 'Date', 'Message-ID']
        
        for header in priority_headers:
            if header in self.eml_reader.headers:
                self.headers_text.insert(tk.END, f"{header}: {self.eml_reader.headers[header]}\n")
        
        # Add separator
        self.headers_text.insert(tk.END, "\n" + "="*50 + "\n\n")
        
        # Display all other headers
        for header, value in self.eml_reader.headers.items():
            if header not in priority_headers:
                self.headers_text.insert(tk.END, f"{header}: {value}\n")
    
    def _display_content(self):
        """Display email content"""
        self._update_content_display()
    
    def _update_content_display(self):
        """Update content display based on selected type"""
        self.content_text.delete(1.0, tk.END)
        
        content_type = self.content_type_var.get()
        
        if content_type == "auto":
            content = self.eml_reader.get_preferred_body()
        elif content_type == "html":
            content = self.eml_reader.html_body
        else:  # text
            content = self.eml_reader.plain_text_body
        
        if content.strip():
            self.content_text.insert(tk.END, content)
        else:
            self.content_text.insert(tk.END, "Brak zawartości tego typu.")
    
    def _display_attachments(self):
        """Display attachments list"""
        # Clear existing items
        for item in self.attachments_tree.get_children():
            self.attachments_tree.delete(item)
        
        # Add regular attachments
        for att in self.eml_reader.attachments:
            size_str = self._format_size(att.size)
            self.attachments_tree.insert("", "end", values=(att.filename, att.content_type, size_str),
                                       tags=("attachment",))
        
        # Add inline attachments
        for att in self.eml_reader.inline_attachments:
            size_str = self._format_size(att.size)
            name = f"{att.filename} (inline)"
            self.attachments_tree.insert("", "end", values=(name, att.content_type, size_str),
                                       tags=("inline",))
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _on_content_type_change(self, event):
        """Handle content type selection change"""
        self._update_content_display()
    
    def open_in_browser(self):
        """Open HTML content in external browser"""
        if not self.eml_reader.html_body.strip():
            messagebox.showwarning("Ostrzeżenie", "Brak zawartości HTML do wyświetlenia.")
            return
        
        try:
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(self.eml_reader.html_body)
                temp_file = f.name
            
            # Open in browser
            webbrowser.open(f'file://{temp_file}')
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć w przeglądarce: {e}")
    
    def save_selected_attachment(self):
        """Save selected attachment to file"""
        selection = self.attachments_tree.selection()
        if not selection:
            messagebox.showwarning("Ostrzeżenie", "Proszę wybrać załącznik do zapisania.")
            return
        
        item = selection[0]
        values = self.attachments_tree.item(item, "values")
        filename = values[0].replace(" (inline)", "")  # Remove inline marker
        
        # Find the attachment
        attachment = None
        for att in self.eml_reader.attachments + self.eml_reader.inline_attachments:
            if att.filename == filename:
                attachment = att
                break
        
        if not attachment:
            messagebox.showerror("Błąd", "Nie można znaleźć załącznika.")
            return
        
        # Ask for save location
        save_path = filedialog.asksaveasfilename(
            title="Zapisz załącznik",
            initialname=attachment.filename,
            defaultextension=os.path.splitext(attachment.filename)[1]
        )
        
        if save_path:
            if attachment.save_to_file(save_path):
                messagebox.showinfo("Sukces", f"Załącznik zapisany jako: {save_path}")
            else:
                messagebox.showerror("Błąd", "Nie można zapisać załącznika.")
    
    def save_all_attachments(self):
        """Save all attachments to a directory"""
        if not self.eml_reader.attachments and not self.eml_reader.inline_attachments:
            messagebox.showwarning("Ostrzeżenie", "Brak załączników do zapisania.")
            return
        
        # Ask for directory
        save_dir = filedialog.askdirectory(title="Wybierz folder do zapisania załączników")
        if not save_dir:
            return
        
        saved_count = 0
        all_attachments = self.eml_reader.attachments + self.eml_reader.inline_attachments
        
        for attachment in all_attachments:
            save_path = os.path.join(save_dir, attachment.filename)
            
            # Handle filename conflicts
            counter = 1
            original_path = save_path
            while os.path.exists(save_path):
                name, ext = os.path.splitext(original_path)
                save_path = f"{name}_{counter}{ext}"
                counter += 1
            
            if attachment.save_to_file(save_path):
                saved_count += 1
        
        messagebox.showinfo("Ukończono", f"Zapisano {saved_count} z {len(all_attachments)} załączników.")