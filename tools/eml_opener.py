"""
EML File Opening Utility - Handles different ways to open EML files
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
import platform
import webbrowser
import tempfile
import subprocess
import shutil
import html
from typing import Optional, List, Dict, Callable


class EmlOpeningDialog:
    """Dialog for selecting how to open EML files"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.result = None
        self.dialog = None
        
    def show_selection_dialog(self, file_path: str = None, eml_content: str = None) -> Optional[str]:
        """
        Show dialog to select how to open EML file
        Returns: 'integrated', 'browser', 'system', or None if cancelled
        """
        if not file_path and not eml_content:
            return None
            
        self.result = None
        self._create_dialog()
        self._populate_options(file_path, eml_content)
        
        # Center dialog on parent
        if self.parent:
            self.dialog.transient(self.parent)
            self.dialog.grab_set()
        
        # Wait for user choice
        self.dialog.wait_window()
        return self.result
    
    def _create_dialog(self):
        """Create the selection dialog"""
        self.dialog = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.dialog.title("Wybierz sposób otwarcia pliku EML")
        self.dialog.geometry("450x300")
        self.dialog.resizable(False, False)
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Jak chcesz otworzyć plik EML?", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Options frame
        self.options_frame = ttk.Frame(main_frame)
        self.options_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x")
        
        ttk.Button(buttons_frame, text="Anuluj", 
                  command=self._cancel).pack(side="right", padx=(10, 0))
    
    def _populate_options(self, file_path: str, eml_content: str):
        """Populate available opening options"""
        options = self._detect_available_options(file_path, eml_content)
        
        for i, option in enumerate(options):
            self._create_option_button(option, i)
    
    def _detect_available_options(self, file_path: str, eml_content: str) -> List[Dict]:
        """Detect available options for opening EML files"""
        options = []
        
        # Always available: Integrated viewer
        options.append({
            'id': 'integrated',
            'title': 'Zintegrowany czytnik',
            'description': 'Otworzyć w wbudowanym czytniku aplikacji\n• Podgląd tekstu i HTML\n• Obsługa załączników\n• Bezpieczne przeglądanie',
            'icon': '📧',
            'available': True
        })
        
        # Browser option
        options.append({
            'id': 'browser',
            'title': 'Przeglądarka internetowa',
            'description': 'Otworzyć w domyślnej przeglądarce\n• Pełne renderowanie HTML\n• Obsługa stylów CSS\n• Interaktywne linki',
            'icon': '🌐',
            'available': True
        })
        
        # System application
        system_app = self._detect_system_mail_app()
        options.append({
            'id': 'system',
            'title': 'Aplikacja systemowa',
            'description': f'Otworzyć w {system_app}\n• Domyślna aplikacja pocztowa\n• Pełna funkcjonalność mail\n• Integracja z systemem',
            'icon': '📮',
            'available': bool(system_app)
        })
        
        return options
    
    def _detect_system_mail_app(self) -> str:
        """Detect system default mail application"""
        system = platform.system().lower()
        
        if system == "windows":
            # Try to detect Outlook, Thunderbird, or other mail clients
            common_apps = [
                ("Outlook", r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE"),
                ("Outlook", r"C:\Program Files (x86)\Microsoft Office\root\Office16\OUTLOOK.EXE"),
                ("Thunderbird", r"C:\Program Files\Mozilla Thunderbird\thunderbird.exe"),
                ("Thunderbird", r"C:\Program Files (x86)\Mozilla Thunderbird\thunderbird.exe"),
            ]
            
            for name, path in common_apps:
                if os.path.exists(path):
                    return name
            
            return "Domyślna aplikacja pocztowa"
            
        elif system == "darwin":  # macOS
            return "Apple Mail"
            
        elif system == "linux":
            # Check for common Linux mail clients
            common_apps = ["thunderbird", "evolution", "kmail"]
            for app in common_apps:
                if shutil.which(app):
                    return app.capitalize()
            
            return "Domyślna aplikacja pocztowa"
        
        return "Aplikacja systemowa"
    
    def _create_option_button(self, option: Dict, index: int):
        """Create option button"""
        # Option frame
        option_frame = ttk.Frame(self.options_frame)
        option_frame.pack(fill="x", pady=5)
        
        # Button style based on availability
        state = "normal" if option['available'] else "disabled"
        
        # Create button with icon and text
        btn = ttk.Button(
            option_frame,
            text=f"{option['icon']} {option['title']}",
            command=lambda opt_id=option['id']: self._select_option(opt_id),
            state=state,
            width=25
        )
        btn.pack(side="left", padx=(0, 10))
        
        # Description label
        desc_label = ttk.Label(
            option_frame,
            text=option['description'],
            font=('Arial', 9),
            foreground="gray" if not option['available'] else "black"
        )
        desc_label.pack(side="left", fill="x", expand=True)
    
    def _select_option(self, option_id: str):
        """Handle option selection"""
        self.result = option_id
        self.dialog.destroy()
    
    def _cancel(self):
        """Handle cancel"""
        self.result = None
        self.dialog.destroy()


class EmlOpener:
    """Main class for opening EML files in different ways"""
    
    def __init__(self, parent=None):
        self.parent = parent
    
    def open_eml_file(self, file_path: str, method: str = None) -> bool:
        """
        Open EML file with specified method or show selection dialog
        
        Args:
            file_path: Path to EML file
            method: 'integrated', 'browser', 'system', or None for dialog
        
        Returns:
            True if successfully opened
        """
        if not os.path.exists(file_path):
            messagebox.showerror("Błąd", "Plik EML nie istnieje.")
            return False
        
        # Read EML content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                eml_content = f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            for encoding in ['cp1252', 'iso-8859-1', 'ascii']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        eml_content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                messagebox.showerror("Błąd", "Nie można odczytać pliku EML.")
                return False
        
        return self.open_eml_content(eml_content, method, file_path)
    
    def open_eml_content(self, eml_content: str, method: str = None, source_file: str = None) -> bool:
        """
        Open EML content with specified method or show selection dialog
        
        Args:
            eml_content: EML content as string
            method: 'integrated', 'browser', 'system', or None for dialog
            source_file: Original file path (optional)
        
        Returns:
            True if successfully opened
        """
        # If no method specified, show selection dialog
        if method is None:
            dialog = EmlOpeningDialog(self.parent)
            method = dialog.show_selection_dialog(source_file, eml_content)
            
            if method is None:  # User cancelled
                return False
        
        # Open with selected method
        try:
            if method == 'integrated':
                return self._open_with_integrated_viewer(eml_content)
            elif method == 'browser':
                return self._open_with_browser(eml_content)
            elif method == 'system':
                return self._open_with_system_app(eml_content, source_file)
            else:
                messagebox.showerror("Błąd", f"Nieznana metoda otwarcia: {method}")
                return False
                
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć pliku EML: {str(e)}")
            return False
    
    def _open_with_integrated_viewer(self, eml_content: str) -> bool:
        """Open with integrated EML viewer"""
        try:
            from tools.eml_viewer import EmlViewer
            
            viewer = EmlViewer(parent=self.parent)
            if viewer.open_eml_content(eml_content):
                viewer.show()
                return True
            else:
                messagebox.showerror("Błąd", "Nie można otworzyć w zintegrowanym czytniku.")
                return False
                
        except ImportError as e:
            messagebox.showerror("Błąd", f"Nie można załadować zintegrowanego czytnika: {str(e)}")
            return False
    
    def _open_with_browser(self, eml_content: str) -> bool:
        """Open EML content in browser"""
        try:
            # Parse email to extract HTML content
            import email
            import email.policy
            
            message = email.message_from_string(eml_content, policy=email.policy.default)
            html_content = self._extract_html_content(message)
            
            if not html_content:
                # If no HTML content, create HTML from plain text
                plain_content = self._extract_plain_content(message)
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{message.get('Subject', 'Email Content')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 10px; margin-bottom: 20px; }}
        .content {{ white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="header">
        <strong>Od:</strong> {message.get('From', 'Nieznany')}<br>
        <strong>Temat:</strong> {message.get('Subject', 'Brak tematu')}<br>
        <strong>Data:</strong> {message.get('Date', 'Nieznana')}
    </div>
    <div class="content">{html.escape(plain_content)}</div>
</body>
</html>"""
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_file = f.name
            
            # Open in browser
            webbrowser.open(f'file://{temp_file}')
            return True
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć w przeglądarce: {str(e)}")
            return False
    
    def _open_with_system_app(self, eml_content: str, source_file: str = None) -> bool:
        """Open with system default mail application"""
        try:
            # Use source file if available, otherwise create temporary file
            if source_file and os.path.exists(source_file):
                temp_file = source_file
                cleanup_temp = False
            else:
                # Create temporary EML file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.eml', delete=False, encoding='utf-8') as f:
                    f.write(eml_content)
                    temp_file = f.name
                cleanup_temp = True
            
            # Open with system default application
            system = platform.system().lower()
            
            if system == "windows":
                os.startfile(temp_file)
            elif system == "darwin":  # macOS
                subprocess.run(["open", temp_file])
            else:  # Linux and others
                subprocess.run(["xdg-open", temp_file])
            
            return True
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć w aplikacji systemowej: {str(e)}")
            return False
    
    def _extract_html_content(self, message) -> str:
        """Extract HTML content from email message"""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/html":
                    content_disposition = part.get('Content-Disposition', '')
                    if 'attachment' not in content_disposition:
                        try:
                            return part.get_content()
                        except:
                            payload = part.get_payload(decode=True)
                            if payload:
                                charset = part.get_content_charset() or 'utf-8'
                                return payload.decode(charset, errors='ignore')
        else:
            if message.get_content_type() == "text/html":
                try:
                    return message.get_content()
                except:
                    payload = message.get_payload(decode=True)
                    if payload:
                        charset = message.get_content_charset() or 'utf-8'
                        return payload.decode(charset, errors='ignore')
        
        return ""
    
    def _extract_plain_content(self, message) -> str:
        """Extract plain text content from email message"""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    content_disposition = part.get('Content-Disposition', '')
                    if 'attachment' not in content_disposition:
                        try:
                            return part.get_content()
                        except:
                            payload = part.get_payload(decode=True)
                            if payload:
                                charset = part.get_content_charset() or 'utf-8'
                                return payload.decode(charset, errors='ignore')
        else:
            if message.get_content_type() == "text/plain":
                try:
                    return message.get_content()
                except:
                    payload = message.get_payload(decode=True)
                    if payload:
                        charset = message.get_content_charset() or 'utf-8'
                        return payload.decode(charset, errors='ignore')
        
        return "Brak zawartości tekstowej"


def open_eml_file_with_dialog(file_path: str, parent=None) -> bool:
    """
    Convenience function to open EML file with selection dialog
    
    Args:
        file_path: Path to EML file
        parent: Parent window for dialog
    
    Returns:
        True if successfully opened
    """
    opener = EmlOpener(parent)
    return opener.open_eml_file(file_path)


def open_eml_content_with_dialog(eml_content: str, parent=None) -> bool:
    """
    Convenience function to open EML content with selection dialog
    
    Args:
        eml_content: EML content as string
        parent: Parent window for dialog
    
    Returns:
        True if successfully opened
    """
    opener = EmlOpener(parent)
    return opener.open_eml_content(eml_content)