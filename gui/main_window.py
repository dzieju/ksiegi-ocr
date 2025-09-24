import customtkinter as ctk
from gui.modern_theme import ModernTheme
from gui.tab_exchange_config import ExchangeConfigTab
from gui.tab_mail_search import MailSearchTab
from gui.tab_system import SystemTab
from gui.tab_zakupy import ZakupiTab

class MainWindow(ctk.CTk):
    def __init__(self):
        print("DEBUG: MainWindow.__init__() started")
        super().__init__()
        print("DEBUG: MainWindow super().__init__() completed")
        
        # Initialize modern theme
        print("DEBUG: Setting up ModernTheme...")
        try:
            ModernTheme.setup_theme()
            print("DEBUG: ModernTheme setup completed successfully")
        except Exception as e:
            print(f"DEBUG: ModernTheme setup failed: {e}")
        
        self.title("Księga Przychodów i Rozchodów")
        self.geometry("900x600")
        print("DEBUG: Window title and geometry set")
        
        # Configure window
        try:
            self.configure(fg_color=ModernTheme.COLORS['background'])
            print("DEBUG: Window background color configured")
        except Exception as e:
            print(f"DEBUG: Window background configuration failed: {e}")
            self.configure(fg_color="lightgray")
        
        # TEST: Add test widgets directly to MainWindow (outside of any container)
        print("DEBUG: Adding test widgets directly to MainWindow...")
        try:
            self.test_label_main = ctk.CTkLabel(self, text="🚨 TEST: MainWindow Direct Widget", 
                                              font=("Arial", 18, "bold"), 
                                              text_color="red")
            self.test_label_main.pack(pady=5)
            
            self.test_button_main = ctk.CTkButton(self, text="TEST: MainWindow Direct Button", 
                                                command=lambda: print("DEBUG: MainWindow direct button clicked!"))
            self.test_button_main.pack(pady=5)
            print("DEBUG: Test widgets added directly to MainWindow successfully")
        except Exception as e:
            print(f"DEBUG: Failed to add test widgets to MainWindow: {e}")
            print("🚨 CONSOLE MESSAGE: Test widgets could not be added directly to MainWindow - this indicates a fundamental rendering issue!")
        
        # Create main container with padding
        print("DEBUG: Creating main container...")
        try:
            main_container = ctk.CTkFrame(
                self, 
                **ModernTheme.get_frame_style('section')
            )
            main_container.pack(fill="both", expand=True, padx=ModernTheme.SPACING['medium'], pady=ModernTheme.SPACING['medium'])
            print("DEBUG: Main container created successfully")
        except Exception as e:
            print(f"DEBUG: Main container creation failed: {e}")
            # Fallback to simple frame
            main_container = ctk.CTkFrame(self)
            main_container.pack(fill="both", expand=True, padx=16, pady=16)

        # Create modern tabview
        print("DEBUG: Creating tabview...")
        try:
            self.tabview = ctk.CTkTabview(
                main_container,
                corner_radius=10,
                border_width=1,
                border_color=ModernTheme.COLORS['border'],
                fg_color=ModernTheme.COLORS['surface']
            )
            self.tabview.pack(fill="both", expand=True)
            print("DEBUG: Tabview created successfully")
        except Exception as e:
            print(f"DEBUG: Tabview creation failed: {e}")
            # Fallback to simple tabview
            self.tabview = ctk.CTkTabview(main_container)
            self.tabview.pack(fill="both", expand=True)

        # Add tabs with modern styling
        print("DEBUG: Adding tabs...")
        tab_names = {
            "Przeszukiwanie Poczty": "📧",
            "Konfiguracja poczty": "⚙️", 
            "Zakupy": "🛒",
            "System": "🔧"
        }
        
        # Create tabs
        for tab_name, icon in tab_names.items():
            try:
                self.tabview.add(f"{icon} {tab_name}")
                print(f"DEBUG: Added tab: {icon} {tab_name}")
            except Exception as e:
                print(f"DEBUG: Failed to add tab {tab_name}: {e}")

        # TEST: Add test widgets directly to CTkTabview (outside of tabs)
        print("DEBUG: Adding test widgets directly to CTkTabview...")
        try:
            self.test_label_tabview = ctk.CTkLabel(self.tabview, text="🎯 TEST: TabView Direct Widget", 
                                                  font=("Arial", 16, "bold"), 
                                                  text_color="blue")
            self.test_label_tabview.pack(pady=5, before=self.tabview._segmented_button)
            
            self.test_button_tabview = ctk.CTkButton(self.tabview, text="TEST: TabView Direct Button", 
                                                   command=lambda: print("DEBUG: TabView direct button clicked!"))
            self.test_button_tabview.pack(pady=5, before=self.tabview._segmented_button)
            print("DEBUG: Test widgets added directly to CTkTabview successfully")
        except Exception as e:
            print(f"DEBUG: Failed to add test widgets to CTkTabview: {e}")
            print("🚨 CONSOLE MESSAGE: Test widgets could not be added directly to CTkTabview - this indicates a tabview rendering issue!")

        # Initialize tab content
        print("DEBUG: Initializing tab content...")
        self._initialize_tabs()
        
        # TEST SUMMARY: Check if test widgets are visible
        print("\n" + "="*60)
        print("🧪 WIDGET VISIBILITY TEST SUMMARY:")
        print("="*60)
        try:
            main_widgets_visible = hasattr(self, 'test_label_main') and hasattr(self, 'test_button_main')
            tabview_widgets_visible = hasattr(self, 'test_label_tabview') and hasattr(self, 'test_button_tabview')
            
            print(f"✅ MainWindow direct widgets created: {main_widgets_visible}")
            print(f"✅ TabView direct widgets created: {tabview_widgets_visible}")
            
            if not main_widgets_visible:
                print("🚨 CONSOLE MESSAGE: MainWindow direct widgets FAILED - fundamental window rendering issue!")
            if not tabview_widgets_visible:
                print("🚨 CONSOLE MESSAGE: TabView direct widgets FAILED - tabview rendering issue!")
            
            if main_widgets_visible and tabview_widgets_visible:
                print("✅ Both test widget sets created successfully - if you don't see them, there's a display/theme issue!")
            
        except Exception as e:
            print(f"🚨 CONSOLE MESSAGE: Error checking test widget visibility: {e}")
        
        print("="*60)
        print("DEBUG: MainWindow initialization completed")
        print("="*60 + "\n")
        
    def _initialize_tabs(self):
        """Initialize tab contents with modern components"""
        print("DEBUG: _initialize_tabs() started")
        
        # Mail Search Tab
        print("DEBUG: Initializing Mail Search Tab...")
        try:
            mail_search_frame = self.tabview.tab("📧 Przeszukiwanie Poczty")
            print(f"DEBUG: Mail search frame obtained: {mail_search_frame}")
            self.mail_search_tab = MailSearchTab(mail_search_frame)
            print("DEBUG: Mail Search Tab initialized successfully")
        except Exception as e:
            print(f"DEBUG: Mail Search Tab initialization failed: {e}")
        
        # Exchange Config Tab  
        print("DEBUG: Initializing Exchange Config Tab...")
        try:
            exchange_frame = self.tabview.tab("⚙️ Konfiguracja poczty")
            print(f"DEBUG: Exchange frame obtained: {exchange_frame}")
            self.exchange_tab = ExchangeConfigTab(exchange_frame)
            print("DEBUG: Exchange Config Tab initialized successfully")
        except Exception as e:
            print(f"DEBUG: Exchange Config Tab initialization failed: {e}")
        
        # Purchases Tab
        print("DEBUG: Initializing Zakupy Tab...")
        try:
            zakupy_frame = self.tabview.tab("🛒 Zakupy")
            print(f"DEBUG: Zakupy frame obtained: {zakupy_frame}")
            self.zakupy_tab = ZakupiTab(zakupy_frame)
            print("DEBUG: Zakupy Tab initialized successfully")
        except Exception as e:
            print(f"DEBUG: Zakupy Tab initialization failed: {e}")
        
        # System Tab
        print("DEBUG: Initializing System Tab...")
        try:
            system_frame = self.tabview.tab("🔧 System") 
            print(f"DEBUG: System frame obtained: {system_frame}")
            self.system_tab = SystemTab(system_frame)
            print("DEBUG: System Tab initialized successfully")
        except Exception as e:
            print(f"DEBUG: System Tab initialization failed: {e}")
            
        print("DEBUG: _initialize_tabs() completed")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()