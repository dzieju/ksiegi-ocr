import sys
import traceback
import os

from exchangelib.winzone import MS_TIMEZONE_TO_IANA_MAP

# Mapowanie niestandardowej strefy czasowej Exchange na prawidłową strefę IANA
MS_TIMEZONE_TO_IANA_MAP['Customized Time Zone'] = "Europe/Warsaw"

from gui.main_window import MainWindow
import tkinter as tk

# Import poppler utilities for PDF processing support
from tools.poppler_utils import print_poppler_status, test_poppler_startup

# Import OCR engines for Tesseract detection
from tools.ocr_engines import ocr_manager

def main():
    """Main application entry point with error handling."""
    
    # Display OCR engine availability status (from PR #118)
    print_poppler_status()
    print()
    
    # Check OCR engine availability (PR #118 feature)
    print("Sprawdzanie dostępności silników OCR...")
    available_engines = ocr_manager.get_available_engines()
    if available_engines:
        print(f"✓ OCR engines available: {', '.join(available_engines)}")
    else:
        print("✗ No OCR engines available")
    print()
    
    # For debug mode: set KSIEGI_DEBUG=1 && python main.py
    debug_mode = os.environ.get('KSIEGI_DEBUG', '0') == '1'
    
    if debug_mode:
        # Debug mode: wrap GUI initialization in try/except for development
        try:
            # Initialize and run the main application
            app = MainWindow()
            app.geometry("900x700+100+100")  # Set default window geometry
            app.mainloop()
            
        except Exception as e:
            print(f"\n{'='*60}")
            print("✗ BŁĄD podczas inicjalizacji aplikacji:")
            print(f"{'='*60}")
            print("PEŁNY TRACEBACK:")
            traceback.print_exc()
            print(f"{'='*60}")
            print("Aplikacja nie mogła zostać uruchomiona. Sprawdź szczegóły błędu powyżej.")
            print("\nNaciśnij Enter aby wyjść...")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                pass
            sys.exit(1)
    else:
        # Production mode: run directly without exception handling
        app = MainWindow()
        app.geometry("900x700+100+100")  # Set default window geometry
        app.mainloop()

if __name__ == "__main__":
    main()