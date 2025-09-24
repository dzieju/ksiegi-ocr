import sys
import traceback

from exchangelib.winzone import MS_TIMEZONE_TO_IANA_MAP

# Mapowanie niestandardowej strefy czasowej Exchange na prawidłową strefę IANA
MS_TIMEZONE_TO_IANA_MAP['Customized Time Zone'] = "Europe/Warsaw"

from gui.main_window import MainWindow
import tkinter as tk

# Import poppler utilities for PDF processing support
from tools.poppler_utils import print_poppler_status, test_poppler_startup

# Import OCR engines for Tesseract detection
from tools.ocr_engines import ocr_manager

# Live logger for stderr restoration during development
from tools.live_logger import get_live_logger

def main():
    """Main application entry point with error handling."""
    
    # Store original stdout and stderr for robust error handling
    # This ensures errors are always visible in console even if logs are redirected
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    app = None
    
    try:
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
        
        # Redirect stdout/stderr to original console streams for robust error handling
        # This ensures all GUI initialization errors are visible in console
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        
        # Comprehensive GUI initialization with full error handling
        app = MainWindow()
        
        # Ustaw domyślną geometrię okna (900x700+100+100) zgodnie z wymaganiami
        app.geometry("900x700+100+100")
        # Ustaw minimalny rozmiar
        app.minsize(800, 600)
        
        print("✓ GUI successfully initialized")
        
        # Start the main event loop
        print("Starting main event loop...")
        app.mainloop()
        
    except Exception as startup_error:
        print(f"\n{'='*60}", file=original_stderr)
        print("✗ FATAL ERROR during application startup:", file=original_stderr)
        print(f"{'='*60}", file=original_stderr)
        print("FULL TRACEBACK:", file=original_stderr)
        traceback.print_exc(file=original_stderr)
        print(f"{'='*60}", file=original_stderr)
        print("Application cannot start. Please check the error details above.", file=original_stderr)
        print("\nPress Enter to exit...", file=original_stderr)
        try:
            input()  # Prevent shell from closing immediately
        except (EOFError, KeyboardInterrupt):
            pass  # Handle cases where input is not available
        sys.exit(1)
    
    finally:
        # This finally block is no longer needed as mainloop is now in try block
        pass

if __name__ == "__main__":
    main()