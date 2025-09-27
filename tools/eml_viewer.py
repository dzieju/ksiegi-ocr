"""
EML Viewer Tool - Integrated EML file viewer for the application
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import email
import email.policy
import os
import tempfile
import subprocess
import platform
import webbrowser
import html
import base64
import quopri
from typing import Optional, List, Dict, Any

# Try to import tkhtmlview for HTML rendering
try:
    from tkhtmlview import HTMLLabel
    HTML_VIEWER_AVAILABLE = True
except ImportError:
    HTML_VIEWER_AVAILABLE = False


class EmlViewer:
    """Integrated EML file viewer with attachment support"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.window = None
        self.email_message = None
        
    def open_eml_file(self, file_path: str) -> bool:
        """Open and display an EML file"""
        try:
            with open(file_path, 'rb') as f:
                # Use the modern email policy for better parsing
                self.email_message = email.message_from_bytes(f.read(), policy=email.policy.default)
            
            self._create_viewer_window()
            self._populate_content()
            return True
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć pliku EML: {str(e)}")
            return False
    
    def open_eml_content(self, eml_content: str) -> bool:
        """Open and display EML content from string"""
        try:
            self.email_message = email.message_from_string(eml_content, policy=email.policy.default)
            self._create_viewer_window()
            self._populate_content()
            return True
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można przetworzyć zawartości EML: {str(e)}")
            return False
    
    def _create_viewer_window(self):
        """Create the main viewer window"""
        self.window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.window.title("Podgląd wiadomości EML")
        self.window.geometry("800x600")
        
        # Make window resizable
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        # Create main frame
        main_frame = ttk.Frame(self.window)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Header frame for email metadata
        header_frame = ttk.LabelFrame(main_frame, text="Informacje o wiadomości", padding=10)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Content notebook for different views
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew")
        
        # Store references for later use
        self.header_frame = header_frame
        
        # Add close button
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        ttk.Button(button_frame, text="Zamknij", command=self.window.destroy).pack(side="right")
        
    def _populate_content(self):
        """Populate the viewer with email content"""
        if not self.email_message:
            return
            
        self._populate_header()
        self._populate_body()
        self._populate_attachments()
        
    def _populate_header(self):
        """Populate header information"""
        msg = self.email_message
        
        # Clear existing header content
        for widget in self.header_frame.winfo_children():
            widget.destroy()
            
        # Configure grid
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        # Add header fields
        headers = [
            ("Od:", msg.get('From', 'Nieznany')),
            ("Do:", msg.get('To', 'Nieznany')),
            ("Temat:", msg.get('Subject', 'Brak tematu')),
            ("Data:", msg.get('Date', 'Nieznana')),
        ]
        
        if msg.get('Cc'):
            headers.append(("Kopia:", msg.get('Cc')))
            
        for row, (label, value) in enumerate(headers):
            ttk.Label(self.header_frame, text=label, font=('Arial', 9, 'bold')).grid(
                row=row, column=0, sticky="nw", padx=(0, 10), pady=2
            )
            
            # Handle long values with text wrapping
            value_label = ttk.Label(self.header_frame, text=str(value), font=('Arial', 9))
            value_label.grid(row=row, column=1, sticky="ew", pady=2)
    
    def _populate_body(self):
        """Populate email body content"""
        # Extract both plain text and HTML content
        plain_content, html_content = self._extract_body_both()
        
        # Create text body tab
        body_frame = ttk.Frame(self.notebook)
        self.notebook.add(body_frame, text="Treść (tekst)")
        
        body_frame.grid_rowconfigure(0, weight=1)
        body_frame.grid_columnconfigure(0, weight=1)
        
        # Text widget with scrollbar
        text_widget = scrolledtext.ScrolledText(
            body_frame, 
            wrap=tk.WORD, 
            font=('Arial', 10),
            state='normal'
        )
        text_widget.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        text_widget.insert('1.0', plain_content)
        text_widget.config(state='disabled')  # Make read-only
        
        # Create HTML body tab if HTML content exists
        if html_content and html_content.strip():
            self._create_html_tab(html_content)
        
    def _populate_attachments(self):
        """Populate attachments tab if any exist"""
        attachments = self._extract_attachments()
        
        if not attachments:
            return
            
        # Create attachments tab
        att_frame = ttk.Frame(self.notebook)
        self.notebook.add(att_frame, text=f"Załączniki ({len(attachments)})")
        
        att_frame.grid_rowconfigure(0, weight=1)
        att_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview for attachments
        tree = ttk.Treeview(att_frame, columns=("Size", "Type"), show="tree headings")
        tree.heading("#0", text="Nazwa pliku")
        tree.heading("Size", text="Rozmiar")
        tree.heading("Type", text="Typ")
        
        tree.column("#0", width=300)
        tree.column("Size", width=100)
        tree.column("Type", width=150)
        
        # Add scrollbars
        v_scroll = ttk.Scrollbar(att_frame, orient="vertical", command=tree.yview)
        h_scroll = ttk.Scrollbar(att_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Grid the treeview and scrollbars
        tree.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=5)
        v_scroll.grid(row=0, column=1, sticky="ns", pady=5)
        h_scroll.grid(row=1, column=0, sticky="ew", padx=(5, 0))
        
        # Add attachments to tree
        for i, attachment in enumerate(attachments):
            size_str = f"{len(attachment['content']):,} bytes" if attachment['content'] else "Unknown"
            tree.insert("", "end", text=attachment['filename'], 
                       values=(size_str, attachment['content_type']),
                       tags=(str(i),))
        
        # Button frame for attachment actions
        btn_frame = ttk.Frame(att_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Zapisz zaznaczony", 
                  command=lambda: self._save_attachment(tree, attachments)).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Zapisz wszystkie", 
                  command=lambda: self._save_all_attachments(attachments)).pack(side="left", padx=5)
    
    def _create_html_tab(self, html_content: str):
        """Create HTML tab with appropriate viewer"""
        html_frame = ttk.Frame(self.notebook)
        self.notebook.add(html_frame, text="Treść (HTML)")
        
        html_frame.grid_rowconfigure(1, weight=1)
        html_frame.grid_columnconfigure(0, weight=1)
        
        # Always show "Open in browser" button for full HTML experience
        btn_frame = ttk.Frame(html_frame)
        btn_frame.grid(row=0, column=0, sticky="ew", pady=(5, 5), padx=5)
        
        ttk.Button(btn_frame, text="Otwórz w przeglądarce", 
                  command=lambda: self._open_html_in_browser(html_content)).pack(side="left")
        
        if HTML_VIEWER_AVAILABLE:
            # Use tkhtmlview if available
            try:
                html_widget = HTMLLabel(html_frame, html=html_content)
                html_widget.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
                return
            except Exception as e:
                print(f"Error using tkhtmlview: {e}")
        
        # Fallback: Show HTML source when tkhtmlview is not available
        fallback_frame = ttk.Frame(html_frame)
        fallback_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        fallback_frame.grid_rowconfigure(0, weight=1)
        fallback_frame.grid_columnconfigure(0, weight=1)
        
        # HTML source view
        html_text = scrolledtext.ScrolledText(
            fallback_frame, 
            wrap=tk.WORD, 
            font=('Courier', 9),
            state='normal'
        )
        html_text.grid(row=0, column=0, sticky="nsew")
        html_text.insert('1.0', html_content)
        html_text.config(state='disabled')
    
    def _open_html_in_browser(self, html_content: str):
        """Open HTML content in default browser"""
        try:
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                # Add basic HTML structure if not present
                if not html_content.strip().lower().startswith('<!doctype') and not html_content.strip().lower().startswith('<html'):
                    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Email Content</title>
