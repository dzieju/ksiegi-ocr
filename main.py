from exchangelib.winzone import MS_TIMEZONE_TO_IANA_MAP

# Mapowanie niestandardowej strefy czasowej Exchange na prawidłową strefę IANA
MS_TIMEZONE_TO_IANA_MAP['Customized Time Zone'] = "Europe/Warsaw"

from gui.main_window import MainWindow

if __name__ == "__main__":
    # Utwórz główne okno
    app = MainWindow()
    # Ustaw domyślny rozmiar okna
    app.geometry("1400x900")
    # Ustaw minimalny rozmiar
    app.minsize(1200, 700)
    app.mainloop()