import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta, date
from exchangelib import Credentials, Account, Configuration, DELEGATE, errors
import pdfplumber
from tkcalendar import DateEntry
import traceback
import pdfminer

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

        self.date_from_var = tk.StringVar()
        self.date_to_var = tk.StringVar()
        self.search_all_folders_var = tk.BooleanVar()
        self.excluded_folders = set()
        self.exclude_mode_var = tk.BooleanVar(value=False)  # False: pomijane, True: tylko te

        self.results = []
        self.matched_items = []

        ttk.Label(self, text="Podaj NIP do wyszukania:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self, textvariable=self.nip_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self, text="Wybierz folder poczty:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.folder_combo = ttk.Combobox(self, textvariable=self.folder_var, width=50, state="readonly")
        self.folder_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self, text="Folder docelowy:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.target_combo = ttk.Combobox(self, textvariable=self.target_folder_var, width=50, state="readonly")
        self.target_combo.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(self, text="Odśwież foldery", command=self.load_folders).grid(row=1, column=2, rowspan=2, padx=5, pady=5)
        ttk.Button(self, text="Pomiń foldery...", command=self.open_exclude_folders_dialog).grid(row=1, column=3, rowspan=2, padx=5, pady=5)

        ttk.Checkbutton(
            self,
            text="Przeszukaj całą skrzynkę pocztową (wszystkie foldery)",
            variable=self.search_all_folders_var
        ).grid(row=2, column=2, sticky="w", padx=5, pady=5)

        ttk.Label(self, text="Data od:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        try:
            self.date_from_entry = DateEntry(self, textvariable=self.date_from_var, width=12, date_pattern="yyyy-mm-dd", locale="pl_PL")
        except Exception:
            self.date_from_entry = DateEntry(self, textvariable=self.date_from_var, width=12, date_pattern="yyyy-mm-dd")
        self.date_from_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self, text="Data do:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        try:
            self.date_to_entry = DateEntry(self, textvariable=self.date_to_var, width=12, date_pattern="yyyy-mm-dd", locale="pl_PL")
        except Exception:
            self.date_to_entry = DateEntry(self, textvariable=self.date_to_var, width=12, date_pattern="yyyy-mm-dd")
        self.date_to_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self, text="Szybki wybór dat:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        frame = ttk.Frame(self)
        frame.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(frame, text="Ostatnie 7 dni", command=lambda: self.set_date_range("7dni")).pack(side="left", padx=2)
        ttk.Button(frame, text="Bieżący miesiąc", command=lambda: self.set_date_range("aktualny_miesiac")).pack(side="left", padx=2)
        ttk.Button(frame, text="Poprzedni miesiąc", command=lambda: self.set_date_range("poprzedni_miesiac")).pack(side="left", padx=2)
        ttk.Button(frame, text="Ostatnie 3 miesiące", command=lambda: self.set_date_range("3miesiace")).pack(side="left", padx=2)
        ttk.Button(frame, text="Wyczyść", command=lambda: self.set_date_range("wyczysc")).pack(side="left", padx=2)

        ttk.Button(self, text="Szukaj faktur", command=self.search_invoices).grid(row=6, column=1, pady=10)

        self.tree = ttk.Treeview(
            self,
            columns=("subject", "date", "filename", "folder"),
            show="headings",
            height=15
        )
        self.tree.heading("subject", text="Temat")
        self.tree.heading("date", text="Data")
        self.tree.heading("filename", text="Plik PDF")
        self.tree.heading("folder", text="Folder/Ścieżka")
        self.tree.column("subject", width=300)
        self.tree.column("date", width=100)
        self.tree.column("filename", width=250)
        self.tree.column("folder", width=600, minwidth=300, stretch=True)
        self.tree.grid(row=7, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        self.tree.bind("<Double-1>", self.preview_pdf)

        self.grid_rowconfigure(7, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)

        ttk.Button(self, text="Zapisz wybrany PDF", command=self.save_pdf).grid(row=8, column=1, pady=5)
        ttk.Button(self, text="Przenieś wiadomości", command=self.move_messages).grid(row=9, column=1, pady=10)

        self.load_last_state()
        self.load_folders()
        os.makedirs(TEMP_FOLDER, exist_ok=True)

    def set_date_range(self, mode):
        today = date.today()
        if mode == "7dni":
            self.date_from_var.set((today - timedelta(days=7)).strftime("%Y-%m-%d"))
            self.date_to_var.set(today.strftime("%Y-%m-%d"))
        elif mode == "aktualny_miesiac":
            self.date_from_var.set(today.replace(day=1).strftime("%Y-%m-%d"))
            self.date_to_var.set(today.strftime("%Y-%m-%d"))
        elif mode == "poprzedni_miesiac":
            first_today = today.replace(day=1)
            last_prev = first_today - timedelta(days=1)
            first_prev = last_prev.replace(day=1)
            self.date_from_var.set(first_prev.strftime("%Y-%m-%d"))
            self.date_to_var.set(last_prev.strftime("%Y-%m-%d"))
        elif mode == "3miesiace":
            month = today.month - 2
            year = today.year
            if month <= 0:
                month += 12
                year -= 1
            first_3ago = date(year, month, 1)
            self.date_from_var.set(first_3ago.strftime("%Y-%m-%d"))
            self.date_to_var.set(today.strftime("%Y-%m-%d"))
        elif mode == "wyczysc":
            self.date_from_var.set("")
            self.date_to_var.set("")

    def get_folder_path(self, folder):
        names = []
        while folder and hasattr(folder, "name") and folder.name:
            names.append(folder.name)
            folder = folder.parent
        return "/".join(reversed(names))

    def open_exclude_folders_dialog(self):
        if not self.folder_list:
            messagebox.showwarning("Brak folderów", "Najpierw odśwież listę folderów.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Wybierz foldery do pominięcia lub wyłączności")
        dialog.minsize(400, 200)
        dialog.geometry("700x450")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        dialog.configure(borderwidth=4, relief="solid")

        # Tryb wykluczania
        mode_frame = tk.Frame(dialog)
        mode_frame.pack(fill="x", side="top", padx=10, pady=(8, 10))
        tk.Checkbutton(
            mode_frame,
            text="Szukaj tylko w tych folderach (pozostałe pomiń)",
            variable=self.exclude_mode_var
        ).pack(anchor="w")

        main_frame = tk.Frame(dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        x_scroll = tk.Scrollbar(main_frame, orient="horizontal")
        y_scroll = tk.Scrollbar(main_frame, orient="vertical")
        canvas = tk.Canvas(main_frame, bd=0, highlightthickness=0,
                           xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        x_scroll.config(command=canvas.xview)
        y_scroll.config(command=canvas.yview)
        x_scroll.pack(side="bottom", fill="x")
        y_scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner_labelframe = tk.LabelFrame(canvas, text="Zaznacz foldery", padx=6, pady=6, borderwidth=2, relief="groove")
        canvas.create_window((0, 0), window=inner_labelframe, anchor="nw")

        columns = max(4, min(len(self.folder_list), 8))
        self.exclude_vars = {}
        for idx, folder in enumerate(self.folder_list):
            var = tk.BooleanVar(value=folder in self.excluded_folders)
            chk = tk.Checkbutton(inner_labelframe, text=folder, variable=var, anchor="w", takefocus=True)
            row = idx // columns
            col = idx % columns
            chk.grid(row=row, column=col, sticky="w", padx=2, pady=2)
            self.exclude_vars[folder] = var
            inner_labelframe.grid_columnconfigure(col, weight=1)

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner_labelframe.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig("all", width=e.width))

        inner_labelframe.focus_set()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill="x", side="bottom")
        ttk.Button(
            btn_frame, text="Wyczyść wybór",
            command=lambda: [v.set(False) for v in self.exclude_vars.values()]
        ).pack(side="left", padx=5, pady=10)
        ttk.Button(
            btn_frame, text="Zapisz wybór i zamknij",
            command=lambda: self._save_excluded_folders_and_close(dialog)
        ).pack(side="right", padx=5, pady=10)

    def _save_excluded_folders_and_close(self, dialog):
        self.excluded_folders = {f for f, v in self.exclude_vars.items() if v.get()}
        self.save_last_state()
        dialog.destroy()

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
                if self.folder_var.get() not in self.folder_list:
                    self.folder_var.set(self.folder_list[0])
                if self.target_folder_var.get() not in self.folder_list:
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
                    self.date_from_var.set(state.get("date_from", ""))
                    self.date_to_var.set(state.get("date_to", ""))
                    self.target_folder_var.set(state.get("target_folder", "Archiwum"))
                    self.search_all_folders_var.set(state.get("search_all_folders", False))
                    self.excluded_folders = set(state.get("excluded_folders", []))
                    self.exclude_mode_var.set(state.get("exclude_mode", False))
            except Exception:
                pass

    def save_last_state(self):
        state = {
            "last_folder": self.folder_var.get(),
            "last_nip": self.nip_var.get().strip(),
            "date_from": self.date_from_var.get(),
            "date_to": self.date_to_var.get(),
            "target_folder": self.target_folder_var.get(),
            "search_all_folders": self.search_all_folders_var.get(),
            "excluded_folders": list(self.excluded_folders),
            "exclude_mode": self.exclude_mode_var.get()
        }
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)

    def search_invoices(self):
        nip = self.nip_var.get().strip()
        folder_name = self.folder_var.get().strip()
        date_from_str = self.date_from_var.get()
        date_to_str = self.date_to_var.get()
        date_from = None
        date_to = None
        try:
            if date_from_str:
                date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
            if date_to_str:
                date_to = datetime.strptime(date_to_str, "%Y-%m-%d") + timedelta(days=1)
        except Exception as e:
            messagebox.showerror("Błąd daty", f"Nieprawidłowy format daty: {str(e)}")
            return

        self.results.clear()
        self.matched_items.clear()
        for row in self.tree.get_children():
            self.tree.delete(row)

        if not nip:
            messagebox.showwarning("Brak danych", "Wprowadź NIP.")
            return

        self.save_last_state()

        seen_filenames = set()

        try:
            if self.search_all_folders_var.get():
                if self.exclude_mode_var.get():
                    # Tryb: szukaj TYLKO w zaznaczonych folderach
                    folders_to_search = [
                        f for f in self.account.root.walk()
                        if hasattr(f, "name") and f.name in self.excluded_folders
                    ]
                else:
                    # Tryb: pomiń zaznaczone foldery (domyślny)
                    folders_to_search = [
                        f for f in self.account.root.walk()
                        if hasattr(f, "all") and (not hasattr(f, "name") or f.name not in self.excluded_folders)
                    ]
            else:
                folder = next((f for f in self.account.root.walk() if hasattr(f, "name") and f.name == folder_name), None)
                if folder is None:
                    messagebox.showerror("Błąd folderu", f"Nie znaleziono folderu: {folder_name}")
                    return
                if not self.exclude_mode_var.get():
                    if folder.name in self.excluded_folders:
                        messagebox.showwarning("Folder pominięty", f"Wybrany folder {folder_name} jest na liście wykluczonych.")
                        return
                else:
                    if folder.name not in self.excluded_folders:
                        messagebox.showwarning("Folder nie jest wybrany do przeszukania", f"Wybrany folder {folder_name} nie znajduje się na liście wybranych.")
                        return
                folders_to_search = [folder]

            for folder in folders_to_search:
                folder_path = self.get_folder_path(folder)
                try:
                    for item in folder.all().order_by("-datetime_received")[:200]:
                        dt = item.datetime_received
                        if date_from and dt < date_from.replace(tzinfo=dt.tzinfo):
                            continue
                        if date_to and dt >= date_to.replace(tzinfo=dt.tzinfo):
                            continue

                        for att in item.attachments:
                            if not att.name.lower().endswith(".pdf"):
                                continue

                            if att.name in seen_filenames:
                                continue
                            seen_filenames.add(att.name)

                            local_path = os.path.join(TEMP_FOLDER, att.name)
                            try:
                                with open(local_path, "wb") as f:
                                    f.write(att.content)

                                if os.path.getsize(local_path) < 100:
                                    os.remove(local_path)
                                    continue

                                try:
                                    pdf = pdfplumber.open(local_path)
                                    full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                                    pdf.close()
                                except (pdfminer.pdfdocument.PDFPasswordIncorrect,
                                        pdfminer.pdfparser.PDFSyntaxError,
                                        pdfplumber.utils.PdfminerException,
                                        Exception):
                                    try:
                                        os.remove(local_path)
                                    except Exception:
                                        pass
                                    continue

                                if nip in full_text:
                                    self.tree.insert(
                                        "",
                                        "end",
                                        values=(item.subject, item.datetime_received.date(), local_path, folder_path)
                                    )
                                    self.results.append(local_path)
                                    self.matched_items.append(item)
                                else:
                                    os.remove(local_path)
                            except Exception:
                                try:
                                    os.remove(local_path)
                                except Exception:
                                    pass
                except Exception as e:
                    if ("Access is denied" in str(e) or
                        "cannot access System folder" in str(e) or
                        isinstance(e, errors.ErrorAccessDenied)):
                        with open("pdf_error.log", "a", encoding="utf-8") as logf:
                            logf.write(f"Folder pominięty przez błąd dostępu: {folder_path}\n{str(e)}\n{'-'*40}\n")
                        continue
                    else:
                        tb = traceback.format_exc()
                        messagebox.showerror("Błąd folderu", f"{folder_path}\n{str(e)}\n\n{tb}")

        except Exception as e:
            tb = traceback.format_exc()
            messagebox.showerror("Błąd połączenia", f"{str(e)}\n\n{tb}")

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