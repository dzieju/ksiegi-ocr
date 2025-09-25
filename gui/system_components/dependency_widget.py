"""
Dependency checklist widget for System tab.
Displays system dependencies with status indicators.
"""
import tkinter as tk
from tkinter import ttk
import threading
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
        
        self.refresh_btn = ttk.Button(buttons_frame, text="Odśwież", command=self.refresh_dependencies, width=10)
        self.refresh_btn.pack(side="right")
        
        self.status_label = ttk.Label(header_frame, text="Sprawdzanie...", foreground="blue")
        self.status_label.pack(side="right", padx=(0, 10))
        
        # Scrollable frame for dependencies
        self.create_scrollable_frame()
    
    def create_scrollable_frame(self):
        """Create scrollable frame for dependencies list."""
        # Create canvas and scrollbar
        canvas = tk.Canvas(self, height=200)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
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
        self.refresh_btn.config(state="normal", text="Odśwież")
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
        self.refresh_btn.config(state="normal", text="Odśwież")
        self.checking = False
    
    def _create_dependency_item(self, result: Dict, index: int):
        """Create a single dependency item widget."""
        item_frame = ttk.Frame(self.scrollable_frame)
        item_frame.pack(fill="x", padx=5, pady=1)
        
        # Configure grid columns
        item_frame.columnconfigure(1, weight=1)
        
        # Status emoji
        status_label = ttk.Label(item_frame, text=result['emoji'], font=("Arial", 12))
        status_label.grid(row=0, column=0, padx=(0, 8), sticky="w")
        
        # Dependency name and required indicator
        name_text = result['name']
        if result['required']:
            name_text += " (WYMAGANE)"
        
        name_label = ttk.Label(item_frame, text=name_text, font=("Arial", 9, "bold"))
        name_label.grid(row=0, column=1, sticky="w")
        
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
        desc_label.grid(row=2, column=1, sticky="w", padx=(0, 5))
        
        # Add installation hint for missing required dependencies
        if result['required'] and result['status'] == 'error':
            hint_text = self._get_installation_hint(result['name'])
            if hint_text:
                hint_label = ttk.Label(item_frame, text=f"💡 {hint_text}", 
                                      font=("Arial", 8), foreground="blue")
                hint_label.grid(row=3, column=1, sticky="w", padx=(0, 5))
        
        # Add separator for visual clarity
        if index < len(self.results) - 1:
            separator = ttk.Separator(self.scrollable_frame, orient="horizontal")
            separator.pack(fill="x", padx=10, pady=2)
    
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
                
                # Add installation hint if needed
                if result['required'] and result['status'] == 'error':
                    hint = self._get_installation_hint(result['name'])
                    if hint:
                        report_lines.append(f"   Instalacja: {hint}")
                
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