</head>
<body>
{html_content}
</body>
</html>"""
                f.write(html_content)
                temp_file = f.name
            
            # Open in default browser
            webbrowser.open(f'file://{temp_file}')
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć HTML w przeglądarce: {str(e)}")
    
    def _extract_body_both(self) -> tuple[str, str]:
        """Extract both plain text and HTML body content"""
        if not self.email_message:
            return "Brak zawartości", ""
            
        plain_text = ""
        html_content = ""
        
        try:
            if self.email_message.is_multipart():
                for part in self.email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = part.get('Content-Disposition', '')
                    
                    # Skip attachments
                    if 'attachment' in content_disposition:
                        continue
                    
                    if content_type == "text/plain" and not plain_text:
                        plain_text = self._decode_part_content(part)
                    elif content_type == "text/html" and not html_content:
                        html_content = self._decode_part_content(part)
            else:
                content_type = self.email_message.get_content_type()
                if content_type == "text/plain":
                    plain_text = self._decode_part_content(self.email_message)
                elif content_type == "text/html":
                    html_content = self._decode_part_content(self.email_message)
                    
        except Exception as e:
            plain_text = f"Błąd odczytu zawartości: {str(e)}"
        
        # If we have HTML but no plain text, create plain text from HTML
        if html_content and not plain_text:
            plain_text = self._html_to_text(html_content)
        
        # If we have neither, provide default message
        if not plain_text and not html_content:
            plain_text = "Nie można wyświetlić zawartości wiadomości"
            
        return plain_text, html_content
    
    def _decode_part_content(self, part) -> str:
        """Decode email part content with proper charset and encoding handling"""
        try:
            # Try modern method first
            content = part.get_content()
            if isinstance(content, str):
                return content
        except:
            pass
        
        # Fallback to manual decoding
        try:
            payload = part.get_payload()
            encoding = part.get('Content-Transfer-Encoding', '').lower()
            charset = part.get_content_charset() or 'utf-8'
            
            # Handle different transfer encodings
            if encoding == 'base64':
                if isinstance(payload, str):
                    payload = base64.b64decode(payload)
                else:
                    payload = base64.b64decode(payload)
            elif encoding == 'quoted-printable':
                if isinstance(payload, str):
                    payload = quopri.decodestring(payload.encode())
                else:
                    payload = quopri.decodestring(payload)
            elif isinstance(payload, str):
                # No special encoding, but might need charset conversion
                return payload
            
            # Decode bytes to string with proper charset
            if isinstance(payload, bytes):
                # Try specified charset first
                try:
                    return payload.decode(charset)
                except (UnicodeDecodeError, LookupError):
                    # Fallback to common charsets
                    for fallback_charset in ['utf-8', 'cp1252', 'iso-8859-1', 'ascii']:
                        try:
                            return payload.decode(fallback_charset, errors='ignore')
                        except (UnicodeDecodeError, LookupError):
                            continue
                    
                    # Last resort: decode with errors ignored
                    return payload.decode('utf-8', errors='ignore')
            
            return str(payload)
            
        except Exception as e:
            return f"Błąd dekodowania zawartości: {str(e)}"
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text"""
        try:
            import re
            # Unescape HTML entities
            text = html.unescape(html_content)
            # Remove HTML tags
            text = re.sub('<[^<]+?>', ' ', text)
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        except Exception:
            return html_content
    def _extract_body(self) -> str:
        """Extract email body text (legacy method for compatibility)"""
        plain_text, _ = self._extract_body_both()
        return plain_text
    
    def _extract_attachments(self) -> List[Dict[str, Any]]:
        """Extract attachment information"""
        attachments = []
        
        if not self.email_message or not self.email_message.is_multipart():
            return attachments
            
        try:
            for part in self.email_message.walk():
                # Skip the multipart container itself
                if part.is_multipart():
                    continue
                    
                content_disposition = part.get('Content-Disposition', '')
                filename = part.get_filename()
                
                # Check if this is an attachment
                if 'attachment' in content_disposition or filename:
                    if not filename:
                        # Try to generate a filename if none exists
                        content_type = part.get_content_type()
                        if content_type:
                            ext = content_type.split('/')[-1]
                            filename = f"attachment.{ext}"
                        else:
                            filename = "attachment.bin"
                    
                    try:
                        # Try modern method first
                        content = part.get_content()
                        if isinstance(content, str):
                            content = content.encode('utf-8')
                    except:
                        # Fallback to older method
                        try:
                            content = part.get_payload(decode=True)
                            if not content:
                                content = b""
                        except:
                            content = b""
                    
                    attachments.append({
                        'filename': filename,
                        'content_type': part.get_content_type() or 'application/octet-stream',
                        'content': content,
                        'part': part
                    })
                        
        except Exception as e:
            print(f"Error extracting attachments: {e}")
            
        return attachments
    
    def _save_attachment(self, tree, attachments):
        """Save selected attachment"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Brak zaznaczenia", "Proszę wybrać załącznik do zapisania.")
            return
            
        # Get attachment index from tags
        item = selection[0]
        tags = tree.item(item, 'tags')
        if not tags:
            return
            
        try:
            att_index = int(tags[0])
            attachment = attachments[att_index]
            
            # Ask user where to save
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                title="Zapisz załącznik",
                initialfile=attachment['filename'],
                defaultextension=""
            )
            
            if filename:
                with open(filename, 'wb') as f:
                    f.write(attachment['content'])
                messagebox.showinfo("Zapisano", f"Załącznik zapisany jako: {filename}")
                
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać załącznika: {str(e)}")
    
    def _save_all_attachments(self, attachments):
        """Save all attachments to a directory"""
        if not attachments:
            return
            
        from tkinter import filedialog
        directory = filedialog.askdirectory(title="Wybierz folder do zapisania załączników")
        
        if directory:
            saved_count = 0
            for attachment in attachments:
                try:
                    filepath = os.path.join(directory, attachment['filename'])
                    # Handle duplicate filenames
                    counter = 1
                    base_path = filepath
                    while os.path.exists(filepath):
                        name, ext = os.path.splitext(base_path)
                        filepath = f"{name}_{counter}{ext}"
                        counter += 1
                    
                    with open(filepath, 'wb') as f:
                        f.write(attachment['content'])
                    saved_count += 1
                    
                except Exception as e:
                    print(f"Error saving attachment {attachment['filename']}: {e}")
                    
            messagebox.showinfo("Zapisano", f"Zapisano {saved_count} z {len(attachments)} załączników.")
    
    def show(self):
        """Show the viewer window"""
        if self.window:
            self.window.lift()
            self.window.focus_force()


def main():
    """Test function"""
    root = tk.Tk()
    root.withdraw()  # Hide root window
    
    from tkinter import filedialog
    file_path = filedialog.askopenfilename(
        title="Wybierz plik EML",
        filetypes=[("EML files", "*.eml"), ("All files", "*.*")]
    )
    
    if file_path:
        viewer = EmlViewer(root)
        if viewer.open_eml_file(file_path):
            viewer.show()
            root.mainloop()


if __name__ == "__main__":
    main()