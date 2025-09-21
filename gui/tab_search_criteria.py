"""
Search Criteria Tab - Zakładka Kryteria Wyszukiwania

This tab provides a comprehensive interface for defining search criteria,
saving/loading criteria sets, and executing searches based on the defined parameters.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
from datetime import datetime, date, timedelta
from typing import List, Optional
from models.search_criteria import SearchCriteria, SearchCriteriaManager


class TabSearchCriteria(ttk.Frame):
    """Search Criteria Tab for managing and executing advanced searches."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Initialize models
        self.criteria = SearchCriteria()
        self.criteria_manager = SearchCriteriaManager()
        
        # Variables
        self.text_query_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.amount_min_var = tk.StringVar()
        self.amount_max_var = tk.StringVar()
        self.include_attachments_var = tk.BooleanVar(value=True)
        self.case_sensitive_var = tk.BooleanVar(value=False)
        self.whole_words_only_var = tk.BooleanVar(value=False)
        self.search_in_subject_var = tk.BooleanVar(value=True)
        self.search_in_body_var = tk.BooleanVar(value=True)
        self.search_in_attachments_var = tk.BooleanVar(value=True)
        
        # Selected criteria for saving/loading
        self.selected_criteria_var = tk.StringVar()
        
        self.setup_ui()
        self.load_saved_criteria_list()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Create main container with scrollable frame
        canvas = tk.Canvas(self)
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
        
        # Main content frame
        main_frame = self.scrollable_frame
        
        # Title
        title_label = ttk.Label(main_frame, text="Kryteria Wyszukiwania", 
                               font=("TkDefaultFont", 14, "bold"))
        title_label.pack(pady=(10, 20))
        
        # Create sections
        self.create_basic_search_section(main_frame)
        self.create_date_range_section(main_frame)
        self.create_amount_range_section(main_frame)
        self.create_search_options_section(main_frame)
        self.create_folder_filters_section(main_frame)
        self.create_file_extensions_section(main_frame)
        self.create_actions_section(main_frame)
        self.create_saved_criteria_section(main_frame)
        
        # Bind variable changes to update criteria
        self.bind_variable_changes()
    
    def create_basic_search_section(self, parent):
        """Create basic search parameters section."""
        section_frame = ttk.LabelFrame(parent, text="Podstawowe Parametry Wyszukiwania", 
                                     padding="10")
        section_frame.pack(fill="x", padx=10, pady=5)
        
        # Text query
        ttk.Label(section_frame, text="Tekst do wyszukania:").grid(row=0, column=0, 
                                                                   sticky="w", padx=5, pady=5)
        text_entry = ttk.Entry(section_frame, textvariable=self.text_query_var, width=40)
        text_entry.grid(row=0, column=1, padx=5, pady=5, columnspan=2)
        
        # Category
        ttk.Label(section_frame, text="Kategoria:").grid(row=1, column=0, 
                                                         sticky="w", padx=5, pady=5)
        category_combo = ttk.Combobox(section_frame, textvariable=self.category_var, 
                                    values=["", "Faktury", "Umowy", "Korespondencja", 
                                           "Dokumenty", "Raporty", "Inne"], 
                                    state="readonly", width=15)
        category_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Clear button
        ttk.Button(section_frame, text="Wyczyść", 
                  command=self.clear_basic_search).grid(row=1, column=2, 
                                                       padx=5, pady=5, sticky="e")
    
    def create_date_range_section(self, parent):
        """Create date range selection section."""
        section_frame = ttk.LabelFrame(parent, text="Zakres Dat", padding="10")
        section_frame.pack(fill="x", padx=10, pady=5)
        
        # Date from
        ttk.Label(section_frame, text="Data od:").grid(row=0, column=0, 
                                                      sticky="w", padx=5, pady=5)
        self.date_from_var = tk.StringVar()
        date_from_entry = ttk.Entry(section_frame, textvariable=self.date_from_var, 
                                   width=12)
        date_from_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(section_frame, text="📅", 
                  command=lambda: self.select_date("from")).grid(row=0, column=2, 
                                                                 padx=2, pady=5)
        
        # Date to
        ttk.Label(section_frame, text="Data do:").grid(row=0, column=3, 
                                                      sticky="w", padx=5, pady=5)
        self.date_to_var = tk.StringVar()
        date_to_entry = ttk.Entry(section_frame, textvariable=self.date_to_var, 
                                 width=12)
        date_to_entry.grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(section_frame, text="📅", 
                  command=lambda: self.select_date("to")).grid(row=0, column=5, 
                                                               padx=2, pady=5)
        
        # Quick date selection buttons
        quick_frame = ttk.Frame(section_frame)
        quick_frame.grid(row=1, column=0, columnspan=6, pady=10)
        
        ttk.Button(quick_frame, text="Ostatni tydzień", 
                  command=lambda: self.set_quick_date("week")).pack(side="left", padx=2)
        ttk.Button(quick_frame, text="Ostatni miesiąc", 
                  command=lambda: self.set_quick_date("month")).pack(side="left", padx=2)
        ttk.Button(quick_frame, text="Ostatnie 3 miesiące", 
                  command=lambda: self.set_quick_date("3months")).pack(side="left", padx=2)
        ttk.Button(quick_frame, text="Wyczyść daty", 
                  command=self.clear_dates).pack(side="left", padx=2)
    
    def create_amount_range_section(self, parent):
        """Create amount range selection section."""
        section_frame = ttk.LabelFrame(parent, text="Zakres Kwot", padding="10")
        section_frame.pack(fill="x", padx=10, pady=5)
        
        # Amount from
        ttk.Label(section_frame, text="Kwota od:").grid(row=0, column=0, 
                                                        sticky="w", padx=5, pady=5)
        ttk.Entry(section_frame, textvariable=self.amount_min_var, 
                 width=15).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(section_frame, text="PLN").grid(row=0, column=2, 
                                                 sticky="w", padx=2, pady=5)
        
        # Amount to
        ttk.Label(section_frame, text="Kwota do:").grid(row=0, column=3, 
                                                        sticky="w", padx=5, pady=5)
        ttk.Entry(section_frame, textvariable=self.amount_max_var, 
                 width=15).grid(row=0, column=4, padx=5, pady=5)
        ttk.Label(section_frame, text="PLN").grid(row=0, column=5, 
                                                 sticky="w", padx=2, pady=5)
    
    def create_search_options_section(self, parent):
        """Create search options section."""
        section_frame = ttk.LabelFrame(parent, text="Opcje Wyszukiwania", padding="10")
        section_frame.pack(fill="x", padx=10, pady=5)
        
        # Search location options
        location_frame = ttk.Frame(section_frame)
        location_frame.pack(fill="x", pady=5)
        
        ttk.Label(location_frame, text="Szukaj w:", 
                 font=("TkDefaultFont", 9, "bold")).pack(side="left", padx=5)
        
        ttk.Checkbutton(location_frame, text="Temat", 
                       variable=self.search_in_subject_var).pack(side="left", padx=10)
        ttk.Checkbutton(location_frame, text="Treść", 
                       variable=self.search_in_body_var).pack(side="left", padx=10)
        ttk.Checkbutton(location_frame, text="Załączniki", 
                       variable=self.search_in_attachments_var).pack(side="left", padx=10)
        
        # Search behavior options
        behavior_frame = ttk.Frame(section_frame)
        behavior_frame.pack(fill="x", pady=5)
        
        ttk.Checkbutton(behavior_frame, text="Uwzględnij wielkość liter", 
                       variable=self.case_sensitive_var).pack(side="left", padx=10)
        ttk.Checkbutton(behavior_frame, text="Tylko całe słowa", 
                       variable=self.whole_words_only_var).pack(side="left", padx=10)
        ttk.Checkbutton(behavior_frame, text="Uwzględnij załączniki", 
                       variable=self.include_attachments_var).pack(side="left", padx=10)
    
    def create_folder_filters_section(self, parent):
        """Create folder filtering section."""
        section_frame = ttk.LabelFrame(parent, text="Filtrowanie Folderów", padding="10")
        section_frame.pack(fill="x", padx=10, pady=5)
        
        # Excluded folders
        exclude_frame = ttk.Frame(section_frame)
        exclude_frame.pack(fill="x", pady=5)
        
        ttk.Label(exclude_frame, text="Pomiń foldery:").pack(side="left", padx=5)
        self.exclude_folders_var = tk.StringVar()
        exclude_entry = ttk.Entry(exclude_frame, textvariable=self.exclude_folders_var, 
                                 width=30)
        exclude_entry.pack(side="left", padx=5)
        ttk.Label(exclude_frame, text="(oddziel przecinkami)").pack(side="left", padx=5)
        
        # Included folders only
        include_frame = ttk.Frame(section_frame)
        include_frame.pack(fill="x", pady=5)
        
        ttk.Label(include_frame, text="Tylko foldery:").pack(side="left", padx=5)
        self.include_folders_var = tk.StringVar()
        include_entry = ttk.Entry(include_frame, textvariable=self.include_folders_var, 
                                 width=30)
        include_entry.pack(side="left", padx=5)
        ttk.Label(include_frame, text="(oddziel przecinkami)").pack(side="left", padx=5)
    
    def create_file_extensions_section(self, parent):
        """Create file extensions filtering section."""
        section_frame = ttk.LabelFrame(parent, text="Rozszerzenia Plików", padding="10")
        section_frame.pack(fill="x", padx=10, pady=5)
        
        ext_frame = ttk.Frame(section_frame)
        ext_frame.pack(fill="x", pady=5)
        
        ttk.Label(ext_frame, text="Rozszerzenia:").pack(side="left", padx=5)
        self.file_extensions_var = tk.StringVar()
        ext_entry = ttk.Entry(ext_frame, textvariable=self.file_extensions_var, 
                             width=25)
        ext_entry.pack(side="left", padx=5)
        ttk.Label(ext_frame, text="(np. pdf,doc,txt)").pack(side="left", padx=5)
        
        # Quick extension selection
        quick_ext_frame = ttk.Frame(section_frame)
        quick_ext_frame.pack(fill="x", pady=5)
        
        ttk.Button(quick_ext_frame, text="PDF", 
                  command=lambda: self.add_extension("pdf")).pack(side="left", padx=2)
        ttk.Button(quick_ext_frame, text="DOC", 
                  command=lambda: self.add_extension("doc,docx")).pack(side="left", padx=2)
        ttk.Button(quick_ext_frame, text="XLS", 
                  command=lambda: self.add_extension("xls,xlsx")).pack(side="left", padx=2)
        ttk.Button(quick_ext_frame, text="TXT", 
                  command=lambda: self.add_extension("txt")).pack(side="left", padx=2)
        ttk.Button(quick_ext_frame, text="Wyczyść", 
                  command=lambda: self.file_extensions_var.set("")).pack(side="left", padx=5)
    
    def create_actions_section(self, parent):
        """Create actions section with search and validation buttons."""
        section_frame = ttk.LabelFrame(parent, text="Działania", padding="10")
        section_frame.pack(fill="x", padx=10, pady=5)
        
        button_frame = ttk.Frame(section_frame)
        button_frame.pack(fill="x", pady=5)
        
        ttk.Button(button_frame, text="Waliduj Kryteria", 
                  command=self.validate_criteria).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Resetuj Wszystkie", 
                  command=self.reset_all_criteria).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Wykonaj Wyszukiwanie", 
                  command=self.execute_search, 
                  style="Accent.TButton").pack(side="right", padx=5)
    
    def create_saved_criteria_section(self, parent):
        """Create saved criteria management section."""
        section_frame = ttk.LabelFrame(parent, text="Zapisane Kryteria", padding="10")
        section_frame.pack(fill="x", padx=10, pady=5)
        
        # List of saved criteria
        list_frame = ttk.Frame(section_frame)
        list_frame.pack(fill="x", pady=5)
        
        ttk.Label(list_frame, text="Zapisane zestawy:").pack(side="left", padx=5)
        self.criteria_listbox = ttk.Combobox(list_frame, 
                                           textvariable=self.selected_criteria_var, 
                                           state="readonly", width=20)
        self.criteria_listbox.pack(side="left", padx=5)
        
        # Management buttons
        manage_frame = ttk.Frame(section_frame)
        manage_frame.pack(fill="x", pady=5)
        
        ttk.Button(manage_frame, text="Wczytaj", 
                  command=self.load_selected_criteria).pack(side="left", padx=2)
        ttk.Button(manage_frame, text="Zapisz Jako...", 
                  command=self.save_criteria_as).pack(side="left", padx=2)
        ttk.Button(manage_frame, text="Usuń", 
                  command=self.delete_selected_criteria).pack(side="left", padx=2)
        ttk.Button(manage_frame, text="Eksportuj", 
                  command=self.export_criteria).pack(side="left", padx=2)
        ttk.Button(manage_frame, text="Importuj", 
                  command=self.import_criteria).pack(side="left", padx=2)
        ttk.Button(manage_frame, text="Odśwież", 
                  command=self.load_saved_criteria_list).pack(side="right", padx=2)
        
        # Results area
        self.create_results_section(parent)
    
    def create_results_section(self, parent):
        """Create search results display section."""
        section_frame = ttk.LabelFrame(parent, text="Wyniki Wyszukiwania", padding="10")
        section_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Results text area with scrollbar
        results_frame = ttk.Frame(section_frame)
        results_frame.pack(fill="both", expand=True)
        
        self.results_text = tk.Text(results_frame, height=8, wrap=tk.WORD)
        results_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", 
                                        command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_text.pack(side="left", fill="both", expand=True)
        results_scrollbar.pack(side="right", fill="y")
        
        # Default text
        self.results_text.insert("1.0", "Wyniki wyszukiwania będą wyświetlone tutaj po wykonaniu wyszukiwania.")
        self.results_text.config(state="disabled")
    
    def bind_variable_changes(self):
        """Bind variable changes to update the criteria model."""
        variables = [
            self.text_query_var, self.category_var, self.amount_min_var, 
            self.amount_max_var, self.date_from_var, self.date_to_var,
            self.exclude_folders_var, self.include_folders_var, 
            self.file_extensions_var
        ]
        
        for var in variables:
            var.trace_add('write', self.on_variable_changed)
    
    def on_variable_changed(self, *args):
        """Called when any variable changes to update the criteria model."""
        try:
            # Update text fields
            self.criteria.text_query = self.text_query_var.get()
            self.criteria.category = self.category_var.get()
            
            # Update amounts
            try:
                self.criteria.amount_min = float(self.amount_min_var.get()) if self.amount_min_var.get().strip() else None
            except ValueError:
                self.criteria.amount_min = None
                
            try:
                self.criteria.amount_max = float(self.amount_max_var.get()) if self.amount_max_var.get().strip() else None
            except ValueError:
                self.criteria.amount_max = None
            
            # Update dates
            self.criteria.date_from = self.parse_date(self.date_from_var.get())
            self.criteria.date_to = self.parse_date(self.date_to_var.get())
            
            # Update boolean flags
            self.criteria.include_attachments = self.include_attachments_var.get()
            self.criteria.case_sensitive = self.case_sensitive_var.get()
            self.criteria.whole_words_only = self.whole_words_only_var.get()
            self.criteria.search_in_subject = self.search_in_subject_var.get()
            self.criteria.search_in_body = self.search_in_body_var.get()
            self.criteria.search_in_attachments = self.search_in_attachments_var.get()
            
            # Update folder filters
            self.criteria.exclude_folders = set(
                folder.strip() for folder in self.exclude_folders_var.get().split(',') 
                if folder.strip()
            )
            self.criteria.include_folders = set(
                folder.strip() for folder in self.include_folders_var.get().split(',') 
                if folder.strip()
            )
            
            # Update file extensions
            self.criteria.file_extensions = set(
                ext.strip().lower() for ext in self.file_extensions_var.get().split(',') 
                if ext.strip()
            )
            
        except Exception as e:
            print(f"Error updating criteria: {e}")
    
    def parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string in various formats."""
        if not date_str.strip():
            return None
        
        formats = ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None
    
    def format_date(self, date_obj: Optional[date]) -> str:
        """Format date object to string."""
        return date_obj.strftime('%Y-%m-%d') if date_obj else ''
    
    def select_date(self, date_type: str):
        """Open date selection dialog."""
        # Simple date input dialog
        current_date = datetime.now().date()
        date_str = tk.simpledialog.askstring(
            "Wybierz datę", 
            f"Wprowadź datę (YYYY-MM-DD):",
            initialvalue=current_date.strftime('%Y-%m-%d')
        )
        
        if date_str:
            if date_type == "from":
                self.date_from_var.set(date_str)
            else:
                self.date_to_var.set(date_str)
    
    def set_quick_date(self, period: str):
        """Set quick date ranges."""
        today = datetime.now().date()
        
        if period == "week":
            start_date = today - timedelta(days=7)
        elif period == "month":
            start_date = today - timedelta(days=30)
        elif period == "3months":
            start_date = today - timedelta(days=90)
        else:
            return
        
        self.date_from_var.set(self.format_date(start_date))
        self.date_to_var.set(self.format_date(today))
    
    def clear_dates(self):
        """Clear date fields."""
        self.date_from_var.set("")
        self.date_to_var.set("")
    
    def clear_basic_search(self):
        """Clear basic search fields."""
        self.text_query_var.set("")
        self.category_var.set("")
    
    def add_extension(self, extensions: str):
        """Add file extensions to the list."""
        current = self.file_extensions_var.get()
        if current:
            new_extensions = f"{current},{extensions}"
        else:
            new_extensions = extensions
        self.file_extensions_var.set(new_extensions)
    
    def validate_criteria(self):
        """Validate current search criteria."""
        errors = self.criteria.validate()
        
        if errors:
            error_message = "Błędy walidacji:\n\n" + "\n".join(f"• {error}" for error in errors)
            messagebox.showerror("Błędy walidacji", error_message)
        else:
            messagebox.showinfo("Walidacja", "Kryteria wyszukiwania są prawidłowe!")
    
    def reset_all_criteria(self):
        """Reset all search criteria to defaults."""
        if messagebox.askyesno("Resetuj kryteria", "Czy na pewno chcesz zresetować wszystkie kryteria?"):
            self.criteria.reset()
            self.update_ui_from_criteria()
    
    def update_ui_from_criteria(self):
        """Update UI elements from criteria model."""
        self.text_query_var.set(self.criteria.text_query)
        self.category_var.set(self.criteria.category)
        self.amount_min_var.set(str(self.criteria.amount_min) if self.criteria.amount_min is not None else "")
        self.amount_max_var.set(str(self.criteria.amount_max) if self.criteria.amount_max is not None else "")
        self.date_from_var.set(self.format_date(self.criteria.date_from))
        self.date_to_var.set(self.format_date(self.criteria.date_to))
        
        self.include_attachments_var.set(self.criteria.include_attachments)
        self.case_sensitive_var.set(self.criteria.case_sensitive)
        self.whole_words_only_var.set(self.criteria.whole_words_only)
        self.search_in_subject_var.set(self.criteria.search_in_subject)
        self.search_in_body_var.set(self.criteria.search_in_body)
        self.search_in_attachments_var.set(self.criteria.search_in_attachments)
        
        self.exclude_folders_var.set(','.join(self.criteria.exclude_folders))
        self.include_folders_var.set(','.join(self.criteria.include_folders))
        self.file_extensions_var.set(','.join(self.criteria.file_extensions))
    
    def load_saved_criteria_list(self):
        """Load the list of saved criteria."""
        saved_criteria = self.criteria_manager.list_saved_criteria()
        self.criteria_listbox['values'] = saved_criteria
        
        if saved_criteria and not self.selected_criteria_var.get():
            self.selected_criteria_var.set(saved_criteria[0])
    
    def load_selected_criteria(self):
        """Load the selected criteria from the list."""
        selected_name = self.selected_criteria_var.get()
        if not selected_name:
            messagebox.showwarning("Brak wyboru", "Wybierz kryteria do wczytania.")
            return
        
        criteria = self.criteria_manager.load_criteria(selected_name)
        if criteria:
            self.criteria = criteria
            self.update_ui_from_criteria()
            messagebox.showinfo("Sukces", f"Wczytano kryteria: {selected_name}")
        else:
            messagebox.showerror("Błąd", f"Nie udało się wczytać kryteriów: {selected_name}")
    
    def save_criteria_as(self):
        """Save current criteria with a new name."""
        name = tk.simpledialog.askstring(
            "Zapisz kryteria", 
            "Podaj nazwę dla zestawu kryteriów:",
            initialvalue=""
        )
        
        if name:
            if self.criteria_manager.save_criteria(name, self.criteria):
                messagebox.showinfo("Sukces", f"Zapisano kryteria: {name}")
                self.load_saved_criteria_list()
                self.selected_criteria_var.set(name)
            else:
                messagebox.showerror("Błąd", "Nie udało się zapisać kryteriów.")
    
    def delete_selected_criteria(self):
        """Delete selected criteria."""
        selected_name = self.selected_criteria_var.get()
        if not selected_name:
            messagebox.showwarning("Brak wyboru", "Wybierz kryteria do usunięcia.")
            return
        
        if messagebox.askyesno("Usuń kryteria", f"Czy na pewno chcesz usunąć kryteria '{selected_name}'?"):
            if self.criteria_manager.delete_criteria(selected_name):
                messagebox.showinfo("Sukces", f"Usunięto kryteria: {selected_name}")
                self.load_saved_criteria_list()
                self.selected_criteria_var.set("")
            else:
                messagebox.showerror("Błąd", "Nie udało się usunąć kryteriów.")
    
    def export_criteria(self):
        """Export criteria to file."""
        selected_name = self.selected_criteria_var.get()
        if not selected_name:
            messagebox.showwarning("Brak wyboru", "Wybierz kryteria do eksportu.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Eksportuj kryteria",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            if self.criteria_manager.export_criteria(selected_name, filename):
                messagebox.showinfo("Sukces", f"Wyeksportowano kryteria do: {filename}")
            else:
                messagebox.showerror("Błąd", "Nie udało się wyeksportować kryteriów.")
    
    def import_criteria(self):
        """Import criteria from file."""
        filename = filedialog.askopenfilename(
            title="Importuj kryteria",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            name = tk.simpledialog.askstring(
                "Importuj kryteria", 
                "Podaj nazwę dla importowanych kryteriów:",
                initialvalue=os.path.splitext(os.path.basename(filename))[0]
            )
            
            if name:
                if self.criteria_manager.import_criteria(filename, name):
                    messagebox.showinfo("Sukces", f"Zaimportowano kryteria: {name}")
                    self.load_saved_criteria_list()
                    self.selected_criteria_var.set(name)
                else:
                    messagebox.showerror("Błąd", "Nie udało się zaimportować kryteriów.")
    
    def execute_search(self):
        """Execute search based on current criteria."""
        # Validate criteria first
        errors = self.criteria.validate()
        if errors:
            error_message = "Błędy walidacji:\n\n" + "\n".join(f"• {error}" for error in errors)
            messagebox.showerror("Błędy walidacji", error_message)
            return
        
        if self.criteria.is_empty():
            messagebox.showwarning("Puste kryteria", "Zdefiniuj kryteria wyszukiwania przed wykonaniem.")
            return
        
        # Update results display
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert("1.0", "Wykonywanie wyszukiwania...\n\n")
        self.results_text.insert(tk.END, f"Kryteria wyszukiwania:\n")
        self.results_text.insert(tk.END, f"• Tekst: {self.criteria.text_query or '(brak)'}\n")
        self.results_text.insert(tk.END, f"• Kategoria: {self.criteria.category or '(wszystkie)'}\n")
        self.results_text.insert(tk.END, f"• Data od: {self.format_date(self.criteria.date_from) or '(brak)'}\n")
        self.results_text.insert(tk.END, f"• Data do: {self.format_date(self.criteria.date_to) or '(brak)'}\n")
        self.results_text.insert(tk.END, f"• Uwzględnij załączniki: {'Tak' if self.criteria.include_attachments else 'Nie'}\n")
        self.results_text.insert(tk.END, f"• Wielkość liter: {'Tak' if self.criteria.case_sensitive else 'Nie'}\n")
        self.results_text.insert(tk.END, f"• Tylko całe słowa: {'Tak' if self.criteria.whole_words_only else 'Nie'}\n")
        
        if self.criteria.exclude_folders:
            self.results_text.insert(tk.END, f"• Pomijane foldery: {', '.join(self.criteria.exclude_folders)}\n")
        if self.criteria.include_folders:
            self.results_text.insert(tk.END, f"• Tylko foldery: {', '.join(self.criteria.include_folders)}\n")
        if self.criteria.file_extensions:
            self.results_text.insert(tk.END, f"• Rozszerzenia: {', '.join(self.criteria.file_extensions)}\n")
        
        self.results_text.insert(tk.END, "\n" + "="*50 + "\n")
        self.results_text.insert(tk.END, "UWAGA: Implementacja wykonania wyszukiwania zostanie dodana\n")
        self.results_text.insert(tk.END, "w zależności od wymagań konkretnego systemu wyszukiwania.\n")
        self.results_text.insert(tk.END, "Obecnie wyświetlane są tylko parametry wyszukiwania.\n")
        
        self.results_text.config(state="disabled")
        
        messagebox.showinfo("Wyszukiwanie", "Symulacja wyszukiwania wykonana. Zobacz wyniki poniżej.")