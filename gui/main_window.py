import tkinter as tk
from tkinter import ttk
from gui.mail_config_widget import MailConfigWidget
from gui.tab_mail_search import MailSearchTab
from gui.tab_system import SystemTab
from gui.tab_zakupy import ZakupiTab
from tools import logger
from tools.version_info import format_title_bar

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        logger.log("Inicjalizacja MainWindow")
        
        # Set title with program name, PR number, and version
        title_text = format_title_bar()
        self.title(title_text)
        logger.log(f"Tytuł aplikacji ustawiony: {title_text}")
        self.geometry("900x600")

        style = ttk.Style(self)
        style.theme_use("clam")
        logger.log("Konfiguracja stylu GUI zakończona")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)
        logger.log("Utworzenie głównego Notebook")

        # Zakładka: Przeszukiwanie Poczty (first tab)
        logger.log("Ładowanie zakładki: Przeszukiwanie Poczty")
        mail_search_tab = MailSearchTab(notebook)
        notebook.add(mail_search_tab, text="Przeszukiwanie Poczty")
        logger.log("Zakładka 'Przeszukiwanie Poczty' załadowana")

        # Zakładka: Konfiguracja poczty
        logger.log("Ładowanie zakładki: Konfiguracja poczty")
        mail_config_tab = MailConfigWidget(notebook)
        notebook.add(mail_config_tab, text="Konfiguracja poczty")
        logger.log("Zakładka 'Konfiguracja poczty' załadowana")

        # Zakładka: Zakupy
        logger.log("Ładowanie zakładki: Zakupy")
        zakupy_tab = ZakupiTab(notebook)
        notebook.add(zakupy_tab, text="Zakupy")
        logger.log("Zakładka 'Zakupy' załadowana")

        # Dodanie rozbudowanej zakładki System
        logger.log("Ładowanie zakładki: System")
        system_tab = SystemTab(notebook)
        notebook.add(system_tab, text="System")
        logger.log("Zakładka 'System' załadowana")
        
        # Store reference to system tab for title updates
        self.system_tab = system_tab
        
        logger.log("MainWindow - wszystkie komponenty załadowane pomyślnie")
    
    def refresh_title_bar(self):
        """Refresh the title bar with current version information."""
        title_text = format_title_bar()
        self.title(title_text)
        logger.log(f"Tytuł aplikacji odświeżony: {title_text}")
        
        # Also refresh system tab if it exists
        if hasattr(self, 'system_tab') and self.system_tab:
            self.system_tab.refresh_version_info()

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()