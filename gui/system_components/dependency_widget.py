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
        
        self.refresh_btn = ttk.Button(header_frame, text="Odśwież", command=self.refresh_dependencies, width=10)
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
        
        # Add separator for visual clarity
        if index < len(self.results) - 1:
            separator = ttk.Separator(self.scrollable_frame, orient="horizontal")
            separator.pack(fill="x", padx=10, pady=2)
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status display."""
        if status == 'ok':
            return 'green'
        elif status == 'warning':
            return 'orange'
        else:
            return 'red'
    
    def get_results(self) -> List[Dict]:
        """Get current dependency check results."""
        return self.results
    
    def get_summary_text(self) -> str:
        """Get summary text for external display."""
        if not self.results:
            return "Sprawdzanie zależności..."
        
        summary = self.dependency_checker.get_summary()
        return f"{summary['emoji']} {summary['message']}"