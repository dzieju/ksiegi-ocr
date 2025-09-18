from gui.main_window import MainWindow
import tkinter as tk

if __name__ == "__main__":
    # Utwórz główne okno
    app = MainWindow()
    # Ustaw domyślny rozmiar okna (np. 1400x900)
    app.geometry("1400x900")
    # Ustaw minimalny rozmiar (np. 1200x700)
    app.minsize(1200, 700)
    app.mainloop()