import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from exchangelib import Credentials, Account, Configuration, DELEGATE
import pdfplumber
from tkcalendar import DateEntry

CONFIG_FILE = "exchange_config.json"
STATE_FILE = "invoice_search_state.json"
TEMP_FOLDER = "temp_invoices"

class InvoiceSearchTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.nip_var = tk.StringVar()
        self.folder_var = tk.StringVar()
        self.target_folder_var = tk.StringVar()
        self.folder_list = []
        self.results = []
        self.matched_items = []

        # Get default dates: from = first day of current month, to = today
        today = datetime.now().date()
        first_day_of_month = datetime(today.year, today.month, 1).date()
        
        self.date_from = first_day_of_month
        self.date_to = today

        ttk.Label(self, text="Podaj NIP do wyszukania:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self, textvariable=self.nip_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self, text="Wybierz folder poczty:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.folder_combo = ttk.Combobox(self, textvariable=self.folder_var, width=50, state="readonly")
        self.folder_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self, text="Folder docelowy:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.target_combo = ttk.Combobox(self, textvariable=self.target_folder_var, width=50, state="readonly")
        self.target_combo.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(self, text="Odśwież foldery", command=self.load_folders).grid(row=1, column=2, rowspan=2, padx=5, pady=5)

        ttk.Label(self, text="Data od:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.date_from_entry = DateEntry(self, width=12, background='darkblue', foreground='white', borderwidth=2, year=self.date_from.year, month=self.date_from.month, day=self.date_from.day)
        self.date_from_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(self, text="Data do:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.date_to_entry = DateEntry(self, width=12, background='darkblue', foreground='white', borderwidth=2, year=self.date_to.year, month=self.date_to.month, day=self.date_to.day)
        self.date_to_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        ttk.Button(self, text="Szukaj faktur", command=self.search_invoices).grid(row=5, column=1, pady=10)

        self.tree = ttk.Treeview(self, columns=("subject", "date", "filename"), show="headings", height=15)
        self.tree.heading("subject", text="Temat")
        self.tree.heading("date", text="Data")
        self.tree.heading("filename", text="Plik PDF")
        self.tree.column("subject", width=300)
        self.tree.column("date", width=100)
        self.tree.column("filename", width=250)
        self.tree.grid(row=6, column=0, columnspan=3, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.preview_pdf)

        ttk.Button(self, text="Zapisz wybrany PDF", command=self.save_pdf).grid(row=7, column=1, pady=5)
        ttk.Button(self, text="Przenieś wiadomości", command=self.move_messages).grid(row=8, column=1, pady=10)

        self.load_folders()
        self.load_last_state()
        os.makedirs(TEMP_FOLDER, exist_ok=True)

    def load_folders(self):
        if not os.path.exists(CONFIG_FILE):
            messagebox.showerror("Brak konfiguracji", "Nie znaleziono pliku exchange_config.json.")
            return

        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)

            creds = Credentials(username=cfg["username"], password=cfg["password"])
            config = Configuration(server=cfg["server"], credentials=creds)
            self.account = Account(primary_smtp_address=cfg["email"], config=config, autodiscover=False, access_type=DELEGATE)

            self.folder_list = [f.name for f in self.account.root.walk() if hasattr(f, "name") and f.name]
            self.folder_list.sort()

            self.folder_combo["values"] = self.folder_list
            self.target_combo["values"] = self.folder_list

            if self.folder_list:
                self.folder_var.set(self.folder_list[0])
                self.target_folder_var.set(self.folder_list[-1])

        except Exception as e:
            messagebox.showerror("Błąd połączenia", str(e))

    def load_last_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    state = json.load(f)
                    self.folder_var.set(state.get("last_folder", "Inbox"))
                    self.nip_var.set(state.get("last_nip", ""))
                    self.target_folder_var.set(state.get("target_folder", "Archiwum"))
                    
                    # Load saved dates if available, otherwise use defaults
                    if "date_from" in state:
                        try:
                            date_from = datetime.strptime(state["date_from"], "%Y-%m-%d").date()
                            self.date_from_entry.set_date(date_from)
                        except:
                            pass
                    
                    if "date_to" in state:
                        try:
                            date_to = datetime.strptime(state["date_to"], "%Y-%m-%d").date()
                            self.date_to_entry.set_date(date_to)
                        except:
                            pass
            except:
                pass

    def save_last_state(self):
        state = {
            "last_folder": self.folder_var.get(),
            "last_nip": self.nip_var.get().strip(),
            "date_from": self.date_from_entry.get_date().strftime("%Y-%m-%d"),
            "date_to": self.date_to_entry.get_date().strftime("%Y-%m-%d"),
            "target_folder": self.target_folder_var.get()
        }
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)

    def search_invoices(self):
        nip = self.nip_var.get().strip()
        folder_name = self.folder_var.get().strip()
        
        # Get dates from DateEntry widgets
        date_from = self.date_from_entry.get_date()
        date_to = self.date_to_entry.get_date()

        self.results.clear()
        self.matched_items.clear()
        for row in self.tree.get_children():
            self.tree.delete(row)

        if not nip or not folder_name:
            messagebox.showwarning("Brak danych", "Wprowadź NIP i wybierz folder.")
            return
            
        if not date_from or not date_to:
            messagebox.showerror("Błąd dat", "Proszę wybrać obie daty - od i do.")
            return
            
        if date_from > date_to:
            messagebox.showerror("Błąd dat", "Data 'od' nie może być późniejsza niż data 'do'.")
            return

        self.save_last_state()

        try:
            folder = next((f for f in self.account.root.walk() if hasattr(f, "name") and f.name == folder_name), None)
            if folder is None:
                messagebox.showerror("Błąd folderu", f"Nie znaleziono folderu: {folder_name}")
                return

            # Convert dates to datetime for comparison (include full day)
            date_from_dt = datetime.combine(date_from, datetime.min.time()).replace(tzinfo=timezone.utc)
            date_to_dt = datetime.combine(date_to, datetime.max.time()).replace(tzinfo=timezone.utc)

            for item in folder.all().order_by("-datetime_received")[:200]:
                # Check if email date is within the selected range (inclusive)
                if not (date_from_dt <= item.datetime_received <= date_to_dt):
                    continue

                for att in item.attachments:
                    if not att.name.lower().endswith(".pdf"):
                        continue

                    local_path = os.path.join(TEMP_FOLDER, att.name)
                    try:
                        with open(local_path, "wb") as f:
                            f.write(att.content)

                        pdf = pdfplumber.open(local_path)
                        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                        pdf.close()

                        if nip in full_text:
                            self.tree.insert("", "end", values=(item.subject, item.datetime_received.date(), local_path))
                            self.results.append(local_path)
                            self.matched_items.append(item)
                        else:
                            os.remove(local_path)

                    except Exception as e:
                        messagebox.showerror("Błąd PDF", f"{att.name}: {str(e)}")

        except Exception as e:
            messagebox.showerror("Błąd połączenia", str(e))

    def preview_pdf(self, event):
        selected = self.tree.focus()
        if not selected:
            return

        values = self.tree.item(selected, "values")
        filename = values[2]

        try:
            subprocess.Popen([filename], shell=True)
        except Exception as e:
            messagebox.showerror("Błąd podglądu", str(e))

    def save_pdf(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Brak wyboru", "Wybierz plik PDF z listy.")
            return

        values = self.tree.item(selected, "values")
        source_path = values[2]
        suggested_name = os.path.basename(source_path)

        dest_path = filedialog.asksaveasfilename(
            initialfile=suggested_name,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )

        if dest_path:
            try:
                shutil.copy(source_path, dest_path)
                messagebox.showinfo("Zapisano", f"Plik zapisano jako:\n{dest_path}")
            except Exception as e:
                messagebox.showerror("Błąd zapisu", str(e))

    def move_messages(self):
        target_name = self.target_folder_var.get().strip()
        if not target_name:
            messagebox.showwarning("Brak folderu docelowego", "Wybierz folder docelowy.")
            return

        try:
            target_folder = next((f for f in self.account.root.walk() if hasattr(f, "name") and f.name == target_name), None)
            if target_folder is None:
                messagebox.showerror("Błąd folderu", f"Nie znaleziono folderu docelowego: {target_name}")
                return

            moved = 0
            for item in self.matched_items:
                item.move(to_folder=target_folder)
                moved += 1

            messagebox.showinfo("Przeniesiono", f"Przeniesiono {moved} wiadomości do folderu: {target_name}")

        except Exception as e:
            messagebox.showerror("Błąd przenoszenia", str(e))