"""
PDF handling utilities including opening, NIP validation, and PDF processing.
"""
import os
import subprocess
import pdfplumber
import pdfminer
from tkinter import messagebox

TEMP_FOLDER = "temp_invoices"


class PDFProcessor:
    """Handles PDF file operations and content processing."""
    
    def __init__(self):
        # Ensure temp folder exists
        os.makedirs(TEMP_FOLDER, exist_ok=True)
    
    def process_pdf_attachment(self, att, item, folder_path, nip, seen_filenames, 
                             attachment_counter, search_manager):
        """Process a single PDF attachment in a worker thread"""
        if search_manager.search_cancelled:
            return None

        try:
            print(f"Załącznik: {att.name}")
            if not att.name.lower().endswith(".pdf"):
                return None

            if att.name in seen_filenames:
                return None
            seen_filenames.add(att.name)

            # Update progress
            search_manager.progress_queue.put(f"Przetwarzanie załącznika {attachment_counter}: {att.name}")

            local_path = os.path.join(TEMP_FOLDER, att.name)
            try:
                # Save attachment to local file
                with open(local_path, "wb") as f:
                    f.write(att.content)

                # Validate file size
                if not self._validate_pdf_size(local_path, att.name):
                    return None

                print(f"Otwieram PDF: {att.name}")

                # Extract text and check for NIP
                if self._check_nip_in_pdf(local_path, nip, att.name):
                    print(f"ZNALEZIONO NIP w załączniku: {att.name}")
                    return {
                        'type': 'match_found',
                        'subject': item.subject,
                        'date': item.datetime_received.date(),
                        'local_path': local_path,
                        'folder_path': folder_path,
                        'item': item
                    }
                else:
                    print(f"NIP NIE ZNALEZIONY w załączniku: {att.name}")
                    self._cleanup_file(local_path)
                    return None

            except Exception as e:
                print(f"Błąd obsługi załącznika {att.name}: {e}")
                self._cleanup_file(local_path)
                return None

        except Exception as e:
            print(f"Błąd przetwarzania załącznika {att.name}: {e}")
            return None
    
    def _validate_pdf_size(self, local_path, filename):
        """Validate PDF file size."""
        if os.path.getsize(local_path) < 100:
            print(f"Pominięto załącznik (za mały): {filename}")
            os.remove(local_path)
            return False
        return True
    
    def _check_nip_in_pdf(self, local_path, nip, filename):
        """Check if NIP exists in PDF content."""
        try:
            pdf = pdfplumber.open(local_path)
            full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            pdf.close()
            return nip in full_text
        except (pdfminer.pdfdocument.PDFPasswordIncorrect,
                pdfminer.pdfparser.PDFSyntaxError,
                pdfplumber.utils.PdfminerException,
                Exception) as ex:
            print(f"Błąd przy czytaniu PDF: {filename}, wyjątek: {ex}")
            self._cleanup_file(local_path)
            return False
    
    def _cleanup_file(self, local_path):
        """Clean up temporary PDF file."""
        try:
            if os.path.exists(local_path):
                os.remove(local_path)
        except Exception as e2:
            print(f"Błąd usuwania pliku PDF: {e2}")
    
    def preview_pdf(self, filename):
        """Open PDF file in system default viewer."""
        try:
            print(f"Otwieram PDF w podglądzie: {filename}")
            subprocess.Popen([filename], shell=True)
        except Exception as e:
            print(f"Błąd podglądu PDF: {e}")
            messagebox.showerror("Błąd podglądu", str(e))
            raise
    
    def validate_pdf_path(self, pdf_path):
        """Validate that PDF file exists and is readable."""
        if not pdf_path:
            return False
        if not os.path.exists(pdf_path):
            return False
        if not pdf_path.lower().endswith('.pdf'):
            return False
        return True
    
    def get_pdf_info(self, pdf_path):
        """Get basic information about a PDF file."""
        if not self.validate_pdf_path(pdf_path):
            return None
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return {
                    'page_count': len(pdf.pages),
                    'file_size': os.path.getsize(pdf_path),
                    'filename': os.path.basename(pdf_path)
                }
        except Exception as e:
            print(f"Błąd odczytu informacji PDF: {e}")
            return None