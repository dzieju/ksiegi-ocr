from exchangelib.winzone import MS_TIMEZONE_TO_IANA_MAP

# Mapowanie niestandardowej strefy czasowej Exchange na prawidłową strefę IANA
MS_TIMEZONE_TO_IANA_MAP['Customized Time Zone'] = "Europe/Warsaw"

from gui.main_window import MainWindow
import tkinter as tk

if __name__ == "__main__":
    print("DEBUG: Starting application...")
    # Utwórz główne okno
    app = MainWindow()
    print("DEBUG: MainWindow created successfully")
    # Ustaw domyślny rozmiar okna (np. 1400x900)
    app.geometry("1400x900")
    print("DEBUG: Window geometry set to 1400x900")
    # Ustaw minimalny rozmiar (np. 1200x700)
    app.minsize(1200, 700)
    print("DEBUG: Window minimum size set to 1200x700")
    print("DEBUG: Starting mainloop()...")
    app.mainloop()
    print("DEBUG: mainloop() completed - application closed")