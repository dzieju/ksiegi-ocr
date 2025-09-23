import customtkinter as ctk
from gui.modern_theme import ModernTheme
from gui.tab_exchange_config import ExchangeConfigTab
from gui.tab_mail_search import MailSearchTab
from gui.tab_system import SystemTab
from gui.tab_zakupy import ZakupiTab

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize modern theme
        ModernTheme.setup_theme()
        
        self.title("Księga Przychodów i Rozchodów")
        self.geometry("900x600")
        
        # Configure window
        self.configure(fg_color=ModernTheme.COLORS['background'])
        
        # Create main container with padding
        main_container = ctk.CTkFrame(
            self, 
            **ModernTheme.get_frame_style('section')
        )
        main_container.pack(fill="both", expand=True, padx=ModernTheme.SPACING['medium'], pady=ModernTheme.SPACING['medium'])

        # Create modern tabview
        self.tabview = ctk.CTkTabview(
            main_container,
            corner_radius=10,
            border_width=1,
            border_color=ModernTheme.COLORS['border'],
            fg_color=ModernTheme.COLORS['surface']
        )
        self.tabview.pack(fill="both", expand=True)

        # Add tabs with modern styling
        tab_names = {
            "Przeszukiwanie Poczty": "📧",
            "Konfiguracja poczty": "⚙️", 
            "Zakupy": "🛒",
            "System": "🔧"
        }
        
        # Create tabs
        for tab_name, icon in tab_names.items():
            self.tabview.add(f"{icon} {tab_name}")

        # Initialize tab content
        self._initialize_tabs()
    def _initialize_tabs(self):
        """Initialize tab contents with modern components"""
        
        # Mail Search Tab
        mail_search_frame = self.tabview.tab("📧 Przeszukiwanie Poczty")
        self.mail_search_tab = MailSearchTab(mail_search_frame)
        
        # Exchange Config Tab  
        exchange_frame = self.tabview.tab("⚙️ Konfiguracja poczty")
        self.exchange_tab = ExchangeConfigTab(exchange_frame)
        
        # Purchases Tab
        zakupy_frame = self.tabview.tab("🛒 Zakupy")
        self.zakupy_tab = ZakupiTab(zakupy_frame)
        
        # System Tab
        system_frame = self.tabview.tab("🔧 System") 
        self.system_tab = SystemTab(system_frame)

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()