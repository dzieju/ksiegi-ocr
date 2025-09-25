#!/usr/bin/env python3
"""
Dark Mode Theme Support

PERFORMANCE NOTE: Lightweight module - no heavy dependencies.
Uses only built-in tkinter theming, so no optimization needed.
"""
import tkinter as tk
from tkinter import ttk

DARK_BG = "#222"
DARK_FG = "#EEE"

def toggle_theme():
    """Toggle between light and dark themes"""
    root = tk._get_default_root()
    style = ttk.Style()
    current = style.theme_use()
    if current == "clam":
        style.theme_use("alt")
        style.configure(".", foreground=DARK_FG, background=DARK_BG)
        style.configure("TButton", foreground=DARK_FG, background=DARK_BG)
        root.configure(background=DARK_BG)
    else:
        style.theme_use("clam")
        root.configure(background="SystemButtonFace")