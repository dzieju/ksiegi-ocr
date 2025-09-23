"""
Tooltip utility for adding contextual help to GUI elements
"""

import customtkinter as ctk
from typing import Optional

class CTkToolTip:
    """
    Custom tooltip implementation for CustomTkinter widgets
    Provides contextual help when hovering over UI elements
    """
    
    def __init__(self, widget, text: str, delay: int = 500, wraplength: int = 300):
        """
        Initialize tooltip
        
        Args:
            widget: The widget to attach tooltip to
            text: Tooltip text to display
            delay: Delay in milliseconds before showing tooltip
            wraplength: Maximum width of tooltip text
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplength = wraplength
        self.tooltip_window: Optional[ctk.CTkToplevel] = None
        self.after_id = None
        
        # Bind events
        self.widget.bind('<Enter>', self._on_enter)
        self.widget.bind('<Leave>', self._on_leave)
        self.widget.bind('<ButtonPress>', self._on_leave)
    
    def _on_enter(self, event=None):
        """Handle mouse enter event"""
        if self.after_id:
            self.widget.after_cancel(self.after_id)
        self.after_id = self.widget.after(self.delay, self._show_tooltip)
    
    def _on_leave(self, event=None):
        """Handle mouse leave event"""
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        self._hide_tooltip()
    
    def _show_tooltip(self):
        """Show the tooltip"""
        if self.tooltip_window:
            return
            
        # Get widget position
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        
        # Create tooltip window
        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Configure tooltip appearance
        self.tooltip_window.configure(fg_color=("#FFFFE0", "#2B2B2B"))  # Light yellow background
        
        # Create tooltip label
        label = ctk.CTkLabel(
            self.tooltip_window,
            text=self.text,
            font=("Segoe UI", 10),
            text_color=("#000000", "#FFFFFF"),
            fg_color="transparent",
            wraplength=self.wraplength,
            justify="left"
        )
        label.pack(padx=8, pady=6)
        
        # Ensure tooltip stays on top
        self.tooltip_window.lift()
    
    def _hide_tooltip(self):
        """Hide the tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    
    def update_text(self, new_text: str):
        """Update tooltip text"""
        self.text = new_text
        self._hide_tooltip()  # Hide current tooltip if showing


def add_tooltip(widget, text: str, delay: int = 500) -> CTkToolTip:
    """
    Convenience function to add tooltip to a widget
    
    Args:
        widget: Widget to add tooltip to
        text: Tooltip text
        delay: Delay before showing tooltip
        
    Returns:
        CTkToolTip instance
    """
    return CTkToolTip(widget, text, delay)


# Common tooltip texts for the application
TOOLTIPS = {
    'backup_create': 'Tworzy kopię zapasową aktualnej konfiguracji i danych aplikacji',
    'backup_restore': 'Przywraca dane z wcześniej utworzonej kopii zapasowej',
    'logs_show': 'Wyświetla logi aplikacji w nowym oknie do debugowania',
    'update_check': 'Sprawdza dostępność nowych wersji aplikacji',
    'report_send': 'Wysyła raport o błędach lub uwagach do deweloperów',
    'theme_toggle': 'Przełącza między jasnym a ciemnym trybem interfejsu',
    'app_restart': 'Ponownie uruchamia aplikację z nową konfiguracją',
    'pdf_select': 'Wybierz plik PDF zawierający faktury do przetworzenia',
    'ocr_process': 'Rozpoczyna automatyczne rozpoznawanie numerów faktur z PDF',
    'ocr_preview': 'Podgląd logów OCR w osobnym oknie',
    'mail_search': 'Wyszukuje emaile w skonfigurowanej skrzynce pocztowej',
    'exchange_config': 'Konfiguracja połączenia z serwerem Exchange',
    'ocr_engine': 'Wybór silnika OCR: Tesseract, EasyOCR lub PaddleOCR',
    'ocr_language': 'Języki rozpoznawania tekstu (np. pol+eng)',
    'ocr_confidence': 'Minimalny poziom pewności rozpoznania (0-100)',
}