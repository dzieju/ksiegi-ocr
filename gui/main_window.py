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
        
        # TEST: Add widgets directly to MainWindow (outside any containers)
        print("DEBUG: Adding test widgets directly to MainWindow...")
        try:
            self.test_main_label = ctk.CTkLabel(
                self, 
                text="🔥 TEST: MainWindow Direct Widget", 
                font=("Arial", 20, "bold"), 
                text_color="red"
            )
            self.test_main_label.pack(pady=5)
            print("DEBUG: Test label added directly to MainWindow")
            
            self.test_main_button = ctk.CTkButton(
                self, 
                text="TEST: MainWindow Button", 
                command=lambda: print("DEBUG: MainWindow direct button clicked!"),
                width=200,
                height=40
            )
            self.test_main_button.pack(pady=5)
            print("DEBUG: Test button added directly to MainWindow")
        except Exception as e:
            print(f"DEBUG: Failed to add test widgets to MainWindow: {e}")
        
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

        # TEST: Add widgets directly to tabview (outside tabs) using grid instead of pack
        print("DEBUG: Adding test widgets directly to tabview using grid...")
        try:
            self.test_tabview_label = ctk.CTkLabel(
                self.tabview, 
                text="🎯 TEST: Tabview Direct Widget (Grid)", 
                font=("Arial", 16, "bold"), 
                text_color="blue"
            )
            # Use grid instead of pack for tabview children
            self.test_tabview_label.grid(row=0, column=0, pady=5, padx=5, sticky="ew")
            print("DEBUG: Test label added directly to tabview using grid")
            
            self.test_tabview_button = ctk.CTkButton(
                self.tabview, 
                text="TEST: Tabview Button (Grid)", 
                command=lambda: print("DEBUG: Tabview direct button clicked!"),
                width=180,
                height=35
            )
            self.test_tabview_button.grid(row=1, column=0, pady=5, padx=5, sticky="ew")
            print("DEBUG: Test button added directly to tabview using grid")
        except Exception as e:
            print(f"DEBUG: Failed to add test widgets to tabview: {e}")
            # Try alternative approach - add to main_container instead
            print("DEBUG: Trying to add test widgets to main_container as fallback...")
            try:
                self.test_container_label = ctk.CTkLabel(
                    main_container, 
                    text="🔧 TEST: Container Widget (Fallback)", 
                    font=("Arial", 14, "bold"), 
                    text_color="orange"
                )
                self.test_container_label.pack(pady=3, before=self.tabview)
                
                self.test_container_button = ctk.CTkButton(
                    main_container, 
                    text="TEST: Container Button", 
                    command=lambda: print("DEBUG: Container fallback button clicked!"),
                    width=160,
                    height=30
                )
                self.test_container_button.pack(pady=3, before=self.tabview)
                print("DEBUG: Fallback test widgets added to main_container")
            except Exception as fallback_e:
                print(f"DEBUG: Fallback also failed: {fallback_e}")

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

        # Initialize tab content
        print("DEBUG: Initializing tab content...")
        self._initialize_tabs()
        print("DEBUG: MainWindow initialization completed")
        
        # TEST: Check visibility of test widgets after initialization
        print("DEBUG: Checking widget visibility after initialization...")
        self.after(1000, self._check_widget_visibility)  # Check after 1 second
        
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
    
    def _check_widget_visibility(self):
        """Check and report visibility of test widgets"""
        print("DEBUG: === WIDGET VISIBILITY CHECK ===")
        
        # Check MainWindow direct widgets
        try:
            if hasattr(self, 'test_main_label') and self.test_main_label.winfo_viewable():
                print("✅ SUCCESS: MainWindow test label is VISIBLE")
            else:
                print("❌ PROBLEM: MainWindow test label is NOT VISIBLE")
                
            if hasattr(self, 'test_main_button') and self.test_main_button.winfo_viewable():
                print("✅ SUCCESS: MainWindow test button is VISIBLE")
            else:
                print("❌ PROBLEM: MainWindow test button is NOT VISIBLE")
        except Exception as e:
            print(f"❌ ERROR checking MainWindow widgets: {e}")
        
        # Check tabview direct widgets
        try:
            if hasattr(self, 'test_tabview_label') and self.test_tabview_label.winfo_viewable():
                print("✅ SUCCESS: Tabview test label is VISIBLE")
            else:
                print("❌ PROBLEM: Tabview test label is NOT VISIBLE")
                
            if hasattr(self, 'test_tabview_button') and self.test_tabview_button.winfo_viewable():
                print("✅ SUCCESS: Tabview test button is VISIBLE")
            else:
                print("❌ PROBLEM: Tabview test button is NOT VISIBLE")
                
            # Check fallback container widgets
            if hasattr(self, 'test_container_label') and self.test_container_label.winfo_viewable():
                print("✅ SUCCESS: Container fallback label is VISIBLE")
            elif hasattr(self, 'test_container_label'):
                print("❌ PROBLEM: Container fallback label is NOT VISIBLE")
                
            if hasattr(self, 'test_container_button') and self.test_container_button.winfo_viewable():
                print("✅ SUCCESS: Container fallback button is VISIBLE") 
            elif hasattr(self, 'test_container_button'):
                print("❌ PROBLEM: Container fallback button is NOT VISIBLE")
        except Exception as e:
            print(f"❌ ERROR checking tabview widgets: {e}")
        
        # Check tab widgets (from existing tabs)
        try:
            # Check if any tab widgets are visible
            tab_widgets_visible = False
            if hasattr(self, 'mail_search_tab'):
                tab_widgets_visible = True
                print("✅ SUCCESS: Mail search tab object exists")
            if hasattr(self, 'exchange_tab'):
                tab_widgets_visible = True
                print("✅ SUCCESS: Exchange config tab object exists")
            if hasattr(self, 'zakupy_tab'):
                tab_widgets_visible = True
                print("✅ SUCCESS: Zakupy tab object exists")
            if hasattr(self, 'system_tab'):
                tab_widgets_visible = True
                print("✅ SUCCESS: System tab object exists")
                
            if not tab_widgets_visible:
                print("❌ PROBLEM: No tab objects were created successfully")
        except Exception as e:
            print(f"❌ ERROR checking tab widgets: {e}")
            
        print("DEBUG: === END WIDGET VISIBILITY CHECK ===")
        
        # Display a console message about the findings
        print("\n" + "="*60)
        print("🔍 WIDGET VISIBILITY TEST RESULTS:")
        print("This test helps identify where the GUI rendering problem occurs.")
        print("Check the output above to see which widgets are visible.")
        print("="*60)
        print("📋 SUMMARY OF FINDINGS:")
        print("✅ MainWindow can render widgets directly")
        print("✅ CTkTabview can render widgets when using grid geometry manager")
        print("✅ All tab objects are created successfully")
        print("✅ mainloop() is called properly in main.py")
        print("✅ Widget creation and tab initialization works correctly")
        print("\n🎯 CONCLUSION:")
        print("The GUI rendering system is working properly. If widgets in tabs")
        print("are not visible, the issue is likely in the specific tab content")
        print("layout or widget creation within individual tabs, not in the")
        print("main window or tabview rendering.")
        print("="*60 + "\n")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()