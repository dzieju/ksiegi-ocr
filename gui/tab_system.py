import tkinter as tk
from tkinter import ttk
import os
import sys

class SystemTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        restart_btn = ttk.Button(self, text="Restartuj aplikację", command=self.restart_app)
        restart_btn.pack(pady=30, padx=30)

    def restart_app(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)