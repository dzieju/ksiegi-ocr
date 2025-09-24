from exchangelib.winzone import MS_TIMEZONE_TO_IANA_MAP

# Mapowanie niestandardowej strefy czasowej Exchange na prawidłową strefę IANA
MS_TIMEZONE_TO_IANA_MAP['Customized Time Zone'] = "Europe/Warsaw"

from gui.main_window import MainWindow
import tkinter as tk

# Import poppler utilities for PDF processing support
from tools.poppler_utils import print_poppler_status, test_poppler_startup

# Import OCR engines for Tesseract detection
from tools.ocr_engines import ocr_manager

if __name__ == "__main__":
    print("=" * 60)
    print("KSIEGI-OCR - System uruchamiania")
    print("=" * 60)
    
    # Test poppler integration on startup
    print("\nTesting Poppler integration...")
    poppler_success, poppler_message = test_poppler_startup()
    if poppler_success:
        print(f"✓ {poppler_message}")
    else:
        print(f"✗ {poppler_message}")
        print("WARNING: Poppler integration issues detected. PDF processing may not work correctly.")
    
    # Show detailed poppler status
    print_poppler_status()
    
    # Test OCR engines availability
    print("\nTesting OCR engines availability...")
    available_engines = ocr_manager.get_available_engines()
    if available_engines:
        print(f"✓ OCR engines available: {', '.join(available_engines)}")
        current_engine = ocr_manager.get_current_engine()
        if current_engine:
            print(f"  Current engine: {current_engine}")
    else:
        print("✗ No OCR engines available")
        print("  Check installation instructions displayed above")
    
    print("\nStarting GUI application...")
    print("=" * 60)
    
    # Utwórz główne okno
    app = MainWindow()
    # Ustaw domyślny rozmiar okna (np. 1400x900)
    app.geometry("1400x900")
    # Ustaw minimalny rozmiar (np. 1200x700)
    app.minsize(1200, 700)
    app.mainloop()