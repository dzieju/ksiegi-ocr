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
        
    def create_search_criteria_widgets(self, save_pdf_callback=None):
        """Create search criteria input widgets"""
        # Title label
        title_label = ttk.Label(
            self.parent, 
            text="Przeszukiwanie Poczty", 
            font=("Arial", 12),
            foreground="blue"
        )
        title_label.pack(pady=10)
        
        # Folder frame
        folder_frame = ttk.Frame(self.parent)
        folder_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(folder_frame, text="Folder przeszukiwania (z podfolderami):").pack(side="left")
        folder_entry = ttk.Entry(folder_frame, textvariable=self.vars['folder_path'], width=40)
        folder_entry.pack(side="left", padx=5)
        
        # Add folder discovery button
        discover_button = ttk.Button(folder_frame, text="Wykryj foldery", command=self.discover_callback)
        discover_button.pack(side="left", padx=5)
        
        # Placeholder for folder exclusion checkboxes (will be added dynamically)
        
        # Subject search frame
        subject_frame = ttk.Frame(self.parent)
        subject_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(subject_frame, text="Czego mam szukać w temacie maila:").pack(side="left")
        ttk.Entry(subject_frame, textvariable=self.vars['subject_search'], width=40).pack(side="left", padx=5)
        
        # Body search frame
        body_frame = ttk.Frame(self.parent)
        body_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(body_frame, text="Czego mam szukać w treści maila:").pack(side="left")
        ttk.Entry(body_frame, textvariable=self.vars['body_search'], width=40).pack(side="left", padx=5)
        
        # PDF search frame
        pdf_frame = ttk.Frame(self.parent)
        pdf_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(pdf_frame, text="Wyszukaj w pliku PDF (automatyczny zapis):").pack(side="left")
        ttk.Entry(pdf_frame, textvariable=self.vars['pdf_search_text'], width=40).pack(side="left", padx=5)
        
        # Sender frame
        sender_frame = ttk.Frame(self.parent)
        sender_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(sender_frame, text="Nadawca maila:").pack(side="left")
        ttk.Entry(sender_frame, textvariable=self.vars['sender'], width=40).pack(side="left", padx=5)
        
        # Checkboxes frame
        checkboxes_frame = ttk.Frame(self.parent)
        checkboxes_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Checkbutton(checkboxes_frame, text="Tylko nieprzeczytane", variable=self.vars['unread_only']).pack(side="left", padx=5)
        ttk.Checkbutton(checkboxes_frame, text="Tylko z załącznikami", variable=self.vars['attachments_required']).pack(side="left", padx=5)
        ttk.Checkbutton(checkboxes_frame, text="Tylko bez załączników", variable=self.vars['no_attachments_only']).pack(side="left", padx=5)
        
        # Attachment name frame
        attachment_name_frame = ttk.Frame(self.parent)
        attachment_name_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(attachment_name_frame, text="Nazwa załącznika (zawiera):").pack(side="left")
        ttk.Entry(attachment_name_frame, textvariable=self.vars['attachment_name'], width=40).pack(side="left", padx=5)
        
        # Attachment extension frame
        attachment_ext_frame = ttk.Frame(self.parent)
        attachment_ext_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(attachment_ext_frame, text="Rozszerzenie załącznika:").pack(side="left")
        ttk.Entry(attachment_ext_frame, textvariable=self.vars['attachment_extension'], width=40).pack(side="left", padx=5)
    
        return None  # No longer returning save_pdf_button
    
    def create_date_period_widgets(self):
        """Create date period selection widgets"""
        # Date period frame
        date_frame = ttk.Frame(self.parent)
        date_frame.pack(fill="x", padx=5, pady=(15, 5))
        
        ttk.Label(date_frame, text="Okres wiadomości:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        # Create frame for period buttons
        period_frame = ttk.Frame(date_frame)
        period_frame.pack(side="left", padx=5)
        
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
            ).pack(side="left", padx=5)
    
    def create_control_widgets(self, search_callback):
        """Create search button and status widgets"""
        search_frame = ttk.Frame(self.parent)
        search_frame.pack(fill="x", pady=20)
        
        search_button = ttk.Button(search_frame, text="Rozpocznij wyszukiwanie", command=search_callback)
        search_button.pack(side="left", padx=5)
        
        status_label = ttk.Label(search_frame, text="Gotowy", foreground="green")
        status_label.pack(side="left", padx=10)
        
        return search_button, status_label
    
    def create_results_widget(self):
        """Create results area widget - now returns a frame for the new ResultsDisplay"""
        results_frame = ttk.Frame(self.parent)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        return results_frame
    
    def create_folder_exclusion_checkboxes(self, folders, exclusion_vars, hide_callback=None, uncheck_all_callback=None, check_all_callback=None, is_visible=True):
        """Create checkboxes for folder exclusion with hide/show functionality"""
        if not folders:
            return None, None
            
        # Create main container frame
        container_frame = ttk.Frame(self.parent)
        container_frame.pack(fill="x", padx=5, pady=5)
        
        # Create header frame with title and hide/show button
        header_frame = ttk.Frame(container_frame)
        header_frame.pack(fill="x", pady=(0, 5))
        
        # Title label
        title_label = ttk.Label(header_frame, text="Wyklucz te foldery:", font=("Arial", 10, "bold"))
        title_label.pack(side="left")
        
        # Hide/Show button
        toggle_text = "Ukryj" if is_visible else "Pokaż"
        toggle_button = ttk.Button(header_frame, text=toggle_text, width=8)
        if hide_callback:
            toggle_button.config(command=lambda: hide_callback(toggle_button))
        toggle_button.pack(side="right", padx=(10, 0))
        
        # Save settings button
        save_button = ttk.Button(header_frame, text="Zapisz ustawienia", width=15)
        save_button.pack(side="right", padx=(5, 0))
        
        # Check all button
        check_all_button = ttk.Button(header_frame, text="Zaznacz wszystko", width=15)
        if check_all_callback:
            check_all_button.config(command=check_all_callback)
        check_all_button.pack(side="right", padx=(5, 0))
        
        # Uncheck all button
        uncheck_all_button = ttk.Button(header_frame, text="Odznacz wszystkie", width=15)
        if uncheck_all_callback:
            uncheck_all_button.config(command=uncheck_all_callback)
        uncheck_all_button.pack(side="right", padx=(5, 0))
        
        # Create frame for checkboxes
        checkboxes_frame = ttk.Frame(container_frame, relief="sunken", borderwidth=1)
        checkboxes_frame.pack(fill="x", padx=5, pady=5)
        
        # Initially hide or show based on is_visible parameter
        if not is_visible:
            checkboxes_frame.pack_forget()
        
        # Create checkboxes in multiple columns if there are many folders
        max_columns = 3
        folders_per_column = max(1, len(folders) // max_columns + (1 if len(folders) % max_columns else 0))
        
        # Create column frames for organizing checkboxes
        column_frames = []
        for col in range(max_columns):
            col_frame = ttk.Frame(checkboxes_frame)
            col_frame.pack(side="left", fill="both", expand=True, padx=2)
            column_frames.append(col_frame)
        
        for i, folder_name in enumerate(folders):
            var = tk.BooleanVar()
            exclusion_vars[folder_name] = var
            
            column = i // folders_per_column
            if column >= max_columns:
                column = max_columns - 1
            
            checkbox = ttk.Checkbutton(
                column_frames[column], 
                text=folder_name, 
                variable=var
            )
            checkbox.pack(anchor="w", padx=5, pady=2)
        
        return container_frame, (toggle_button, save_button, check_all_button, uncheck_all_button, checkboxes_frame)