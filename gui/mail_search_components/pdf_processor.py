"""
PDF text extraction and search functionality for mail search
"""
import io
import os
import tempfile
from tools.logger import log

# Global variables for lazy loading
_poppler_path = None
_ocr_manager = None
_pdf_processing_initialized = False

def _initialize_pdf_processing():
    """Initialize PDF processing only when needed"""
    global _poppler_path, _pdf_processing_initialized
    
    if _pdf_processing_initialized:
        return _poppler_path
    
    log("📄 Inicjalizacja przetwarzania PDF dla wyszukiwania...")
    
    # Import poppler utilities for automatic path detection
    try:
        from tools.poppler_utils import get_poppler_path
        _poppler_path = get_poppler_path()
        if _poppler_path:
            log(f"Poppler detected at: {_poppler_path}")
        else:
            log("Warning: Poppler not detected, using fallback path")
            _poppler_path = r"C:\poppler\Library\bin"  # Fallback
    except ImportError as e:
        log(f"Failed to import poppler_utils, using fallback path: {e}")
        _poppler_path = r"C:\poppler\Library\bin"  # Fallback
    
    _pdf_processing_initialized = True
    return _poppler_path

def _get_ocr_manager():
    """Get OCR manager with lazy loading"""
    global _ocr_manager
    if _ocr_manager is None:
        try:
            from tools.ocr_engines import ocr_manager
            _ocr_manager = ocr_manager
            log("Advanced OCR engine manager available")
            return True, _ocr_manager
        except ImportError as e:
            log(f"Advanced OCR not available: {e}")
            return False, None
    return True, _ocr_manager

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    log(f"Advanced OCR engine manager not available: {e}")

# Try to import required packages, handle missing dependencies gracefully
try:
    import pytesseract
    from pdf2image import convert_from_bytes
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    HAVE_OCR = True
    log("PDF OCR dependencies available")
except ImportError as e:
    HAVE_OCR = False
    log(f"PDF OCR dependencies not available: {e}")

try:
    import pdfplumber
    HAVE_PDFPLUMBER = True
    log("pdfplumber available for text extraction")
except ImportError as e:
    HAVE_PDFPLUMBER = False
    log(f"pdfplumber not available: {e}")


