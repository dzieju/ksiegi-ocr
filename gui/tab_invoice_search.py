import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
from datetime import datetime, timedelta, date
from tkcalendar import DateEntry

# Import our new modules
from mail.exchange_utils import ExchangeConnection
from mail.search_utils import EmailSearcher
from pdf.pdf_utils import PDFProcessor
from utils.state_utils import ApplicationStateManager

TEMP_FOLDER = "temp_invoices"

class InvoiceSearchTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Initialize utility classes
        self.exchange_connection = ExchangeConnection()
        self.pdf_processor = PDFProcessor()
        self.email_searcher = EmailSearcher(self.exchange_connection, self.pdf_processor)
        self.state_manager = ApplicationStateManager()

        # GUI variables
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

        # Search button and progress
        search_frame = ttk.Frame(self)
        search_frame.grid(row=6, column=1, pady=10)
        self.search_button = ttk.Button(search_frame, text="Szukaj faktur", command=self.toggle_search)
        self.search_button.pack(side="left", padx=(0, 10))
        
        self.progress_label = ttk.Label(search_frame, text="")
        self.progress_label.pack(side="left")

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

        # Start processing queues
        self._process_result_queue()
        self._process_progress_queue()

    def destroy(self):
        """Cleanup when widget is destroyed"""
        self.cancel_search()
        super().destroy()

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

    def toggle_search(self):
        """Toggle between starting and cancelling search"""
        if self.email_searcher.search_manager.is_search_active():
            self.cancel_search()
        else:
            self.search_invoices()

    def cancel_search(self):
        """Cancel ongoing search"""
        self.email_searcher.search_manager.cancel_search()
        self.progress_label.config(text="Anulowanie...")
        self.search_button.config(text="Szukaj faktur")

    def _process_result_queue(self):
        """Process results from worker threads"""
        try:
            results = self.email_searcher.search_manager.get_results()
            for result in results:
                if result['type'] == 'match_found':
                    self.tree.insert(
                        "",
                        "end",
                        values=(result['subject'], result['date'], result['local_path'], result['folder_path'])
                    )
                    self.results.append(result['local_path'])
                    self.matched_items.append(result['item'])
                elif result['type'] == 'search_complete':
                    self.search_button.config(text="Szukaj faktur")
                    self.progress_label.config(text=f"Zakończono. Znaleziono {len(self.results)} wyników.")
        except Exception as e:
            print(f"Błąd przetwarzania kolejki wyników: {e}")
        
        # Schedule next check
        self.after(100, self._process_result_queue)

    def _process_progress_queue(self):
        """Process progress updates from worker threads"""
        try:
            updates = self.email_searcher.search_manager.get_progress_updates()
            for progress in updates:
                self.progress_label.config(text=progress)
        except Exception as e:
            print(f"Błąd przetwarzania kolejki postępu: {e}")
        
        # Schedule next check
        self.after(100, self._process_progress_queue)

    def load_folders(self):
        print("Ładowanie folderów Exchange...")
        try:
            self.folder_list = self.exchange_connection.load_all_folders()
            self.folder_combo["values"] = self.folder_list
            self.target_combo["values"] = self.folder_list

            if self.folder_list:
                if self.folder_var.get() not in self.folder_list:
                    self.folder_var.set(self.folder_list[0])
                if self.target_folder_var.get() not in self.folder_list:
                    self.target_folder_var.set(self.folder_list[-1])
            print("Załadowano foldery.")
        except Exception as e:
            print(f"Błąd ładowania folderów: {e}")
            messagebox.showerror("Błąd połączenia", str(e))

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
        print("Zapisuję wykluczone foldery:", self.exclude_vars)
        self.excluded_folders = {f for f, v in self.exclude_vars.items() if v.get()}
        self.save_last_state()
        dialog.destroy()

    def load_last_state(self):
        """Load last application state."""
        widgets = {
            'folder_var': self.folder_var,
            'target_folder_var': self.target_folder_var,
            'search_all_folders_var': self.search_all_folders_var,
            'exclude_mode_var': self.exclude_mode_var,
            'nip_var': self.nip_var,
            'date_from_var': self.date_from_var,
            'date_to_var': self.date_to_var
        }
        self.state_manager.apply_state_to_widgets(widgets)
        # Load excluded folders separately
        self.excluded_folders = set(self.state_manager.current_state.get('excluded_folders', []))

    def save_last_state(self):
        """Save current application state."""
        self.state_manager.update_folder_settings(
            self.folder_var, self.target_folder_var, self.search_all_folders_var,
            self.excluded_folders, self.exclude_mode_var
        )
        self.state_manager.update_search_settings(
            self.nip_var, self.date_from_var, self.date_to_var
        )
        self.state_manager.save_current_state()

    def search_invoices(self):
        """Start the threaded search process"""
        nip = self.nip_var.get().strip()
        folder_name = self.folder_var.get().strip()
        date_from_str = self.date_from_var.get()
        date_to_str = self.date_to_var.get()
        
        # Validate inputs
        date_from = None
        date_to = None
        try:
            if date_from_str:
                date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
            if date_to_str:
                date_to = datetime.strptime(date_to_str, "%Y-%m-%d") + timedelta(days=1)
        except Exception as e:
            print(f"Błąd daty: {e}")
            messagebox.showerror("Błąd daty", f"Nieprawidłowy format daty: {str(e)}")
            return

        if not nip:
            print("Nie podano NIP do wyszukania.")
            messagebox.showwarning("Brak danych", "Wprowadź NIP.")
            return

        # Clear previous results
        self.results.clear()
        self.matched_items.clear()
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Update UI
        self.search_button.config(text="Anuluj wyszukiwanie")
        self.progress_label.config(text="Rozpoczynam wyszukiwanie...")

        # Save state
        self.save_last_state()

        # Start search in background thread
        self.email_searcher.search_manager.start_search(
            self.email_searcher.search_emails_for_nip,
            nip=nip, 
            folder_name=folder_name, 
            date_from=date_from, 
            date_to=date_to,
            search_all_folders=self.search_all_folders_var.get(),
            excluded_folders=self.excluded_folders,
            exclude_mode=self.exclude_mode_var.get(),
            folder_list=self.folder_list
        )

    def preview_pdf(self, event):
        selected = self.tree.focus()
        if not selected:
            return

        values = self.tree.item(selected, "values")
        filename = values[2]

        try:
            self.pdf_processor.preview_pdf(filename)
        except Exception as e:
            print(f"Błąd podglądu PDF: {e}")
            messagebox.showerror("Błąd podglądu", str(e))

    def save_pdf(self):
        selected = self.tree.focus()
        if not selected:
            print("Nie wybrano pliku PDF do zapisania.")
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
                print(f"Kopiuję PDF: {source_path} -> {dest_path}")
                shutil.copy(source_path, dest_path)
                messagebox.showinfo("Zapisano", f"Plik zapisano jako:\n{dest_path}")
            except Exception as e:
                print(f"Błąd zapisu PDF: {e}")
                messagebox.showerror("Błąd zapisu", str(e))

    def move_messages(self):
        target_name = self.target_folder_var.get().strip()
        if not target_name:
            print("Nie wybrano folderu docelowego do przeniesienia wiadomości.")
            messagebox.showwarning("Brak folderu docelowego", "Wybierz folder docelowy.")
            return

        try:
            target_folder = self.exchange_connection.find_folder_by_display_name(target_name)
            if target_folder is None:
                print(f"Nie znaleziono folderu docelowego: {target_name}")
                messagebox.showerror("Błąd folderu", f"Nie znaleziono folderu docelowego: {target_name}")
                return

            moved = 0
            for item in self.matched_items:
                print(f"Przenoszę wiadomość: {item.subject}")
                item.move(to_folder=target_folder)
                moved += 1

            print(f"Przeniesiono {moved} wiadomości do folderu: {target_name}")
            messagebox.showinfo("Przeniesiono", f"Przeniesiono {moved} wiadomości do folderu: {target_name}")

        except Exception as e:
            print(f"Błąd przenoszenia wiadomości: {e}")
            messagebox.showerror("Błąd przenoszenia", str(e))