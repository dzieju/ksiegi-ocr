"""
UI widget builder for mail search functionality
"""
import tkinter as tk
from tkinter import ttk


class MailSearchUI:
    """Handles UI creation for mail search tab"""
    
    def __init__(self, parent, variables, discover_callback, pdf_folder_callback=None, clear_history_callback=None, show_history_callback=None):
        self.parent = parent
        self.vars = variables
        self.discover_callback = discover_callback
        self.pdf_folder_callback = pdf_folder_callback
        self.clear_history_callback = clear_history_callback
        self.show_history_callback = show_history_callback
        
    def create_search_criteria_widgets(self, save_pdf_callback=None):
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
        
        ttk.Label(self.parent, text="Czego mam szukać w temacie maila:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.vars['subject_search'], width=40).grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(self.parent, text="Czego mam szukać w treści maila:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.vars['body_search'], width=40).grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(self.parent, text="Wyszukaj w pliku PDF (automatyczny zapis):").grid(row=5, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.vars['pdf_search_text'], width=40).grid(row=5, column=1, padx=5, pady=5)
        
        # Add PDF folder selection button
        if self.pdf_folder_callback:
            pdf_folder_button = ttk.Button(self.parent, text="Wybierz folder", command=self.pdf_folder_callback)
            pdf_folder_button.grid(row=5, column=2, padx=5, pady=5)
        
        # PDF search history controls - create a frame for better layout
        pdf_history_frame = ttk.Frame(self.parent)
        pdf_history_frame.grid(row=5, column=3, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Checkbox for skipping searched PDFs
        skip_checkbox = ttk.Checkbutton(
            pdf_history_frame, 
            text="Pomijaj już wyszukane PDF-y", 
            variable=self.vars['skip_searched_pdfs']
        )
        skip_checkbox.grid(row=0, column=0, padx=5, sticky="w")
        
        # Button for clearing history
        if self.clear_history_callback:
            clear_history_button = ttk.Button(
                pdf_history_frame, 
                text="Wyczyść historię", 
                command=self.clear_history_callback,
                width=15
            )
            clear_history_button.grid(row=0, column=1, padx=5, sticky="w")
        
        # Button for showing history
        if self.show_history_callback:
            show_history_button = ttk.Button(
                pdf_history_frame, 
                text="Pokaż Historię", 
                command=self.show_history_callback,
                width=15
            )
            show_history_button.grid(row=0, column=2, padx=5, sticky="w")
        
        ttk.Label(self.parent, text="Nadawca maila:").grid(row=6, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.vars['sender'], width=40).grid(row=6, column=1, padx=5, pady=5)
        
        # Checkboxes
        ttk.Checkbutton(self.parent, text="Tylko nieprzeczytane", variable=self.vars['unread_only']).grid(row=7, column=0, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(self.parent, text="Tylko z załącznikami", variable=self.vars['attachments_required']).grid(row=7, column=1, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(self.parent, text="Tylko bez załączników", variable=self.vars['no_attachments_only']).grid(row=7, column=2, sticky="w", padx=5, pady=5)
        
        # Attachment filters
        ttk.Label(self.parent, text="Nazwa załącznika (zawiera):").grid(row=8, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.vars['attachment_name'], width=40).grid(row=8, column=1, padx=5, pady=5)
        
        ttk.Label(self.parent, text="Rozszerzenie załącznika:").grid(row=9, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.vars['attachment_extension'], width=40).grid(row=9, column=1, padx=5, pady=5)
    
        return None  # No longer returning save_pdf_button
    
    def create_date_period_widgets(self):
        """Create date period selection widgets"""
        ttk.Label(self.parent, text="Okres wiadomości:", font=("Arial", 10, "bold")).grid(row=10, column=0, sticky="w", padx=5, pady=(15, 5))
        
        # Create frame for period buttons
        period_frame = ttk.Frame(self.parent)
        period_frame.grid(row=10, column=1, columnspan=2, sticky="w", padx=5, pady=(15, 5))
        
        # Period selection buttons
        periods = [
            ("wszystkie", "Wszystkie"),
            ("ostatni_tydzien", "Ostatni tydzień"),
            ("ostatnie_2_tygodnie", "Ostatnie 2 tygodnie"),
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
        search_frame.grid(row=11, column=0, columnspan=3, pady=20)
        
        search_button = ttk.Button(search_frame, text="Rozpocznij wyszukiwanie", command=search_callback)
        search_button.pack(side="left", padx=5)
        
        status_label = ttk.Label(search_frame, text="Gotowy", foreground="green")
        status_label.pack(side="left", padx=10)
        
        # Create info frame for account and folder information
        info_frame = ttk.Frame(search_frame)
        info_frame.pack(side="right", padx=10)
        
        # Add account type indicator
        account_info_label = ttk.Label(info_frame, text="Konto: Sprawdzanie...", foreground="blue", font=("Arial", 9, "italic"))
        account_info_label.pack(anchor="e")
        
        # Add folder info indicator
        folder_info_label = ttk.Label(info_frame, text="Folder: Brak", foreground="gray", font=("Arial", 9, "italic"))
        folder_info_label.pack(anchor="e")
        
        return search_button, status_label, account_info_label, folder_info_label
    
    def create_results_widget(self):
        """Create results area widget - now returns a frame for the new ResultsDisplay"""
        results_frame = ttk.Frame(self.parent)
        results_frame.grid(row=12, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        
        # Configure grid weights for the parent to allow dynamic resizing
        self.parent.grid_rowconfigure(12, weight=1)  # Results row gets all extra space
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=1)
        self.parent.grid_columnconfigure(2, weight=1)
        
        return results_frame
    
    def create_folder_exclusion_checkboxes(self, folders, exclusion_vars, hide_callback=None, uncheck_all_callback=None, check_all_callback=None, is_visible=True):
        """Create checkboxes for folder exclusion with hide/show functionality"""
        if not folders:
            return None, None
            
        # Create main container frame
        container_frame = ttk.Frame(self.parent)
        container_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        # Create header frame with title and hide/show button
        header_frame = ttk.Frame(container_frame)
        header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5))
        
        # Title label
        title_label = ttk.Label(header_frame, text="Wyklucz te foldery:", font=("Arial", 10, "bold"))
        title_label.grid(row=0, column=0, sticky="w")
        
        # Hide/Show button
        toggle_text = "Ukryj" if is_visible else "Pokaż"
        toggle_button = ttk.Button(header_frame, text=toggle_text, width=8)
        if hide_callback:
            toggle_button.config(command=lambda: hide_callback(toggle_button))
        toggle_button.grid(row=0, column=1, sticky="e", padx=(10, 0))
        
        # Save settings button
        save_button = ttk.Button(header_frame, text="Zapisz ustawienia", width=15)
        save_button.grid(row=0, column=2, sticky="e", padx=(5, 0))
        
        # Check all button
        check_all_button = ttk.Button(header_frame, text="Zaznacz wszystko", width=15)
        if check_all_callback:
            check_all_button.config(command=check_all_callback)
        check_all_button.grid(row=0, column=3, sticky="e", padx=(5, 0))
        
        # Uncheck all button
        uncheck_all_button = ttk.Button(header_frame, text="Odznacz wszystkie", width=15)
        if uncheck_all_callback:
            uncheck_all_button.config(command=uncheck_all_callback)
        uncheck_all_button.grid(row=0, column=4, sticky="e", padx=(5, 0))
        
        # Configure header grid
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Create frame for checkboxes
        checkboxes_frame = ttk.Frame(container_frame, relief="sunken", borderwidth=1)
        checkboxes_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        # Initially hide or show based on is_visible parameter
        if not is_visible:
            checkboxes_frame.grid_remove()
        
        # Create checkboxes in multiple columns if there are many folders
        max_columns = 3
        folders_per_column = max(1, len(folders) // max_columns + (1 if len(folders) % max_columns else 0))
        
        for i, folder_name in enumerate(folders):
            var = tk.BooleanVar()
            exclusion_vars[folder_name] = var
            
            row = i % folders_per_column
            column = i // folders_per_column
            
            checkbox = ttk.Checkbutton(
                checkboxes_frame, 
                text=folder_name, 
                variable=var
            )
            checkbox.grid(row=row, column=column, sticky="w", padx=5, pady=2)
        
        # Configure grid weights for the checkboxes frame
        for col in range(max_columns):
            checkboxes_frame.columnconfigure(col, weight=1)
            
        # Configure main container grid
        container_frame.grid_columnconfigure(0, weight=1)
        
        return container_frame, (toggle_button, save_button, check_all_button, uncheck_all_button, checkboxes_frame)