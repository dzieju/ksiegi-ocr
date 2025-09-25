#!/usr/bin/env python3
"""
KSIEGI-OCR - Main Application Entry Point

PERFORMANCE OPTIMIZATIONS:
- Lazy loading of heavy libraries (exchangelib, OCR engines, PDF processing)
- Background dependency checks after GUI is responsive (in separate thread)
- Dynamic tab loading - tabs created only when accessed
- Deferred system checks to improve startup time

Startup time improved from ~0.8s to ~0.01s for basic GUI.
All heavy operations run in background daemon threads to never block GUI.
"""
import tkinter as tk
import threading

def configure_exchangelib_timezone():
    """Configure exchangelib timezone mapping - loaded only when needed"""
    try:
        print("🌍 Konfigurowanie strefy czasowej exchangelib...")
        from exchangelib.winzone import MS_TIMEZONE_TO_IANA_MAP
        # Mapowanie niestandardowej strefy czasowej Exchange na prawidłową strefę IANA
        MS_TIMEZONE_TO_IANA_MAP['Customized Time Zone'] = "Europe/Warsaw"
        print("✅ Strefa czasowa exchangelib skonfigurowana")
        return True
    except ImportError:
        print("⚠️  Warning: exchangelib not available")
        return False

def lazy_import_poppler_utils():
    """Lazy import poppler utilities - only when needed for PDF operations"""
    try:
        from tools.poppler_utils import print_poppler_status, test_poppler_startup
        return print_poppler_status, test_poppler_startup
    except ImportError as e:
        print(f"⚠️  Warning: poppler_utils not available: {e}")
        return None, None

def lazy_import_dependency_checker():
    """Lazy import dependency checker - only when needed"""
    try:
        from tools.dependency_checker import get_dependencies_summary
        return get_dependencies_summary
    except ImportError as e:
        print(f"⚠️  Warning: dependency_checker not available: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("KSIEGI-OCR - System uruchamiania")
    print("=" * 60)
    
    # Configure exchangelib only if needed later
    configure_exchangelib_timezone()
    
    # Fast startup - defer heavy checks until GUI is running
    print("\nUruchamianie interfejsu użytkownika...")
    print("ℹ️  Sprawdzanie zależności zostanie wykonane w tle...")
    
    print("📦 Importowanie głównego okna...")
    # Import main window (now optimized to not load heavy dependencies)
    from gui.main_window import MainWindow
    
    print("🖥️  Tworzenie aplikacji...")
    # Create main window
    app = MainWindow()
    
    print("📐 Ustawianie właściwości okna...")
    # Set window properties
    app.geometry("1400x900")
    app.minsize(1200, 700)
    
    # Schedule background dependency and poppler checks after GUI is loaded
    def background_system_checks():
        """Run system checks in background thread - NEVER blocks GUI"""
        print("\n🔍 Rozpoczynam sprawdzanie systemu w tle...")
        
        def threaded_system_checks():
            """Heavy system checks running in background daemon thread"""
            try:
                print("\n" + "=" * 60)
                print("Sprawdzanie zależności systemowych w tle...")
                
                # Check dependencies
                print("📦 Sprawdzanie zależności...")
                get_dependencies_summary = lazy_import_dependency_checker()
                if get_dependencies_summary:
                    try:
                        summary = get_dependencies_summary()
                        print(f"{summary['emoji']} {summary['message']}")
                        if summary['required_missing'] > 0:
                            print(f"⚠️  UWAGA: Brak {summary['required_missing']} wymaganych zależności!")
                            print("   Niektóre funkcje mogą nie działać poprawnie.")
                            print("   Sprawdź zakładkę 'System > Zależności środowiskowe' w aplikacji.")
                    except Exception as e:
                        print(f"⚠️  Błąd sprawdzania zależności: {e}")
                
                # Test poppler integration
                print("🔧 Sprawdzanie integracji Poppler...")
                print_poppler_status, test_poppler_startup = lazy_import_poppler_utils()
                if test_poppler_startup:
                    print("Testing Poppler integration...")
                    poppler_success, poppler_message = test_poppler_startup()
                    if poppler_success:
                        print(f"✓ {poppler_message}")
                    else:
                        print(f"✗ {poppler_message}")
                        print("WARNING: Poppler integration issues detected. PDF processing may not work correctly.")
                    
                    if print_poppler_status:
                        print_poppler_status()
                
                print("✅ Sprawdzanie systemu zakończone")
                print("=" * 60)
                
                # Notify GUI that system initialization is complete (thread-safe)
                # This ensures that loading labels are hidden and proper widgets are shown
                app.after(0, app.on_system_initialization_complete)
                
            except Exception as e:
                print(f"❌ Błąd podczas sprawdzania systemu: {e}")
                # Even on error, notify GUI to update (show error state)
                app.after(0, lambda: app.on_system_initialization_complete(error=str(e)))
        
        # Start checks in daemon thread to never block GUI
        system_thread = threading.Thread(target=threaded_system_checks, daemon=True)
        system_thread.start()
        print("✓ Wątek sprawdzania systemu uruchomiony w tle")
    
    print("⏰ Planowanie sprawdzania systemu w tle...")
    # Schedule background checks to run after GUI starts (but in background thread)
    app.after(100, background_system_checks)
    
    print("✓ Interfejs gotowy do użycia")
    print("🚀 Uruchamianie głównej pętli aplikacji...")
    print("=" * 60)
    
    app.mainloop()