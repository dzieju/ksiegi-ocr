#!/usr/bin/env python3
"""
KSIEGI-OCR - Main Application Entry Point
Simple startup after reverting PR #132-#136 optimizations
"""
import tkinter as tk

def configure_exchangelib_timezone():
    """Configure exchangelib timezone mapping"""
    try:
        from exchangelib.winzone import MS_TIMEZONE_TO_IANA_MAP
        # Mapowanie niestandardowej strefy czasowej Exchange na prawidłową strefę IANA
        MS_TIMEZONE_TO_IANA_MAP['Customized Time Zone'] = "Europe/Warsaw"
        print("Strefa czasowa exchangelib skonfigurowana")
    except ImportError:
        print("Warning: exchangelib not available")

if __name__ == "__main__":
    print("KSIEGI-OCR - Uruchamianie aplikacji")
    
    # Configure exchangelib
    configure_exchangelib_timezone()
    
    # Import and create main window
    from gui.main_window import MainWindow
    
    # Create main window
    app = MainWindow()
    
    # Set window properties
    app.geometry("1200x800")
    app.minsize(1000, 600)
    
    print("Aplikacja gotowa")
    app.mainloop()