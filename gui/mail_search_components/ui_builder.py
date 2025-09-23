"""
UI widget builder for mail search functionality
"""
import tkinter as tk
from tkinter import ttk


class MailSearchUI:
    """Handles UI creation for mail search tab"""
    
    def __init__(self, parent, variables, discover_callback):
        self.parent = parent
        self.vars = variables
        self.discover_callback = discover_callback
        
    def create_search_criteria_widgets(self):
        """Create search criteria input widgets"""
        # Title label
        title_label = ttk.Label(
            self.parent, 
            text="Przeszukiwanie Poczty", 
            font=("Arial", 12),
            foreground="blue"
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Search criteria fields
        ttk.Label(self.parent, text="Folder przeszukiwania (z podfolderami):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        folder_entry = ttk.Entry(self.parent, textvariable=self.vars['folder_path'], width=40)
        folder_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Add folder discovery button
        discover_button = ttk.Button(self.parent, text="Wykryj foldery", command=self.discover_callback)
        discover_button.grid(row=1, column=2, padx=5, pady=5)
        
        # Placeholder for folder exclusion checkboxes (will be added dynamically)
        # Row 2 is reserved for the checkbox frame
        
        ttk.Label(self.parent, text="Co ma szukać w temacie maila:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.vars['subject_search'], width=40).grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(self.parent, text="Nadawca maila:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.vars['sender'], width=40).grid(row=4, column=1, padx=5, pady=5)
        
        # Checkboxes
        ttk.Checkbutton(self.parent, text="Tylko nieprzeczytane", variable=self.vars['unread_only']).grid(row=5, column=0, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(self.parent, text="Tylko z załącznikami", variable=self.vars['attachments_required']).grid(row=5, column=1, sticky="w", padx=5, pady=5)
        
        # Attachment filters
        ttk.Label(self.parent, text="Nazwa załącznika (zawiera):").grid(row=6, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.vars['attachment_name'], width=40).grid(row=6, column=1, padx=5, pady=5)
        
        ttk.Label(self.parent, text="Rozszerzenie załącznika:").grid(row=7, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.vars['attachment_extension'], width=40).grid(row=7, column=1, padx=5, pady=5)
    
    def create_date_period_widgets(self):
        """Create date period selection widgets"""
        ttk.Label(self.parent, text="Okres wiadomości:", font=("Arial", 10, "bold")).grid(row=8, column=0, sticky="w", padx=5, pady=(15, 5))
        
        # Create frame for period buttons
        period_frame = ttk.Frame(self.parent)
        period_frame.grid(row=8, column=1, columnspan=2, sticky="w", padx=5, pady=(15, 5))
        
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
                variable=self.vars['selected_period'], 
                value=value
            ).grid(row=0, column=i, padx=5, sticky="w")
    
    def create_control_widgets(self, search_callback):
        """Create search button and status widgets"""
        search_frame = ttk.Frame(self.parent)
        search_frame.grid(row=9, column=0, columnspan=3, pady=20)
        
        search_button = ttk.Button(search_frame, text="Rozpocznij wyszukiwanie", command=search_callback)
        search_button.pack(side="left", padx=5)
        
        status_label = ttk.Label(search_frame, text="Gotowy", foreground="green")
        status_label.pack(side="left", padx=10)
        
        return search_button, status_label
    
    def create_results_widget(self):
        """Create results area widget - now returns a frame for the new ResultsDisplay"""
        results_frame = ttk.Frame(self.parent)
        results_frame.grid(row=10, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        
        # Configure grid weights for the parent to allow dynamic resizing
        self.parent.grid_rowconfigure(10, weight=1)  # Results row gets all extra space
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=1)
        self.parent.grid_columnconfigure(2, weight=1)
        
        return results_frame
    
    def create_folder_exclusion_checkboxes(self, folders, exclusion_vars):
        """Create checkboxes for folder exclusion"""
        if not folders:
            return None
            
        # Create frame for checkboxes
        frame = ttk.LabelFrame(self.parent, text="Wyklucz te foldery:", padding=5)
        frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        # Create checkboxes in multiple columns if there are many folders
        max_columns = 3
        folders_per_column = max(1, len(folders) // max_columns + (1 if len(folders) % max_columns else 0))
        
        for i, folder_name in enumerate(folders):
            var = tk.BooleanVar()
            exclusion_vars[folder_name] = var
            
            row = i % folders_per_column
            column = i // folders_per_column
            
            checkbox = ttk.Checkbutton(
                frame, 
                text=folder_name, 
                variable=var
            )
            checkbox.grid(row=row, column=column, sticky="w", padx=5, pady=2)
        
        # Configure grid weights for the frame
        for col in range(max_columns):
            frame.columnconfigure(col, weight=1)
        
        return frame