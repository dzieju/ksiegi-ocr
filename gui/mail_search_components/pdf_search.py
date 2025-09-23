"""
PDF search functionality with OCR support for mail search
"""
import os
import tempfile
import threading
import time
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Configuration paths for OCR (if available)
POPPLER_PATH = r"C:\poppler\Library\bin" if os.name == 'nt' else None
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe" if os.name == 'nt' else "tesseract"

if OCR_AVAILABLE and os.name == 'nt' and os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


class PDFSearchResult:
    """Represents search results from a PDF"""
    def __init__(self, query, pdf_path):
        self.query = query
        self.pdf_path = pdf_path
        self.matches = []
        self.search_method = ""
        self.error = None
        
    def add_match(self, page_number, text_snippet, context=""):
        """Add a match to the results"""
        self.matches.append({
            'page': page_number,
            'text': text_snippet,
            'context': context
        })
    
    def get_summary(self):
        """Get a summary of search results"""
        if self.error:
            return f"Błąd wyszukiwania: {self.error}"
        
        count = len(self.matches)
        if count == 0:
            return f"Fraza '{self.query}' nie została znaleziona w pliku PDF"
        
        method_info = f" ({self.search_method})"
        return f"Znaleziono {count} wystąpień frazy '{self.query}'{method_info}"


class PDFSearcher:
    """PDF search utility with text and OCR support"""
    
    def __init__(self, progress_callback=None, result_callback=None):
        self.progress_callback = progress_callback or (lambda msg: None)
        self.result_callback = result_callback or (lambda result: None)
        self.search_cancelled = False
        
    def cancel_search(self):
        """Cancel ongoing search"""
        self.search_cancelled = True
    
    def search_pdf(self, pdf_path, search_query, threaded=True):
        """
        Search for text in PDF file
        
        Args:
            pdf_path: Path to PDF file
            search_query: Text to search for
            threaded: Whether to run search in background thread
        """
        if not search_query or not search_query.strip():
            result = PDFSearchResult(search_query, pdf_path)
            result.error = "Brak frazy do wyszukania"
            self.result_callback(result)
            return
            
        if not os.path.exists(pdf_path):
            result = PDFSearchResult(search_query, pdf_path)
            result.error = "Plik PDF nie istnieje"
            self.result_callback(result)
            return
        
        if threaded:
            thread = threading.Thread(
                target=self._search_worker, 
                args=(pdf_path, search_query.strip()),
                daemon=True
            )
            thread.start()
        else:
            self._search_worker(pdf_path, search_query.strip())
    
    def _search_worker(self, pdf_path, search_query):
        """Worker method that performs the actual search"""
        result = PDFSearchResult(search_query, pdf_path)
        
        try:
            self.search_cancelled = False
            
            # First try text-based search if pdfplumber is available
            if PDFPLUMBER_AVAILABLE:
                self.progress_callback("Wyszukiwanie tekstu w PDF...")
                if self._search_text_pdf(pdf_path, search_query, result):
                    result.search_method = "wyszukiwanie tekstowe"
                    self.result_callback(result)
                    return
            
            # If text search didn't work or isn't available, try OCR
            if OCR_AVAILABLE:
                self.progress_callback("Wykonywanie OCR na pliku PDF...")
                if self._search_ocr_pdf(pdf_path, search_query, result):
                    result.search_method = "OCR"
                    self.result_callback(result)
                    return
            
            # No search method available
            result.error = "Brak dostępnych bibliotek do wyszukiwania PDF (pdfplumber/pytesseract)"
            self.result_callback(result)
            
        except Exception as e:
            result.error = f"Błąd podczas wyszukiwania: {str(e)}"
            self.result_callback(result)
    
    def _search_text_pdf(self, pdf_path, search_query, result):
        """Search using text extraction (pdfplumber)"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    if self.search_cancelled:
                        return False
                        
                    text = page.extract_text()
                    if text and search_query.lower() in text.lower():
                        # Find all occurrences in this page
                        lines = text.split('\n')
                        for line_num, line in enumerate(lines):
                            if search_query.lower() in line.lower():
                                # Create context (line before and after if available)
                                context_lines = []
                                if line_num > 0:
                                    context_lines.append(lines[line_num - 1])
                                context_lines.append(line)
                                if line_num < len(lines) - 1:
                                    context_lines.append(lines[line_num + 1])
                                
                                context = '\n'.join(context_lines)
                                result.add_match(page_num, line.strip(), context)
                        
                        self.progress_callback(f"Strona {page_num}: znaleziono wystąpienia")
                
                return len(result.matches) > 0
                
        except Exception as e:
            self.progress_callback(f"Błąd wyszukiwania tekstowego: {str(e)}")
            return False
    
    def _search_ocr_pdf(self, pdf_path, search_query, result):
        """Search using OCR (pytesseract + pdf2image)"""
        try:
            # Convert PDF to images
            self.progress_callback("Konwertowanie PDF do obrazów...")
            
            convert_kwargs = {'dpi': 300}
            if POPPLER_PATH and os.path.exists(POPPLER_PATH):
                convert_kwargs['poppler_path'] = POPPLER_PATH
            
            images = convert_from_path(pdf_path, **convert_kwargs)
            total_pages = len(images)
            
            for page_num, image in enumerate(images, 1):
                if self.search_cancelled:
                    return False
                    
                self.progress_callback(f"OCR strony {page_num}/{total_pages}...")
                
                # Perform OCR
                ocr_text = pytesseract.image_to_string(image, lang='pol+eng')
                
                if search_query.lower() in ocr_text.lower():
                    # Find all occurrences in this page
                    lines = ocr_text.split('\n')
                    for line_num, line in enumerate(lines):
                        if line.strip() and search_query.lower() in line.lower():
                            # Create context
                            context_lines = []
                            if line_num > 0 and lines[line_num - 1].strip():
                                context_lines.append(lines[line_num - 1])
                            context_lines.append(line)
                            if line_num < len(lines) - 1 and lines[line_num + 1].strip():
                                context_lines.append(lines[line_num + 1])
                            
                            context = '\n'.join(context_lines)
                            result.add_match(page_num, line.strip(), context)
            
            return len(result.matches) > 0
            
        except Exception as e:
            self.progress_callback(f"Błąd OCR: {str(e)}")
            return False