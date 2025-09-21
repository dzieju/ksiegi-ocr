"""
Zakładka kryteriów wyszukiwania.
"""
import tkinter as tk
from tkinter import ttk
from gui.base_tab import BaseTab
from models import SearchCriteria


class SearchCriteriaTab(BaseTab):
    """Zakładka kryteriów wyszukiwania."""
    
    def setup_ui(self) -> None:
        """Konfiguruje interfejs użytkownika."""
        self._create_main_email_section()
        self._create_main_attachment_section()
        self._create_extraction_section()
        self._create_related_emails_section()

    def _create_main_email_section(self) -> None:
        """Tworzy sekcję kryteriów głównego emaila."""
        frame = self.create_labeled_frame("Kryteria Wyszukiwania Głównego E-maila")
        
        self.create_config_entry(frame, "Folder przeszukiwania:", "main_email_folder", 0, width=50)
        self.create_config_entry(frame, "Temat e-maila zawiera:", "main_email_subject", 1, width=50)
        self.create_config_entry(frame, "Nadawca e-maila zawiera:", "main_email_sender", 2, width=50)
        self.create_config_entry(frame, "Tylko nieprzeczytane:", "main_email_unread", 3, is_bool=True)
        self.create_config_entry(frame, "Wymagane załączniki:", "main_email_attachments", 4, is_bool=True)
        
        frame.grid_columnconfigure(1, weight=1)

    def _create_main_attachment_section(self) -> None:
        """Tworzy sekcję kryteriów głównego załącznika."""
        frame = self.create_labeled_frame("Kryteria Głównego Załącznika")
        
        self.create_config_entry(frame, "Nazwa załącznika zawiera:", "attachment_name", 0, width=50)
        self.create_config_entry(frame, "Rozszerzenie załącznika:", "attachment_extension", 1, width=50)
        
        frame.grid_columnconfigure(1, weight=1)

    def _create_extraction_section(self) -> None:
        """Tworzy sekcję ekstraktowania danych."""
        frame = self.create_labeled_frame("Ekstrakcja Danych z Głównego Załącznika")
        
        self.create_config_entry(frame, "Wzorzec Regex:", "extraction_regex", 0, width=70)
        
        # Dodaj przykład
        ttk.Label(
            frame, 
            text="Przykład: \\b(?:F/M|QN|F/)\\s*[\\w\\s\\/-]*\\d[\\w\\s\\/-]*\\b",
            font=("Segoe UI", 8),
            foreground="gray"
        ).grid(row=1, column=1, sticky="w", padx=5, pady=(0, 5))
        
        frame.grid_columnconfigure(1, weight=1)

    def _create_related_emails_section(self) -> None:
        """Tworzy sekcję powiązanych emaili."""
        frame = self.create_labeled_frame("Kryteria Wyszukiwania Powiązanych E-maili/Faktur")
        
        self.create_config_entry(frame, "Folder przeszukiwania:", "related_folder", 0, width=50)
        self.create_config_entry(frame, "Rozszerzenie pliku:", "related_extension", 1, width=50)
        
        frame.grid_columnconfigure(1, weight=1)

    def load_from_search_criteria(self, criteria: SearchCriteria) -> None:
        """
        Ładuje wartości z obiektu SearchCriteria.
        
        Args:
            criteria: Obiekt z kryteriami wyszukiwania
        """
        values = {
            "main_email_folder": criteria.main_email.folder_path,
            "main_email_subject": criteria.main_email.subject_contains,
            "main_email_sender": criteria.main_email.sender_contains,
            "main_email_unread": criteria.main_email.only_unread,
            "main_email_attachments": criteria.main_email.require_attachments,
            "attachment_name": criteria.main_attachment.name_contains,
            "attachment_extension": criteria.main_attachment.extension,
            "extraction_regex": criteria.extraction.regex_pattern,
            "related_folder": criteria.related_emails.folder_path,
            "related_extension": criteria.related_emails.file_extension
        }
        
        self.set_all_values(values)

    def save_to_search_criteria(self) -> SearchCriteria:
        """
        Tworzy obiekt SearchCriteria z wartości z GUI.
        
        Returns:
            Obiekt SearchCriteria
        """
        values = self.get_all_values()
        
        # Utwórz słownik w starym formacie dla kompatybilności
        criteria_dict = {
            "glowny_email": {
                "folder_sciezka": values.get("main_email_folder", ""),
                "temat_zawiera": values.get("main_email_subject", ""),
                "nadawca_zawiera": values.get("main_email_sender", ""),
                "tylko_nieprzeczytane": values.get("main_email_unread", True),
                "wymagane_zalaczniki": values.get("main_email_attachments", True)
            },
            "glowny_zalacznik": {
                "nazwa_zawiera": values.get("attachment_name", ""),
                "rozszerzenie": values.get("attachment_extension", "")
            },
            "ekstrakcja_z_zalacznika": {
                "wzorzec_regex": values.get("extraction_regex", "")
            },
            "powiazane_emaile_faktury": {
                "folder_sciezka": values.get("related_folder", ""),
                "rozszerzenie_pliku": values.get("related_extension", "")
            }
        }
        
        return SearchCriteria.from_dict(criteria_dict)