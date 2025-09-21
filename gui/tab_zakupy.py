import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class ZakupiTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Initialize file path variable
        self.file_path_var = tk.StringVar()
        
        # Create UI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Title label
        title_label = ttk.Label(
            self, 
            text="Zakładka Zakupy - Odczyt numerów faktur", 
            font=("Arial", 12),
            foreground="blue"
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # PDF file selection
        ttk.Label(self, text="Plik PDF:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self, textvariable=self.file_path_var, width=60).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(self, text="Wybierz plik", command=self.wybierz_plik_pdf).grid(row=1, column=2, padx=5, pady=5)
        
        # Invoice reading button
        ttk.Button(self, text="Odczytaj numery faktur", command=self.odczytaj_numery_faktur).grid(row=2, column=1, pady=20)
        
        # Status label
        self.status_label = ttk.Label(self, text="Brak wybranego pliku", foreground="blue")
        self.status_label.grid(row=3, column=1, pady=5)
        
    def wybierz_plik_pdf(self):
        """Funkcja do wyboru pliku PDF"""
        filepath = filedialog.askopenfilename(
            title="Wybierz plik PDF", 
            filetypes=[("PDF files", "*.pdf")]
        )
        if filepath:
            self.file_path_var.set(filepath)
            self.status_label.config(text="Plik wybrany", foreground="green")
            
    def odczytaj_numery_faktur(self):
        """Placeholder funkcja odczytu numerów faktur"""
        filepath = self.file_path_var.get().strip()
        
        if not filepath:
            messagebox.showwarning("Brak pliku", "Proszę najpierw wybrać plik PDF.")
            return
            
        # Placeholder implementation
        messagebox.showinfo(
            "Funkcja odczytu", 
            "Funkcja odczytu niezaimplementowana\n\n"
            f"Wybrany plik: {filepath.split('/')[-1]}"
        )
        self.status_label.config(text="Funkcja odczytu wywołana", foreground="orange")