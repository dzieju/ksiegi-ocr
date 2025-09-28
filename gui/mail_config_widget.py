import tkinter as tk
from tkinter import ttk

AUTH_METHODS = ["PLAIN", "LOGIN", "CRAM-MD5", "OAUTH2"]

class MailConfigWidget(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.accounts = []
        self.selected_main_account = tk.IntVar(value=0)
        self.account_count_var = tk.IntVar(value=1)
        self.account_frames = []

        ttk.Label(self, text="Liczba kont pocztowych:").pack(anchor="w")
        count_spin = ttk.Spinbox(self, from_=1, to=10, textvariable=self.account_count_var, width=5, command=self.refresh_accounts)
        count_spin.pack(anchor="w", pady=5)
        self.accounts_frame = ttk.Frame(self)
        self.accounts_frame.pack(fill="both", expand=True)
        self.refresh_accounts()

    def refresh_accounts(self):
        for frame in self.account_frames:
            frame.destroy()
        self.account_frames = []

        for i in range(self.account_count_var.get()):
            frame = ttk.LabelFrame(self.accounts_frame, text=f"Konto pocztowe #{i+1}")
            frame.pack(fill="x", pady=5)
            # Typ konta
            type_var = tk.StringVar(value="IMAP/SMTP")
            ttk.Label(frame, text="Typ konta:").grid(row=0, column=0)
            ttk.Combobox(frame, values=["IMAP/SMTP", "POP3", "Exchange"], textvariable=type_var).grid(row=0, column=1)
            # Serwer, login, hasło, port, SSL/TLS
            ttk.Label(frame, text="Serwer:").grid(row=1, column=0)
            ttk.Entry(frame).grid(row=1, column=1)
            ttk.Label(frame, text="Login:").grid(row=2, column=0)
            ttk.Entry(frame).grid(row=2, column=1)
            ttk.Label(frame, text="Hasło:").grid(row=3, column=0)
            ttk.Entry(frame, show="*").grid(row=3, column=1)
            ttk.Label(frame, text="Port:").grid(row=4, column=0)
            ttk.Entry(frame).grid(row=4, column=1)
            ttk.Checkbutton(frame, text="SSL/TLS").grid(row=5, column=0, columnspan=2)
            # Metoda uwierzytelniania
            ttk.Label(frame, text="Metoda uwierzytelniania:").grid(row=6, column=0)
            auth_var = tk.StringVar(value=AUTH_METHODS[0])
            ttk.Combobox(frame, values=AUTH_METHODS, textvariable=auth_var).grid(row=6, column=1)
            # Przycisk wyboru konta głównego
            ttk.Radiobutton(frame, text="Ustaw jako główne", variable=self.selected_main_account, value=i).grid(row=7, column=0, columnspan=2)
            self.account_frames.append(frame)
