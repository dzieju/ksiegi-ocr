from exchangelib.winzone import MS_TIMEZONE_TO_IANA_MAP

# Mapowanie niestandardowej strefy czasowej Exchange na prawidłową strefę IANA
MS_TIMEZONE_TO_IANA_MAP['Customized Time Zone'] = "Europe/Warsaw"

from gui.main_window import MainWindow
import tkinter as tk

# Import poppler utilities for PDF processing support
from tools.poppler_utils import print_poppler_status, test_poppler_startup

# Import dependency checker for startup validation
from tools.dependency_checker import get_dependencies_summary

# Import logger for application startup logging
from tools import logger

if __name__ == "__main__":
    # Log application startup
    logger.log("=== APLIKACJA KSIEGI-OCR - START ===")
    logger.log("Rozpoczynanie inicjalizacji aplikacji")
    
    print("=" * 60)
    print("KSIEGI-OCR - System uruchamiania")
    print("=" * 60)
    
    # Check system dependencies
    print("\nSprawdzanie zależności systemowych...")
    logger.log("Sprawdzanie zależności systemowych")
    try:
        summary = get_dependencies_summary()
        print(f"{summary['emoji']} {summary['message']}")
        logger.log(f"Status zależności: {summary['message']}")
        if summary['required_missing'] > 0:
            print(f"⚠️  UWAGA: Brak {summary['required_missing']} wymaganych zależności!")
            print("   Niektóre funkcje mogą nie działać poprawnie.")
            print("   Sprawdź zakładkę 'System > Zależności środowiskowe' w aplikacji.")
            logger.log(f"UWAGA: Brak {summary['required_missing']} wymaganych zależności")
    except Exception as e:
        print(f"⚠️  Błąd sprawdzania zależności: {e}")
        logger.log(f"Błąd sprawdzania zależności: {e}")
    
    # Test poppler integration on startup
    print("\nTesting Poppler integration...")
    logger.log("Testowanie integracji Poppler")
    poppler_success, poppler_message = test_poppler_startup()
    if poppler_success:
        print(f"✓ {poppler_message}")
        logger.log(f"Poppler OK: {poppler_message}")
    else:
        print(f"✗ {poppler_message}")
        print("WARNING: Poppler integration issues detected. PDF processing may not work correctly.")
        logger.log(f"Błąd Poppler: {poppler_message}")
    
    # Show detailed poppler status
    print_poppler_status()
    
    print("\nStarting GUI application...")
    print("=" * 60)
    logger.log("Uruchamianie interfejsu graficznego")
    
    # Utwórz główne okno
    logger.log("Tworzenie głównego okna aplikacji")
    app = MainWindow()
    # Ustaw domyślny rozmiar okna (np. 1400x900)
    app.geometry("1400x900")
    # Ustaw minimalny rozmiar (np. 1200x700)
    app.minsize(1200, 700)
    logger.log("Główne okno utworzone, rozpoczynanie pętli głównej")
    logger.log("=== INICJALIZACJA APLIKACJI ZAKOŃCZONA ===")
    app.mainloop()