class PDFProcessor:
    """Handles PDF text extraction and search operations"""
    
    def __init__(self):
        self.search_cancelled = False
    
    def cancel_search(self):
        """Cancel ongoing PDF processing"""
        self.search_cancelled = True
    
    def search_in_pdf_attachment(self, attachment, search_text, attachment_name=""):
        """
        Search for text in a PDF attachment
        
        Args:
            attachment: Email attachment object with content
            search_text: Text to search for (case-insensitive)
            attachment_name: Name of the attachment for logging
            
        Returns:
            dict: {
                'found': bool,
                'matches': list of found text snippets,
                'method': 'text_extraction' or 'ocr'
            }
        """
        if self.search_cancelled:
            return {'found': False, 'matches': [], 'method': 'cancelled'}
        
        if not attachment or not hasattr(attachment, 'content') or not attachment.content:
            return {'found': False, 'matches': [], 'method': 'no_content'}
        
        # Check if PDF processing is available
        if not HAVE_PDFPLUMBER and not HAVE_OCR:
            log("PDF search not available: missing dependencies (pdfplumber, pytesseract)")
            return {'found': False, 'matches': [], 'method': 'missing_dependencies'}
        
        search_text_lower = search_text.lower().strip()
        if not search_text_lower:
            return {'found': False, 'matches': [], 'method': 'empty_search'}
        
        log(f"Wyszukiwanie '{search_text}' w załączniku PDF: {attachment_name}")
        
        try:
            # First try text extraction (faster) if available
            if HAVE_PDFPLUMBER:
                result = self._search_with_text_extraction(attachment.content, search_text_lower, attachment_name)
                if result['found']:
                    return result
            
            # If text extraction fails or finds nothing, try OCR if available
            if HAVE_OCR and not self.search_cancelled:
                result = self._search_with_ocr(attachment.content, search_text_lower, attachment_name)
                return result
                
        except Exception as e:
            log(f"Error searching PDF {attachment_name}: {str(e)}")
            return {'found': False, 'matches': [], 'method': 'error', 'error': str(e)}
        
        return {'found': False, 'matches': [], 'method': 'not_found'}
    
    def _search_with_text_extraction(self, pdf_content, search_text_lower, attachment_name):
        """Try to extract text directly from PDF and search"""
        if not HAVE_PDFPLUMBER:
            return {'found': False, 'matches': [], 'method': 'pdfplumber_not_available'}
            
        try:
            log(f"Próba ekstrakcji tekstu z PDF: {attachment_name}")
            
            # Use pdfplumber to extract text
            with io.BytesIO(pdf_content) as pdf_stream:
                with pdfplumber.open(pdf_stream) as pdf:
                    all_text = ""
                    for page_num, page in enumerate(pdf.pages):
                        if self.search_cancelled:
                            break
                        
                        page_text = page.extract_text()
                        if page_text:
                            all_text += page_text + "\n"
                    
                    if all_text.strip():
                        # Search for the text (case-insensitive)
                        all_text_lower = all_text.lower()
                        if search_text_lower in all_text_lower:
                            matches = self._extract_matches(all_text, search_text_lower)
                            log(f"Tekst znaleziony w PDF {attachment_name} przez ekstrakcję tekstu")
                            return {'found': True, 'matches': matches, 'method': 'text_extraction'}
                        else:
                            log(f"Tekst nie znaleziony w PDF {attachment_name} przez ekstrakcję tekstu")
                    else:
                        log(f"Brak tekstu do ekstrakcji z PDF {attachment_name}")
                        
        except Exception as e:
            log(f"Error during text extraction from {attachment_name}: {str(e)}")
        
        return {'found': False, 'matches': [], 'method': 'text_extraction_failed'}
    
    def _search_with_ocr(self, pdf_content, search_text_lower, attachment_name):
        """Use OCR to extract text from PDF and search"""
        if not HAVE_OCR:
            return {'found': False, 'matches': [], 'method': 'ocr_not_available'}
            
        try:
            log(f"Próba OCR z PDF: {attachment_name}")
            
            # Convert PDF to images
            images = convert_from_bytes(pdf_content, dpi=200, poppler_path=POPPLER_PATH)
            
            all_ocr_text = ""
            
            # Use advanced OCR engine manager if available, otherwise fallback to pytesseract
            if HAVE_ADVANCED_OCR:
                try:
                    log(f"Używam zaawansowanego OCR dla PDF {attachment_name}")
                    
                    # Progress callback for OCR
                    def progress_callback(processed, total):
                        if not self.search_cancelled:
                            log(f"OCR PDF {attachment_name}: {processed + 1}/{total} stron")
                    
                    # Use batch OCR processing
                    ocr_results = ocr_manager.perform_ocr_batch(
                        images, 
                        language='pol+eng',
                        progress_callback=progress_callback
                    )
                    
                    # Combine all results
                    all_ocr_text = "\n".join(filter(None, ocr_results))
                    
                except Exception as e:
                    log(f"Błąd zaawansowanego OCR, fallback do pytesseract: {e}")
                    # Fallback to original method
                    for page_num, image in enumerate(images):
                        if self.search_cancelled:
                            break
                        
                        log(f"OCR (fallback) strona {page_num + 1}/{len(images)} z PDF {attachment_name}")
                        page_text = pytesseract.image_to_string(image, lang='pol+eng')
                        if page_text:
                            all_ocr_text += page_text + "\n"
            else:
                # Original single-threaded processing
                for page_num, image in enumerate(images):
                    if self.search_cancelled:
                        break
                    
                    log(f"OCR strona {page_num + 1}/{len(images)} z PDF {attachment_name}")
                    
                    # Perform OCR
                    page_text = pytesseract.image_to_string(image, lang='pol+eng')
                    if page_text:
                        all_ocr_text += page_text + "\n"
            
            if all_ocr_text.strip():
                # Search for the text (case-insensitive)
                all_ocr_text_lower = all_ocr_text.lower()
                if search_text_lower in all_ocr_text_lower:
                    matches = self._extract_matches(all_ocr_text, search_text_lower)
                    log(f"Tekst znaleziony w PDF {attachment_name} przez OCR")
                    return {'found': True, 'matches': matches, 'method': 'ocr'}
                else:
                    log(f"Tekst nie znaleziony w PDF {attachment_name} przez OCR")
            else:
                log(f"Brak tekstu z OCR z PDF {attachment_name}")
                
        except Exception as e:
            log(f"Error during OCR from {attachment_name}: {str(e)}")
        
        return {'found': False, 'matches': [], 'method': 'ocr_failed'}
    
    def _extract_matches(self, full_text, search_text_lower):
        """Extract text snippets around matches"""
        matches = []
        full_text_lower = full_text.lower()
        
        # Find all occurrences
        start = 0
        while True:
            pos = full_text_lower.find(search_text_lower, start)
            if pos == -1:
                break
            
            # Extract context around the match (50 chars before and after)
            context_start = max(0, pos - 50)
            context_end = min(len(full_text), pos + len(search_text_lower) + 50)
            
            context = full_text[context_start:context_end].strip()
            if context not in matches:  # Avoid duplicates
                matches.append(context)
            
            start = pos + 1
        
        return matches[:5]  # Limit to 5 matches to avoid too much data