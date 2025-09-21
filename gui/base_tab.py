"""
Bazowa klasa dla zakładek GUI w ksiegi-ocr.
"""
import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod


class BaseTab(ttk.Frame, ABC):
    """Bazowa klasa dla wszystkich zakładek."""
    
    def __init__(self, parent):
        """
        Inicjalizuje bazową zakładkę.
        
        Args:
            parent: Widget rodzica (notebook)
        """
        super().__init__(parent)
        self.widgets = {}
        self.setup_ui()

    @abstractmethod
    def setup_ui(self) -> None:
        """Konfiguruje interfejs użytkownika zakładki."""
        pass

    def create_labeled_frame(self, title: str, padding: int = 10) -> ttk.LabelFrame:
        """
        Tworzy ramkę z etykietą.
        
        Args:
            title: Tytuł ramki
            padding: Padding ramki
            
        Returns:
            Utworzona ramka
        """
        frame = ttk.LabelFrame(self, text=title, padding=padding)
        frame.pack(fill="x", padx=10, pady=5)
        return frame

    def create_config_entry(self, parent: ttk.Widget, label_text: str, var_key: str,
                           row: int, col: int = 0, show_char: str = None,
                           is_bool: bool = False, is_int: bool = False,
                           width: int = 40) -> tuple:
        """
        Tworzy pole konfiguracji z etykietą.
        
        Args:
            parent: Widget rodzica
            label_text: Tekst etykiety
            var_key: Klucz zmiennej
            row: Numer wiersza
            col: Numer kolumny
            show_char: Znak do ukrycia tekstu (dla haseł)
            is_bool: Czy to pole boolean
            is_int: Czy to pole liczbowe
            width: Szerokość pola
            
        Returns:
            Krotka (zmienna, typ_zmiennej)
        """
        ttk.Label(parent, text=label_text).grid(
            row=row, column=col, sticky="w", padx=5, pady=2
        )

        if is_bool:
            var = tk.BooleanVar()
            widget = ttk.Checkbutton(parent, variable=var)
            var_type = "bool"
        elif is_int:
            var = tk.StringVar()
            widget = ttk.Spinbox(parent, from_=0, to=999, textvariable=var, width=width-2)
            var_type = "int"
        else:
            var = tk.StringVar()
            widget = ttk.Entry(parent, textvariable=var, width=width, show=show_char)
            var_type = "str"

        widget.grid(row=row, column=col + 1, sticky="ew", padx=5, pady=2)
        
        self.widgets[var_key] = (var, var_type)
        return var, var_type

    def get_value(self, key: str):
        """
        Pobiera wartość z widgetu.
        
        Args:
            key: Klucz widgetu
            
        Returns:
            Wartość widgetu
        """
        if key in self.widgets:
            var, var_type = self.widgets[key]
            if var_type == "bool":
                return var.get()
            elif var_type == "int":
                try:
                    return int(var.get())
                except ValueError:
                    return 0
            else:
                return var.get()
        return None

    def set_value(self, key: str, value) -> None:
        """
        Ustawia wartość w widgecie.
        
        Args:
            key: Klucz widgetu
            value: Wartość do ustawienia
        """
        if key in self.widgets:
            var, var_type = self.widgets[key]
            if var_type == "bool":
                var.set(bool(value))
            else:
                var.set(str(value) if value is not None else "")

    def get_all_values(self) -> dict:
        """
        Pobiera wszystkie wartości z widgetów.
        
        Returns:
            Słownik z wartościami
        """
        values = {}
        for key in self.widgets:
            values[key] = self.get_value(key)
        return values

    def set_all_values(self, values: dict) -> None:
        """
        Ustawia wszystkie wartości w widgetach.
        
        Args:
            values: Słownik z wartościami
        """
        for key, value in values.items():
            self.set_value(key, value)