import tkinter as tk
from tkinter import ttk


class ZakupiTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Placeholder label with styling consistent with other tabs
        placeholder_label = ttk.Label(
            self, 
            text="To jest zakładka Zakupy", 
            font=("Arial", 12),
            foreground="blue"
        )
        placeholder_label.pack(expand=True)