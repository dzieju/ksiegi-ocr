"""
Dependency checklist widget for System tab.
Displays system dependencies with status indicators and installation/update links.
"""
import tkinter as tk
from tkinter import ttk
import threading
import webbrowser
from typing import List, Dict
from tools.dependency_checker import get_dependency_checker


class DependencyWidget(ttk.Frame):
    """Widget for displaying system dependencies checklist."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.dependency_checker = get_dependency_checker()
        self.results = []
        self.checking = False
        
        self.setup_widgets()
        
        # Start initial check
        self.refresh_dependencies()
    
    def setup_widgets(self):
        """Setup the dependency widget UI."""
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=5, pady=(0, 10))
        
        title_label = ttk.Label(header_frame, text="Zależności środowiskowe:", font=("Arial", 10, "bold"))
        title_label.pack(side="left")
        
        # Buttons frame
        buttons_frame = ttk.Frame(header_frame)
        buttons_frame.pack(side="right")
        
        self.export_btn = ttk.Button(buttons_frame, text="Eksportuj", command=self.export_status, width=10)
        self.export_btn.pack(side="right", padx=(5, 0))
        
        self.refresh_btn = ttk.Button(buttons_frame, text="Odśwież zależności", command=self.refresh_dependencies, width=15)
        self.refresh_btn.pack(side="right")
        
        self.status_label = ttk.Label(header_frame, text="Sprawdzanie...", foreground="blue")
        self.status_label.pack(side="right", padx=(0, 10))
        
        # Scrollable frame for dependencies
        self.create_scrollable_frame()
    
    def create_scrollable_frame(self):
        """Create scrollable frame for dependencies list with details panel."""
        # Main container with two panels
        main_container = ttk.Frame(self)
        main_container.pack(fill="both", expand=True)
        
        # Left panel for dependencies list
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Create canvas and scrollbar for left panel
        canvas = tk.Canvas(left_panel, height=200)
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel support
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Right panel for dependency details
        self.details_panel = ttk.LabelFrame(main_container, text="Szczegóły zależności", width=300)
        self.details_panel.pack(side="right", fill="y", padx=(5, 0))
        self.details_panel.pack_propagate(False)  # Maintain fixed width
        
        # Details panel content
        self.details_content = ttk.Frame(self.details_panel)
        self.details_content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initial message in details panel
        self.details_info_label = ttk.Label(
            self.details_content, 
            text="Kliknij na zależność aby zobaczyć szczegóły, linki instalacji i instrukcje.",
            wraplength=280,
            justify="center",
            foreground="gray"
        )
        self.details_info_label.pack(expand=True)
    
    def refresh_dependencies(self):
        """Refresh dependency check in background thread."""
        if self.checking:
            return
            
        self.checking = True
        self.refresh_btn.config(state="disabled", text="Sprawdzam...")
        self.status_label.config(text="Sprawdzanie zależności...", foreground="blue")
        
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Show loading indicator
        loading_label = ttk.Label(self.scrollable_frame, text="🔄 Sprawdzanie zależności...", font=("Arial", 9))
        loading_label.pack(pady=10)
        
        def check_in_background():
            try:
                # Get fresh dependency results
                results = self.dependency_checker.check_all_dependencies()
                summary = self.dependency_checker.get_summary()
                
                # Update UI in main thread
                self.after(0, lambda: self._update_ui(results, summary))
            except Exception as e:
                self.after(0, lambda: self._handle_error(str(e)))
        
        thread = threading.Thread(target=check_in_background, daemon=True)
        thread.start()
    
    def _update_ui(self, results: List[Dict], summary: Dict):
        """Update UI with dependency results (called in main thread)."""
        # Clear loading indicator
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Update status
        self.status_label.config(text=summary['message'], 
                                foreground=self._get_status_color(summary['status']))
        
        # Create dependency items
        for i, result in enumerate(results):
            self._create_dependency_item(result, i)
        
        # Reset button
        self.refresh_btn.config(state="normal", text="Odśwież zależności")
        self.checking = False
        
        self.results = results
    
    def _handle_error(self, error_msg: str):
        """Handle error in dependency checking."""
        # Clear loading indicator
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        error_label = ttk.Label(self.scrollable_frame, text=f"❌ Błąd sprawdzania: {error_msg}", 
                               foreground="red", font=("Arial", 9))
        error_label.pack(pady=10)
        
        self.status_label.config(text="Błąd sprawdzania zależności", foreground="red")
        self.refresh_btn.config(state="normal", text="Odśwież zależności")
        self.checking = False
    
    def _create_dependency_item(self, result: Dict, index: int):
        """Create a single dependency item widget with click handler."""
        item_frame = ttk.Frame(self.scrollable_frame, relief="solid", borderwidth=1)
        item_frame.pack(fill="x", padx=5, pady=1)
        
        # Configure grid columns
        item_frame.columnconfigure(1, weight=1)
        
        # Status emoji
        status_label = ttk.Label(item_frame, text=result['emoji'], font=("Arial", 12))
        status_label.grid(row=0, column=0, padx=(8, 8), pady=8, sticky="w")
        
        # Dependency name and required indicator
        name_text = result['name']
        if result['required']:
            name_text += " (WYMAGANE)"
        
        name_label = ttk.Label(item_frame, text=name_text, font=("Arial", 9, "bold"))
        name_label.grid(row=0, column=1, sticky="w", pady=8)
        
        # Version/status info
        info_text = result['message']
        if result['version']:
            info_text = f"{result['version']} - {info_text}"
        
        info_label = ttk.Label(item_frame, text=info_text, 
                              font=("Arial", 8), 
                              foreground=self._get_status_color(result['status']))
        info_label.grid(row=1, column=1, sticky="w", padx=(0, 5))
        
        # Description
        desc_label = ttk.Label(item_frame, text=result['description'], 
                              font=("Arial", 8), foreground="gray")
        desc_label.grid(row=2, column=1, sticky="w", padx=(0, 5), pady=(0, 8))
        
        # Make entire item clickable
        def on_click(event=None):
            self._show_dependency_details(result)
            # Highlight selected item
            self._highlight_selected_item(item_frame)
        
        # Bind click events to all child widgets
        for widget in [item_frame, status_label, name_label, info_label, desc_label]:
            widget.bind("<Button-1>", on_click)
            widget.bind("<Enter>", lambda e, frame=item_frame: self._on_item_hover_enter(frame))
            widget.bind("<Leave>", lambda e, frame=item_frame: self._on_item_hover_leave(frame))
        
        # Add separator for visual clarity
        if index < len(self.results) - 1:
            separator = ttk.Separator(self.scrollable_frame, orient="horizontal")
            separator.pack(fill="x", padx=10, pady=2)
    
    def _show_dependency_details(self, result: Dict):
        """Show detailed information for a dependency in the right panel."""
        # Clear existing content
        for widget in self.details_content.winfo_children():
            widget.destroy()
        
        # Dependency header
        header_frame = ttk.Frame(self.details_content)
        header_frame.pack(fill="x", pady=(0, 10))
        
        # Emoji and name
        emoji_label = ttk.Label(header_frame, text=result['emoji'], font=("Arial", 16))
        emoji_label.pack(side="left")
        
        name_frame = ttk.Frame(header_frame)
        name_frame.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        name_label = ttk.Label(name_frame, text=result['name'], font=("Arial", 11, "bold"))
        name_label.pack(anchor="w")
        
        if result['required']:
            req_label = ttk.Label(name_frame, text="(WYMAGANE)", font=("Arial", 9), foreground="red")
            req_label.pack(anchor="w")
        
        # Status information
        status_frame = ttk.LabelFrame(self.details_content, text="Status", padding=10)
        status_frame.pack(fill="x", pady=(0, 10))
        
        status_text = result['message']
        if result['version']:
            status_text = f"Wersja: {result['version']}\nStatus: {result['message']}"
        
        status_label = ttk.Label(status_frame, text=status_text, 
                                foreground=self._get_status_color(result['status']),
                                font=("Arial", 9))
        status_label.pack(anchor="w")
        
        # Description
        desc_frame = ttk.LabelFrame(self.details_content, text="Opis", padding=10)
        desc_frame.pack(fill="x", pady=(0, 10))
        
        desc_label = ttk.Label(desc_frame, text=result['description'], 
                              wraplength=260, justify="left", font=("Arial", 9))
        desc_label.pack(anchor="w")
        
        # Links and actions
        actions_frame = ttk.LabelFrame(self.details_content, text="Linki i akcje", padding=10)
        actions_frame.pack(fill="x", pady=(0, 10))
        
        # Add appropriate action buttons based on status
        if result['status'] == 'error' and result.get('install_link'):
            # Missing dependency - show install link
            install_btn = ttk.Button(
                actions_frame, 
                text="📥 Otwórz stronę instalacji",
                command=lambda: self._open_link(result['install_link'])
            )
            install_btn.pack(fill="x", pady=(0, 5))
        
        if result['status'] == 'warning' and result.get('update_available') and result.get('update_link'):
            # Outdated dependency - show update link  
            update_btn = ttk.Button(
                actions_frame, 
                text="🔄 Otwórz stronę aktualizacji",
                command=lambda: self._open_link(result['update_link'])
            )
            update_btn.pack(fill="x", pady=(0, 5))
        elif result.get('update_link'):
            # Show general update link for OK dependencies
            update_btn = ttk.Button(
                actions_frame, 
                text="🔄 Sprawdź aktualizacje",
                command=lambda: self._open_link(result['update_link'])
            )
            update_btn.pack(fill="x", pady=(0, 5))
        
        # Installation command for missing required dependencies
        if result['required'] and result['status'] == 'error' and result.get('install_cmd'):
            cmd_frame = ttk.LabelFrame(self.details_content, text="Komenda instalacji", padding=10)
            cmd_frame.pack(fill="x", pady=(0, 10))
            
            cmd_text = tk.Text(cmd_frame, height=2, wrap="word", font=("Courier", 9))
            cmd_text.pack(fill="x")
            cmd_text.insert("1.0", result['install_cmd'])
            cmd_text.config(state="disabled")
            
            # Copy command button
            copy_btn = ttk.Button(
                cmd_frame, 
                text="📋 Kopiuj komendę",
                command=lambda: self._copy_to_clipboard(result['install_cmd'])
            )
            copy_btn.pack(fill="x", pady=(5, 0))
    
    def _open_link(self, url: str):
        """Open a URL in the default web browser."""
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Nie można otworzyć linku {url}: {e}")
    
    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            # Show brief feedback
            from tkinter import messagebox
            messagebox.showinfo("Skopiowano", "Komenda została skopiowana do schowka!")
        except Exception as e:
            print(f"Nie można skopiować do schowka: {e}")
    
    def _highlight_selected_item(self, selected_frame):
        """Highlight the selected dependency item."""
        # Reset all items to normal appearance
        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, ttk.Frame) and widget != selected_frame:
                widget.config(relief="solid", borderwidth=1)
        
        # Highlight selected item
        selected_frame.config(relief="solid", borderwidth=2)
    
    def _on_item_hover_enter(self, frame):
        """Handle mouse enter on dependency item."""
        if frame.cget("borderwidth") != "2":  # Not selected
            frame.config(relief="raised", borderwidth=1)
    
    def _on_item_hover_leave(self, frame):
        """Handle mouse leave on dependency item."""
        if frame.cget("borderwidth") != "2":  # Not selected
            frame.config(relief="solid", borderwidth=1)
    
    def _get_installation_hint(self, dependency_name: str) -> str:
        """Get installation hint for missing dependency."""
        hints = {
            'Tkinter': 'Zainstaluj tkinter: apt-get install python3-tk (Ubuntu/Debian)',
            'Tesseract OCR': 'Zainstaluj tesseract: apt-get install tesseract-ocr (Ubuntu/Debian)',
            'pdfplumber': 'pip install pdfplumber',
            'EasyOCR': 'pip install easyocr',
            'PaddleOCR': 'pip install paddlepaddle paddleocr',
            'PIL/Pillow': 'pip install Pillow',
            'OpenCV': 'pip install opencv-python',
            'pdf2image': 'pip install pdf2image',
            'exchangelib': 'pip install exchangelib',
            'tkcalendar': 'pip install tkcalendar',
            'pdfminer.six': 'pip install pdfminer.six',
            'Poppler': 'Zainstaluj poppler-utils: apt-get install poppler-utils (Ubuntu/Debian)'
        }
        return hints.get(dependency_name, '')
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status display."""
        if status == 'ok':
            return 'green'
        elif status == 'warning':
            return 'orange'
        else:
            return 'red'
    
    def export_status(self):
        """Export dependency status to a text file."""
        if not self.results:
            return
        
        try:
            from tkinter import filedialog
            import datetime
            
            # Get filename from user
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Eksportuj status zależności",
                initialvalue=f"ksiegi-ocr-dependencies-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
            )
            
            if not filename:
                return
            
            # Generate report
            report_lines = []
            report_lines.append("KSIEGI-OCR - Raport zależności środowiskowych")
            report_lines.append("=" * 50)
            report_lines.append(f"Data wygenerowania: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")
            
            # Summary
            summary = self.dependency_checker.get_summary()
            report_lines.append(f"PODSUMOWANIE: {summary['message']}")
            report_lines.append(f"Status ogólny: {summary['status']}")
            report_lines.append(f"Sprawdzono: {summary['total']} zależności")
            report_lines.append(f"OK: {summary['ok']}, Ostrzeżenia: {summary['warning']}, Błędy: {summary['error']}")
            report_lines.append("")
            
            # Detailed results
            report_lines.append("SZCZEGÓŁOWE WYNIKI:")
            report_lines.append("-" * 30)
            
            for result in self.results:
                status_symbol = result['emoji']
                required_text = " (WYMAGANE)" if result['required'] else ""
                version_text = f" - {result['version']}" if result['version'] else ""
                
                report_lines.append(f"{status_symbol} {result['name']}{required_text}")
                report_lines.append(f"   Status: {result['message']}{version_text}")
                report_lines.append(f"   Opis: {result['description']}")
                
                # Add installation/update information
                if result['status'] == 'error' and result.get('install_cmd'):
                    report_lines.append(f"   Instalacja: {result['install_cmd']}")
                if result.get('install_link'):
                    report_lines.append(f"   Link instalacji: {result['install_link']}")
                if result.get('update_available') and result.get('update_link'):
                    report_lines.append(f"   Link aktualizacji: {result['update_link']}")
                
                report_lines.append("")
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            
            # Show success message
            from tkinter import messagebox
            messagebox.showinfo("Eksport zakończony", f"Raport zapisano do pliku:\n{filename}")
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Błąd eksportu", f"Nie udało się wyeksportować raportu:\n{str(e)}")
    
    def get_results(self) -> List[Dict]:
        """Get current dependency check results."""
        return self.results
    
    def get_summary_text(self) -> str:
        """Get summary text for external display."""
        if not self.results:
            return "Sprawdzanie zależności..."
        
        summary = self.dependency_checker.get_summary()
        return f"{summary['emoji']} {summary['message']}"