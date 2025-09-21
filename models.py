"""
Moduł z modelami danych używanymi w aplikacji ksiegi-ocr.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class MainEmailCriteria:
    """Kryteria wyszukiwania głównego emaila."""
    folder_path: str = "Skrzynka odbiorcza/Kompensaty Quadra"
    subject_contains: str = ""
    sender_contains: str = ""
    only_unread: bool = True
    require_attachments: bool = True


@dataclass
class AttachmentCriteria:
    """Kryteria załącznika."""
    name_contains: str = "kompensata"
    extension: str = "pdf"


@dataclass
class ExtractionCriteria:
    """Kryteria ekstrakcji danych z załącznika."""
    regex_pattern: str = r'\b(?:F/M|QN|F/)\s*[\w\s\/-]*\d[\w\s\/-]*\b'


@dataclass
class RelatedEmailCriteria:
    """Kryteria wyszukiwania powiązanych emaili."""
    folder_path: str = "Skrzynka odbiorcza/Faktury"
    file_extension: str = "pdf"


@dataclass
class SearchCriteria:
    """Kompletne kryteria wyszukiwania."""
    main_email: MainEmailCriteria = field(default_factory=MainEmailCriteria)
    main_attachment: AttachmentCriteria = field(default_factory=AttachmentCriteria)
    extraction: ExtractionCriteria = field(default_factory=ExtractionCriteria)
    related_emails: RelatedEmailCriteria = field(default_factory=RelatedEmailCriteria)
    months_back_compensation: int = 8
    months_back_invoices: int = 4

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchCriteria':
        """
        Tworzy obiekt SearchCriteria z słownika.
        
        Args:
            data: Słownik z danymi
            
        Returns:
            Obiekt SearchCriteria
        """
        main_email_data = data.get("glowny_email", {})
        main_email = MainEmailCriteria(
            folder_path=main_email_data.get("folder_sciezka", "Skrzynka odbiorcza/Kompensaty Quadra"),
            subject_contains=main_email_data.get("temat_zawiera", ""),
            sender_contains=main_email_data.get("nadawca_zawiera", ""),
            only_unread=main_email_data.get("tylko_nieprzeczytane", True),
            require_attachments=main_email_data.get("wymagane_zalaczniki", True)
        )

        main_attachment_data = data.get("glowny_zalacznik", {})
        main_attachment = AttachmentCriteria(
            name_contains=main_attachment_data.get("nazwa_zawiera", "kompensata"),
            extension=main_attachment_data.get("rozszerzenie", "pdf")
        )

        extraction_data = data.get("ekstrakcja_z_zalacznika", {})
        extraction = ExtractionCriteria(
            regex_pattern=extraction_data.get("wzorzec_regex", 
                                            r'\b(?:F/M|QN|F/)\s*[\w\s\/-]*\d[\w\s\/-]*\b')
        )

        related_data = data.get("powiazane_emaile_faktury", {})
        related_emails = RelatedEmailCriteria(
            folder_path=related_data.get("folder_sciezka", "Skrzynka odbiorcza/Faktury"),
            file_extension=related_data.get("rozszerzenie_pliku", "pdf")
        )

        return cls(
            main_email=main_email,
            main_attachment=main_attachment,
            extraction=extraction,
            related_emails=related_emails,
            months_back_compensation=data.get("miesiace_wstecz_kompensaty", 8),
            months_back_invoices=data.get("miesiace_wstecz_faktury", 4)
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Konwertuje obiekt do słownika.
        
        Returns:
            Słownik z danymi
        """
        return {
            "glowny_email": {
                "folder_sciezka": self.main_email.folder_path,
                "temat_zawiera": self.main_email.subject_contains,
                "nadawca_zawiera": self.main_email.sender_contains,
                "tylko_nieprzeczytane": self.main_email.only_unread,
                "wymagane_zalaczniki": self.main_email.require_attachments
            },
            "glowny_zalacznik": {
                "nazwa_zawiera": self.main_attachment.name_contains,
                "rozszerzenie": self.main_attachment.extension
            },
            "ekstrakcja_z_zalacznika": {
                "wzorzec_regex": self.extraction.regex_pattern
            },
            "powiazane_emaile_faktury": {
                "folder_sciezka": self.related_emails.folder_path,
                "rozszerzenie_pliku": self.related_emails.file_extension
            },
            "miesiace_wstecz_kompensaty": self.months_back_compensation,
            "miesiace_wstecz_faktury": self.months_back_invoices
        }