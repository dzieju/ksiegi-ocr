"""
PDF History Display Window
Modal window for displaying PDF search history in a table format
"""
import tkinter as tk
from tkinter import ttk, messagebox


class PDFHistoryDisplayWindow:
    """Modal window to display PDF search history in a table format"""
    
    def __init__(self, parent, pdf_history_manager):
        """
        Initialize the history display window
        
        Args:
            parent: Parent widget
            pdf_history_manager: PDFHistoryManager instance
        """
        self.parent = parent
        self.pdf_history_manager = pdf_history_manager
        self.window = None
        
    def show(self):
        """Show the history display window"""
        try:
            # Create modal window
            self.window = tk.Toplevel(self.parent)
            self.window.title("Historia wyszukiwania PDF")
            self.window.geometry("800x600")
            self.window.resizable(True, True)
            
            # Make it modal
            self.window.transient(self.parent)
            self.window.grab_set()
            
            # Center the window
            self._center_window()
            
            # Create widgets
            self._create_widgets()
            
            # Load and display data
            self._load_history_data()
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd wyświetlania historii: {e}")
    
    def _center_window(self):
        """Center the window on the parent"""
        try:
            self.window.update_idletasks()
            
            # Get dimensions
            window_width = self.window.winfo_reqwidth()
            window_height = self.window.winfo_reqheight()
            
            # Get parent position and size
            parent_x = self.parent.winfo_rootx()
            parent_y = self.parent.winfo_rooty()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            
            # Calculate center position
            x = parent_x + (parent_width // 2) - (window_width // 2)
            y = parent_y + (parent_height // 2) - (window_height // 2)
            
            self.window.geometry(f"+{x}+{y}")
            
        except Exception:
            # If centering fails, just continue
            pass
    
    def _create_widgets(self):
        """Create the window widgets"""
        # Main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Historia wyszukiwania PDF", 
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Create treeview frame with scrollbars
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill="both", expand=True)
        
        # Create Treeview for table display
        columns = ("filename", "date", "sender_email")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        # Define column headings
        self.tree.heading("filename", text="Nazwa pliku PDF")
        self.tree.heading("date", text="Data")
        self.tree.heading("sender_email", text="Adres email nadawcy")
        
        # Configure column widths
        self.tree.column("filename", width=250, minwidth=150)
        self.tree.column("date", width=150, minwidth=100)
        self.tree.column("sender_email", width=300, minwidth=200)
        
        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Info label for showing record count
        self.info_label = ttk.Label(main_frame, text="", font=("Arial", 10, "italic"))
        self.info_label.pack(pady=(10, 0))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        
        # Refresh button
        refresh_button = ttk.Button(
            button_frame, 
            text="Odśwież", 
            command=self._refresh_data
        )
        refresh_button.pack(side="left", padx=(0, 10))
        
        # Close button
        close_button = ttk.Button(
            button_frame, 
            text="Zamknij", 
            command=self._close_window
        )
        close_button.pack(side="left")
        
        # Bind window close event
        self.window.protocol("WM_DELETE_WINDOW", self._close_window)
        
        # Bind Escape key to close
        self.window.bind('<Escape>', lambda e: self._close_window())
    
    def _load_history_data(self):
        """Load and display history data in the table"""
        try:
            # Clear existing data
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Get history data
            history_entries = self.pdf_history_manager.get_history_for_display()
            
            # Populate treeview
            for entry in history_entries:
                self.tree.insert("", "end", values=(
                    entry["filename"],
                    entry["date"],
                    entry["sender_email"]
                ))
            
            # Update info label
            count = len(history_entries)
            if count == 0:
                self.info_label.config(text="Brak zapisanej historii wyszukiwania PDF")
            elif count == 1:
                self.info_label.config(text="1 wpis w historii")
            else:
                self.info_label.config(text=f"{count} wpisów w historii")
                
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd ładowania danych historii: {e}")
            self.info_label.config(text="Błąd ładowania danych")
    
    def _refresh_data(self):
        """Refresh the history data"""
        self._load_history_data()
    
    def _close_window(self):
        """Close the window"""
        try:
            if self.window:
                self.window.grab_release()
                self.window.destroy()
                self.window = None
        except Exception:
            pass