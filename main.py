import sys
import traceback

# Wykomentowane importy dla ultra-minimalnego testu tkinter
# from exchangelib.winzone import MS_TIMEZONE_TO_IANA_MAP
# 
# # Mapowanie niestandardowej strefy czasowej Exchange na prawidłową strefę IANA
# MS_TIMEZONE_TO_IANA_MAP['Customized Time Zone'] = "Europe/Warsaw"
# 
# from gui.main_window import MainWindow
# import tkinter as tk
# 
# # Import poppler utilities for PDF processing support
# from tools.poppler_utils import print_poppler_status, test_poppler_startup
# 
# # Import OCR engines for Tesseract detection
# from tools.ocr_engines import ocr_manager
# 
# # Live logger for stderr restoration during development
# from tools.live_logger import get_live_logger

def main():
    """Main application entry point with error handling."""
    
    # Store original stdout and stderr for robust error handling
    # This ensures errors are always visible in console even if logs are redirected
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    try:
        print("=" * 60)
        print("ULTRA-MINIMALNY TEST OKNA TKINTER")
        print("=" * 60)
        
        # Redirect stdout/stderr to original console streams for robust error handling
        # This ensures all GUI initialization errors are visible in console
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        
        print("Tworzenie okna testowego tkinter...")
        
        # Ultra-minimalny test okna tkinter
        import tkinter as tk
        
        root = tk.Tk()
        root.title("Test Window")
        root.geometry("900x700+100+100")
        
        # Dodaj etykietę z wymaganym tekstem
        label = tk.Label(root, text="Czy widzisz to okno?", font=("Arial", 16))
        label.pack(expand=True)
        
        print("✓ Okno tkinter pomyślnie utworzone")
        print("Uruchamianie pętli zdarzeń...")
        
        # Start the main event loop
        root.mainloop()
        
        print("Okno zostało zamknięte.")
        
    except Exception as startup_error:
        print(f"\n{'='*60}", file=original_stderr)
        print("✗ BŁĄD podczas testowania okna tkinter:", file=original_stderr)
        print(f"{'='*60}", file=original_stderr)
        print("PEŁNY TRACEBACK:", file=original_stderr)
        traceback.print_exc(file=original_stderr)
        print(f"{'='*60}", file=original_stderr)
        print("Test okna tkinter nie powiódł się. Sprawdź szczegóły błędu powyżej.", file=original_stderr)
        print("\nNaciśnij Enter aby wyjść...", file=original_stderr)
        try:
            input()  # Prevent shell from closing immediately
        except (EOFError, KeyboardInterrupt):
            pass  # Handle cases where input is not available
        sys.exit(1)

if __name__ == "__main__":
    main()