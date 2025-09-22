"""
UI widget builder for mail search functionality
"""
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


class MailSearchUI:
    """Handles UI creation for mail search tab"""
    
    def __init__(self, parent, variables):
        self.parent = parent
        self.vars = variables
        
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
        ttk.Label(self.parent, text="Folder przeszukiwania:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.vars['folder_path'], width=40).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self.parent, text="Co ma szukać w temacie maila:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.vars['subject_search'], width=40).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(self.parent, text="Nadawca maila:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.vars['sender'], width=40).grid(row=3, column=1, padx=5, pady=5)
        
        # Checkboxes
        ttk.Checkbutton(self.parent, text="Tylko nieprzeczytane", variable=self.vars['unread_only']).grid(row=4, column=0, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(self.parent, text="Tylko z załącznikami", variable=self.vars['attachments_required']).grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        # Attachment filters
        ttk.Label(self.parent, text="Nazwa załącznika (zawiera):").grid(row=5, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.vars['attachment_name'], width=40).grid(row=5, column=1, padx=5, pady=5)
        
        ttk.Label(self.parent, text="Rozszerzenie załącznika:").grid(row=6, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.vars['attachment_extension'], width=40).grid(row=6, column=1, padx=5, pady=5)
    
    def create_date_period_widgets(self):
        """Create date period selection widgets"""
        ttk.Label(self.parent, text="Okres wiadomości:", font=("Arial", 10, "bold")).grid(row=7, column=0, sticky="w", padx=5, pady=(15, 5))
        
        # Create frame for period buttons
        period_frame = ttk.Frame(self.parent)
        period_frame.grid(row=7, column=1, columnspan=2, sticky="w", padx=5, pady=(15, 5))
        
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
        search_frame.grid(row=8, column=0, columnspan=3, pady=20)
        
        search_button = ttk.Button(search_frame, text="Rozpocznij wyszukiwanie", command=search_callback)
        search_button.pack(side="left", padx=5)
        
        status_label = ttk.Label(search_frame, text="Gotowy", foreground="green")
        status_label.pack(side="left", padx=10)
        
        return search_button, status_label
    
    def create_results_widget(self):
        """Create results area widget"""
        results_area = ScrolledText(self.parent, wrap="word", width=120, height=25)
        results_area.grid(row=9, column=0, columnspan=3, padx=10, pady=10)
        return results_area