import customtkinter as ctk
from gui.tab_exchange_config import ExchangeConfigTab
from gui.tab_mail_search import MailSearchTab
from gui.tab_system import SystemTab
from gui.tab_zakupy import ZakupiTab

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Księga Przychodów i Rozchodów")
        self.geometry("900x600")
        
        # Create main tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # Add tabs
        self.tabview.add("Przeszukiwanie Poczty")
        self.tabview.add("Konfiguracja poczty") 
        self.tabview.add("Zakupy")
        self.tabview.add("System")

        # Initialize tab content
        self._initialize_tabs()
        
    def _initialize_tabs(self):
        """Initialize tab contents"""
        
        # Mail Search Tab
        mail_search_frame = self.tabview.tab("Przeszukiwanie Poczty")
        self.mail_search_tab = MailSearchTab(mail_search_frame)
        
        # Exchange Config Tab  
        exchange_frame = self.tabview.tab("Konfiguracja poczty")
        self.exchange_tab = ExchangeConfigTab(exchange_frame)
        
        # Purchases Tab
        zakupy_frame = self.tabview.tab("Zakupy")
        self.zakupy_tab = ZakupiTab(zakupy_frame)
        
        # System Tab
        system_frame = self.tabview.tab("System") 
        self.system_tab = SystemTab(system_frame)

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()