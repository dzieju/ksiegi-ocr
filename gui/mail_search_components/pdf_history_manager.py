"""
PDF search history management module
Handles tracking of previously searched PDFs and skipping logic
"""
import json
import os
import hashlib
from datetime import datetime
from tools.logger import log


class PDFHistoryManager:
    """Manages PDF search history to track and skip previously searched PDFs"""
    
    def __init__(self, history_file_path="pdf_search_history.json"):
        """
        Initialize PDF history manager
        
        Args:
            history_file_path: Path to the JSON file storing search history
        """
        self.history_file_path = history_file_path
        self.history_data = self._load_history()
        
    def _load_history(self):
        """Load history data from JSON file"""
        try:
            if os.path.exists(self.history_file_path):
                with open(self.history_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    log(f"[PDF HISTORY] Załadowano historię z {len(data.get('searched_pdfs', {}))} PDF-ami")
                    return data
            else:
                log("[PDF HISTORY] Brak pliku historii, tworzę nową historię")
                return {"searched_pdfs": {}, "skipped_pdfs": {}}
        except Exception as e:
            log(f"[PDF HISTORY] Błąd ładowania historii: {e}, tworzę nową")
            return {"searched_pdfs": {}, "skipped_pdfs": {}}
    
    def _save_history(self):
        """Save history data to JSON file"""
        try:
            with open(self.history_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
            log(f"[PDF HISTORY] Zapisano historię do {self.history_file_path}")
        except Exception as e:
            log(f"[PDF HISTORY] Błąd zapisywania historii: {e}")
    
    def _get_pdf_identifier(self, attachment_name, attachment_content):
        """
        Generate unique identifier for PDF attachment
        
        Args:
            attachment_name: Name of the PDF attachment
            attachment_content: Binary content of the PDF
            
        Returns:
            str: Unique identifier for the PDF
        """
        try:
            # Create hash of PDF content for reliable identification
            content_hash = hashlib.sha256(attachment_content).hexdigest()[:16]
            # Use both name and content hash for identification
            pdf_id = f"{attachment_name}_{content_hash}"
            return pdf_id
        except Exception as e:
            log(f"[PDF HISTORY] Błąd generowania identyfikatora PDF: {e}")
            # Fallback to just attachment name
            return attachment_name
    
    def is_pdf_already_searched(self, attachment_name, attachment_content, search_text):
        """
        Check if PDF has already been searched with this search text
        
        Args:
            attachment_name: Name of the PDF attachment
            attachment_content: Binary content of the PDF
            search_text: Text being searched for
            
        Returns:
            bool: True if PDF was already searched with this text
        """
        try:
            pdf_id = self._get_pdf_identifier(attachment_name, attachment_content)
            searched_pdfs = self.history_data.get("searched_pdfs", {})
            
            if pdf_id in searched_pdfs:
                pdf_searches = searched_pdfs[pdf_id].get("searches", {})
                search_key = search_text.lower().strip()
                
                if search_key in pdf_searches:
                    last_searched = pdf_searches[search_key].get("last_searched")
                    log(f"[PDF HISTORY] PDF {attachment_name} już przeszukany dla '{search_text}' dnia {last_searched}")
                    return True
            
            return False
        except Exception as e:
            log(f"[PDF HISTORY] Błąd sprawdzania historii PDF: {e}")
            return False  # In case of error, don't skip
    
    def mark_pdf_as_searched(self, attachment_name, attachment_content, search_text, found_matches=None, sender_email=None):
        """
        Mark PDF as searched with given search text
        
        Args:
            attachment_name: Name of the PDF attachment
            attachment_content: Binary content of the PDF
            search_text: Text that was searched for
            found_matches: List of matches found (optional)
            sender_email: Email address of the sender (optional)
        """
        try:
            pdf_id = self._get_pdf_identifier(attachment_name, attachment_content)
            searched_pdfs = self.history_data.setdefault("searched_pdfs", {})
            
            if pdf_id not in searched_pdfs:
                searched_pdfs[pdf_id] = {
                    "attachment_name": attachment_name,
                    "first_searched": datetime.now().isoformat(),
                    "sender_email": sender_email,
                    "searches": {}
                }
            else:
                # Update sender email if provided and not already set
                if sender_email and not searched_pdfs[pdf_id].get("sender_email"):
                    searched_pdfs[pdf_id]["sender_email"] = sender_email
            
            search_key = search_text.lower().strip()
            searched_pdfs[pdf_id]["searches"][search_key] = {
                "last_searched": datetime.now().isoformat(),
                "found_matches": bool(found_matches) if found_matches is not None else None,
                "match_count": len(found_matches) if found_matches else 0
            }
            
            self._save_history()
            log(f"[PDF HISTORY] Oznaczono PDF {attachment_name} jako przeszukany dla '{search_text}'")
            
        except Exception as e:
            log(f"[PDF HISTORY] Błąd oznaczania PDF jako przeszukany: {e}")
    
    def mark_pdf_as_skipped(self, attachment_name, attachment_content, search_text):
        """
        Mark PDF as skipped during search
        
        Args:
            attachment_name: Name of the PDF attachment
            attachment_content: Binary content of the PDF
            search_text: Text being searched for
        """
        try:
            pdf_id = self._get_pdf_identifier(attachment_name, attachment_content)
            skipped_pdfs = self.history_data.setdefault("skipped_pdfs", {})
            
            if pdf_id not in skipped_pdfs:
                skipped_pdfs[pdf_id] = {
                    "attachment_name": attachment_name,
                    "first_skipped": datetime.now().isoformat(),
                    "skip_count": 0
                }
            
            skipped_pdfs[pdf_id]["skip_count"] += 1
            skipped_pdfs[pdf_id]["last_skipped"] = datetime.now().isoformat()
            skipped_pdfs[pdf_id]["last_search_text"] = search_text
            
            self._save_history()
            log(f"[PDF HISTORY] Oznaczono PDF {attachment_name} jako pominięty (łącznie: {skipped_pdfs[pdf_id]['skip_count']} razy)")
            
        except Exception as e:
            log(f"[PDF HISTORY] Błąd oznaczania PDF jako pominięty: {e}")
    
    def clear_history(self):
        """Clear all search history"""
        try:
            self.history_data = {"searched_pdfs": {}, "skipped_pdfs": {}}
            self._save_history()
            log("[PDF HISTORY] Historia PDF została wyczyszczona")
            return True
        except Exception as e:
            log(f"[PDF HISTORY] Błąd czyszczenia historii: {e}")
            return False
    
    def get_history_stats(self):
        """
        Get statistics about search history
        
        Returns:
            dict: Statistics about searched and skipped PDFs
        """
        try:
            searched_count = len(self.history_data.get("searched_pdfs", {}))
            skipped_count = len(self.history_data.get("skipped_pdfs", {}))
            
            total_searches = 0
            total_skips = 0
            
            for pdf_data in self.history_data.get("searched_pdfs", {}).values():
                total_searches += len(pdf_data.get("searches", {}))
            
            for pdf_data in self.history_data.get("skipped_pdfs", {}).values():
                total_skips += pdf_data.get("skip_count", 0)
            
            return {
                "unique_searched_pdfs": searched_count,
                "unique_skipped_pdfs": skipped_count,
                "total_searches": total_searches,
                "total_skips": total_skips
            }
        except Exception as e:
            log(f"[PDF HISTORY] Błąd pobierania statystyk: {e}")
            return {"unique_searched_pdfs": 0, "unique_skipped_pdfs": 0, "total_searches": 0, "total_skips": 0}
    
    def get_history_for_display(self):
        """
        Get history data formatted for display in table
        
        Returns:
            list: List of dictionaries with keys: filename, date, sender_email
        """
        try:
            history_entries = []
            searched_pdfs = self.history_data.get("searched_pdfs", {})
            
            for pdf_data in searched_pdfs.values():
                filename = pdf_data.get("attachment_name", "Nieznany")
                first_searched = pdf_data.get("first_searched", "")
                sender_email = pdf_data.get("sender_email", "Brak danych")
                
                # Format date for display
                try:
                    if first_searched:
                        # Parse ISO format and format for display
                        dt = datetime.fromisoformat(first_searched.replace('Z', '+00:00'))
                        formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        formatted_date = "Brak danych"
                except Exception:
                    formatted_date = first_searched
                
                history_entries.append({
                    "filename": filename,
                    "date": formatted_date,
                    "sender_email": sender_email
                })
            
            # Sort by date (newest first)
            history_entries.sort(key=lambda x: x["date"], reverse=True)
            
            return history_entries
            
        except Exception as e:
            log(f"[PDF HISTORY] Błąd pobierania historii do wyświetlenia: {e}")
            return []