import tkinter as tk
from tkinter import ttk

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Księga Przychodów i Rozchodów")
        self.geometry("900x600")

        style = ttk.Style(self)
        style.theme_use("clam")

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        
        # Initialize tab references to None (lazy loading)
        self.mail_search_tab = None
        self.exchange_tab = None
        self.zakupy_tab = None
        self.system_tab = None
        
        # Add placeholder frames for lazy loading
        self._create_tab_placeholders()
        
        # Bind tab selection event for lazy loading
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        # Load the first tab immediately for better UX
        self._load_mail_search_tab()

    def _create_tab_placeholders(self):
        """Create placeholder frames for all tabs"""
        # Placeholder for Mail Search tab
        mail_placeholder = ttk.Frame(self.notebook)
        self.notebook.add(mail_placeholder, text="Przeszukiwanie Poczty")
        
        # Placeholder for Exchange Config tab
        exchange_placeholder = ttk.Frame(self.notebook)
        self.notebook.add(exchange_placeholder, text="Konfiguracja poczty")
        
        # Placeholder for Zakupy tab
        zakupy_placeholder = ttk.Frame(self.notebook)
        self.notebook.add(zakupy_placeholder, text="Zakupy")
        
        # Placeholder for System tab
        system_placeholder = ttk.Frame(self.notebook)
        self.notebook.add(system_placeholder, text="System")

    def _on_tab_changed(self, event):
        """Handle tab change events to load tabs on demand"""
        selected_tab = self.notebook.select()
        tab_index = self.notebook.index(selected_tab)
        
        # Load the appropriate tab based on index
        if tab_index == 0 and self.mail_search_tab is None:
            self._load_mail_search_tab()
        elif tab_index == 1 and self.exchange_tab is None:
            self._load_exchange_tab()
        elif tab_index == 2 and self.zakupy_tab is None:
            self._load_zakupy_tab()
        elif tab_index == 3 and self.system_tab is None:
            self._load_system_tab()

    def _load_mail_search_tab(self):
        """Lazy load the Mail Search tab"""
        if self.mail_search_tab is None:
            print("📬 Ładowanie zakładki: Przeszukiwanie Poczty...")
            try:
                from gui.tab_mail_search import MailSearchTab
                self.mail_search_tab = MailSearchTab(self.notebook)
                self.notebook.forget(0)  # Remove placeholder
                self.notebook.insert(0, self.mail_search_tab, text="Przeszukiwanie Poczty")
                print("✓ Zakładka Przeszukiwanie Poczty załadowana")
            except Exception as e:
                print(f"⚠️  Błąd ładowania zakładki Przeszukiwanie Poczty: {e}")

    def _load_exchange_tab(self):
        """Lazy load the Exchange Config tab"""
        if self.exchange_tab is None:
            print("⚙️  Ładowanie zakładki: Konfiguracja poczty...")
            try:
                from gui.tab_exchange_config import ExchangeConfigTab
                self.exchange_tab = ExchangeConfigTab(self.notebook)
                self.notebook.forget(1)  # Remove placeholder
                self.notebook.insert(1, self.exchange_tab, text="Konfiguracja poczty")
                print("✓ Zakładka Konfiguracja poczty załadowana")
            except Exception as e:
                print(f"⚠️  Błąd ładowania zakładki Konfiguracja poczty: {e}")

    def _load_zakupy_tab(self):
        """Lazy load the Zakupy tab with heavy OCR dependencies"""
        if self.zakupy_tab is None:
            print("🛒 Ładowanie zakładki: Zakupy (z OCR)...")
            try:
                from gui.tab_zakupy import ZakupiTab
                self.zakupy_tab = ZakupiTab(self.notebook)
                self.notebook.forget(2)  # Remove placeholder
                self.notebook.insert(2, self.zakupy_tab, text="Zakupy")
                print("✓ Zakładka Zakupy załadowana")
            except Exception as e:
                print(f"⚠️  Błąd ładowania zakładki Zakupy: {e}")

    def _load_system_tab(self):
        """Lazy load the System tab"""
        if self.system_tab is None:
            print("🔧 Ładowanie zakładki: System...")
            try:
                from gui.tab_system import SystemTab
                self.system_tab = SystemTab(self.notebook)
                self.notebook.forget(3)  # Remove placeholder
                self.notebook.insert(3, self.system_tab, text="System")
                print("✓ Zakładka System załadowana")
            except Exception as e:
                print(f"⚠️  Błąd ładowania zakładki System: {e}")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()